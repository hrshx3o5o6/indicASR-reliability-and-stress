---
type: metric
updated: 2026-09-10
metric: lid-reliability
direction: "higher acc / better calibration"
---

# [[lid-reliability]] — LID accuracy & calibration

The model's LID is not just sometimes wrong — the vendor says so ([[F-001-hindi-belt-lid-absorption|F-001]]). The project's question is whether the **uncertainty signal** is trustworthy enough to drive abstention and routing.

## Metrics

- **Top-1 / top-2 / top-3 accuracy** of `identify()` against true language.
- **Confusion matrix** — *which* wrong language wins matters (bho→hi absorption is the headline case).
- **Calibration**: reliability diagram of top-1 probability vs empirical correctness; ECE. "hi 0.98" must mean something different from "hi 0.51".
- **Margin & entropy**: top1−top2 margin and normalized entropy of the top-k distribution → features for the reliability model (Exp B).
- **Explicit-label disagreement**: run `transcribe(lang=X, return_lid=True)` on audio labeled X; how often does the model's own LID disagree? Free second signal.

## Hypotheses (link to [[THESIS]])

- P3: absorption is concentrated in {bho, mai, ur} → hi.
- H: top-k margin separates "confused but recoverable" from "confidently wrong" — this is precisely what Exp C multi-hypothesis decoding will consume.
- ⚠️ to-verify: Core vs Flex LID behavior may differ (Flex card publishes per-language identify acc: ml/ta 0.98, kn/bn 0.96, ur 0.49, mai 0.36, hi 0.26, bho 0.05 — vendor-reported).

## Pitfall

`allowed_langs` is a **hard filter with silent reassignment** ([[indic-transcribe-core]]) — never use it during measurement, only as a designed probe. Otherwise it will fabricate good-looking accuracy.
