import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


async def main():
    # Setup InMemoryRunner for testing the workflow locally
    runner = InMemoryRunner(app=app)

    test_queries = [
        "What are your shipping rates to France?",
        "Can you help me track package #12345?",
        "What is the capital of France?",
        "Do you have a physical office in Paris?",
        "How do I request a return or refund for my order?",
    ]

    for query in test_queries:
        print("\n==========================================")
        print(f"USER QUERY: {query}")
        print("==========================================")

        session = await runner.session_service.create_session(
            app_name=app.name, user_id="test_user"
        )

        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            ),
        ):
            # Print content streaming (role='model' content)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)

            # Print final node output
            if event.output is not None:
                # If it's a dict/model output (like the classifier node output), print it formatted
                print(f"\n[Node Output]: {event.output}")

        # Respect rate limits between runs
        await asyncio.sleep(4)


if __name__ == "__main__":
    asyncio.run(main())
