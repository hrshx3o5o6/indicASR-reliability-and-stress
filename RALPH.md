# RALPH.md — orient contract for one stateless pass

> The outer loop (`scripts/ralph.sh`) invokes a **fresh agent** with this file and a
> single task. You have **no memory of previous passes**. Everything you need is on
> disk. Do exactly one task, prove it, stop.

## Boot sequence (every pass)

1. Read `.ralph/state.json` — loop status, `sandbox.asr_url`, last receipt.
2. Read `.ralph/tasks.json` — the task you were given is the one in `current_task` /
   passed as the only task; do **not** pick a different one.
3. Read `REPORT.md` §7 (claim ledger) and `docs/REPRODUCE.md` — the pass must move a
   named claim or repro gap forward.
4. Read `40-pipeline/INFRA-NOTES.md` for known blockers (P-1…P-16).

## Rules

- **One task per pass.** Do not start other tasks, do not refactor unrelated code.
- **The receipt is the truth.** Before you finish, the task's `receipt` command MUST
  exit 0 and produce the stated evidence. If you cannot make it pass, leave the task
  in a truthful failed/blocked state — do not fake it.
- **Evidence over narrative.** Never claim success without running the command.
- **No invented data.** If a number is needed and not measured, write `TODO`.
- **Scope discipline.** Prefer the smallest change that makes the receipt pass.
- **Secrets.** Never write `HF_TOKEN` or any credential into a tracked file or into a
  sandbox command. Weights stay in the ASR service ([[D-003-model-as-service]]).
- **Write normal prose** in report/docs; do not use caveman shorthand in committed
  documentation.
- **Update the vault when a claim changes.** New empirical claim → `F-###`; consequential
  choice → `D-###`; bump `updated:` frontmatter on every edited note.

## Compute routing

- `compute: none` → work on cached `data/challenge/results/*.jsonl`; no model needed.
- `compute: model` → the ASR service must be reachable; use `sandbox.asr_url` via
  `code/asr_client.py`. If `asr_url` is unset, mark the task `blocked` and stop.
- Risky/agent-written code may run in the reqly sandbox via `scripts/ralph_sandbox.py`.
  Model weights and secrets never enter the sandbox.

## Sandbox usage — reqly MCP tools (prefer for `exec: sandbox` tasks)

opencode has the **reqly** MCP server available ([[D-005-reqly-mcp-partial-sandbox]]):

| Tool | Use |
| --- | --- |
| `reqly_create_sandbox` | start an ephemeral E2B sandbox (`template: "python"`) |
| `reqly_exec` | run a command in it (`{sandbox_id, command}`) |
| `reqly_write_file` / `reqly_read_file` / `reqly_list_files` | move artifacts |
| `reqly_destroy_sandbox` | tear it down |

**Rule for `exec: sandbox` tasks:** do the risky/experimental execution through
these reqly tools, and prefer running the task's **receipt** inside the sandbox
(create → upload inputs → exec receipt → read outputs → destroy) so the proof
originates in isolation. For `exec: local` tasks, run normally on the host.

**Important limitation — read this before assuming isolation.** Adding the reqly
MCP server gives opencode *sandbox tools*; it does **not** confine opencode's
built-in `bash`/`edit`/`read` tools, which still run on the **host**. So this is
partial, tool-level sandboxing: use reqly deliberately. Do not treat the session
as a security boundary.

Requirements: reqly running on `localhost:3100` with `SANDBOX_PROVIDER=managed`
and `E2B_API_KEY` set. Fallback CLI helper:

```bash
python3 scripts/ralph_sandbox.py --command "<cmd>"          # exec in a fresh E2B sandbox
python3 scripts/ralph_sandbox.py --command "<cmd>" --keep   # inspect, destroy manually
```

## Finish protocol

The outer loop runs your task's `receipt` for you and updates state/ledger — you do
**not** edit `.ralph/state.json` or `.ralph/tasks.json`. Just do the work, then stop.
If the task is open-ended, leave the artifact and a short note in the task's expected
output path so the receipt can check it.

## After the loop

The loop stops when: no pending tasks, `RALPH_MAX_PASSES` reached, `.ralph/STOP`
exists, or 3 consecutive receipts fail. Failed tasks stay `failed` for human review.
