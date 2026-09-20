---
type: experiment
id: EXP-E
title: "Diarization + multi-speaker pipeline"
status: done
phase: pilot-results
depends: ["EXP-D"]
updated: 2026-09-20
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

| Measure | Result (2026-09-17, buggy — VOID) | Result (2026-09-20, fixed — REAL) |
| --- | ---: | ---: |
| No-diarization WER | ~~99.91%~~ | **66.6%** |
| Oracle-turn WER | ~~99.80%~~ | **57.7%** |
| Automatic VAD/cluster WER | ~~100.00%~~ | **82.6%** |
| Automatic DER | 62.51% | 62.51% (unchanged, unaffected by the bug) |

**Bug found, fixed, and re-measured 2026-09-20.** The original numbers were
produced by a bug in `code/run_exp_e.py`'s `transcribe_clip()`, which called
`asr.transcribe(...)[0]` without `return_lid=True`. Since `transcribe()`
returns a bare `str` in that case, `[0]` indexed the **first character** of
the string, not a tuple element (every other call site in this project, e.g.
EXP-A/EXP-D, correctly passes `return_lid=True` and unpacks `(text, lid)`).
Verified directly on the old per-sample records: a 60 s two-chunk clip's
`no_diarization_transcript` was literally `"य उ"`. Bug fixed; re-ran against a
live local ASR service (M5 Mac, MPS) with Core re-vendored to the current HF
revision. New transcripts are fluent and match the reference content
(spot-checked). Full writeup and per-sample table: `F-003`.

**Revised validity finding.** Oracle turns give a real but modest improvement
over no diarization (66.6%→57.7%, ~9 points) — not a rescue, 57.7% WER is
still far from usable. The more striking result: the **toy automatic VAD/KMeans
diarizer makes things worse than doing nothing** (82.6% vs. 66.6%) — 3 of 4
recordings got worse or flat under automatic segmentation. This shifts the
interpretation from "Core degrades on short turns" (the old, bug-driven
reading) to "turn-boundary quality matters a lot, and a naive automatic
diarizer is actively counterproductive here."

**Verdict.** EXP-E pilot's real result: partial improvement from oracle
turns, net harm from the toy automatic diarizer. Strengthens rather than
removes the case for turn padding/context and a real neural diarizer before
expanding the benchmark — now on real numbers instead of a bug artifact.
