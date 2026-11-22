"""llm-gateway HTTP API.

Run from the repo root:  uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.schemas import ChatRequest, ChatResponse

app = FastAPI(
    title="llm-gateway",
    version="0.2.0",
    description="Governed LLM Gateway (Layer 1): one API in front of the LLM provider.",
)


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness check (for Docker / load balancers later)."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(body: ChatRequest) -> ChatResponse:
    """Block 2: echo the message back. Block 3 replaces this with app.llm.complete()."""
    return ChatResponse(reply=body.message)
