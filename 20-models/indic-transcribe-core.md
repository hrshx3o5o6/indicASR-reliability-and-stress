---
type: model
updated: 2026-09-17
hf: "bodhan-ai/indic-transcribe-core"
params: "1.2B"
languages: 25
base_model: "nvidia/canary-1b-v2"
license: "Indic Open Model License v1.0"
gated: true
role: "baseline (Exp A)"
---

# [[indic-transcribe-core]]

**Multilingual ASR for 25 Indian languages, native-script output.** Released 5 Sep 2026 by Bodhan AI / AI4Bharat. Fine-tune of [[canary-1b-v2]].
Source: [HF model card](https://huggingface.co/bodhan-ai/indic-transcribe-core) (fetched 2026-09-10).

## Verified facts

|              |                                                                                                                                                                         |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Architecture | FastConformer encoder (32L, 811M) + Transformer decoder (24L, 419M)                                                                                                     |
| Vocab        | 7,152 tokens (1,152 special/task + 6,000 multilingual), BPE, byte fallback **disabled**                                                                                 |
| Checkpoint   | 4.6 GB, fp32 on disk / bf16 at inference                                                                                                                                |
| Audio in     | 16 kHz mono (auto-resampled), wav/flac/mp3, **single speaker**                                                                                                          |
| Output       | Native script only — no ITN, no romanization, spoken numbers stay words                                                                                                 |
| Code-mixing  | Native handling (Hinglish etc. as spoken)                                                                                                                               |
| LID          | Built in, one extra decoder step (not a second encoder pass)                                                                                                            |
| License      | Indic Open Model License v1.0 — free research/commercial self-host; hosted-API use needs written consent (nonprofit/acad exempt); ⚠️ fine-tunes must carry same license |

**Gated repo:** requires accepting the license on HF before `snapshot_download` works → this is Day-1 setup friction, do it first. ⚠️ to-verify: exact token/env handling (`HF_TOKEN`).

## Inference API (from model card — ⚠️ to-verify against actual repo code)

```python
from huggingface_hub import snapshot_download
from indic_transcribe import IndicTranscribe          # model code ships in the repo, no NeMo needed
asr = IndicTranscribe.from_pretrained(snapshot_download("bodhan-ai/indic-transcribe-core"))

asr("audio.wav", lang="hi")                            # plain transcription
text, lid = asr.transcribe("a.wav", return_lid=True)   # auto-LID + transcript
# lid == {"lang": "ta", "source": "auto", "topk": [("ta", 0.97), ...]}
text, lid = asr.transcribe("a.wav", lang="hi", return_lid=True)
# lid["source"] == "explicit" → disagreement metadata/model stays visible
asr.identify("a.wav")                                  # ranked distribution, LID-only
# [("ta", 0.9812), ("ml", 0.0104), ("kn", 0.0031), ...]
from indic_transcribe import RECOMMENDED_LANGS
asr.identify("a.wav", allowed_langs=RECOMMENDED_LANGS) # HARD filter — excluded audio is
                                                       # silently reassigned, never flagged
```

## Why this API is a gift for this project

1. `return_lid=True` gives **ranked LID top-k + explicit/explicit-source flag** → the exact features [[lid-reliability]] needs (entropy, margin, top-1) with zero hacking.
2. `source: explicit` disagreement = free signal: *model disagrees with your known label*.
3. `allowed_langs` silent reassignment is a designed probe: restrict candidates to {hi, bho, mai} and measure how often bho audio "becomes" hi. Direct measurement of absorption ([[F-001-hindi-belt-lid-absorption|F-001]]).

## What the card does NOT document — RESOLVED by code audit (vendored @ `4d29eeb7a099`, 2026-09-10)

| Question | Verdict |
| --- | --- |
| Token-level probabilities? | **Yes, via DIY hook** — `transcribe(**generate_kwargs)` passes through to HF `generate()`; pass `output_scores=True, return_dict_in_generate=True` and hold `asr.model`. Not exposed in the wrapper's return. |
| Timestamps? | **No** — no alignment path anywhere in the wrapper/model API. |
| Beam vs greedy? | **Greedy default** (`generation_config.json`: `num_beams: 1, do_sample: false`); beam is caller-selectable via generate_kwargs. |
| LID calibration / temperature? | Plain fp32 softmax over raw logits, one decoder step (`lid.py::lid_from_encoder_states`). Vendor's own verdict: **"There is no useful default confidence threshold"** (see [[F-002-vendor-lid-internals]]). |
| `transcribe` vs `identify` consistency? | **Same path** — both call `lid_from_encoder_states` on the same encoder states; `transcribe(lang=None)` reuses the encoder output. Cannot disagree. |
| `RECOMMENDED_LANGS`? | 27 minus `bhb` **only** — docstring says "minus bgc,bhb" but code excludes just `bhb`. ⚠️ Docstring/code mismatch; confirm intended set with vendor or measure both. |

**Card-vs-code contradictions (audit findings):**
- Card says native-script-only; **code exposes all three modes on Core too** (`native/mixed/romanised` — shared wrapper with Flex, `MODES` in `indic_transcribe.py`). Vendor's marketing cut the API docs, not the capability.
- Card says 25 languages; `LANGUAGES` tuple in code has **27** (includes `hne`, `bgc`) — matches Flex's list. LID metrics quoted in `lid.py` are over this 27-lang checkpoint line.

**Hard operational constraints (from code):**
- `max_seconds=45` default — longer clips **raise**, by design ("221 s file → 149 words vs 450-word reference"). Suite must use ≤30 s clips; long-form needs chunking (out of scope v0).
- Short clips (<1 s) are centre-padded to 1 s, matching training.
- `WEAK_LID_LANGS = {bho, hi, mai, ur}` — `transcribe(lang=None)` emits a **UserWarning** when LID lands on one of these. Catch warnings in the runner → free feature.
- Wrapper refuses to chunk; whole-file decode only. `all_modes()` helper exists (one encode, 3 decodes).
- hi/ur: vendor code says the pair "genuinely cannot be separated" — resolve from metadata ([[F-002-vendor-lid-internals]]).

## Local run setup (verified on this machine)

- Apple M5, no CUDA → device `mps`, dtype fp32 (wrapper forces fp32 on non-CUDA: `dtype = bf16 only if cuda`). M5 unified memory handles 4.6 GB fp32 fine.
- `.venv` (python 3.12, uv), torch 2.14.0 (MPS ✓), transformers 5.17.0, jiwer 4.0.0, snapshot @ `4d29eeb7a099`; local checkpoint and loader view verified on 2026-09-13.
- Secrets in `code/.env` (gitignored). Weights via `scripts/download_model.py`.

## Vendor-reported Voice of India OI-WER (⚠️ re-measure, don't trust)

Avg **8.7** · hi 3.5 · bn 4.3 · ur 5.0 · mr 5.7 · kn 7.4 · as 8.2 · pa 8.3 · or 8.7 · ta 9.0 · gu 9.2 · ml 11.5 · te 11.4 · mai 11.3 · bho 13.3 · (hne 13.6, not a Core language)

## Documented limitations (quoted intent, our stress tests below)

- Native script only → ITN is downstream (our Exp D territory)
- Single speaker → diarization pairing needed (Exp E)
- **"Bhojpuri, Maithili and Urdu are absorbed by Hindi far too often to be trusted. Pass `lang` explicitly whenever you have it."** — vendor's own words; P3 of [[THESIS]] predicts we confirm and quantify this.

## Card re-check 2026-09-17 (current card modified 2026-09-15 — NEWER than our snapshot)

Both cards were updated 2026-09-15 (HF API `lastModified`), i.e. **after** our 09-10 card fetch and code audit. Full re-fetch: `/tmp/core-card.md` (verbatim copy, 2026-09-17).

| Item | Card (current, 09-15) | Ours (EXP-A–E) | Verdict |
| --- | --- | --- | --- |
| OI-WER avg 8.7 (VOI) | same numbers as 09-10 card; now with a **competitive table** (Saaras V3 10.7, Flex 11.3, Gemini 3 Pro 21.1, Indic Conformer 17.8) | Our whitespace-token WER on our challenge slice: **22.0%** mean, ml 34.1%, condition-spread mild (clean 21.2 / noise 23.2 / telephone 22.0) | Not comparable — different corpora/metric; our slice is harder + 80 samples. Directionally consistent (language variance >> condition variance). |
| "Bhojpuri, Maithili and Urdu are absorbed by Hindi far too often to be trusted. Pass `lang` explicitly." (Limitations) | unchanged | [[F-001]] verified: bho auto-LID 0/10 correct; hi/mai/ur 10/10 | **Confirmed** (absorption one-directional in our slice) |
| "handles noisy real-world conditions, from crowded markets to call-center floors" (intro) | unchanged | clean vs noise vs telephone: 21.2 / 23.2 / 22.0 WER on deterministic transforms | No contradiction on *mild* synthetic degradation; untested on real markets/call-center audio |
| "Single speaker … pair it with a diarization module and transcribe each speaker turn separately" | unchanged | [[F-003]]: oracle-turn WER 99.8% on DiarBench slice | **Qualified**: remedy insufficient as stated — short-turn context also needed |
| NEW since 09-10: **long-audio section** — 45 s hard refusal is "deliberate", `long_form.py` ships pause-splitting chunker (≤30 s pieces, loop-collapse), `inference.py` CLI | Our vendored snapshot `4d29eeb7a099` has **no `long_form.py`/`inference.py`** (verified via repo tree listing 09-17: both now in repo, `lid.py` 10.5 KB) | EXP-E pilot used raw turn cuts; sub-1s turns centre-padded to 1 s per code audit | **Repo updated after our vendoring** — re-vendor `long_form.py`, `inference.py`, and diff `indic_transcribe.py`/`lid.py` before any further code claims. Chunker targets long audio, not short conversational turns |
| "Automatic language ID is uneven" + `identify` ranked-distribution rationale | unchanged, now with explicit ml/ta vs bho/hi/mai/ur examples | EXP-A 87.5% top-1; EXP-C top-3 coverage 79/80 | Confirmed; unevenness is language-concentrated |
| Capabilities table: "Code-mixed audio ✅", "Transcription output: Native script" | unchanged | EXP-D: Core native entity recall 49.6%, number surface 59.1% — code-mixing handling untested in our suite | ⚠️ Untested claim in our experiments so far |

**Claimable statements (evidence-backed, scoped):**
1. Core's own Limitations admit Hindi-belt LID untrustworthiness; we measured bho 0/10 on our suite ([[F-001]]) — consistent, strengthens the vendor's own warning with independent numbers.
2. The vendor's multi-speaker remedy is **necessary but not sufficient**: oracle turns alone fail on real conversational audio ([[F-003]]).
3. Flex `mixed` ITN trades critical-value integrity for formatting: currency 100%→0%, entity 49.6%→20.5% surface recall ([[F-004]]) — quantifies the card's "occasionally wrong".
4. Vendor OI-WER (8.7) and our challenge-slice WER (22.0%) differ by design: different corpora, different metric; **we cannot claim the vendor number is wrong, only that it does not transfer to our slice**.

## Related

[[indic-transcribe-flex]] (sibling, 27 langs, 3 output modes) · [[canary-1b-v2]] (base) · [[PIPELINE]] · [[oi-wer]]
