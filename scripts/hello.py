"""Block 1: send "hello" to Claude, print the reply and token counts.

Run:  python scripts/hello.py
Done when: the reply AND input/output token counts print.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables (ANTHROPIC_API_KEY, CLAUDE_MODEL)
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

# TODO 1: import anthropic and create a client.
#         No args needed: it reads ANTHROPIC_API_KEY from the environment.

# TODO 2: call client.messages.create(...) with
#         model=MODEL, max_tokens=1024,
#         messages=[ one dict: role "user", content "hello" ]

# TODO 3: response.content is a LIST of blocks. Loop over it and
#         print block.text only when block.type == "text"
#         (there may be a "thinking" block first).

# TODO 4: print response.usage.input_tokens and response.usage.output_tokens
