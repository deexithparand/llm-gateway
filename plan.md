# Build Plan: Governed LLM Gateway (Layer 1)

Learn-by-doing plan for Sunday, 2026-11-22. Each block gets its own branch (`feature/NN-<name>`), which is merged into `dev` through a PR.

| # | Time | Block | What we build | Done when | Branch | Status |
|---|------|-------|---------------|-----------|--------|--------|
| 1 | 14:00–14:25 | LLM API basics | Python script sends "hello" to Claude | Reply + token counts print | `feature/01-llm-basics` | ✅ Done |
| 2 | 14:25–14:55 | FastAPI basics | `POST /chat` that echoes the input | Echo works via `/docs` | `feature/02-fastapi-echo` | ✅ Done |
| 3 | 14:55–15:25 | Connect them | `/chat` calls Claude and returns the reply | First mini gateway answers | `feature/03-chat-claude` | ✅ Done |
| — | 15:25–15:45 | Lunch | | | | |
| 4 | 15:45–16:15 | Auth | Hardcoded API keys mapped to user + team | Bad key → `401` | `feature/04-auth` | ⬜ |
| 5 | 16:15–16:45 | Rate limit | Max 5 requests/min per user, in memory | 6th request → `429` | `feature/05-rate-limit` | ⬜ |
| 6 | 16:45–17:30 | Postgres usage log | `usage_log` table in Docker Postgres (user, team, tokens in/out, latency, success) | One row inserted per call | `feature/06-usage-log` | ⬜ |
| 7 | 17:30–17:55 | Token ceiling | Sum team's monthly tokens from `usage_log` | Over 2000 tokens → `429` | `feature/07-token-ceiling` | ⬜ |
| 8 | 17:55–18:10 | Prompt-injection filter | Block "ignore previous instructions" | Blocked prompt → `400` | `feature/08-injection-filter` | ⬜ |
| 9 | 18:10–18:40 | Ship it | README with diagram + one line per rule; merge `dev` → `main` | Pushed to GitHub | `feature/09-docs` | ⬜ |

**If short on time:** drop or shrink block 8 first. It's the smallest, and nothing depends on it.

## Git flow

```
main      ← stable; only merges from dev at milestones
 └─ dev   ← integration; every feature PR targets dev
     └─ feature/NN-<name>   ← one branch per block
```

```bash
git switch dev && git pull
git switch -c feature/02-fastapi-echo
# ...work, commit...
git push -u origin HEAD
gh pr create --base dev --fill
gh pr merge --squash --delete-branch
```
