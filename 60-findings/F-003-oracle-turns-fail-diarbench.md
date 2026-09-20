---
type: finding
id: F-003
title: "Oracle-turn transcription fails on DiarBench — the vendor's diarize-then-transcribe remedy is insufficient as stated"
status: retracted-pending-rerun
confidence: "invalid — WER figures were a pipeline bug, not a model result"
metric: wer
updated: 2026-09-20
---

# F-003 — Oracle turns do not rescue Core on conversational audio

**Claim (as originally stated, now retracted).** [[indic-transcribe-core]] produces near-empty transcripts on real two-speaker conversational turns **even when given oracle speaker-turn boundaries**, implying the vendor's diarize-then-transcribe remedy is insufficient.

**⚠️ 2026-09-20 audit — the evidence was a code bug, not a model finding.** `IndicTranscribe.transcribe()` returns a bare `str` unless called with `return_lid=True` (`code/vendored/core/indic_transcribe.py:141-201`). `code/run_exp_e.py`'s `transcribe_clip()` called `asr.transcribe(...)[0]` without `return_lid=True` — every EXP-A/EXP-D call site correctly unpacks `text, lid = asr.transcribe(..., return_lid=True)`, but EXP-E's `[0]` indexed the **first character of the returned string**, not a tuple element. Verified directly against the per-sample records (`exp-e-pilot-results.jsonl`, SSD): `no_diarization_transcript` for a 60 s, two-chunk clip was literally `"य उ"` (2 characters for 2 chunks); `oracle_turn_transcript` token counts matched `num_reference_segments` exactly in all 4 recordings (23/23, 12/12, 30/30, 27/27) — i.e. **exactly one character was ever kept per ASR call**, independent of clip length (some oracle segments were 5-27 s long). That pattern is a string-indexing bug, not a "model degrades on short turns" signal — a genuine degradation would still emit partial words. Bug fixed 2026-09-20 (dropped the `[0]`); see the note in `run_exp_e.py`.

**What survives.** `automatic_der` (62.51% mean) does not depend on transcript text — it compares predicted vs. reference speaker-time segments — so the *diarization-quality* number is unaffected by this bug and remains a directionally valid (if toy-baseline) result. All **WER-based** numbers (no-diarization 99.91%, oracle-turn 99.80%, automatic 100.00%) are void.

**Provenance.** `exp-e` (measured 2026-09-17, Core snapshot `4d29eeb7a099`); bug found and code fixed 2026-09-20; **not yet re-run** (requires the ASR service, currently offline — `asr_url` unset).

**Status.** `retracted-pending-rerun`. The real oracle-turn WER on this slice is **unknown** until `code/run_exp_e.py` is re-run against a live model. Do not cite the 99.8%/99.91%/100% WER figures anywhere. The DER figure (62.51%, toy VAD/KMeans baseline) may still be cited as a rough diarization-quality signal.

**Card relation.** No claim can currently be made about whether the vendor's diarize-then-transcribe remedy is sufficient or not on this slice — re-open once EXP-E is re-run.
