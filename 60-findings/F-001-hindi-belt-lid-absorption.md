---
type: finding
id: F-001
title: "Hindi-belt languages are absorbed by Hindi in LID (vendor-reported)"
status: vendor-reported
confidence: "high for Flex — the vendor's own limitation section"
metric: lid-reliability
updated: 2026-09-10
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

**Status.** `vendor-reported` → Exp A re-measures on Core + Flex: top-1/2/3 acc, confusion matrix, absorption rate on clean synthetic Hindi-belt audio ([[indic-tts-corpora]] probe) to separate acoustic vs decoder causes.

**Update 2026-09-10 (code audit):** vendor's own 337k-clip measurements ([[F-002-vendor-lid-internals|F-002]]) refine the picture — the confusion is a **multi-way sink system** (`hne` is the biggest absorber, not Hindi), and hi/ur is declared genuinely inseparable. F-001 remains the card-level claim; F-002 is the mechanism-level account.

**If confirmed with similar rates:** the adaptive-LID project ([[EXP-C]]) has its headline motivation pre-validated. **If refuted:** record honestly — maybe Core fixed what Flex's numbers show; that would itself be a finding about the two training runs.
