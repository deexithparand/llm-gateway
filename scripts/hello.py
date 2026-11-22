"""Block 1: send "hello" to the LLM, print the reply and token counts.

Run from the repo root:  python -m scripts.hello
Done when: the reply AND input/output token counts print.
"""
from dotenv import load_dotenv

load_dotenv()  # loads LLM_* settings from .env

from app.llm import LLMError, complete  # noqa: E402  (needs env loaded first)

try:
    result = complete("hello")
except LLMError as e:
    raise SystemExit(f"LLM call failed ({e.status_code}): {e}")

print(f"[{result.provider} / {result.model}] {result.text}")
print(f"tokens: input={result.input_tokens} output={result.output_tokens}", end="")
print(f" cost=${result.cost_usd}" if result.cost_usd is not None else "")
print(f"stop_reason: {result.stop_reason}")
