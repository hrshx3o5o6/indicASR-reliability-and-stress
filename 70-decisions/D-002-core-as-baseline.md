---
type: decision
id: D-002
title: "Indic-Transcribe-Core is the phase-1 baseline; Flex is an instrument, not the baseline"
status: accepted
date: 2026-09-10
updated: 2026-09-10
---

# D-002 — Core as baseline

## Context
Two sibling models ship together: [[indic-transcribe-core]] (25 langs, native-script, best accuracy) and [[indic-transcribe-flex]] (27 langs, native/mixed/romanized modes, published LID stats).

## Decision
- All phase-1 reliability work measures **Core** (best case, the model people will deploy).
- Flex appears only where its extras are the subject: `mixed` mode as the ITN baseline to beat ([[EXP-D]]), its published LID stats as a hypothesis source ([[F-001-hindi-belt-lid-absorption|F-001]]), `hne`/`bgc` coverage later.

## Rationale
- Core is the accuracy leader (8.7 vs 11.3 avg OI-WER) → if we can predict *its* failures, Flex's failures are a superset problem
- One baseline keeps the day-1–3 scope honest; a two-model factorial design would double runs for little insight this early
- Flex's native-script mode ≈ Core's whole output space, so nothing phase-1 needs is Flex-only

## Consequences
- LID comparisons must not silently compare Core numbers to Flex numbers ([[F-001-hindi-belt-lid-absorption|F-001]] ⚠️) — always re-measure per model
- If Core's card API differs materially from Flex's (e.g. no `mode=` param), that's expected, not a bug
- Revisit if Core proves unusable locally (license gate, VRAM) — fallback documented in [[indic-transcribe-core]]
