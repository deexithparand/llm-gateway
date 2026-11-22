"""Request/response shapes of the gateway's public API (provider-neutral)."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=8000,
        description="The user's prompt",
        examples=["hello"],
    )


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: float | None = Field(default=None, description="Only if the upstream reports it")


class ChatResponse(BaseModel):
    reply: str = Field(description="The model's reply")
    model: str = Field(description="Model that produced the reply")
    usage: Usage


class ErrorDetail(BaseModel):
    code: str = Field(examples=["upstream_unavailable"])
    message: str


class ErrorResponse(BaseModel):
    """One error shape for every gateway-generated error."""
    error: ErrorDetail
