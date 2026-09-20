---
type: experiment
id: EXP-E
title: "Diarization + multi-speaker pipeline"
status: retracted-pending-rerun
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

| Measure | Result |
| --- | ---: |
| No-diarization WER | 99.91% |
| Oracle-turn WER | 99.80% |
| Automatic VAD/cluster WER | 100.00% |
| Automatic DER | 62.51% |

**⚠️ RETRACTED 2026-09-20.** The WER numbers in the table above are void — they
were produced by a bug in `code/run_exp_e.py`'s `transcribe_clip()`, which
called `asr.transcribe(...)[0]` without `return_lid=True`. Since `transcribe()`
returns a bare `str` in that case, `[0]` indexed the **first character** of
the string, not a tuple element (every other call site in this project, e.g.
EXP-A/EXP-D, correctly passes `return_lid=True` and unpacks `(text, lid)`).
Verified directly: a 60 s two-chunk clip's `no_diarization_transcript` was
literally `"य उ"`, and oracle-turn transcript token counts matched
`num_reference_segments` exactly in all 4 recordings regardless of segment
duration (some segments were 5–27 s, not sub-second). That is a string-indexing
artifact, not a "model degrades on short turns" signal. Bug fixed in code;
**Automatic DER (62.51%) is unaffected** (it compares segment timing, not
transcript text) and remains a directionally valid toy-baseline signal. The
"Validity finding" originally written here (short-turn degradation) is
retracted along with the WER numbers — see `F-003` for the full writeup.

**Verdict.** EXP-E pilot **result unknown** pending a rerun with the fixed
code against a live ASR service. DER alone still argues for turn
padding/context and a real neural diarizer before expanding the benchmark,
but the multi-speaker-remedy claim itself is open again.
