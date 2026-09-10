---
type: model
updated: 2026-09-10
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

| | |
| --- | --- |
| Architecture | FastConformer encoder (32L, 811M) + Transformer decoder (24L, 419M) |
| Vocab | 7,152 tokens (1,152 special/task + 6,000 multilingual), BPE, byte fallback **disabled** |
| Checkpoint | 4.6 GB, fp32 on disk / bf16 at inference |
| Audio in | 16 kHz mono (auto-resampled), wav/flac/mp3, **single speaker** |
| Output | Native script only — no ITN, no romanization, spoken numbers stay words |
| Code-mixing | Native handling (Hinglish etc. as spoken) |
| LID | Built in, one extra decoder step (not a second encoder pass) |
| License | Indic Open Model License v1.0 — free research/commercial self-host; hosted-API use needs written consent (nonprofit/acad exempt); ⚠️ fine-tunes must carry same license |

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

## What the card does NOT document (→ Exp A open questions)

- [ ] Token-level probabilities / decoder logprobs — available? how?
- [ ] Timestamps / word-level alignment — available?
- [ ] Beam vs greedy decoding; is decoding config exposed?
- [ ] `identify()` softmax temperature / calibration of those top-k numbers
- [ ] Do `transcribe` and `identify` share the same LID path (consistency)?
- [ ] `RECOMMENDED_LANGS` contents

## Vendor-reported Voice of India OI-WER (⚠️ re-measure, don't trust)

Avg **8.7** · hi 3.5 · bn 4.3 · ur 5.0 · mr 5.7 · kn 7.4 · as 8.2 · pa 8.3 · or 8.7 · ta 9.0 · gu 9.2 · ml 11.5 · te 11.4 · mai 11.3 · bho 13.3 · (hne 13.6, not a Core language)

## Documented limitations (quoted intent, our stress tests below)

- Native script only → ITN is downstream (our Exp D territory)
- Single speaker → diarization pairing needed (Exp E)
- **"Bhojpuri, Maithili and Urdu are absorbed by Hindi far too often to be trusted. Pass `lang` explicitly whenever you have it."** — vendor's own words; P3 of [[THESIS]] predicts we confirm and quantify this.

## Related

[[indic-transcribe-flex]] (sibling, 27 langs, 3 output modes) · [[canary-1b-v2]] (base) · [[PIPELINE]] · [[oi-wer]]
