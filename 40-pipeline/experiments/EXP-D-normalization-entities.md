---
type: experiment
id: EXP-D
title: "Semantics-preserving normalization + entity correction"
status: planned
phase: day-3
depends: ["EXP-B"]
updated: 2026-09-10
---

# EXP-D — Normalization & entity correction

**Question.** Can Core's native-script output be converted to application-ready text (digits, dates, entities, mixed script) **without changing the speaker's meaning**? And does that layer beat Flex's built-in ITN?

## Two sub-systems

### 1. Normalization (numbers, dates, currency, units, technical terms)
- Word→digit normalization per language (Core outputs spoken numbers as words — see [[critical-value-accuracy]])
- **Acceptance test: [[semantic-slot-accuracy]] must not regress; [[critical-value-accuracy]] must improve.** A normalization that raises OI-WER but flips meaning is rejected ([[THESIS]] rule 4)
- Baseline to beat: Flex `mode="mixed"` (built-in ITN) — the Flex card itself admits mixed mode "will occasionally get it wrong"; measure both, compare on identical audio
- ⚠️ Normalizer versioned + pinned; self-inflicted errors go to the `normalization` bucket of [[error-taxonomy]]

### 2. Entity correction (conservative by design)
```
transcript → entity detection → candidate generation → contextual validation → correct ONLY at high confidence
```
- Never "correct" merely because a database form is more frequent
- Every correction logged with evidence; wrong corrections tracked as findings
- Cases: "Rahul Sharma"→"Rahul Verma" (must NOT fire), "Chennai IIT"→"IIT Madras" (may fire only with strong contextual evidence)

## Evaluation

Same suite as [[EXP-A]]; deltas reported per metric + per bucket; entity-correction precision/recall on the entity subset; ITN comparison table Core+ours vs Flex-mixed.

## Output

Normalization + entity layers gated behind the reliability engine (apply to accept/warn cases; abstain cases bypass or route to [[EXP-C]]).
