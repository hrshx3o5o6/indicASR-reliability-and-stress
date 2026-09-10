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
