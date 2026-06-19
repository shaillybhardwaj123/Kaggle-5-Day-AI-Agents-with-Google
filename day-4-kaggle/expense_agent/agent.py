# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import json
import base64
import logging
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.workflow import Workflow, START, node
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import google.auth

# Configure standard logger
logger = logging.getLogger("expense-workflow.agent")

# Setup local credentials fallback
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except Exception:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# Pydantic models
class Expense(BaseModel):
    amount: float
    submitter: str
    category: str
    description: str
    date: str

class WorkflowState(BaseModel):
    original_expense: Optional[dict] = None
    cleaned_expense: Optional[dict] = None
    redacted_categories: List[str] = Field(default_factory=list)
    security_event: bool = False
    security_reason: Optional[str] = None
    review_status: str = "pending"
    review_comments: Optional[str] = None

class ReviewResult(BaseModel):
    approved: bool
    needs_human_review: bool = False
    comments: str

# ----------------- Security Functions -----------------

SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CC_REGEX = re.compile(r'\b(?:\d[- ]*?){13,19}\b')

def scrub_personal_data(description: str) -> tuple[str, List[str]]:
    redacted_categories = []
    cleaned = description
    
    # Redact SSN
    if SSN_REGEX.search(cleaned):
        cleaned = SSN_REGEX.sub("[REDACTED_SSN]", cleaned)
        redacted_categories.append("SSN")
        
    # Redact Credit Card
    def cc_replacer(match):
        val = match.group(0)
        digits_only = re.sub(r'[- ]', '', val)
        if 13 <= len(digits_only) <= 19:
            return "[REDACTED_CREDIT_CARD]"
        return val
        
    before_cc = cleaned
    cleaned = CC_REGEX.sub(cc_replacer, cleaned)
    if cleaned != before_cc:
        redacted_categories.append("Credit Card")
        
    return cleaned, redacted_categories

INJECTION_TRIGGERS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore instructions",
    "ignore the rules",
    "ignore rules",
    "bypass the rules",
    "bypass rules",
    "bypass verification",
    "bypass check",
    "force auto-approval",
    "force approval",
    "force approve",
    "auto-approve",
    "auto approve",
    "override rules",
    "override instruction",
    "override system",
    "system prompt",
    "forget all prior",
    "forget previous",
    "forget the rules",
    "you must approve",
    "automatically approve",
    "disable checks",
    "disable validation",
]

def detect_prompt_injection(description: str) -> bool:
    desc_lower = description.lower()
    for trigger in INJECTION_TRIGGERS:
        if trigger in desc_lower:
            return True
    return False

def parse_expense_input(node_input: Any) -> Expense:
    text = ""
    if isinstance(node_input, str):
        text = node_input
    elif isinstance(node_input, dict):
        return _parse_expense_from_dict(node_input)
    elif hasattr(node_input, "parts") and node_input.parts:
        text = node_input.parts[0].text
    else:
        text = str(node_input)
        
    text = text.strip()
    try:
        event = json.loads(text)
    except Exception as e:
        raise ValueError(f"Failed to parse input as JSON: {e}. Input: {text[:200]}")
        
    data = None
    if isinstance(event, dict):
        if "message" in event and isinstance(event["message"], dict):
            data = event["message"].get("data")
        elif "data" in event:
            data = event.get("data")
        else:
            data = event
            
    if isinstance(data, str):
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            data = json.loads(decoded)
        except Exception:
            try:
                data = json.loads(data)
            except Exception:
                raise ValueError(f"Failed to decode data string: {data[:200]}")
                
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict payload, got: {type(data)}")
        
    return Expense(**data)

def _parse_expense_from_dict(data: dict) -> Expense:
    if "message" in data and isinstance(data["message"], dict):
        return parse_expense_input(json.dumps(data))
    if "data" in data:
        val = data["data"]
        if isinstance(val, (dict, str)):
            return parse_expense_input(json.dumps(data))
    return Expense(**data)

# ----------------- Workflow Nodes -----------------

@node
def security_checkpoint(ctx: Context, node_input: Any) -> Event:
    logger.info("Entering security checkpoint...")
    try:
        expense = parse_expense_input(node_input)
    except Exception as e:
        logger.error(f"Input parsing failure: {e}")
        return Event(
            output={"error": f"Invalid expense format: {e}"},
            route="security_alert",
            state={"review_status": "error", "review_comments": f"Failed to parse: {e}"}
        )
        
    # Scrub personal data (SSN & Credit Card)
    cleaned_desc, redacted_cats = scrub_personal_data(expense.description)
    
    cleaned_expense = Expense(
        amount=expense.amount,
        submitter=expense.submitter,
        category=expense.category,
        description=cleaned_desc,
        date=expense.date
    )
    
    if redacted_cats:
        logger.warning(f"Redacted sensitive fields in description: {redacted_cats}")
    
    # Defend against prompt injection
    is_injection = detect_prompt_injection(expense.description)
    
    state_update = {
        "original_expense": expense.model_dump(),
        "cleaned_expense": cleaned_expense.model_dump(),
        "redacted_categories": redacted_cats,
        "security_event": is_injection,
    }
    
    if is_injection:
        logger.error("Security alert: Prompt injection attempt detected!")
        state_update["security_reason"] = "Prompt injection attempt detected in expense description."
        state_update["review_status"] = "security_flagged"
        state_update["review_comments"] = "Flagged due to prompt injection attempt. Routed directly to Human Review."
        
        return Event(
            output=cleaned_expense.model_dump(),
            route="security_alert",
            state=state_update
        )
    else:
        logger.info("Security checkpoint passed. Routing to LLM reviewer.")
        return Event(
            output=cleaned_expense.model_dump(),
            route="clean",
            state=state_update
        )

# LLM Reviewer Node
llm_reviewer = LlmAgent(
    name="llm_reviewer",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    You are an expert AI expense reviewer. Review the provided expense details (passed as a JSON-like object) and determine whether it should be approved.
    
    Review guidelines:
    1. Category 'software' is generally allowed if the amount is under $500.
    2. IDE Licenses are approved tools.
    3. Submitter must be a valid company email ending with '@company.com'.
    4. The date must be reasonable.
    
    You must evaluate the expense against these guidelines.
    Return a structured output conforming to the ReviewResult schema:
    - approved: boolean (true if the expense meets all criteria, false otherwise)
    - needs_human_review: boolean (true if the expense is borderline or you are unsure)
    - comments: string (brief explanation of your decision)
    """,
    output_schema=ReviewResult,
    output_key="review_result"
)

@node
def post_llm_routing(ctx: Context, node_input: dict) -> Event:
    approved = node_input.get("approved", False)
    needs_human = node_input.get("needs_human_review", False)
    comments = node_input.get("comments", "")
    
    cleaned_expense = ctx.state.get("cleaned_expense") or {}
    amount = cleaned_expense.get("amount", 0.0)
    if amount >= 100.0:
        needs_human = True
        approved = False
        comments = f"Expense amount ${amount:.2f} is $100 or more; forced human review."
        
    logger.info(f"LLM reviewer decision - Approved: {approved}, Needs Human: {needs_human}, Comments: {comments}")
    
    if needs_human or (not approved and not needs_human):
        return Event(
            output={"status": "needs_human_review", "comments": comments},
            route="needs_human_review",
            state={"review_status": "pending_human_review", "review_comments": comments}
        )
    else:
        return Event(
            output={"status": "approved", "comments": comments},
            route="complete",
            state={"review_status": "approved", "review_comments": comments}
        )

@node
async def human_review(ctx: Context, node_input: Any):
    cleaned_expense_dict = ctx.state.get("cleaned_expense")
    redacted_categories = ctx.state.get("redacted_categories", [])
    security_event = ctx.state.get("security_event", False)
    
    review_msg = "=== MANUAL HUMAN REVIEW REQUIRED ===\n"
    if security_event:
        review_msg += "⚠️ WARNING: Security Event (Prompt Injection) Detected!\n"
    if redacted_categories:
        review_msg += f"🔒 Redacted sensitive data: {', '.join(redacted_categories)}\n"
        
    review_msg += f"Cleaned Expense Details:\n{json.dumps(cleaned_expense_dict, indent=2)}\n\n"
    review_msg += "Do you approve this expense? (Type 'approve' or 'reject' to resume the workflow)"
    
    if not ctx.resume_inputs or "human_approval" not in ctx.resume_inputs:
        logger.info("Workflow paused waiting for manual human review.")
        yield RequestInput(
            interrupt_id="human_approval",
            message=review_msg
        )
        return
        
    reply = ctx.resume_inputs["human_approval"].strip().lower()
    if "approve" in reply:
        status = "approved"
    else:
        status = "rejected"
        
    logger.info(f"Human reviewer resumed workflow with decision: {status}")
    yield Event(
        output={"status": status, "comments": f"Human review outcome: {reply}"},
        state={"review_status": status, "review_comments": f"Human review outcome: {reply}"}
    )

@node
def final_output(ctx: Context, node_input: Any):
    review_status = ctx.state.get("review_status", "pending")
    review_comments = ctx.state.get("review_comments", "")
    redacted_categories = ctx.state.get("redacted_categories", [])
    security_event = ctx.state.get("security_event", False)
    
    result_text = f"Expense review completed.\nStatus: {review_status.upper()}\nComments: {review_comments}\n"
    if security_event:
        result_text += "⚠️ Note: Security event was logged for this transaction.\n"
    if redacted_categories:
        result_text += f"🔒 Redacted categories: {', '.join(redacted_categories)}\n"
        
    logger.info(f"Final output generated - Status: {review_status.upper()}")
    
    yield Event(
        content=types.Content(
            role='model',
            parts=[types.Part.from_text(text=result_text)]
        )
    )
    yield Event(output={
        "status": review_status,
        "comments": review_comments,
        "security_event": security_event,
        "redacted_categories": redacted_categories
    })

# ----------------- Graph Definition -----------------

root_agent = Workflow(
    name="expense_reviewer_workflow",
    edges=[
        (START, security_checkpoint),
        (
            security_checkpoint,
            {
                "security_alert": human_review,
                "clean": llm_reviewer,
            }
        ),
        (llm_reviewer, post_llm_routing),
        (
            post_llm_routing,
            {
                "needs_human_review": human_review,
                "complete": final_output,
            }
        ),
        (human_review, final_output)
    ],
    state_schema=WorkflowState
)

app = App(
    root_agent=root_agent,
    name="expense_agent",
)
