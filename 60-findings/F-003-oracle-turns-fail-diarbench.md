---
type: finding
id: F-003
title: "Oracle turns roughly halve error vs. no diarization, but stay far from usable — and naive automatic diarization makes it worse, not better"
status: verified
confidence: "high for this 4-recording slice; small-n (n=4), 2 languages — see original scope caveats"
metric: wer
updated: 2026-09-20
---

# F-003 — Oracle turns help but do not rescue Core on conversational audio

**Claim (revised 2026-09-20, after re-measurement with corrected code).**
On this 4-recording DiarBench slice, giving [[indic-transcribe-core]] oracle
speaker-turn boundaries reduces WER from 66.6% (no diarization) to 57.7%
(oracle turns) — a real but modest improvement, not a rescue. **Naive
automatic diarization (energy-VAD + spectral-KMeans) makes things worse, not
better**: 82.6% WER, higher than doing nothing.

**⚠️ 2026-09-20 bug found, fixed, and re-measured.** The original 09-17 numbers
(no-diar 99.91%, oracle-turn 99.80%, automatic 100.00%) were a code bug, not a
model result: `code/run_exp_e.py`'s `transcribe_clip()` called
`asr.transcribe(...)[0]` without `return_lid=True`; since `transcribe()`
returns a bare `str` in that case, `[0]` indexed the first *character*, not a
tuple element — every transcript was truncated to ~1 char per clip. Verified
directly on the old per-sample records at the time. Fixed the `[0]` bug in
`run_exp_e.py`, re-vendored Core to the current HF revision (`e083ab7d...`,
confirmed the `return_lid` contract is unchanged), and **re-ran the pilot
end-to-end** against a live local ASR service (M5 Mac, MPS, `code/data/model`,
2026-09-20).

**Real per-sample results (2026-09-20 rerun):**

| Sample | Lang | No-diar WER | Oracle-turn WER | Auto VAD/KMeans WER |
| --- | --- | ---: | ---: | ---: |
| hindi_085 | hi | 53.4% | 47.4% | 68.4% |
| hindi_065 | hi | 47.2% | 28.7% | 98.5% |
| tamil_092 | ta | 74.6% | 73.0% | 73.0% |
| tamil_076 | ta | 91.3% | 81.5% | 90.8% |
| **Mean** | | **66.6%** | **57.7%** | **82.6%** |

Transcripts are now fluent, real Hindi/Tamil text matching the reference
content (spot-checked) — not the 1-character garbage from the bug. Automatic
DER (62.51%, toy VAD/KMeans baseline) is unchanged from the original run, as
expected — it never depended on transcript text.

**Interpretation.** Oracle turn boundaries help (66.6%→57.7%, ~9 points) but
57.7% WER is still far from usable — the vendor's "pair it with a diarization
module" remedy is a real, measurable improvement, not a fix. More strikingly,
the **toy automatic diarizer actively hurts** relative to doing nothing at all
(82.6% vs. 66.6%) — 3 of 4 recordings got worse or flat under automatic
segmentation, driven by over/under-segmentation errors compounding with
short-turn ASR weakness. This reframes the original interpretation: the
problem is not primarily "Core degrades on short turns" (the old, bug-driven
reading) but that **turn-boundary quality matters a lot**, and a naive VAD
baseline is actively counterproductive — a stronger point in favor of
investing in a real neural diarizer before shipping any multi-speaker path.

**Provenance.** `exp-e` original run measured 2026-09-17 (Core snapshot
`4d29eeb7a099`, bug present); bug found, fixed, and re-measured 2026-09-20
(Core snapshot `e083ab7d...`). Artifact:
`code/data/challenge/results/exp-e-v2/exp-e-pilot-summary.json` (SSD; not yet
copied into the repo's replication bundle — same P-14 gap as the rest of the
suite).

**Status.** `verified` for this slice, same scope limits as the original
(n=4, 2 languages, DER from a simple energy-VAD/KMeans baseline). The 2026-09-17
numbers are void and superseded; cite only the 2026-09-20 table above.

**Card relation.** Directly qualifies the vendor's Limitations remedy. Revised
verdict: the remedy is a **real, partial improvement** (not "insufficient as
stated" in the sense of doing nothing — it does help) but does not reach
usable accuracy on its own, and the vendor's implicit assumption that any
diarization is better than none does **not** hold for a naive/toy diarizer on
this slice.
