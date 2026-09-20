---
type: doc
title: "Reproducing the Indic ASR Reliability Experiments"
status: draft
version: 0.1
updated: 2026-09-19
---

# Reproducing the Indic ASR Reliability Experiments

This document is the operational counterpart to `REPORT.md`. It is written so an
independent party can rebuild the challenge suite, run every experiment, and compare
aggregate outputs against the recorded values.

> **Status: draft.** Command flags are verified against the runners in `code/`.
> Dependency versions and artifact checksums are not yet pinned (see §12).

---

## 1. What you will reproduce

| EXP | Question | Aggregate to reproduce |
|---|---|---|
| A | Baseline census | WER 22.01%, LID top-1 87.5%, bho 0/10 |
| B | Reliability features | OOF ROC-AUC 0.515, all-ABSTAIN |
| C | Top-K LID decoding | top-3 truth 79/80, oracle 22.38% |
| D | Flex native vs mixed | flex_mixed WER 33.54%, currency 0% |
| E | Diarization pilot | oracle-turn WER 99.80% (n=4) |
| F | Real-noise robustness | not run |

## 2. Hardware and OS

Recorded runs: Apple Silicon (M5, 10 cores), macOS, CPU/MPS. Core and Flex are 1.2B
and fit in unified memory in fp32. No NVIDIA GPU is required; CUDA works but is not
what the recorded numbers used. Expect EXP-D to take on the order of an hour on CPU
(recorded: 3074.7 s for 80 rows × 3 modes).

## 3. Software versions observed at run time

These are the versions the current results were produced with. They are **not yet
locked** — use them to reproduce, and pin them (see §12) before publication.

| Package | Observed |
|---|---|
| Python | 3.12.12 (via `uv`) |
| torch | 2.14.0 (MPS available) |
| transformers | 5.17.0 |
| huggingface_hub | 1.31.0 |
| numpy / pandas / scikit-learn | per environment |
| jiwer | metrics |

`code/requirements.txt` lists the intended dependencies but is unpinned.

## 4. Repository layout

```
bodhanaiASR/
  REPORT.md                 report skeleton
  docs/REPRODUCE.md         this file
  40-pipeline/experiments/  EXP-A..F protocols
  50-dataset/               suite spec + annotation schema + dataset registry
  60-findings/              F-001..004
  code/
    run_baseline.py         EXP-A
    run_exp_b.py            EXP-B
    run_exp_c.py            EXP-C
    run_exp_d.py            EXP-D
    run_exp_e.py            EXP-E
    analyze_exp_a.py        EXP-A summary
    prepare_exp_d_annotations.py / curate_exp_d_annotations.py
    score_exp_d_semantics.py
    scripts/                access, download, materialize, degrade
    vendored/core/          vendor model code @ pinned revision
    tests/test_run_baseline.py
```

Data and weights live outside git. On the recorded machine `code/data` and `code/.venv`
are symlinks into an external SSD. Recreate them as real directories or your own
symlinks; the runners accept absolute `--audio-root` / `--model-dir` paths either way.

## 5. Credentials and model access

Both models are gated. Accept the license on Hugging Face, then:

```bash
cd code
printf 'HF_TOKEN=hf_...\n' > .env     # gitignored; never commit
.venv/bin/python scripts/verify_access.py
```

`verify_access.py` prints the authenticated user, confirms both repos, and shows the
Core snapshot SHA. Record the SHA — all recorded numbers used `4d29eeb7a099`.

## 6. Environment setup

```bash
cd code
uv venv .venv --python 3.12
uv pip sync --python .venv/bin/python requirements.lock
```

`requirements.lock` (committed 2026-09-20) is a frozen `uv pip freeze` snapshot of
the environment every experiment in this report actually ran against — torch 2.14.0,
transformers 5.17.0, etc. Regenerate it after any dependency change with
`uv pip freeze --python .venv/bin/python > requirements.lock`. It does **not**
include `fastapi`/`uvicorn`/`pydantic` — those are only needed for the optional
model-as-a-service pattern (§15), never actually stood up locally; every
experiment in this report loaded the model in-process instead. Install them
separately (`uv pip install --python .venv/bin/python fastapi uvicorn pydantic`)
only if you use §15.

## 7. Model download and local loader

```bash
cd code
.venv/bin/python scripts/download_model.py          # Core weights, ~4.6 GB
```

If the network is flaky, `scripts/parallel_download.sh` fetches `model.safetensors`
as resumable parts and verifies the SHA-256 against the HF `x-linked-etag`.
Assemble the local model directory `data/model/` (checkpoint + tokenizer + feature
extractor + model modules). `IndicTranscribe.from_pretrained("data/model", device=...)`
is the loader used by the runners. Flex weights go under `data/models/indic-transcribe-flex/`.

## 8. Challenge suite construction

1. Fetch raw shards (FLEURS validation for hi/ta/te/ml/kn/ur; Bhojpuri benchmark;
   Maithili shard):

   ```bash
   bash scripts/download_fleurs_shards.sh
   bash scripts/download_single_shard.sh
   ```

2. Materialize seed manifests + WAVs:

   ```bash
   .venv/bin/python scripts/materialize_fleurs_seed.py \
     --raw-dir data/challenge/raw/fleurs \
     --output-root data/challenge --samples-per-language 4
   .venv/bin/python scripts/materialize_regional_seed.py \
     --raw-dir data/challenge/raw \
     --output-root data/challenge --samples-per-language 10
   ```

3. Build the stratified 80-row suite (adds paired noise/telephone twins):

   ```bash
   .venv/bin/python scripts/build_exp_a_stratified.py \
     --clean-manifest data/challenge/manifests/exp-a-v1-clean32.jsonl \
     --root data/challenge \
     --output-root data/challenge \
     --output data/challenge/manifests/exp-a-v1-80.jsonl
   ```

Expected: 80 rows, 10 per language, 32 clean + 24 background_noise + 24 telephone,
48 `synthetic: true`, every synthetic row carries a `clean_twin`.

## 9. Running each experiment

All commands run from `code/`. `--device` accepts `cpu` or `mps`.

```bash
# EXP-A baseline census
.venv/bin/python run_baseline.py \
  --manifest data/challenge/manifests/exp-a-v1-80.jsonl \
  --model-dir data/model --audio-root data/challenge --device cpu \
  --output data/challenge/results/exp-a-v1-baseline.jsonl
.venv/bin/python analyze_exp_a.py \
  --input data/challenge/results/exp-a-v1-baseline.jsonl \
  --output data/challenge/results/exp-a-v1-summary.json

# EXP-B reliability + abstention
.venv/bin/python run_exp_b.py \
  --input data/challenge/results/exp-a-v1-baseline.jsonl \
  --audio-root data/challenge \
  --output-dir data/challenge/results/exp-b-v1 --acceptable-wer 0.2

# EXP-C top-K LID decoding
.venv/bin/python run_exp_c.py \
  --input data/challenge/results/exp-a-v1-baseline.jsonl \
  --model-dir data/model --audio-root data/challenge \
  --output-dir data/challenge/results/exp-c --top-k 3 --device cpu

# EXP-D Flex comparison (+ annotation + semantic scoring)
.venv/bin/python run_exp_d.py \
  --manifest data/challenge/manifests/exp-a-v1-80.jsonl \
  --core-results data/challenge/results/exp-a-v1-baseline.jsonl \
  --flex-model-dir data/models/indic-transcribe-flex \
  --audio-root data/challenge \
  --output-dir data/challenge/results/exp-d --device cpu
.venv/bin/python prepare_exp_d_annotations.py \
  --manifest data/challenge/manifests/exp-a-v1-80.jsonl \
  --output data/challenge/manifests/exp-d-v1-annotations.jsonl
.venv/bin/python curate_exp_d_annotations.py \
  --manifest data/challenge/manifests/exp-d-v1-annotations.jsonl \
  --output data/challenge/manifests/exp-d-v1-annotations-curated.jsonl
.venv/bin/python score_exp_d_semantics.py \
  --annotations data/challenge/manifests/exp-d-v1-annotations-curated.jsonl \
  --results data/challenge/results/exp-d/exp-d-flex-results.jsonl \
  --output data/challenge/results/exp-d/exp-d-semantic-curated-summary.json

# EXP-E diarization pilot
.venv/bin/python run_exp_e.py \
  --hindi  data/exp-e/indic-diarbench/hindi \
  --tamil  data/exp-e/indic-diarbench/tamil \
  --model-dir data/model \
  --output-dir data/challenge/results/exp-e --device cpu
```

## 10. Expected aggregate outputs

Compare against the recorded summaries. Small numeric drift is expected across
hardware/library versions; LID and Bhojpuri results should be stable.

| Artifact | Field | Expected |
|---|---|---|
| `exp-a-v1-summary.json` | `mean_wer` | 0.2201 |
| | `auto_lid_accuracy` | 0.875 |
| | `by_language.bho.auto_lid_accuracy` | 0.0 |
| `exp-b-v1/exp-b-summary.json` | `oof_roc_auc` | 0.515 |
| | `decision_counts` | accept 0 / warn 0 / abstain 80 |
| `exp-c/exp-c-summary.json` | `truth_in_topk` | 79 |
| | `oracle_topk_wer` | 0.2238 |
| `exp-d/exp-d-summary.json` | `mean_wer.flex_mixed` | 0.3354 |
| `exp-d-semantic-curated-summary.json` | `mean_currency_recall.flex_mixed` | 0.0 |
| `exp-e-pilot-summary.json` | `mean_wer.oracle_turn_wer` | 0.9980 |

## 11. Unit tests

```bash
cd code
.venv/bin/python -m pytest tests/ -q
```

## 12. Reproducibility gaps to close before publication

1. ~~**Lock dependencies**~~ — **closed 2026-09-20**, `code/requirements.lock`.
2. **Commit summaries + checksums** — most experiment summaries now live in
   `code/results/summaries/` (2026-09-20); still missing per-sample checksums
   and the raw EXP-A/B/C/D Core per-sample JSONL (still SSD-only).
3. **Single entry point** — add `make repro` (or `scripts/repro.sh`) that chains §7–§10.
4. **Parameterize paths** — remove hardcoded SSD/symlink assumptions.
5. **Log seeds and decode config** — write `seed`, `device`, `torch`/`transformers`
   versions into every result JSON.
6. ~~**Re-vendor** vendor code after the 2026-09-15 HF update~~ — **closed
   2026-09-20**, `code/vendored/{core,flex}/REVISION`.
7. ~~**Reconcile** the EXP-D annotation count discrepancy~~ — **closed
   2026-09-20**, `REPORT.md` §5.4.

## 13. Troubleshooting

- **`from_pretrained` fails under transformers v5** — custom `auto_map` code can break
  across major versions; pin transformers to the recorded 5.17.0, or fall back to the
  last known-good 4.x line and note the change.
- **Downloads stall / DNS errors** — LFS CDN hosts are flaky on some networks; use
  `scripts/parallel_download.sh` (resumable range fetch) and re-run; it resumes.
- **MPS dtype** — the wrapper defaults to fp32 on non-CUDA devices; that is what the
  recorded numbers used. Do not switch to bf16 on MPS without re-baselining.
- **Clips over 45 s** — the wrapper raises; ensure suite clips respect the cap.

## 14. Storage

- Core + Flex weights ≈ 9.2 GB. Challenge audio ≈ 62 MB. Raw shards ≈ 2.5 GB.
  EXP-E DiarBench ≈ 2.35 GB. Results ≈ 6.3 MB. Reserve ≥ 20 GB.

## 15. Model-as-a-service mode (Pattern 1, 2026-09-19)

Heavy inference can be externalised so it never runs in a sandbox
([[D-003-model-as-service]], [[D-004-sandboxed-thin-clients]]). This is the planned
default for the sandboxed Ralph loop.

1. Start the pinned service where the weights live:

   ```bash
   cd code
   .venv/bin/python asr_service.py --model-dir data/model --device mps --port 8100
   ```

2. Expose it on a **public hostname** (reqly blocks loopback/private ranges):

   ```bash
   cloudflared tunnel --url http://localhost:8100
   ```

3. Point runners at it with `--asr-url https://<host>` instead of `--model-dir`.
   Responses echo `{revision, dtype, decoding}`; assert the revision matches
   `4d29eeb7a099` before trusting a pass.

Cache-first rule: most re-scoring (OI-WER, CIs, calibration, annotation passes,
report generation) reads existing `results/*.jsonl` and needs **no** service call.
Only reruns (`exp-f-real-noise`, `neural-diarizer`, full-suite expansions) call the
service. Never place weights or `HF_TOKEN` inside a sandbox.
