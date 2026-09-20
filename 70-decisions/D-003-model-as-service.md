---
type: decision
id: D-003
title: "Serve Core/Flex as a pinned HTTP service; sandboxes are thin clients"
status: accepted
date: 2026-09-19
updated: 2026-09-19
---

# D-003 — Model as a service

## Context

The Ralph loop ([[INFRA-NOTES]] §Ralph) needs to run agent-written code inside an
ephemeral sandbox. The available sandbox (reqly → E2B managed microVM) is fixed at
**2 vCPU / 4 GiB RAM / 10 GiB disk / 60-min TTL**, has **no GPU**, and no persistent
volume. Core is 1.2B; the wrapper defaults to **fp32 on non-CUDA** (~4.6 GB weights),
and recorded EXP-D took **3074 s (51 min)** on an M5. Weights therefore cannot run in
the sandbox. See [[INFRA-NOTES]] for the full constraint list.

## Options

1. **Run weights in the sandbox** — infeasible (RAM, disk, TTL, no GPU).
2. **Model-as-a-service + thin sandbox clients** ← chosen
3. **GPU-capable sandbox provider** (Modal/RunPod) as the heavy tier — deferred, see consequences.
4. **Quantize the model to fit** — accuracy drift, re-baseline cost; last resort.

## Decision

Core and Flex run as a **single long-lived, pinned HTTP inference service**
(`code/asr_service.py`) outside every sandbox. Sandboxes and local runners are
**thin clients** (`code/asr_client.py`) selected with `--asr-url`.

- Every response echoes `{revision, dtype, decoding}` so a pass can prove exactly
  which model produced it.
- Interim host: M5 (MPS, fp32, matching recorded baselines) exposed via a
  `cloudflared` tunnel (option A, 2026-09-19). Later: serverless GPU.
- Weights and `HF_TOKEN` stay in the service. Sandboxes receive only the URL.

## Consequences

- + Kills all four sandbox blockers (RAM, disk, TTL, GPU) — sandbox becomes ~1 GB.
- + Improves reproducibility: one pinned service, many ephemeral callers
  (addresses `REPORT.md` §9 / `docs/REPRODUCE.md` §12).
- + Mirrors [[PIPELINE]]: ASR is a stage, not the whole system.
- + Enables Pattern-3 cache-first tasks (most claims re-score from cached JSONL
  with zero model compute).
- − Adds a network dependency; a pass fails if the tunnel/service is down
  (mitigation: receipts record service unreachability as a distinct failure).
- − Interim tunnel URL is not stable across restarts (mitigation: named tunnel or
  record URL in `.ralph/state.json`).
- − The service is a trust boundary: sandboxed code may be hostile, the service is
  not isolated from it. Acceptable — inference is a pure function and weights are
  read-only; revisit if untrusted third-party checkpoints are ever served.
- − reqly blocks loopback/private ranges, so the service must be reachable on a
  **public hostname** (tunnel or cloud), never `localhost:8000`.

Related: [[D-004-sandboxed-thin-clients]] · [[DEPLOYMENT]] · [[INFRA-NOTES]]
