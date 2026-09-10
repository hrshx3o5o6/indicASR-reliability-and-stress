---
type: experiment
id: EXP-E
title: "Diarization + multi-speaker pipeline"
status: planned
phase: post-sprint
depends: ["EXP-D"]
updated: 2026-09-10
---

# EXP-E — Diarization

**Question.** Does segmenting multi-speaker audio (VAD → diarization → per-turn transcription) recover acceptable accuracy on audio Core is explicitly not built for (single-speaker limitation, [[indic-transcribe-core]])? Overlap conditions in the suite exist for this.

## Sketch

```
audio → VAD → diarization → speaker turns → Core per turn → reliability ([[EXP-B]]) → speaker-labelled transcript
```

- Eval: Indic DiarBench where appropriate (see [[DATASETS]]); DER + per-turn OI-WER vs. no-diarization baseline; overlap bucket of [[error-taxonomy]]
- Interaction of interest: diarization errors masquerading as ASR errors (wrong-turn attribution) — bucket `overlap` vs `lid`/`lexical` carefully
- Post-sprint; only after EXP-D stabilizes. Reliability layer should treat each turn as an utterance and carry speaker labels through the [[PIPELINE]] contract.
