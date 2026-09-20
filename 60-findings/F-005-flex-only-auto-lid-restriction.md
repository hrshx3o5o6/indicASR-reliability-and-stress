---
type: finding
id: F-005
title: "Flex recovers 4/10 Bhojpuri auto-LID where Core gets 0/10 — different confusion pattern (absorbed by Maithili, not Hindi), tied on overall WER"
status: verified
confidence: "high for the code fact; high for the empirical Bhojpuri result (n=10); prediction #3 below was wrong and is corrected"
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
   `bgc`/`bhb` — so F-001 would likely still reproduce on Flex on the same
   grounds. **This prediction was wrong** — see below.

**⚠️ Empirically tested 2026-09-20 — the prediction above was wrong, and the
real result is more interesting than the code fact alone.** Ran the same
EXP-A auto-condition call (`run_baseline.py --vendor flex`) against Flex on
the identical 80-sample suite Core used. Result:

| | Core (2026-09-17) | Flex (2026-09-20) |
| --- | ---: | ---: |
| Overall explicit-condition WER | 22.01% | 21.85% (paired bootstrap: **tied**, 95% CI on the diff [-1.5, +1.2] pts, p=0.83) |
| Overall auto-LID top-1 accuracy | 87.5% | 92.5% |
| **Bhojpuri auto-LID accuracy** | **0/10** | **4/10** (Wilson 95% CI [16.8%, 68.7%]) |

Transcription quality is statistically indistinguishable between the two
models on this suite (they're the same base architecture/training recipe on
overlapping data, so this is expected — but it's now measured, not assumed,
and completes the previously-blocked "second-baseline" comparison).
**Bhojpuri LID is not: Core fails all 10, Flex succeeds on 4/10** — a real,
substantial difference, and *not* the one the code diff predicted (the
restriction excludes `bgc`/`bhb`, not `bho`). More interesting than the
raw number: when Flex gets Bhojpuri wrong, it is absorbed by **Maithili**
five times out of six wrong calls, and by Hindi only once — a different
confusion structure than Core's Hindi-belt absorption pattern described in
[[F-001]]. This means the "Hindi-belt LID absorption" framing in F-001/C1 is
**Core-specific**, not a property of the model family as a whole; Flex has
its own (milder) confusion pattern, into Maithili rather than Hindi. Full
per-sample topk: `code/results/summaries/exp-a-v1-flex-baseline.jsonl`;
aggregate: `code/results/summaries/exp-a-v1-flex-summary.json`; CIs:
`code/results/stats/bootstrap.json` (`exp_a_core_vs_flex`,
`exp_a_flex_bho_lid`).

**Status.** Verified, empirically tested — both the code-level asymmetry and
its real effect on this suite. **Partially diagnosed 2026-09-20:** [[F-007]]
shows the gap is a confidence/calibration difference, not the restriction —
Core commits confidently (up to 99.6% probability) to the wrong belt language
on bho clips, while Flex genuinely contests bho against mai/hi with real
probability mass and wins 4/10 of those contests. *Why* Flex's softmax is
less sharp specifically on bho remains open (candidate causes: different bho
training data volume/quality between the two checkpoints; a general effect of
Flex's 27-language output layer vs Core's 25 — untested).

**Card relation.** Neither the Core nor the Flex model card documents this
asymmetry; both describe `allowed_langs`/auto-detection identically. This is
new information not previously captured in `20-models/*` (dossiers last
re-checked 2026-09-17, before this code-level diff was done).
