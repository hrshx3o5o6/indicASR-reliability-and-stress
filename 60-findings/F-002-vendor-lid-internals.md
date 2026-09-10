---
type: finding
id: F-002
title: "Vendor code: LID confusion has structure — sink languages, inseparable hi/ur, no useful confidence threshold"
status: verified
confidence: "high — vendor's own 337k-clip measurements in shipped code"
metric: lid-reliability
updated: 2026-09-10
---

# F-002 — LID internals from the shipped code

**Claim.** The vendor's `lid.py` (Core repo @ `4d29eeb7a099`) documents LID behavior with corpus-scale measurements that restructure F-001's "absorbed by Hindi" picture.

**Evidence.** Vendored at `code/vendored/core/lid.py` (Apache-2.0 header, vendor-measured numbers in docstrings):

1. **Sink structure.** Biggest absorber is **`hne` (Chhattisgarhi)**, not Hindi: `bho→hne` 9,843 · `hi→hne` 8,376 · `mai→hne` 6,574 · `pa→bgc` 5,681. Hindi-belt confusion is a *multi-way sink system*, not a bho→hi pipe.
2. **hi/ur declared inseparable.** NeMo-vs-this agreement check: both disagreements were hi/ur at low confidence, incl. an exact 0.4993 tie; docstring: *"resolve hi/ur from metadata rather than from this score."*
3. **No useful default threshold.** p≥0.7 lifts accuracy 0.779→0.836 but coverage falls faster — "accuracy over the whole corpus only ever drops." Thresholds pay only with a fallback path — which is *exactly* our [[EXP-C]] design, so this is a feature for us.
4. **Per-language top-1 (VOI):** bho 0.047 · hi 0.258 · mai 0.356 · ur 0.490 vs ml 0.979 · ta 0.979 · kn 0.967 · bn 0.964. Overall 0.779 (VOI) / 0.864 (lattice).
5. **Restriction no-ops:** `TRAINED_LANGS` filter = identical accuracy to 4 decimals (model never emits the other ~162 language tokens). `RECOMMENDED_LANGS` (27 − bhb… docstring says −bgc too, code does −bhb only ⚠️) buys +1.4 pts on VOI, mostly `pa` rescued from `bgc`.
6. **Transcription-path impact (P3 refinement):** `lang=None` → LID lands on `WEAK_LID_LANGS` → warning fires → transcription proceeds *through the wrong language's task token* → "confidently wrong script" (e.g., Urdu audio in Devanagari). So absorption has TWO costs: wrong LID label AND wrong-script transcript.

**Interpretation.**
- F-001's "absorbed by a close neighbour" needs updating: the neighbour set includes `hne` and `bgc`, both of which are also *served* languages — echoing `lid.py`'s own note that excluding them is "a product decision, not a metric one." Our EXP-A probe design (restrict to {hi,bho,mai,ur}) measures the pure confusion floor.
- LID top-k + margin features ([[EXP-B]]) remain promising — the vendor measured *thresholding*, not *learned feature combination*. Their "no useful threshold" claim does NOT preclude a multivariate reliability model doing better. That's our P5 hypothesis, and it's still open.
- EXP-A must log script-vs-expected-language mismatch automatically (cost #6) — cheap, decisive evidence.

**Status.** `verified` (vendor code) → EXP-A re-measures end-to-end locally.
