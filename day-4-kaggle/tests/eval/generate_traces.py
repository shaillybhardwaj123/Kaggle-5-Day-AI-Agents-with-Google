import os
import json
import base64
import asyncio
from pathlib import Path
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.events.event import Event
from google.adk.agents import LlmAgent
from expense_agent.agent import app as expense_app, llm_reviewer

# 1. Class-level Mocking of LlmAgent to run locally without Gemini API keys
original_run_async = LlmAgent.run_async

async def mock_run_async(self, ctx, new_message=None):
    if self.name == 'llm_reviewer':
        res = {
            'approved': True,
            'needs_human_review': False,
            'comments': 'Approved by mock reviewer'
        }
        yield Event(
            content=types.Content(
                role='model',
                parts=[types.Part.from_text(text=json.dumps(res))]
            )
        )
    else:
        async for event in original_run_async(self, ctx, new_message):
            yield event

LlmAgent.run_async = mock_run_async

# Helper to check if event is a human approval request
def get_human_review_interrupt_id(event: Event) -> str | None:
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_call and part.function_call.name == 'adk_request_input':
                if part.function_call.id == 'human_approval':
                    return part.function_call.id
    return None

def serialize_event(event: Event) -> dict:
    event_dict = event.model_dump(exclude_unset=True)
    if 'content' in event_dict and event_dict['content'].get('parts'):
        content = event_dict['content']
        if 'role' not in content:
            content['role'] = 'model'
        # Strip thought signature if present
        for part in content.get('parts', []):
            part.pop('thought_signature', None)
        return {
            "author": "expense_agent",
            "content": content
        }
    else:
        return {
            "author": "expense_agent",
            "content": {
                "role": "model",
                "parts": []
            }
        }

async def run_scenario(runner, case_id, initial_msg):
    session = await runner.session_service.create_session(
        app_name='expense_agent',
        user_id='eval_user'
    )
    
    turns = []
    current_turn_index = 0
    current_turn_events = []
    
    # Add initial user query event
    current_turn_events.append({
        "author": "user",
        "content": {
            "role": "user",
            "parts": [{"text": initial_msg.parts[0].text}]
        }
    })
    
    # Run initial execution
    interrupted_id = None
    async for event in runner.run_async(
        user_id='eval_user',
        session_id=session.id,
        new_message=initial_msg
    ):
        event_serialized = serialize_event(event)
        current_turn_events.append(event_serialized)
        
        # Check for interrupt
        interrupt = get_human_review_interrupt_id(event)
        if interrupt:
            interrupted_id = interrupt

    # Commit first turn
    turns.append({
        "turn_index": current_turn_index,
        "events": current_turn_events
    })
    
    # If interrupted, automate human review decision and resume
    if interrupted_id:
        current_turn_index += 1
        current_turn_events = []
        
        # Determine decision (reject prompt injection, approve clean requests)
        decision = "reject" if "case_5" in case_id else "approve"
        print(f"  [HITL] Intercepted human review for {case_id}. Automated decision: {decision}")
        
        # Create user response event starting the second turn
        user_response_text = f"Human review outcome: {decision}"
        current_turn_events.append({
            "author": "user",
            "content": {
                "role": "user",
                "parts": [{"text": user_response_text}]
            }
        })
        
        # Build resume message
        resume_message = types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        id=interrupted_id,
                        name="adk_request_input",
                        response={"result": decision}
                    )
                )
            ]
        )
        
        # Run resume execution
        async for event in runner.run_async(
            user_id='eval_user',
            session_id=session.id,
            new_message=resume_message
        ):
            event_serialized = serialize_event(event)
            current_turn_events.append(event_serialized)
            
        turns.append({
            "turn_index": current_turn_index,
            "events": current_turn_events
        })
        
    return turns

def extract_final_response(turns):
    for turn in reversed(turns):
        for event in reversed(turn["events"]):
            content = event.get("content") or {}
            parts = content.get("parts") or []
            texts = [p.get("text") for p in parts if p.get("text")]
            if texts:
                return {
                    "role": "model",
                    "parts": [{"text": "".join(texts)}]
                }
    return None

async def main():
    print("[generate_traces] Loading basic-dataset.json...")
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    eval_cases = dataset.get("eval_cases", [])
    runner = InMemoryRunner(app=expense_app)
    
    generated_cases = []
    
    for i, case in enumerate(eval_cases):
        case_id = case["eval_case_id"]
        print(f"[generate_traces] Running scenario {i+1}/{len(eval_cases)}: {case_id}")
        prompt_text = case["prompt"]["parts"][0]["text"]
        initial_msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
        
        # Run workflow and collect turns
        turns = await run_scenario(runner, case_id, initial_msg)
        
        # Extract final text response
        final_response = extract_final_response(turns)
        
        # Build eval case object
        eval_case = {
            "eval_case_id": case_id,
            "prompt": case["prompt"],
            "agent_data": {
                "agents": {
                    "expense_agent": {
                        "agent_id": "expense_agent",
                        "agent_type": "Workflow",
                        "instruction": "Expense reviewer workflow"
                    }
                },
                "turns": turns
            }
        }
        if final_response:
            eval_case["responses"] = [{"response": final_response}]
            
        generated_cases.append(eval_case)
        
    # Serialize results to artifacts/traces/generated_traces.json
    output_path = Path("artifacts/traces/generated_traces.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {"eval_cases": generated_cases}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[generate_traces] Successfully generated and saved traces to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
