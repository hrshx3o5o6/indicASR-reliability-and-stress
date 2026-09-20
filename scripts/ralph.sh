#!/usr/bin/env bash
# Outer Ralph loop: repeatedly spawn a fresh agent to complete one task per pass.
#
#   RALPH_AGENT_CMD="opencode run"   ./scripts/ralph.sh
#   RALPH_AGENT_CMD="claude -p"      ./scripts/ralph.sh
#   RALPH_MAX_PASSES=3               ./scripts/ralph.sh
#
# Stop conditions: no pending tasks, max passes reached, .ralph/STOP exists,
# or 3 consecutive failed receipts.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE=".ralph/state.json"
TASKS=".ralph/tasks.json"
LOCK=".ralph/loop.lock"
LOG_DIR=".ralph/logs"
mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK" 2>/dev/null; then
  echo "ralph already running (remove $LOCK if stale)"; exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

MAX="${RALPH_MAX_PASSES:-$(jq -r '.max_passes' "$STATE")}"
echo "ralph: max_passes=$MAX agent='${RALPH_AGENT_CMD:-opencode run}'"

for ((pass = 1; pass <= MAX; pass++)); do
  if [ -f .ralph/STOP ]; then echo "STOP file present — halting"; break; fi

  task=$(jq -r '[.tasks[] | select(.status == "pending")][0].id // empty' "$TASKS")
  if [ -z "$task" ]; then echo "no pending tasks — done"; break; fi

  echo "=== pass $pass / task: $task ==="
  log="$LOG_DIR/pass-$(printf '%02d' "$pass")-$task.log"

  if bash scripts/ralph_pass.sh "$task" 2>&1 | tee "$log"; then
    echo "pass $pass: receipt PASSED"
  else
    echo "pass $pass: receipt FAILED (see $log)"
  fi

  git add -A >/dev/null 2>&1 || true
  git commit -m "ralph: pass $pass — $task" >/dev/null 2>&1 \
    || echo "  (nothing to commit)"

  fails=$(jq -r '.consecutive_failures' "$STATE")
  if [ "$fails" -ge 3 ]; then echo "3 consecutive failures — halting for human review"; break; fi
done

echo "ralph loop finished after $(jq -r '.iteration' "$STATE") pass(es)"
