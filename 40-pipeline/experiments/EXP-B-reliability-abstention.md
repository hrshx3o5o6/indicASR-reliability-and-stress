---
type: experiment
id: EXP-B
title: "Reliability model + selective prediction (abstention)"
status: planned
phase: day-2
depends: ["EXP-A"]
updated: 2026-09-10
---

# EXP-B — Reliability model & abstention

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
