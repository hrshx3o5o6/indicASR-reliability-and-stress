---
type: finding
id: F-009
title: "A round-trip guard catches every critical-value error Flex mixed-mode ITN introduces on held-out Bhojpuri, while keeping 94% of safe rewrites"
status: verified
confidence: "medium-high (holdout n=83 clips / 30 ITN errors, 100 speakers; one language)"
metric: critical-value-accuracy
updated: 2026-10-21
---

# F-009 — Critical-value guard (Flex mixed ITN), tune/holdout result

**Claim.** Accepting Flex `mixed` output only when every digit string in it
round-trips to a spoken-number run in the same clip's `native` decode (and no
spoken currency word is dropped) removes the errors mixed-mode ITN adds. The
shipped output is then as safe as native on numbers while keeping the
formatted digits in most safe cases.

**Evidence.** Guard: `code/guard/` (frozen at commit `250f0c1` before the
holdout was decoded), tests `code/tests/test_guard.py`. Evaluator:
`code/scripts/v2/eval_guard.py`. Decodes (Flex `c0db6b2b`, lang=bho):
`code/results/v2/guard-{tune-benchmark,holdout-train-real}-flex.jsonl`,
summaries `...-summary.json`.

Truth = reference-based round-trip; "wrong" = any digit mismatch or dropped
currency word vs the reference.

| | Tune (benchmark, n=205) | Holdout (train_real, n=83, 100 spk) |
|---|---|---|
| Flex mixed wrong | 106 (52%) [44.9, 58.5] | 47 (57%) [45.9, 66.8] |
| Flex native wrong | 42 (20%) [15.5, 26.5] | 21 (25%) [17.2, 35.6] |
| **Guarded output wrong** | **40 (20%)** [14.7, 25.5] | **19 (23%)** [15.2, 33.0] |
| ITN-introduced errors caught | 67/67 [94.6, 100] | **30/30 [88.6, 100]** |
| Safe mixed outputs kept | 98/99 | 34/36 |

Holdout mixed-mode failure modes: dropped currency word (30), wrong digit
string (37), e.g. "पंचानबे हजार रुपिया" -> "55,000" (95,000 -> 55,000, word dropped).

**Hand audit of the 11 holdout outputs the guard accepted but truth flagged:**
9 are upstream ASR digit errors already present in `native` (dropped/added
digits in UPI/account numbers) which mixed reproduces exactly; 2 are truth
false alarms from reference spellings missing from the parser (`दूई`,
`सत्हत्तर`). None is an ITN-introduced error.

**Provenance.** `exp-d v2` (this pass).

**Interpretation.**
- Changes the C2 recommendation from "do not ship Flex mixed" to "ship
  Flex mixed only behind a round-trip guard".
- The remaining ~20-25% numeric error rate is **ASR**, not ITN: even native
  mode with the language given gets a UPI/account/amount wrong in about 1 in
  4 numeric Bhojpuri clips. The guard cannot see these by design; catching them
  needs a different signal (confirmation UX, checksum rules like IFSC/UPI
  formats, or a second decode).
- Tune/holdout discipline mattered: tuning added 6 spellings; the holdout
  still exposed 2 more (reference side only).

**Status.** verified for Bhojpuri / Flex `c0db6b2b`.

**Limits.** Bhojpuri only (Devanagari parser; Urdu/Dravidian tables not built);
one corpus; truth shares the parser with the guard (audited above);
decimals/ordinals are rejected conservatively; benchmark (tune) clips have no
speaker IDs, so tune/holdout speaker overlap cannot be excluded.
