# llm-gateway: a Governed LLM Gateway

A small FastAPI service that sits **between your apps and Claude**. Apps call the gateway rather than the LLM provider directly. The gateway decides who is allowed in, how much they can use, and records every call.

```
 ┌────────┐   API key    ┌──────────────────────────────┐   provider key   ┌────────┐
 │  Apps  │ ───────────▶ │         llm-gateway          │ ───────────────▶ │ Claude │
 └────────┘              │ auth → rate limit → ceiling  │ ◀─────────────── └────────┘
      ▲                  │ → injection filter → log     │
      └───── reply ───── └──────────────┬───────────────┘
                                        ▼
                                  ┌──────────┐
                                  │ Postgres │  usage_log
                                  └──────────┘
```

## The pain point

Once more than one team starts using LLMs, giving each app the provider's API key directly causes problems:

| Problem | Without a gateway | With the gateway |
|---------|-------------------|------------------|
| **Key sprawl** | One shared provider key gets copied into every app and CI secret | Apps get their own gateway keys. The provider key lives in one place |
| **No attribution** | The monthly bill arrives with no breakdown by user or team | Every call is logged with user, team, tokens and latency |
| **Runaway cost** | A loop or a heavy user can burn through the budget overnight | Per-user rate limits and per-team monthly token ceilings |
| **No guardrails** | Each app re-implements (or skips) input safety checks | Prompt-injection filtering happens centrally, before the request reaches the model |
| **Vendor lock-in** | Every app is coded against one provider's SDK | Apps use one internal API, so the provider can change behind it |

Think of it as an **API gateway / reverse proxy built for LLM traffic**. It plays the same role Azure API Management or Kong plays for REST APIs, except that the unit being metered is **tokens**, not requests.

## Rules (Layer 1)

| Rule | Behaviour | Status code |
|------|-----------|-------------|
| Auth | Unknown or missing API key is rejected; known keys map to a user + team | `401` |
| Rate limit | More than 5 requests/minute per user is rejected | `429` |
| Token ceiling | Team over 2000 tokens this month is rejected | `429` |
| Injection filter | Prompts containing "ignore previous instructions" are blocked | `400` |
| Usage log | Every call writes a row: user, team, tokens in/out, latency, success | — |

## Tech stack

| Layer | Tech | Why |
|-------|------|-----|
| Language | Python 3.14 | The first-class Anthropic SDK and FastAPI ecosystem |
| LLM | Claude via the `anthropic` Python SDK | Official SDK; returns token usage on every response |
| API framework | FastAPI + Uvicorn | Async, typed request models, free interactive docs at `/docs` |
| Database | PostgreSQL (Docker) | Stores usage logs; SQL makes the monthly per-team sums simple |
| DB driver | psycopg 3 | Modern Postgres driver for Python |
| Config | `.env` + python-dotenv | Keeps secrets out of code and git |
| Containers | Docker / Docker Compose | Runs Postgres locally; the gateway itself can be containerised later |
| VCS / PRs | Git + GitHub CLI (`gh`) | `main` ← `dev` ← `feature/*` flow, with PRs raised from the terminal |

## Project layout

```
llm-gateway/
├── app/                # FastAPI gateway (blocks 2+)
├── scripts/
│   └── hello.py        # Block 1: first call to Claude
├── requirements.txt
├── .env.example        # copy to .env and fill in
├── plan.md             # build plan + progress
└── README.md
```

## Getting started

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
python scripts/hello.py
```

See [plan.md](plan.md) for the build plan.
