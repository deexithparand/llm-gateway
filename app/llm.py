"""Provider-neutral LLM client.

The rest of the gateway only ever sees `complete()`, `LLMResult` and `LLMError`.
Provider-specific SDK code lives in one adapter function per provider,
selected by the LLM_PROVIDER env var. Adding a provider = add an adapter
and register it in _PROVIDERS; nothing else in the gateway changes.

Config (env / .env):
    LLM_PROVIDER   which adapter to use (default: anthropic)
    LLM_API_KEY    upstream API key (e.g. KodeKey or an Anthropic key)
    LLM_BASE_URL   optional upstream URL (e.g. https://api.ai.kodekloud.com)
    LLM_MODEL      model id (e.g. claude-sonnet-5-5)
"""
import os
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    stop_reason: str | None = None
    cost_usd: float | None = None  # only some upstreams (e.g. KodeKey) report this


class LLMError(Exception):
    """Upstream LLM call failed. `status_code` lets the gateway map it to an HTTP error."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


# --- Adapters ---------------------------------------------------------------

def _anthropic_complete(prompt: str, model: str, max_tokens: int) -> LLMResult:
    import anthropic

    client = anthropic.Anthropic(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL") or None,  # None -> SDK default endpoint
    )
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.RateLimitError as e:
        raise LLMError(f"upstream rate limited: {e}", status_code=429) from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"upstream error {e.status_code}: {e}", status_code=502) from e
    except anthropic.APIConnectionError as e:
        raise LLMError(f"cannot reach upstream: {e}", status_code=503) from e

    # content is a list of typed blocks (text, thinking, ...); keep only the text.
    text = "".join(block.text for block in response.content if block.type == "text")
    return LLMResult(
        text=text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        model=response.model,
        provider="anthropic",
        stop_reason=response.stop_reason,
        cost_usd=getattr(response.usage, "cost", None),
    )


_PROVIDERS = {
    "anthropic": _anthropic_complete,
}


# --- Public API -------------------------------------------------------------

def complete(prompt: str, max_tokens: int = 1024) -> LLMResult:
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    adapter = _PROVIDERS.get(provider)
    if adapter is None:
        raise LLMError(
            f"unsupported LLM_PROVIDER={provider!r}; supported: {sorted(_PROVIDERS)}",
            status_code=500,
        )
    return adapter(prompt, os.environ["LLM_MODEL"], max_tokens)
