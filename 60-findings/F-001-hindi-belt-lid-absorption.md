---
type: finding
id: F-001
title: "Hindi-belt languages are absorbed by Hindi in LID (vendor-reported)"
status: verified
confidence: "high — vendor claim + EXP-A measurement agree; small-n caveat; scope narrowed to Core specifically, see 2026-09-20 update"
metric: lid-reliability
updated: 2026-09-20
---

# F-001 — Hindi-belt LID absorption

**Claim.** Automatic language ID misclassifies Hindi-belt languages as Hindi at rates that make unguided auto-LID untrustworthy for exactly the languages we care about.

**Provenance.** Vendor model cards, fetched 2026-09-10:
- [[indic-transcribe-flex]] card publishes per-language `identify()` accuracy: bho **0.05**, hi **0.26**, mai **0.36**, ur 0.49 (vs ml/ta 0.98) — "each absorbed by a close neighbour"
- [[indic-transcribe-core]] card: *"Bhojpuri, Maithili and Urdu are absorbed by Hindi far too often to be trusted. Pass `lang` explicitly whenever you have it."*

**Interpretation.** Two distinct failure modes are entangled here and must be separated in [[EXP-A]]:
1. *LID absorption* — audio is bho, model says hi (language ID problem)
2. *Transcription assimilation* — LID says hi, decoder then transcribes bho speech *through Hindi* (task-token problem: cheap, one decoder step, may be lossy)

They demand different fixes ([[EXP-C]] addresses #1 via top-K routing; #2 may need decoder-level work). The hi=0.26 number suggests even true-Hindi audio is being split among belt siblings by the LID head — i.e., the confusion is symmetric-ish, not one-directional. ⚠️ All numbers are Flex's; Core may differ.

**Status.** `verified` 2026-09-17. [[EXP-A]] v1 (80 samples, 8 langs × 10): Bhojpuri auto-LID wrong **10/10** while the other seven languages (incl. hi, mai, ur) were 10/10 correct — one-directional bho→(hi-belt) absorption in this slice, stronger than the symmetric-ish split F-002's vendor table suggested. Core-warning (`WEAK_LID_LANGS`) fired on 50% of samples. Scope caveat: 10 bho rows, clean/synthetic conditions, whitespace-token WER — the EXP-C oracle result (bho truth in top-3 10/10, reranker still picks hi) shows candidate generation survives even where top-1 fails.

**Update 2026-09-10 (code audit):** vendor's own 337k-clip measurements ([[F-002-vendor-lid-internals|F-002]]) refine the picture — the confusion is a **multi-way sink system** (`hne` is the biggest absorber, not Hindi), and hi/ur is declared genuinely inseparable. F-001 remains the card-level claim; F-002 is the mechanism-level account.

**If confirmed with similar rates:** the adaptive-LID project ([[EXP-C]]) has its headline motivation pre-validated. **If refuted:** record honestly — maybe Core fixed what Flex's numbers show; that would itself be a finding about the two training runs.

**Update 2026-09-20 (empirical, resolves the line-23/29 open question — the
opposite direction from what was anticipated).** Ran the same EXP-A
auto-condition test on **Flex**, same 80-sample suite: Bhojpuri auto-LID
**4/10 correct** (Wilson 95% CI [16.8%, 68.7%]), vs Core's 0/10 — Flex is
*better*, not worse, on this axis, and when Flex is wrong it's absorbed by
**Maithili** (5/6 wrong calls), not Hindi (1/6). So: **the "Hindi-belt
absorption" framing in this finding is Core-specific.** It does not
generalize to "the model family absorbs Bhojpuri into Hindi" — Flex shows a
real, different, milder confusion pattern. Overall transcription WER is tied
between the two models (paired bootstrap, 95% CI on the diff spans zero),
so this is specifically a LID-behavior difference, not a general capability
difference. Full writeup: [[F-005-flex-only-auto-lid-restriction|F-005]].
