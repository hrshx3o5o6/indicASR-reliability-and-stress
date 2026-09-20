---
type: decision
id: D-004
title: "Sandbox agent code with reqly/E2B thin clients; route tasks by compute need"
status: accepted
date: 2026-09-19
updated: 2026-09-19
---

# D-004 — Sandboxed thin clients + compute routing

## Context

A future Ralph loop ([[INFRA-NOTES]] §Ralph) must run agent-written verification
code repeatedly without trusting it on the host. reqly (`reqly/`) provides an
ephemeral microVM sandbox (managed/E2B) with create → exec → files → destroy, and an
MCP server exposing the same verbs. Its mock provider cannot execute real commands;
only the E2B managed path can. [[D-003-model-as-service|D-003]] moves model compute
out of the sandbox.

## Decision

- **Default sandbox:** reqly with `SANDBOX_PROVIDER=managed`, `MANAGED_PROVIDER=e2b`,
  `E2B_API_KEY` set. Mock is only for plumbing tests.
- **Every Ralph task is tagged `compute: none | model`.**
  - `none` (majority): runs entirely in the sandbox against cached
    `data/challenge/results/*.jsonl` (OI-WER re-scoring, stats, annotations,
    report/table generation, lockfile, checksums).
  - `model`: sandbox calls the [[D-003-model-as-service|D-003]] service; weights
    never enter the sandbox.
- **State never lives in the sandbox.** Repo + manifests + summaries via git /
  object store; sandbox clones, runs one task, emits a receipt, is destroyed.
- **Receipts:** every pass records `{task_id, claim, command, git_sha, exit,
  status, artifact}` in the style of reqly's own `docs/validation/runs.jsonl`.
- **Secrets:** `HF_TOKEN` and weights stay in the service; do not pass secrets via
  `reqly_exec` (they land in execution records/logs).

## Consequences

- + Isolates the actual risk surface — agent-generated code — at ~1 GB cost.
- + Cache-first means most claims are re-verifiable without any model compute.
- + One receipt format for both local and sandboxed passes.
- − Sandbox 1 MiB output cap → write results to files, read selectively; batch
  commands to avoid ~1 s/file-API roundtrips.
- − 60-min TTL → long experiments must be chunked/resumable.
- − reqly/E2B limits are advisory on the managed path (E2B owns resources and
  isolation; reqly's own policy is not enforced through it). Treat reqly as an
  internal loop driver, not a public security boundary.
- − No persistent volume → weights must not be needed in-sandbox; templates can be
  baked for compute-light toolchains only.

Related: [[D-003-model-as-service]] · [[DEPLOYMENT]] · [[INFRA-NOTES]]
