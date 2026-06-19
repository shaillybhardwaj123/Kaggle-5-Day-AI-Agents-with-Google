import os
import json
import logging
import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from google.adk.cli.fast_api import get_fast_api_app

# Configure standard logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("expense-workflow")

# Absolute path to directory of this file
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Disable prompt telemetry to cloud to run purely local and avoid GCP project constraints
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "false"

# Initialize FastAPI app with trigger sources enabled
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=False,
    trigger_sources=["pubsub"],
    otel_to_cloud=False,
)
app.title = "expense-workflow"
app.description = "API for interacting with the Ambient Expense Approval Agent"

@app.middleware("http")
async def normalize_pubsub_subscription(request: Request, call_next):
    """Normalize fully-qualified subscription paths like 'projects/.../subscriptions/NAME' to 'NAME'."""
    if request.url.path.endswith("/trigger/pubsub") and request.method == "POST":
        body = await request.body()
        try:
            data = json.loads(body)
            sub = data.get("subscription", "")
            if "/" in sub:
                short_name = sub.rsplit("/", 1)[-1]
                data["subscription"] = short_name
                # Override the cached request body
                request._body = json.dumps(data).encode()
                logger.info(f"Normalized subscription path: '{sub}' -> '{short_name}'")
        except Exception as e:
            logger.error(f"Error normalizing subscription path: {e}")
            
    return await call_next(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
