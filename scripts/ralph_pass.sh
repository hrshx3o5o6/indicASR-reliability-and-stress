#!/usr/bin/env bash
# One Ralph pass: invoke a fresh agent for a single task, then run the task's
# receipt and record the result. The agent does not edit loop state.
#
#   ./scripts/ralph_pass.sh <task_id>
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE=".ralph/state.json"
TASKS=".ralph/tasks.json"
LEDGER="docs/validation/runs.jsonl"
LOG_DIR=".ralph/logs"
mkdir -p "$LOG_DIR" docs/validation
touch "$LEDGER"

task_id="${1:?usage: ralph_pass.sh <task_id>}"
task=$(jq -c --arg id "$task_id" '.tasks[] | select(.id == $id)' "$TASKS")
if [ -z "$task" ]; then echo "unknown task: $task_id"; exit 2; fi

title=$(jq -r '.title' <<<"$task")
compute=$(jq -r '.compute' <<<"$task")
action=$(jq -r '.action' <<<"$task")
receipt=$(jq -r '.receipt' <<<"$task")
criterion=$(jq -r '.done_criterion' <<<"$task")
human=$(jq -r '.human_gate // false' <<<"$task")
asr_url=$(jq -r '.sandbox.asr_url // empty' "$STATE")

_set_status() {
  local id="$1" status="$2" note="${3:-}"
  local tmp; tmp=$(mktemp)
  jq --arg id "$id" --arg s "$status" --arg n "$note" \
    '(.tasks[] | select(.id == $id)) |= (.status = $s | .last_receipt = $n)' \
    "$TASKS" > "$tmp" && mv "$tmp" "$TASKS"
}

_mark_task() {
  local id="$1" status="$2" note="${3:-}"
  local tmp; tmp=$(mktemp)
  jq --arg id "$id" --arg s "$status" --arg n "$note" \
    '(.tasks[] | select(.id == $id)) |= (.status = $s | .attempts += 1 | .last_receipt = $n)' \
    "$TASKS" > "$tmp" && mv "$tmp" "$TASKS"
}

if [ "$human" = "true" ]; then
  echo "task '$task_id' is a HUMAN GATE — skipping automated pass"
  exit 0
fi

if [ "$compute" = "model" ] && [ -z "$asr_url" ]; then
  echo "task '$task_id' needs model compute but .ralph/state.json sandbox.asr_url is unset"
  echo "start the ASR service and record its URL first (see docs/REPRODUCE.md §15)"
  _set_status "$task_id" "blocked" "asr_url unset"
  exit 3
fi

_set_status "$task_id" "in_progress" "started"

# --- build the pass prompt -------------------------------------------------- #
prompt_file="$LOG_DIR/prompt-$task_id.md"
cat > "$prompt_file" <<EOF
# Ralph pass — task \`$task_id\`

Read \`RALPH.md\` first. Execute ONLY the task below. You have no memory of prior passes.

**Title:** $title
**Compute:** $compute  (asr_url: ${asr_url:-none})
**Sandbox recommended:** $(jq -r '.exec' <<<"$task")

## Action
$action

## Receipt (must exit 0)
\`\`\`bash
$receipt
\`\`\`

## Done criterion
$criterion

When finished, stop. The outer loop runs the receipt and updates state.
EOF

echo "--- invoking agent ---"
read -r -a AGENT <<< "${RALPH_AGENT_CMD:-opencode run}"
set +e
"${AGENT[@]}" "$(cat "$prompt_file")"
agent_exit=$?
set -e
echo "--- agent exited: $agent_exit ---"

# --- run the receipt -------------------------------------------------------- #
echo "--- receipt: $receipt"
receipt_out=$(cd "$ROOT" && eval "$receipt" 2>&1)
receipt_exit=$?
printf '%s\n' "$receipt_out" | head -c 4000

if [ "$receipt_exit" -eq 0 ]; then
  status="done"; fails=0
else
  status="failed"; fails=$(( $(jq -r '.consecutive_failures' "$STATE") + 1 ))
fi

_mark_task "$task_id" "$status" "exit=$receipt_exit"

# --- update loop state ------------------------------------------------------ #
tmp=$(mktemp)
jq --arg id "$task_id" --arg st "$status" --argjson ex "$receipt_exit" --argjson f "$fails" \
  '.step = "IDLE" | .current_task = null | .last_task = $id
   | .last_receipt = {task: $id, receipt_exit: $ex, status: $st}
   | .consecutive_failures = $f | .iteration += 1' \
  "$STATE" > "$tmp" && mv "$tmp" "$STATE"

# --- append ledger ---------------------------------------------------------- #
jq -nc \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg task "$task_id" \
  --arg claim "$(jq -r '.claim // ""' <<<"$task")" \
  --arg receipt "$receipt" \
  --argjson exit "$receipt_exit" \
  --arg status "$status" \
  --arg sha "$(git rev-parse --short HEAD 2>/dev/null || echo none)" \
  '{ts:$ts, task:$task, claim:$claim, receipt:$receipt, exit:$exit, status:$status, git_sha:$sha}' \
  >> "$LEDGER"

echo "--- task $task_id -> $status ---"
[ "$receipt_exit" -eq 0 ]
