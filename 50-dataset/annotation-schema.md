---
type: dataset
updated: 2026-09-10
---

# annotation-schema — v0 (versioned; breaking changes require `D-###`)

```json
{
  "sample_id": "cs-v0-ta-017",
  "suite_version": "0.1",
  "audio": {
    "path": "audio/ta/cs-v0-ta-017.wav",
    "sr_hz": 16000,
    "channels": 1,
    "duration_s": 7.42
  },
  "language": "ta",
  "conditions": {
    "audio": ["telephone", "background_noise"],
    "content": ["code_mixed", "names"],
    "pair_id": null,
    "degradation_chain": "sox bandpass 300-3400 + noise snr=8db",
    "clean_twin": "cs-v0-ta-016"
  },
  "provenance": {
    "source": "indicvoices",
    "source_id": "iv-ta-88123",
    "synthetic": false,
    "contamination_risk": "unknown|low|medium|high",
    "speaker_id": "iv-ta-spk-204",
    "license": "…",
    "recorded_env": "phone-upload"
  },
  "reference": "நாளைக்கு Chennai meeting இருக்கு",
  "reference_variants": ["சென்னை spelling variant accepted by OI-WER"],
  "entities": [
    {"text": "Chennai", "type": "location", "span_char": [11, 18]}
  ],
  "numbers": [{"text": "ஐயாயிரம்", "value": 5000}],
  "dates": [{"text": "நாளைக்கு", "normalized": "relative+1d", "absolute": null}],
  "currency": [{"text": "ஐயாயிரம் ரூபாய்", "value": 5000, "currency": "INR"}],
  "notes": "speaker hesitant on org name"
}
```

## Field rules

- `conditions` uses **exactly** the taxonomy vocabulary of [[challenge-suite-spec]] — no free-text conditions.
- `reference_variants` = documented spelling/transliteration alternatives → input to [[oi-wer]] scoring.
- `entities` types: `person|location|organization|product|technical` ([[entity-accuracy]]).
- `numbers/dates/currency` pre-extracted at annotation time → [[critical-value-accuracy]] compares against *scripted extraction* from hypotheses.
- `clean_twin`/`degradation_chain` enable the paired interaction analysis (P4); `synthetic` gates separate reporting ([[indic-tts-corpora]] rule).
- Reliability labels (Exp B) are **derived, not annotated**: computed from per-sample error records post-Exp-A ([[EXP-B]]), threshold fixed in a `D-###`.
