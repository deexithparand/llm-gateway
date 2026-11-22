"""llm-gateway HTTP API.

Run from the repo root:  uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs
"""
import logging

from dotenv import load_dotenv

load_dotenv()  # LLM_* settings from .env, before anything reads them

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.llm import LLMError, complete  # noqa: E402
from app.schemas import ChatRequest, ChatResponse, ErrorResponse, Usage  # noqa: E402

log = logging.getLogger("llm-gateway")

app = FastAPI(
    title="llm-gateway",
    version="0.3.0",
    description="Governed LLM Gateway (Layer 1): one API in front of the LLM provider.",
)

# Map upstream failures to (HTTP status -> stable error code + client-safe message).
# Upstream details are logged server-side, never returned to clients.
_UPSTREAM_ERRORS = {
    429: ("upstream_rate_limited", "The LLM provider is rate limiting the gateway. Retry shortly."),
    502: ("upstream_error", "The LLM provider returned an error."),
    503: ("upstream_unavailable", "The LLM provider could not be reached."),
}


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    log.error("LLM call failed (%s): %s", exc.status_code, exc)
    code, message = _UPSTREAM_ERRORS.get(
        exc.status_code, ("gateway_misconfigured", "The gateway is misconfigured.")
    )
    body = ErrorResponse(error={"code": code, "message": message})
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness check (for Docker / load balancers later)."""
    return {"status": "ok"}


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    responses={429: {"model": ErrorResponse}, 500: {"model": ErrorResponse},
               502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def chat(body: ChatRequest) -> ChatResponse:
    """Send the message to the configured LLM and return its reply + token usage.

    A plain `def` (not async): FastAPI runs it in a worker thread, so the
    blocking upstream call doesn't freeze the server for other requests.
    """
    result = complete(body.message)
    return ChatResponse(
        reply=result.text,
        model=result.model,
        usage=Usage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
        ),
    )
