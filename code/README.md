# code/ — implementation workspace

The vault is the IDE; this folder is where the program actually lives. Every run must be traceable to an experiment note (`40-pipeline/experiments/EXP-*.md`), and every result back into one.

## Layout (v0 — filled in Day 1)

```
code/
  README.md            ← this file
  requirements.txt     ← pinned dependencies
  run_baseline.py      ← EXP-A runner: per-sample JSON records out
  features.py          ← EXP-B feature extraction (audio/LID/transcript)
  reliability.py       ← EXP-B scorer + ACCEPT/WARN/ABSTAIN engine (PIPELINE contract)
  metrics/             ← oi-wer/wer, entity, critical-value, selective-prediction
  results/             ← exp-a/*.json … (committed; audio/checkpoints NEVER)
```

## Rules

1. **No experiment without a note, no note without results.** `EXP-*.md` `status:` mirrors reality (`planned → running → done/blocked`).
2. **Pinned everything:** model revision, dependency versions, extractor versions, seeds — logged in the experiment note per run.
3. **Results are JSON** matching [[annotation-schema]] per-sample records + aggregate summaries; plots land in `results/` too and get summarized into findings (`F-###`).
4. **Big files stay out** (see `.gitignore`): audio, model checkpoints, HF cache. Store paths + hashes, not blobs.
5. Results are written even when they contradict the thesis — especially then ([[THESIS]] epistemic rules).

## Day-1 setup sequence (see [[EXP-A]])

1. Accept license gates on HF for `bodhan-ai/indic-transcribe-core` + `indic-transcribe-flex` → `export HF_TOKEN=…`
2. `pip install -r requirements.txt`
3. Smoke test: card example from [[indic-transcribe-core]]; verify every API claim marked `⚠️ to-verify`
4. Metadata probe: token probs? timestamps? `RECOMMENDED_LANGS`? → record verdicts in the model dossier
5. Build suite v0 → run EXP-A → JSONs into `results/exp-a/`

## EXP-A runner v0

The runner accepts one canonical annotation object per line. Required fields
are `sample_id`, nested `audio.path`, and `language`; `conditions`,
`provenance`, `reference`, and annotation fields are preserved. Legacy flat
`id`/`audio` records are also accepted.

```json
{"sample_id":"cs-v0-ta-001","audio":{"path":"data/audio/ta-001.wav"},"language":"ta","conditions":{"audio":["clean"],"content":["normal"]},"provenance":{"source":"fleurs","source_id":"...","synthetic":false,"contamination_risk":"unknown","speaker_id":"..."},"reference":"..."}
```

Run it from `code/`:

```bash
.venv/bin/python run_baseline.py \
  --manifest data/manifests/exp-a.jsonl \
  --model-dir data/model \
  --output results/exp-a/results.jsonl
```

Each output record contains the explicit-language transcript and LID result,
the auto-LID transcript and result, the raw `identify()` ranking, captured
warnings, run duration, and a structured error if that sample failed.

## EXP-B reliability pilot

Run the interpretable reliability scorer over EXP-A results:

```bash
python run_exp_b.py \
  --input /path/to/ssd/data/challenge/results/exp-a-baseline.jsonl \
  --audio-root /path/to/ssd/data/challenge \
  --output-dir /path/to/ssd/data/challenge/results/exp-b
```

It writes feature rows, pipeline decision records, and leave-one-out
risk–coverage metrics. Thresholds fall back to all-abstain when the measured
risk targets are not met.

Summarize a completed run:

```bash
python analyze_exp_a.py \
  --input /path/to/ssd/data/challenge/results/exp-a-baseline.jsonl \
  --output /path/to/ssd/data/challenge/results/exp-a-summary.json
```

## ASR inference service + thin client (Pattern 1, 2026-09-19)

Decision: [[D-003-model-as-service]]. Weights stay in one pinned HTTP service;
runners and sandboxes are thin clients ([[D-004-sandboxed-thin-clients]]).

```
asr_service.py   FastAPI around the vendored IndicTranscribe wrapper
                 POST /transcribe  POST /identify  POST /topk_decode  GET /health
                 echoes {revision, dtype, decoding} per response
asr_client.py    httpx client; runners accept --asr-url to call the service
                 (falls back to the local in-process loader when omitted)
```

Run the service on the machine that holds the weights (M5, MPS, fp32 to match the
recorded baselines), expose it on a public hostname (option A: `cloudflared` tunnel
— reqly blocks loopback/private ranges), then point runners at it:

```bash
.venv/bin/python asr_service.py --model-dir data/model --device mps --port 8100
# elsewhere:
.venv/bin/python run_baseline.py --manifest ... --asr-url https://<tunnel-host> ...
```

Weights and `HF_TOKEN` never enter a sandbox. Design rationale and blockers:
[[INFRA-NOTES]], [[DEPLOYMENT]].

## FLEURS seed materializer

FLEURS parquet shards and extracted audio live on the SSD. The materializer
skips absent or incomplete shards and writes canonical JSONL plus WAV files:

```bash
python scripts/materialize_fleurs_seed.py \
  --raw-dir /path/to/ssd/data/challenge/raw/fleurs \
  --output-root /path/to/ssd/data/challenge \
  --samples-per-language 2
```
