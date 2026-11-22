#!/usr/bin/env bash
# Smoke test for the gateway: starts a throwaway server per scenario,
# fires real HTTP requests, checks status codes + response bodies.
#
# Usage (from the repo root):
#   bash scripts/smoke_test.sh            # all tests (makes 1 real LLM call, ~$0.001)
#   SKIP_LLM=1 bash scripts/smoke_test.sh # skip the test that calls the real LLM
#   PORT=9000 bash scripts/smoke_test.sh  # use another port (default 8001)
#
# Error scenarios work by overriding one env var for that server run only
# (load_dotenv() never overwrites variables that are already set), so your
# .env is never modified.
#
# Exit code: 0 if everything passed, 1 otherwise (CI-friendly).
# Compatible with macOS's default bash 3.2.

set -u

PORT="${PORT:-8001}"
BASE="http://127.0.0.1:${PORT}"
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  if [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python; else PYTHON=python3; fi
fi
LOG="$(mktemp -t llm-gateway-smoke.XXXXXX)"
BODY="$(mktemp -t llm-gateway-body.XXXXXX)"
PASS=0
FAIL=0
SERVER_PID=""

if [ -t 1 ]; then GREEN=$'\033[32m'; RED=$'\033[31m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else GREEN=""; RED=""; DIM=""; RESET=""; fi

cleanup() {
  stop_server
  rm -f "$LOG" "$BODY"
}
trap cleanup EXIT

# start_server [VAR=value ...]  -> starts uvicorn with optional env overrides
start_server() {
  if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "${RED}Port $PORT is already in use. Stop that process or run with PORT=<other>.${RESET}"
    exit 1
  fi
  # PYTHONUNBUFFERED: flush logs immediately so failure output shows the latest lines
  env PYTHONUNBUFFERED=1 "$@" "$PYTHON" -m uvicorn app.main:app --port "$PORT" >"$LOG" 2>&1 &
  SERVER_PID=$!
  if ! curl -s -o /dev/null --retry 20 --retry-connrefused --retry-delay 1 "$BASE/health"; then
    echo "${RED}Server did not start. Log:${RESET}"; cat "$LOG"; exit 1
  fi
}

stop_server() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
    SERVER_PID=""
  fi
}

# check "label" expected_status "expected substring in body" <curl args...>
check() {
  label=$1; expected_status=$2; expected_body=$3; shift 3
  status=$(curl -s -o "$BODY" -w '%{http_code}' "$@")
  if [ "$status" = "$expected_status" ] && grep -q -- "$expected_body" "$BODY"; then
    PASS=$((PASS + 1))
    echo "  ${GREEN}PASS${RESET} $label ${DIM}[$status]${RESET}"
  else
    FAIL=$((FAIL + 1))
    echo "  ${RED}FAIL${RESET} $label: expected $expected_status + '$expected_body', got $status"
    echo "       body: $(head -c 300 "$BODY")"
    echo "       server log (last lines):"; tail -5 "$LOG" | sed 's/^/         /'
  fi
}

PROMPT='{"message":"Reply with just the word: pong"}'

echo "== Normal config"
start_server NOOP=1
check "GET /health"                 200 '"status":"ok"'  "$BASE/health"
check "GET /docs"                   200 'swagger'        "$BASE/docs"
check "POST /chat empty message"    422 'string_too_short' -X POST "$BASE/chat" -H 'content-type: application/json' -d '{"message":""}'
check "POST /chat missing field"    422 '"missing"'        -X POST "$BASE/chat" -H 'content-type: application/json' -d '{}'
check "POST /chat invalid JSON"     422 'json_invalid'     -X POST "$BASE/chat" -H 'content-type: application/json' -d '{"message":}'
if [ "${SKIP_LLM:-0}" = "1" ]; then
  echo "  ${DIM}SKIP POST /chat real LLM call (SKIP_LLM=1)${RESET}"
else
  check "POST /chat real LLM reply"   200 '"input_tokens"'  -X POST "$BASE/chat" -H 'content-type: application/json' -d "$PROMPT"
fi
stop_server

echo "== Bad upstream key (LLM_API_KEY=not-a-real-key)"
start_server LLM_API_KEY=not-a-real-key
check "POST /chat -> upstream_error"        502 '"upstream_error"'        -X POST "$BASE/chat" -H 'content-type: application/json' -d "$PROMPT"
stop_server

echo "== Upstream unreachable (LLM_BASE_URL=http://127.0.0.1:9)"
start_server LLM_BASE_URL=http://127.0.0.1:9
check "POST /chat -> upstream_unavailable"  503 '"upstream_unavailable"'  -X POST "$BASE/chat" -H 'content-type: application/json' -d "$PROMPT"
stop_server

echo "== Unknown provider (LLM_PROVIDER=foo)"
start_server LLM_PROVIDER=foo
check "POST /chat -> gateway_misconfigured" 500 '"gateway_misconfigured"' -X POST "$BASE/chat" -H 'content-type: application/json' -d "$PROMPT"
stop_server

echo
if [ "$FAIL" -eq 0 ]; then
  echo "${GREEN}All $PASS checks passed.${RESET}"
  exit 0
else
  echo "${RED}$FAIL failed${RESET}, $PASS passed."
  exit 1
fi
