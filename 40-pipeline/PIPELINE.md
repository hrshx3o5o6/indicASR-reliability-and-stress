---
type: pipeline
updated: 2026-09-10
---

# PIPELINE — the system under construction

## Target architecture

```
AUDIO (16 kHz mono, single speaker)
  ↓
Indic-Transcribe-Core            [[indic-transcribe-core]]
  ↓
raw transcript + LID distribution + acoustic signals
  ↓
RELIABILITY ANALYSIS
  ├── LID confidence             (top-k, entropy, margin → [[lid-reliability]])
  ├── audio quality              (SNR, clipping, speech rate → Exp B features)
  ├── transcript anomalies       (script consistency, repetition, likelihood)
  ├── entity anomalies           ([[entity-accuracy]])
  └── numeric/date anomalies     ([[critical-value-accuracy]])
  ↓
DECISION ENGINE
  ├── ACCEPT                     high reliability
  ├── ACCEPT WITH WARNING        moderate — attach reasons + uncertain spans
  └── ABSTAIN                    low — route (later) to adaptive LID (Exp C)
  ↓
application-ready transcript
```

## Contract: reliability output (v1)

Every processed utterance emits exactly this JSON shape — this is the interface the demo, the metrics, and later consumers all rely on:

```json
{
  "status": "accept | warn | abstain",
  "language": "ta",
  "language_confidence": 0.962,
  "lid_topk": [["ta", 0.962], ["ml", 0.021]],
  "reliability": 0.54,
  "transcript": "நாளைக்கு Chennai meeting இருக்கிறது",
  "audio": {"snr_db": 7.3, "speech_rate_wps": 5.8, "condition_guess": "telephone"},
  "uncertain_spans": [
    {"text": "Chennai", "confidence": 0.43, "reason": "entity in low-SNR code-mixed segment"}
  ],
  "reasons": ["moderate lid margin", "low SNR", "named entity", "code-mixing"]
}
```

Uncertain **spans**, not just whole-utterance scores — span attribution is a first-class requirement, not a nice-to-have.

## Stage rules

| Stage | Rule |
| --- | --- |
| ASR | Core, unmodified, for all of phase 1. Pass `lang` explicitly *and* record `return_lid=True` output so metadata-vs-model disagreement stays visible. |
| Reliability | Interpretable features only (v1). Logistic regression → LightGBM. No neural confidence model. |
| Decision thresholds | Set by calibration analysis on labeled data — **never chosen a priori**. |
| Post-processing (Exp D) | Semantics-preserving only; every normalization is validated against [[semantic-slot-accuracy]] before adoption. |
| LLM correction | **Forbidden until Exp D**, and then only conservative, evidence-gated correction. |

## Evolution

- Exp A baseline → Exp B +confidence → Exp C +adaptive LID (multi-hypothesis decoding; feeds on `lid_topk` which Core already exposes) → Exp D +normalization/entity → Exp E +diarization.
- Future routing: `abstain` cases from this pipeline become the *input distribution* for the adaptive-LID project — that is the deliberate bridge between the two projects.

## Non-goals for v1

Streaming, real-time reliability estimation, multi-speaker handling (Exp E), romanized/mixed output modes (Flex, Exp D), any production serving.
