---
type: finding
id: F-005
title: "Flex's default auto-LID silently restricts candidates to RECOMMENDED_LANGS; Core does not — the two 'sibling' models are not symmetric here"
status: code-audit-only — not yet empirically tested
confidence: "high for the code fact; untested for effect on our suite (we have not run Flex auto-LID)"
metric: lid-reliability
updated: 2026-09-20
---

# F-005 — Core and Flex disagree on default auto-LID candidate set

**Claim.** [[indic-transcribe-flex]] and [[indic-transcribe-core]] are described in
this project's own dossiers as sharing "the same wrapper" — true for the
`native`/`mixed`/`romanised` mode plumbing, but **not** true for default
auto-LID behavior. In the current vendored code (`indic_transcribe.py`,
`transcribe()`):

```python
# Flex only:
auto = allowed_langs if (allowed_langs is not None or lang is not None) else RECOMMENDED_LANGS
...
top = lid_from_encoder_states(..., allowed_langs=auto, ...)
```

Flex, when called with `lang=None` and no explicit `allowed_langs` (i.e. plain
auto-detection — the exact call our EXP-A "auto" condition and EXP-C use),
silently restricts the LID candidate set to `RECOMMENDED_LANGS` (all trained
languages minus `bgc`, `bhb`). **Core's `transcribe()` has no such branch** —
plain auto-detection on Core searches the *full* candidate set with no
restriction. Confirmed by direct diff of `indic_transcribe.py` between the two
repos (2026-09-20); the asymmetry is not present in either repo's docstring —
it is unstated in both cards.

**Evidence.** Code diff, `code/vendored/{core,flex}/indic_transcribe.py`
(Core sha `e083ab7d...`, Flex sha `c0db6b2b...`, both 2026-09-20). The vendor's
own inline comment on the Flex branch discloses a quantified justification:
*"Measured over 337k clips, excluding [bgc, bhb] lifts pa 0.620 → 0.775 on VOI
and changes no other language by more than +0.013."* This is a vendor-disclosed
number we have not independently verified.

**Why it matters to this project.** All of our auto-LID measurements to date
(EXP-A, EXP-C — including the Bhojpuri 0/10 finding, [[F-001]]) were run
against **Core**, which does not have this restriction, so those results are
unaffected. But it means:
1. Our dossiers' "same wrapper" framing needs a caveat — the two models are
   not interchangeable for auto-LID behavior, only for mode plumbing.
2. If Flex's auto-LID is ever benchmarked (not done in this project), its
   default results are **not directly comparable** to Core's under the same
   call signature — Flex quietly excludes 2 candidate languages by default,
   Core does not.
3. `bho` (Bhojpuri, the language in our headline LID-absorption finding) is
   **not** excluded by Flex's restriction — `RECOMMENDED_LANGS` only drops
   `bgc`/`bhb` — so F-001 would likely still reproduce on Flex, but this has
   not been tested.

**Status.** Code-audit finding only. No new inference was run to produce this
— it is a direct reading of vendored source, verifiable without a live ASR
service (`compute: none`). Promote to an empirically tested claim only after
running Flex's auto-LID on the existing suite and comparing to Core's EXP-A/C
results under matched conditions.

**Card relation.** Neither the Core nor the Flex model card documents this
asymmetry; both describe `allowed_langs`/auto-detection identically. This is
new information not previously captured in `20-models/*` (dossiers last
re-checked 2026-09-17, before this code-level diff was done).
