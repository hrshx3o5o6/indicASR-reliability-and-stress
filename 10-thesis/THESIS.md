---
type: thesis
updated: 2026-09-10
---

# THESIS

> **"Don't make the ASR model blindly better. Make the system better at knowing when its answer is trustworthy."**

State-of-the-art Indic ASR ([[indic-transcribe-core]], OI-WER 8.7 avg on Voice of India) is no longer necessarily the primary bottleneck. The remaining bottleneck is the layer **above** the model:

```
audio → ASR → transcript + language + acoustic signals
      → reliability analysis → accept / warn / abstain
      → application-ready transcript
```

We do **not** build an ASR model ([[D-001-layer-not-model|D-001]]). We characterize failure modes rigorously, then predict when transcripts are wrong, then abstain or route — and only later correct.

---

## Falsifiable predictions (the "unit tests" of the project)

| # | Prediction | Test | Status |
| --- | --- | --- | --- |
| P1 | Aggregate OI-WER hides large language × condition variance | Exp A stratified eval | ☐ |
| P2 | Numbers, dates, currency, and entities fail disproportionately to their WER weight | Exp A critical-value metrics | ☐ |
| P3 | LID is unreliable exactly where predicted: Hindi-belt absorption ([[F-001-hindi-belt-lid-absorption|F-001]]) | Exp A LID probe | ☐ |
| P4 | Condition interactions (e.g. noise × code-mixing) are **non-additive** — worse than the sum of parts | Exp A interaction heatmap | ☐ |
| P5 | Simple interpretable features (LID entropy/margin, SNR, rate, script consistency…) predict a meaningful fraction of transcript failures | Exp B logistic regression | ☐ |
| P6 | Selective prediction reduces error materially at usable coverage (risk–coverage curve) | Exp B | ☐ |
| P7 | P5–P6 motivate adaptive LID / multi-hypothesis decoding as the next project | Exp C design | ☐ |

A prediction that survives gets *verified* with effect sizes; one that dies gets a finding note saying so. **Manufacturing a confirmation is the only unforgivable failure.**

---

## Anti-goals (what we do NOT build)

- A generic "Indian speech-to-text app" or UI wrapper around Indic-Transcribe
- Another ASR model, or a fine-tune before failure modes are understood
- "Indic-Transcribe + ChatGPT" chatbot / generic RAG over transcripts
- An LLM "fix transcript" stage before the baseline is understood
- Overclaiming safety-critical deployment — this is a research/prototype system

---

## Epistemic rules

1. Raw ASR confidence is **not assumed calibrated** — measure it ([[lid-reliability]]).
2. WER alone is never sufficient ([[oi-wer]], [[METRICS]]).
3. Interpretability beats accuracy in the reliability model: logistic regression → gradient boosting; **no neural nets in phase 1**.
4. Correction must be semantics-preserving or it is rejected ([[semantic-slot-accuracy]] guards this).
5. Abstention that simply abstains on every hard example is useless — coverage is part of the metric ([[selective-prediction]]).
6. Vendor-reported numbers (benchmarks, LID stats) are claims to re-measure, not facts ([[F-001-hindi-belt-lid-absorption|F-001]]).
