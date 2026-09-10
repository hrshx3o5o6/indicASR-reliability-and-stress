---
type: experiment
id: EXP-A
title: "Baseline census: where does Core fail, and which signals predict it?"
status: planned
phase: day-1
depends: []
updated: 2026-09-10
---

# EXP-A — Baseline census

**Question.** Where does [[indic-transcribe-core]] actually fail — under which conditions, in which languages — and which *observable* signals co-occur with failure? This is the foundation experiment; everything else consumes its outputs.

## Design

| | |
| --- | --- |
| System | Core, unmodified, as released ([[D-002-core-as-baseline|D-002]]) |
| Data | Challenge suite v0: 50–100 samples, 8 languages, structured conditions ([[challenge-suite-spec]]) |
| Conditions | full condition matrix incl. combinations ([[THESIS]] P4) |
| Languages | ta, hi, te, ml, kn, bho, mai, ur |

## Runs per sample (fixed protocol)

1. `transcribe(lang=truth, return_lid=True)` → transcript + LID w/ `source: explicit` (disagreement signal)
2. `transcribe(return_lid=True)` auto-LID → top-1/top-k LID behavior
3. `identify()` raw (NO `allowed_langs` — silent reassignment would fake accuracy, [[lid-reliability]])
4. LID probe on Hindi-belt: `identify(allowed_langs={hi,bho,mai,ur})` → designed absorption probe ([[F-001-hindi-belt-lid-absorption|F-001]])
5. If metadata available (token probs, timestamps): dump everything, version the extractor

## Metrics

[[oi-wer]] + plain WER · [[entity-accuracy]] · [[critical-value-accuracy]] · [[lid-reliability]] (top-1/2/3, confusion, margin, entropy) · stratified **language × condition** · interaction heatmap (non-additivity test = P4)

## Outputs

- `code/results/exp-a/*.json` per-sample records (schema: [[annotation-schema]])
- Heatmaps: OI-WER by language × condition; LID confusion matrix; interaction grid
- Findings `F-###` for: absorption rate, worst interactions, metadata availability verdicts
- Labeled failure dataset → training input for [[EXP-B]]

## Falsifiable targets

P1 variance, P2 critical-value weighting, P3 absorption, P4 non-additive interactions — each gets confirmed/confirmed-with-effect-size/killed.

## Ablations

None (baseline). Reproducibility: pinned model revision, pinned extractor versions, seeds logged.
