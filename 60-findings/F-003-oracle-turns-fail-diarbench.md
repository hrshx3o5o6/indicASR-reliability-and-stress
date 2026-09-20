---
type: finding
id: F-003
title: "Oracle-turn transcription fails on DiarBench — the vendor's diarize-then-transcribe remedy is insufficient as stated"
status: verified
confidence: "high for this 4-recording slice; small-n, 2 languages"
metric: wer
updated: 2026-09-17
---

# F-003 — Oracle turns do not rescue Core on conversational audio

**Claim.** [[indic-transcribe-core]] produces near-empty transcripts on real two-speaker conversational turns **even when given oracle speaker-turn boundaries**. The vendor's Limitations remedy — *"pair it with a diarization module and transcribe each speaker turn separately"* — is necessary but not sufficient on this slice.

**Evidence.** [[EXP-E]] pilot, `data/challenge/results/exp-e/exp-e-pilot-summary.json` (SSD): 4 Indic DiarBench recordings (2 hi, 2 ta; near/far field; ~60 s each; 2 speakers each). No-diarization WER 99.91% · oracle-turn WER 99.80% · automatic VAD/KMeans WER 100.00% · automatic DER 62.51%. Post-run audit: Core emits 1–2 characters on many annotated turns, including sub-second oracle cuts; a direct annotated-turn decode reproduced the failure. Runner: `code/run_exp_e.py`.

**Provenance.** `exp-e` (measured 2026-09-17, Core snapshot `4d29eeb7a099`).

**Interpretation.** The failure is not diarization quality — oracle turns fail too — it is turn-context/short-segment behavior: Core trains on ≤30 s single-speaker clips and degrades on very short conversational cuts. Next iteration: turn padding/context plus a neural diarizer ([[EXPERIMENT-OBSERVATIONS]] next actions). The card's 45 s limit and `long_form.py` pause-splitting chunker (documented since 09-15) target *long* audio, not short turns — they do not touch this failure.

**Status.** `verified` for this slice (oracle comparison measured end-to-end). Scope limits: 4 recordings, 2 languages, DER from a simple energy-VAD/KMeans baseline. **If turn padding rescues short turns:** the claim narrows to "raw oracle cuts are insufficient" — expected EXP-E iteration 2. **If padding fully rescues:** record that the vendor remedy works with minimal engineering.

**Card relation.** Directly qualifies a Limitations claim on the current [[indic-transcribe-core]] card. This is a *measured qualification*, not a contradiction — the card never claims turn-by-turn transcription works, it only prescribes it.
