"""Request/response shapes of the gateway's public API (provider-neutral)."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=8000,
        description="The user's prompt",
        examples=["hello"],
    )


class ChatResponse(BaseModel):
    reply: str = Field(description="The model's reply (echo in block 2)")
