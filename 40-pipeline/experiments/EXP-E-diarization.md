---
type: experiment
id: EXP-E
title: "Diarization + multi-speaker pipeline"
status: done
phase: pilot-results
depends: ["EXP-D"]
updated: 2026-09-17
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

## Active run (2026-09-17)

- Dataset: `sarvamai/indic-diarbench`, a speaker-attributed Indic conversational benchmark.
- Initial scope: Hindi and Tamil test shards, both supported by Core; downloaded size is approximately 2.35 GB.
- SSD destination: `data/exp-e/indic-diarbench/`.
- Validated inventory: Hindi `94` recordings / `10.74` hours / `8,665` annotated segments; Tamil `93` recordings / `9.98` hours / `10,474` annotated segments.
- Speaker counts: Hindi `2–9`; Tamil `2–6`. Conditions include near-field, far-field, and in-the-wild recordings.
- Next: select a small stratified subset, validate audio/turn annotations, then run no-diarization versus oracle-turn baselines before attempting automatic diarization.
- Synthetic mixtures may be used only as a pipeline smoke test; they will not be reported as the real EXP-E benchmark result.

## Pilot results (2026-09-17)

- Scope: 4 real two-speaker recordings, 2 Hindi and 2 Tamil, near-field and far-field, each approximately 60 seconds.
- Pipeline: full-conversation chunking, oracle annotated-turn transcription, and automatic energy-VAD plus spectral-feature KMeans clustering.

| Measure | Result |
| --- | ---: |
| No-diarization WER | 99.91% |
| Oracle-turn WER | 99.80% |
| Automatic VAD/cluster WER | 100.00% |
| Automatic DER | 62.51% |

**Validity finding.** The selected conversations contain many short turns; exact oracle cuts can be sub-second. Core often emitted only partial characters on these turns, so segmentation alone did not recover usable ASR in this pilot. This is a valid stress result, not evidence that a production neural diarizer has 62.5% DER. The automatic baseline is intentionally simple and must be replaced by a neural diarizer for the next study.

**Verdict.** EXP-E pilot fails the usable-accuracy criterion. Keep Core out of direct multi-speaker full-conversation mode; add turn padding/context and a real diarizer before expanding the benchmark.
