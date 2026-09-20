---
type: experiment
id: EXP-B
title: "Reliability model + selective prediction (abstention)"
status: done
phase: results
depends: ["EXP-A"]
updated: 2026-09-14
---

# EXP-B — Reliability model & abstention

> Live observations and cross-experiment takeaways: [[EXPERIMENT-OBSERVATIONS]].

**Question.** Can simple, interpretable features predict when Core's transcript is wrong — well enough that abstaining on low-reliability cases materially cuts error at acceptable coverage? (P5, P6)

## Features (start list — prune ruthlessly)

| Group | Features |
| --- | --- |
| LID | top-1 prob, top-2 prob, margin, entropy, #plausible langs, explicit-vs-auto `source`, metadata-label disagreement |
| Audio | SNR est., RMS, clipping ratio, silence ratio, duration, speech rate, reverb/noise indicators |
| Transcript | length, repetition/loop stats, script-consistency (output script vs expected language script), unexpected tokens, likelihood/perplexity if obtainable |
| Semantic | entity-confidence, numeric/date consistency vs. anything known |

**Label** `y`: transcript acceptable vs not (threshold defined from Exp-A [[critical-value-accuracy]] + [[entity-accuracy]] + OI-WER per sample — threshold itself is a `D-###` decision, not a vibe).

## Models (in order, interpretable first)

1. Logistic regression (read the coefficients — that IS the failure-mode analysis)
2. LightGBM (only if LR underfits; feature importance still inspectable)
3. **No neural nets in phase 1** ([[THESIS]] rule 3)

Any feature with ~zero correlation to error is **removed and recorded** as a finding — negative results are results.

## Evaluation

[[selective-prediction]] full stack: risk–coverage, AURC, AUROC, selective OI-WER @ coverage grid; calibration plot of reliability score; abstained-set difficulty check (abstained must be *harder* than answered). Per-language breakdown — a detector that only works for Hindi is a finding, not a success.

## Output

Reliability scorer + thresholds → ACCEPT / WARN / ABSTAIN decision engine emitting the [[PIPELINE]] contract JSON (incl. `uncertain_spans` v0: LID-ambiguous segments + low-consistency numeric/entity spans).

## Feeds

Uncertain/abstained cases → routed later to [[EXP-C]]. Score + reasons → demo.

## Results (EXP-B pilot, 2026-09-14)

- Input: 16 successful EXP-A outputs across 8 languages; provisional acceptable label is `WER <= 0.20`, yielding 8 acceptable and 8 unacceptable samples.
- Features: 15 interpretable LID, warning, audio, and transcript features from `code/run_exp_b.py`.
- Model: class-balanced logistic regression with standardization; leave-one-out out-of-fold scoring; no LightGBM or neural model.
- OOF ROC-AUC: `0.469`; average precision: `0.497`; Brier score: `0.349`; AURC: `0.577`.
- Risk stayed at `0.50` at 25%, 50%, 75%, and 100% coverage. No threshold met the pilot targets of ≤10% risk at ≥25% coverage or ≤25% risk at ≥50% coverage.
- The calibrated fallback is therefore `ABSTAIN` for all 16 samples. This is a valid safety result, but not a useful production policy.
- Outputs: `data/challenge/results/exp-b/exp-b-features.jsonl`, `exp-b-decisions.jsonl`, and `exp-b-summary.json` on the SSD.
- Diagnostic: this is not a threshold implementation failure. The top four OOF scores contain two unacceptable transcripts, already giving 50% risk at 25% coverage; no selected subset meets the 10%/25%-coverage or 25%/50%-coverage targets.
- A script-consistency Unicode-name bug was found and fixed before the final rerun; all current samples now report the expected script, and the aggregate metrics are unchanged.

## Threshold policy clarification

- The `≤10%` and `≤25%` risk values are provisional product-safety targets, not statistics estimated from EXP-A and not optimizer outputs.
- The `≥25%` and `≥50%` coverage values are minimum service-availability targets, also provisional.
- The scorer searches observed out-of-fold score cutoffs and accepts a cutoff only when both its risk and coverage targets are met. With this pilot, none are met, so the fallback cutoff is `1.0` and every sample abstains.
- Before the next fit, run a threshold-sensitivity grid and record a decision based on application cost: critical-value errors should have a stricter risk budget than ordinary transcription errors.

## Findings

- **F-002 — clean-slice reliability features do not generalize:** on this 16-sample, source/language-confounded pilot, the feature set is effectively non-predictive of WER. Do not interpret individual logistic coefficients as causal evidence.
- **F-003 — abstention guardrail works:** threshold selection refuses to manufacture an ACCEPT region when the measured risk target is unmet.
- The label threshold, features, and metrics require re-estimation after expanding to 50–100 samples with condition strata. EXP-B is technically complete as a pilot, not publication-grade.
- The 80-sample EXP-A v1 rerun is the calibration dataset for the next EXP-B pass; the pilot thresholds are not carried forward.

## Results (EXP-B v1, 2026-09-14)

- Input: 80 successful EXP-A v1 outputs; provisional `WER <= 0.20` label gives 46 acceptable and 34 unacceptable rows.
- Leave-one-out logistic regression OOF ROC-AUC: `0.515`; average precision: `0.615`; Brier score: `0.279`; AURC: `0.404`.
- One constant feature (`transcript_script_consistency`) was removed automatically and recorded; the remaining 14 features were fit.
- Under the default safety policy (≤10% risk at ≥25% coverage for ACCEPT; ≤25% risk at ≥50% coverage for WARN), no cutoff qualifies. The resulting safe policy is `ABSTAIN` for all 80 rows.
- Sensitivity: relaxing the target to 35% observed risk yields 50% coverage; this is a diagnostic tradeoff, not an acceptable production policy yet.
- Outputs: `data/challenge/results/exp-b-v1/exp-b-features.jsonl`, `exp-b-decisions.jsonl`, and `exp-b-summary.json` on the SSD.

### Expanded findings

- **F-004 — LID failure remains localized:** the 80-sample run reproduces 0/10 Bhojpuri auto-LID accuracy while the other languages score 10/10 in this slice.
- **F-005 — current reliability features remain weak:** the v1 scorer is only marginally above random ranking (ROC-AUC 0.515) and cannot meet conservative risk targets.
- **F-006 — abstention is operating as designed:** the system refuses to claim a safe coverage region when the observed top-score subset still contains too many WER failures.

## Current handoff from EXP-A (2026-09-14)

- EXP-A v0 provides 16 labeled Core outputs across all 8 target languages; expand to 50–100 total samples before fitting or claiming generalization.
- Storage impact for the expansion is approximately 27–68 MB of additional clean audio if the target is 50–100 total samples; saving five persisted variants per new sample would be approximately 138–340 MB.
- EXP-B phase 1 remains CPU/local and interpretable: derive features, define the acceptable-transcript label, fit logistic regression, and choose thresholds from risk–coverage rather than optimizing raw accuracy.
