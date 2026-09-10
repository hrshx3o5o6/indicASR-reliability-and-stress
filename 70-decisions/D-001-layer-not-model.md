---
type: decision
id: D-001
title: "Build the reliability layer above ASR, not a new ASR model"
status: accepted
date: 2026-09-10
updated: 2026-09-10
---

# D-001 — Layer, not model

## Context
[[indic-transcribe-core]] released with 1.3M training hours, 8.7 avg OI-WER, free commercial license. Competing at model level means fighting a well-resourced lab on its own turf.

## Options
1. Fine-tune / build a better Indic ASR — abandoned: compute-blind, redundant, and ignorant of the actual gap
2. **Reliability + middleware layer above ASR** ← chosen
3. Thin app/UI wrapper — abandoned: no research value ([[THESIS]] anti-goals)

## Decision
Build the evaluation + reliability + selective-prediction layer ([[PIPELINE]]): characterize failure modes → predict them → abstain/route → only then correct.

## Consequences
- + Exploits the real gap: knowing-when-wrong is unsolved and unglamorous
- + Every output (failure census, features, calibrated abstention) is reusable regardless of which ASR model ships next
- − We inherit the model's limits (single-speaker, native-script-only) instead of fixing them — mitigation: [[EXP-E]], [[EXP-D]]
- − If vendor ships a well-calibrated confidence API later, part of Exp B's novelty erodes — acceptable; their raw scores still need calibration evidence

Related: [[D-002-core-as-baseline]]
