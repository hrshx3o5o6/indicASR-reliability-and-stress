---
type: dataset
updated: 2026-09-10
priority: 5
access: "open (AI4Bharat)"
license: "⚠️ to-verify"
synthetic: true
---

# [[indic-tts-corpora]] — IndicTTS / TTS engines

TTS corpora + models for the scheduled languages. **Role is unusual and deliberate:** synthesize audio with *perfect known references*, then apply controlled degradations.

- **Use for:** the paired clean↔degraded cells of the interaction matrix (P4): identical utterance, sweep noise level / telephone bandpass / speech rate. Only method that gives full factorial control.
- **Hard rule:** always `synthetic: true` in [[annotation-schema]]; report TTS-derived results separately from natural-speech results — a model may handle synthetic degradation differently from real noise (prove otherwise before mixing).
- **Bonus probe:** TTS in bho/mai/ur lets us test LID absorption on *acoustically clean* Hindi-belt audio — if absorption persists on clean synthetic speech, it's a decoder/LID problem, not an acoustic one. Sharp experiment, cheap to run ([[F-001-hindi-belt-lid-absorption|F-001]]).
- ⚠️ to-verify: TTS quality for bho/mai (may be poor — don't let bad TTS audio manufacture fake ASR errors).
