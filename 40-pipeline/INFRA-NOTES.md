---
type: pipeline
title: "Infrastructure notes — problems encountered and the Ralph loop"
status: active
updated: 2026-09-20
---

# INFRA-NOTES — environment, blockers, and the sandboxed research loop

> Living log of **current problems encountered** while building the verification
> infrastructure, plus the **sandboxed Ralph-loop** design. Companion to
> [[DEPLOYMENT]] and decisions [[D-003-model-as-service]], [[D-004-sandboxed-thin-clients]].
> Add an entry every time a new environment blocker or workaround appears.

## A. Current problems encountered

| # | Problem | Impact | Workaround / plan | Status |
| --- | --- | --- | --- | --- |
| P-1 | Core/Flex are 4.6 GB each; wrapper defaults **fp32 on non-CUDA** | Cannot fit sandbox RAM/disk | Model-as-a-service ([[D-003-model-as-service]]) | open |
| P-2 | Sandbox fixed **2 vCPU / 4 GiB / 10 GiB / 60-min TTL**, no GPU, no volume | Heavy inference infeasible in-sandbox | Thin clients + cache-first; GPU tier later | open |
| P-3 | Core + Flex = 9.2 GB > 10 GiB disk | Even one sandbox can't hold both | Per-experiment, no in-sandbox weights | open |
| P-4 | Sandbox **1 MiB output cap**; file API ~1 s/call | Streaming logs unusable | Write artifacts to files; batch commands | open |
| P-5 | reqly blocks loopback/private/metadata ranges | Model cannot be `localhost` | Public tunnel (M5) or hosted service | mitigated (A) |
| P-6 | No secret injection into sandbox | `HF_TOKEN` would leak into exec logs | Keep secrets in service; URL only in sandbox | mitigated |
| P-7 | Managed/E2B path owns isolation; reqly policy not enforced | reqly is not a hostile-tenant boundary | Trusted internal use only | accepted |
| P-8 | Mock provider cannot execute real commands | Local plumbing works, real runs don't | Use E2B managed for real passes | known |
| P-9 | Model weight download stalls (flaky DNS/LFS CDN) | Multi-hour downloads | `scripts/parallel_download.sh` resumable range fetch | mitigated |
| P-10 | EXP-D is heavy (~3074 s / 80 rows × 3 modes) | Exceeds 60-min sandbox TTL | Chunk; or run inference in service | open |
| P-11 | ~~EXP-D annotation-count discrepancy~~ | Publication blocker | **Closed 2026-09-20** — not a conflict, two different denominators; see `REPORT.md` §5.4 | closed |
| P-12 | Vendor repos changed **2026-09-15**; vendored snapshot `4d29eeb7a099` predates them | Stale code-level claims | Re-vendor + pin both revisions | open |
| P-13 | ~~Whitespace WER, not OI-WER~~ | Limits fairness/semantic claims | **Partially closed 2026-09-20** — `code/metrics/oi_wer.py` (D-006), EXP-A re-scored (`REPORT.md` §5.7). Human-verify 19 rows still open | open (semantic verification remains) |
| P-14 | Dependencies unpinned; artifacts live on SSD not git; no single repro entry point | Not independently reproducible | `docs/REPRODUCE.md` §12; bootstrap/OI-WER artifacts now committed under `code/results/` | open |
| P-15 | 2 MB freebuff transcript; context continuity across sessions | Reorientation cost | Digest into `docs/PRIOR-CONTEXT.md`; Ralph state file | open |
| P-16 | E2B free tier ignores custom vCPU/RAM; no GPU | Cannot scale in-sandbox | Paid tier or GPU provider when needed | known |
| P-17 | Ralph loop ran 10 passes (2026-09-20), **zero completed** — every `compute:none` pass crashed on an opencode agent error (`content[].thinking must be passed back to the API`) before doing work; `set -e` in `scripts/ralph_pass.sh` then aborted before recording the failure, leaving tasks stuck `in_progress`/`"started"` instead of `failed` | Loop looked idle-but-fine when it had silently done nothing for 10 commits | Tier 0–2 claim-strengthening done manually instead (this pass); `ralph_pass.sh`'s `set -e` + failing-receipt-in-`$(...)` interaction still needs a real fix before re-enabling the loop | open |
| P-18 | **EXP-E `[0]`-string-indexing bug** — `run_exp_e.py` took `asr.transcribe(...)[0]` without `return_lid=True`, so `transcribe()`'s bare-string return got indexed by character; every EXP-E transcript was truncated to ~1 char, producing a false near-total-failure WER that had been published as a verified finding (F-003) | A wrong, confidently-stated finding nearly reached the report as fact | **Fixed 2026-09-20** in `run_exp_e.py`; F-003 and `EXP-E-diarization.md` retracted pending rerun | fixed, rerun pending live ASR service |

## B. The sandboxed Ralph loop (design)

**Idea.** An outer loop repeatedly spawns a **fresh, stateless agent** with a fixed
orient prompt. Each pass: read state → do one task → emit a receipt → exit. All
memory lives in files; context never accumulates. `while :; do agent -p "$(cat RALPH.md)"; done`.

**Why.** Claim-strengthening is many independent, verifiable units; each wants a
clean context and a proof.

**Components (to build):**

| Component | Purpose | Location |
| --- | --- | --- |
| Orient prompt | Fixed per-pass instructions; read state → pick task → act → receipt | `RALPH.md` |
| State file | Task queue + status + last receipt + iteration count | `.ralph/state.json` |
| Task queue | One strengthening unit per pass, each with a **receipt command** | `.ralph/tasks.json` |
| Router | Tag each task `compute: none | model`; send to sandbox/service | `scripts/ralph_step.sh` |
| Sandbox | reqly/E2B thin client ([[D-004-sandboxed-thin-clients]]) + reqly **MCP tools** in opencode ([[D-005-reqly-mcp-partial-sandbox]]) | `reqly/`, `scripts/ralph_sandbox.py` |
| Ledger | Append-only receipt log (mirror reqly's) | `docs/validation/runs.jsonl` (project) |

**Pass lifecycle:** `reqly_create_sandbox` → clone repo @ pinned SHA → run one task
(calls service if `compute: model`) → capture receipt → push artifacts → destroy.

**Task map (from `REPORT.md` §7/§9):**
`lockfile`, `commit-artifacts`, `fix-expd-annotation-count`, `oiver`,
`exp-f-real-noise`, `neural-diarizer`, `second-baseline`, `bootstrap-cis`,
`expand-suite`, `human-verify-semantics`.

**Guardrails:** human gate on claim/publication changes; idempotent tasks; one
writer per file per pass; max passes + budget cap; receipts are **commands**, not
narratives; pin the env before looping so receipts don't drift.

**Open decisions:** driver (MCP vs SDK vs hybrid); sequential vs parallel passes;
state tracked in git or not; human-gate granularity (per task vs per claim).

**Status (2026-09-19):** reqly is registered as a **local opencode MCP server**
(`~/.config/opencode/opencode.json` → `mcp.reqly`), so opencode now has
`reqly_create_sandbox` / `reqly_exec` / `reqly_write_file` / `reqly_read_file` /
`reqly_list_files` / `reqly_destroy_sandbox`. This is **partial, tool-level**
sandboxing — built-in `bash`/`edit` still run on the host ([[D-005-reqly-mcp-partial-sandbox]]).
Restart opencode to load the new server. Full in-sandbox execution remains a
future pass. Handshake verified: `tools/list` returns all six tools.

## C. What is sandboxable today (cache-first)

Against cached `data/challenge/results/*.jsonl` — no model compute:
OI-WER re-scoring, bootstrap CIs, significance tests, annotation reconciliation,
semantic re-scoring, selective-prediction/calibration re-analysis, EXP-F data prep,
report/table generation, lockfile/checksum checks.

Model-compute passes (via [[D-003-model-as-service|D-003]]): `exp-f-real-noise`,
`neural-diarizer`, any full-suite rerun.

Related: [[DEPLOYMENT]] · [[roadmap]] · [[EXPERIMENT-OBSERVATIONS]] · [[D-003-model-as-service]] · [[D-004-sandboxed-thin-clients]]
