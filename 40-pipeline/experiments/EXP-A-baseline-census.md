---
type: experiment
id: EXP-A
title: "Baseline census: where does Core fail, and which signals predict it?"
status: done
phase: results
depends: []
updated: 2026-09-14
---

# EXP-A — Baseline census

> Live observations and cross-experiment takeaways: [[EXPERIMENT-OBSERVATIONS]].

**Question.** Where does [[indic-transcribe-core]] actually fail — under which conditions, in which languages — and which *observable* signals co-occur with failure? This is the foundation experiment; everything else consumes its outputs.

## Design

| | |
| --- | --- |
| System | Core, unmodified, as released ([[D-002-core-as-baseline|D-002]]) |
| Data | Challenge suite v0: 50–100 samples, 8 languages, structured conditions ([[challenge-suite-spec]]) |
| Conditions | full condition matrix incl. combinations ([[THESIS]] P4) |
| Languages | ta, hi, te, ml, kn, bho, mai, ur |

## Setup checkpoint (2026-09-13)

- Checkpoint revision `4d29eeb7a0990de4a8febf9a4d5a9c5c61134a0d` downloaded and SHA-256 verified against the vendor hash.
- Local loader assembled at `code/data/model/` from the 4.6 GB checkpoint plus the vendor's tokenizer, feature extractor, and model modules.
- `IndicTranscribe.from_pretrained(..., device="cpu")` loads successfully.
- One-second synthetic-audio decode succeeds and returns transcript text plus ranked LID metadata (`return_lid=True`).
- Smoke decode on silence produced `ठीक है`; this is only an API-path check, not an accuracy result.
- `code/run_baseline.py` is available for canonical JSONL manifests and emits explicit-language, auto-LID, and raw `identify()` results to `code/results/exp-a/results.jsonl`.
- End-to-end runner smoke test passes on a temporary WAV; the synthetic output is not included as an experiment result.

## Current checkpoint (2026-09-14)

- Working storage migrated to `/Volumes/Harshas ssd/Harshas Mac/work/bodhanai-asr-research`.
- `code/data` and `code/.venv` are compatibility symlinks to the SSD; model loading and the 5-test suite still pass after migration.
- **Experiment phase:** baseline run and analysis complete for the EXP-A v0 clean-slice scope.
- The reviewed manifest is on the SSD at `data/challenge/manifests/exp-a-v0.jsonl`: 16 samples, 2 per language across all 8 target languages.
- Sources are FLEURS (`hi, ta, te, ml, kn, ur`), Rural Women Bhojpuri benchmark (`bho`), and IndicVoices Maithili (`mai`). Audio and references are real; no synthetic rows are included.
- Per-sample output is `data/challenge/results/exp-a-baseline.jsonl`; aggregate analysis is `data/challenge/results/exp-a-summary.json`.
- This closes the clean-slice pilot, not the planned 50–100-sample condition matrix. Treat the numbers below as directional and expand before publication claims.

## v1 expansion checkpoint (2026-09-14)

- Expanded manifest: `data/challenge/manifests/exp-a-v1-80.jsonl` on the SSD.
- Stratification: 80 samples total, exactly 10 per target language; 32 real clean samples, 24 paired deterministic background-noise variants, and 24 paired telephone-bandwidth variants.
- Synthetic variants preserve the clean reference, `pair_id`, `clean_twin`, source provenance, and degradation chain. They are flagged `synthetic: true` and are not mixed with clean-only claims.
- Core rerun completed successfully for all 80 samples; EXP-B was refit from this result file.

## Results (EXP-A v1, 2026-09-14)

| Metric | Result |
| --- | ---: |
| Samples / successful runs | 80 / 80 |
| Mean whitespace-token WER | 22.0% |
| Exact transcript match | 3.75% |
| Auto-LID top-1 accuracy | 87.5% (70/80) |
| Explicit-vs-auto LID agreement | 87.5% (70/80) |
| Samples with Core warnings | 50.0% |

Per-condition mean WER: `clean` 21.2% (32), `background_noise` 23.2% (24), `telephone` 22.0% (24). Per-language mean WER: `te` 14.8%, `hi` 14.0%, `bho` 14.1%, `mai` 23.4%, `kn` 24.3%, `ta` 22.4%, `ur` 29.0%, `ml` 34.1%.

The expanded run confirms the Bhojpuri Hindi-belt LID issue: Bhojpuri auto-LID was wrong for all 10 Bhojpuri rows, while the other seven languages were correct in this slice.

The noise and telephone variants are paired synthetic degradations, not independent natural recordings. Their similar aggregate WERs are a measurement result for this particular degradation chain, not evidence that real-world noise has no effect.

Outputs: `data/challenge/results/exp-a-v1-baseline.jsonl` and `data/challenge/results/exp-a-v1-summary.json` on the SSD.

## Results (EXP-A v0 clean slice, 2026-09-14)

| Metric | Result |
| --- | ---: |
| Samples / successful runs | 16 / 16 |
| Mean whitespace-token WER | 22.8% |
| Exact transcript match | 6.25% |
| Auto-LID top-1 accuracy | 87.5% (14/16) |
| Explicit-vs-auto LID agreement | 87.5% (14/16) |
| Samples with warnings | 50.0% |

Per-language mean WER: `te` 2.6%, `hi` 13.9%, `bho` 14.5%, `kn` 26.0%, `mai` 26.3%, `ur` 27.6%, `ta` 34.3%, `ml` 37.4%. Each language has only two samples.

## Findings and limits

- **F-001 — Hindi-belt absorption signal observed:** both Bhojpuri auto-LID predictions were wrong (`hi` and `mai`), while explicit-language decoding completed. This is a two-sample signal, not an estimate of absorption rate.
- Auto-LID was correct for all six FLEURS samples in this slice and both Maithili samples; the only failures were Bhojpuri.
- WER varies substantially by language in this slice, but language, source, speaker, and content are confounded. No causal ranking is justified.
- The current slice is clean/normal only; it does not test noise, telephone bandwidth, code mixing, entities, numbers, dates, or paired degradations.
- Next experiment input is the labeled result set for EXP-B reliability/abstention, after expanding the challenge suite and adding condition strata.

## Verified protocol constraints (from code audit @ `4d29eeb7a099`, 2026-09-10)

- Clips **≤ 30 s** target (wrapper hard-raises past `max_seconds=45`; checkpoint trains at 30 s and degrades past ~60 s). Mono 16 kHz.
- Catch `warnings` in the runner: `transcribe(lang=None)` warns when LID lands on `WEAK_LID_LANGS={bho,hi,mai,ur}` → free feature column.
- Core **does** expose `native/mixed/romanised` modes despite its card ([[indic-transcribe-core]]) → optional `--with-modes` run on a subset (3 decodes/sample) gives the P2 ITN angle inside EXP-A.
- No timestamps; token-level scores via `output_scores=True, return_dict_in_generate=True` passthrough; greedy by default.
- LID probes share the exact path as transcription LID (`lid_from_encoder_states`) — `transcribe(return_lid=True)` and `identify()` cannot disagree by construction.

## Runs per sample (fixed protocol)

1. `transcribe(lang=truth, return_lid=True)` → transcript + LID w/ `source: explicit` (disagreement signal)
2. `transcribe(return_lid=True)` auto-LID → top-1/top-k LID behavior
3. `identify()` raw (NO `allowed_langs` — silent reassignment would fake accuracy, [[lid-reliability]])
4. LID probe on Hindi-belt: `identify(allowed_langs={hi,bho,mai,ur})` → designed absorption probe ([[F-001-hindi-belt-lid-absorption|F-001]])
5. If metadata available (token probs, timestamps): dump everything, version the extractor

## Metrics

[[oi-wer]] + plain WER · [[entity-accuracy]] · [[critical-value-accuracy]] · [[lid-reliability]] (top-1/2/3, confusion, margin, entropy) · stratified **language × condition** · interaction heatmap (non-additivity test = P4)

## Outputs

- `code/results/exp-a/results.jsonl` per-sample records (schema: [[annotation-schema]])
- Heatmaps: OI-WER by language × condition; LID confusion matrix; interaction grid
- Findings `F-###` for: absorption rate, worst interactions, metadata availability verdicts
- Labeled failure dataset → training input for [[EXP-B]]

## Falsifiable targets

P1 variance, P2 critical-value weighting, P3 absorption, P4 non-additive interactions — each gets confirmed/confirmed-with-effect-size/killed.

## Ablations

None (baseline). Reproducibility: pinned model revision, pinned extractor versions, seeds logged.
