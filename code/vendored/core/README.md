---
extra_gated_prompt: "Please provide your details and agree to the [LICENSE](https://github.com/Bodhan-AI/bodhan-model-info/blob/main/licenses/indic-open-model-license/v1/Indic_Open_Model_License.md) [[simpler version](https://github.com/Bodhan-AI/bodhan-model-info/blob/main/licenses/indic-open-model-license/v1/Indic_Open_Model_License_Deed.md)] to request access."
extra_gated_fields:
  Company / Organization: text
  Country: country
  Intended Use Case:
    type: select
    options:
      - Research
      - Commercial
      - Education
      - label: Other
        value: other
  I agree to the license terms: checkbox
language:
- en
- as
- bn
- brx
- doi
- gu
- hi
- kn
- ks
- kok
- mai
- ml
- mni
- mr
- ne
- or
- pa
- sa
- sat
- sd
- ta
- te
- ur
- bho
- bhb
library_name: transformers
pipeline_tag: automatic-speech-recognition
base_model: nvidia/canary-1b-v2
tags:
- automatic-speech-recognition
- speech
- audio
- asr
- multilingual
- indic
- code-switching
- code-mixing
- language-identification
- canary
- fastconformer
metrics:
- wer
- cer
license: other
---

<div align="center">
  <img src="banner.png" alt="Indic-Transcribe-core Banner">
</div>

<h1 id="indic-transcribe-core" style="color:#FFD21E;">Indic-Transcribe-core</h1>

<div align="center">

[![Model Arch](https://img.shields.io/badge/Model_Arch-FastConformer--Transformer-C1440E?style=flat#model-badge)](#model-architecture)
[![Params](https://img.shields.io/badge/Params-1.2B-C1440E?style=flat#model-badge)](#model-architecture)
[![Languages](https://img.shields.io/badge/Languages-25-C1440E?style=flat#model-badge)](#supported-languages)
[![Language](https://img.shields.io/badge/Language-Multilingual-C1440E?style=flat#model-badge)](#supported-languages)
[![License](https://img.shields.io/badge/License-Indic%20Open%20Model%20License%20v1.0-C1440E?style=flat#model-badge)](#license--terms-of-use)


</div>

**Multilingual speech recognition for 25 Indian languages, in each language's native script.**

**Indic-Transcribe-core** is a multilingual Automatic Speech Recognition (ASR) model built for **25 Indian languages**. It is trained to be robust and general purpose: it handles the full diversity of Indian accents and holds up in noisy real-world conditions, from crowded markets to call-center floors, with strong coverage in the domains where Indian voice products are actually built — education, agriculture, and healthcare.

The model transcribes into the native script of the language being spoken, and can identify the language on its own when you don't know it in advance.

This model is ready for commercial use.

---

<h2 id="why-choose-indic-transcribe" style="color:#FFD21E;">Why Choose Indic-Transcribe-core?</h2>

- 🔀 **Code-mixing, natively.** Indians rarely speak one language at a time. Indic-Transcribe-core transcribes Hinglish and other mixed speech as it is actually spoken, instead of forcing it into a single language.
- 🌐 **Language identification built in.** Use the model directly as a language-ID system, or let it auto-detect the language and then transcribe — at the cost of one decoder step, not a second encoder pass.
- 🏥 **Domain coverage where it matters.** Deep vocabulary in education, agriculture, and healthcare.

---

<h2 id="supported-languages" style="color:#FFD21E;">Supported Languages</h2>

The model covers **25 languages** across four groups:

| Group | Languages |
| --- | --- |
| **Indian-accented English** | English |
| **22 constitutionally recognised languages** | Assamese, Bengali, Bodo, Dogri, Gujarati, Hindi, Kannada, Kashmiri, Konkani, Maithili, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Tamil, Telugu, Urdu |
| **Hindi dialect** | Bhojpuri |
| **Low resource** | Bhili |

---

<h2 id="model-architecture" style="color:#FFD21E;">Model Architecture</h2>

**Architecture Type:** NVIDIA Canary: FastConformer encoder with a Transformer decoder.

Indic-Transcribe-core is built on the [nvidia/canary-1b-v2](https://huggingface.co/nvidia/canary-1b-v2) architecture. The FastConformer encoder produces acoustic representations that the Transformer decoder converts into text, with task tokens selecting the target language.

|  |  |
| --- | --- |
| **Model name** | Indic-Transcribe-core |
| **Task** | Speech-to-Text (Automatic Speech Recognition) |
| **Base model** | [nvidia/canary-1b-v2](https://huggingface.co/nvidia/canary-1b-v2) |
| **Total parameters** | 1.2B |
| **Encoder** | FastConformer: 32 layers, 811M params, 1024 hidden dim, 8 attention heads, conv kernel 9 |
| **Decoder** | Transformer: 24 layers, 419M params, 1024 hidden size, 8 attention heads |
| **Vocabulary** | 7,152 tokens (1,152 special / task + 6,000 multilingual) |
| **Sub-word algorithm** | BPE (byte fallback disabled) |
| **Precision** | fp32 on disk, bf16 at inference |
| **Checkpoint size** | 4.6 GB |

<h3 style="color:#FFD21E;">Capabilities</h3>

| Feature | Indic-Transcribe-core |
| --- | :---: |
| Languages | 25 |
| Code-mixed audio | ✅ |
| Transcription output | Native script |
| Automatic language ID | ✅ |

---

<h2 id="results-at-a-glance" style="color:#FFD21E;">Results at a Glance</h2>

Accuracy is reported as **OIWER** — an orthographically-informed word error rate that accepts documented spelling and transliteration variants as correct, scored against multi-reference transcripts. **Lower is better.**

<h3 style="color:#FFD21E;">Voice of India benchmark</h3>

| Model | Average | Assamese | Bhojpuri | Bengali | Gujarati | Hindi | Chhattisgarhi | Kannada | Maithili | Malayalam | Marathi | Odia | Punjabi | Tamil | Telugu | Urdu |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Indic-Transcribe-core** | 8.7 | 8.2 | 13.3 | 4.3 | 9.2 | 3.5 | 13.6 | 7.4 | 11.3 | 11.5 | 5.7 | 8.7 | 8.3 | 9.0 | 11.4 | 5.0 |
| Saaras V3 | 10.7 | 9.1 | 17.9 | 5.2 | 9.7 | 3.8 | 14.0 | 8.8 | 14.2 | 12.2 | 6.5 | 11.1 | 8.6 | 9.1 | 13.5 | 7.5 |
| **Indic-Transcribe-flex** | 11.3 | 9.6 | 18.5 | 5.0 | 10.8 | 4.1 | 13.6 | 9.7 | 15.1 | 13.7 | 6.6 | 10.2 | 9.5 | 10.8 | 13.1 | 5.6 |
| Indic Conformer | 17.8 | 13.1 | 30.3 | 9.5 | 16.3 | 6.5 | 24.5 | 16.3 | 16.3 | 28.2 | 11.6 | 13.1 | 19.1 | 16.2 | 20.0 | 8.0 |
| Gemini 3 Pro | 21.1 | 23.7 | 24.1 | 10.3 | 18.1 | 9.3 | 19.6 | 20.1 | 27.2 | 21.0 | 14.0 | 25.7 | 19.3 | 15.5 | 24.6 | 10.6 |
| Gemini 3 Flash | 23.1 | 25.0 | 20.2 | 11.1 | 20.3 | 7.1 | 21.7 | 18.5 | 28.0 | 30.1 | 14.2 | 23.3 | 23.2 | 17.3 | 25.5 | 11.0 |
| Gemma E4B | 36.1 | 45.0 | 27.0 | 19.6 | 27.3 | 9.1 | 24.0 | 31.0 | 36.7 | 44.4 | 24.4 | 44.4 | 23.4 | 37.9 | 41.6 | 14.2 |
| OmniASR LLM 7B | 44.5 | 23.9 | 26.3 | 20.9 | 32.0 | 9.6 | 20.7 | 35.0 | 44.6 | 48.8 | 24.5 | 72.3 | 31.7 | 40.6 | 48.7 | 14.8 |
| OmniASR CTC 7B | 62.5 | 33.3 | 39.2 | 43.5 | 62.5 | 20.7 | 33.4 | 50.0 | 51.6 | 61.3 | 33.6 | 90.2 | 80.7 | 58.3 | 62.1 | 89.3 |

Indic-Transcribe Core offers better accuracy. Do check out [Indic-Transcribe Flex](https://huggingface.co/bodhan-ai/indic-transcribe-flex) for support for more transcription modes and languages. 

---


<h2 id="how-to-use-this-model" style="color:#FFD21E;">How to Use this Model</h2>

<h3 style="color:#FFD21E;">Installation</h3>

```bash
pip install torch torchaudio transformers sentencepiece soundfile
```

The model code ships inside this repository, so there is nothing else to install — no NeMo,
no other toolkit.

<details>
<summary>Conda environment (recommended for reproducibility)</summary>

```bash
conda create -n indic-transcribe python=3.10 -y
conda activate indic-transcribe
pip install torch torchaudio transformers sentencepiece soundfile
```

</details>

<h3 style="color:#FFD21E;">Input audio requirements</h3>

|  |  |
| --- | --- |
| Sample rate | 16 kHz (resampled automatically if it differs) |
| Channels | Mono |
| Formats | `.wav`, `.flac`, `.mp3` |
| Speakers | Single speaker — see [Limitations](#limitations) |

```bash
# Convert anything to the expected format
ffmpeg -i input.mp3 -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
```

<h3 style="color:#FFD21E;">Basic inference</h3>

```python
# Gated model: accept the terms on this page, then run `hf auth login` once (older installs: `huggingface-cli login`).
import sys
from huggingface_hub import snapshot_download

model_dir = snapshot_download("bodhan-ai/indic-transcribe-core")
sys.path.insert(0, model_dir)          # the model code ships inside the download

from indic_transcribe import IndicTranscribe
asr = IndicTranscribe.from_pretrained(model_dir)
print(asr("audio.wav", lang="hi"))
# मैंने कल पांच बजे तीन फाइलें अपलोड कीं
```

Output is always in the native script of the language being transcribed.

<h3 style="color:#FFD21E;">Automatic language ID + transcription</h3>

When you don't know the language ahead of time, omit `lang`. The model identifies it first,
then transcribes — at the cost of one decoder step, not a second encoder pass.

```python
text, lid = asr.transcribe("unknown_language.wav", return_lid=True)
print(lid["lang"])   # e.g. "ta"
print(text)
```

A language you supply always wins; identification only fills a gap. `return_lid=True` also
works when you *did* supply one, so a disagreement between your metadata and the model stays
visible instead of silent:

```python
text, lid = asr.transcribe("audio.wav", lang="hi", return_lid=True)
# lid == {"lang": "hi", "source": "explicit", "topk": [("hi", 0.9999), ("ur", 0.0001), ...]}
```

<h3 style="color:#FFD21E;">Language identification only</h3>

To use the model purely as a language-ID system, read the predicted language and discard the transcript.

```python
for path in ["a.wav", "b.wav", "c.wav"]:
    print(path, asr.identify(path))
    # [('ta', 0.9812), ('ml', 0.0104), ('kn', 0.0031), ...]
```

`identify` returns the ranked distribution rather than a single string, because for the
confusable pairs the top-1 alone hides how close the decision was. Accuracy is uneven across
languages — the Hindi-belt languages in particular are often absorbed by Hindi. If you have a
language label, pass it.

You can narrow the candidate set when you know your traffic:

```python
from indic_transcribe import RECOMMENDED_LANGS

asr.identify("audio.wav", allowed_langs=RECOMMENDED_LANGS)
```

This is a hard filter — audio in an excluded language is silently reassigned to the nearest
permitted one rather than flagged.

<h3 style="color:#FFD21E;">Long audio</h3>

`asr(...)` decodes a file in one pass and refuses audio longer than 45 s. That limit is
deliberate: the model trains on clips of up to 30 s, and a single pass over long audio
collapses into repetition rather than degrading gracefully. For long audio, use the chunked
helper that ships with the model. It cuts the audio at natural pauses (or at exactly 30 s
when there is none) into pieces of at most 30 s, transcribes each, and joins the text:

```python
from long_form import transcribe_long

print(transcribe_long(asr, "long_audio.wav", lang="hi"))
```

Omit `lang` and the language is identified once, from samples across the whole file.
Pass it whenever you know it — it is faster and avoids a wrong guess.

How the long-audio path works:

```text
audio (.wav / .flac / .mp3, any sample rate, mono or stereo)
  │  load → mono → 16 kHz
  ▼
lang given? ── no ──► identify it (long files: 3 × 20 s windows across the file)
  │
  ▼
≤ 30 s? ── yes ──► decode in one pass ───────────────────────────┐
  │ no                                                           │
  ▼                                                              │
split at pauses                                                  │
  • pause = ≥ 250 ms at least 25 dB below the file's peak        │
  • cut in the middle of the pause nearest 25 s                  │
  • no pause within 30 s → cut at exactly 30 s                   │
  ▼                                                              │
decode each piece (every piece ≤ 30 s)                           │
  • output looping? → split that piece at a pause, decode again  │
  • still looping?  → collapse the repeated phrase               │
  ▼                                                              │
join the pieces ─────────────────────────────────────────────────┴──► transcript
```

Pieces are kept as long as possible because every cut costs a little accuracy — the words
at a cut are the ones most likely to be wrong — and 30 s is the longest input the model
was trained on.

<h3 style="color:#FFD21E;">Command line</h3>

`inference.py` ships with the model and wraps the same calls. It picks the whole-file or
chunked path by duration, and identifies the language when `--lang` is omitted.

```bash
MODEL_DIR=$(python -c 'from huggingface_hub import snapshot_download; print(snapshot_download("bodhan-ai/indic-transcribe-core"))')

python "$MODEL_DIR/inference.py" audio.wav --lang hi
python "$MODEL_DIR/inference.py" long_call.wav --show-lang      # no --lang: identify it, and print it
python "$MODEL_DIR/inference.py" *.wav --lang ta                # several files
```

<h2 style="color:#FFD21E;">NeMo checkpoint</h2>

`nemo/` holds the same model as an NVIDIA NeMo checkpoint, for pipelines already built on NeMo.
Its config names the tokenizer class the model was trained with, which is not part of a stock
NeMo install, so `load_nemo` registers the copy that ships beside it before restoring:

```python
import sys
from huggingface_hub import snapshot_download

model_dir = snapshot_download("bodhan-ai/indic-transcribe-core")
sys.path.insert(0, f"{model_dir}/nemo")      # the loader ships inside the download

from load_nemo import load_nemo_model
model = load_nemo_model(model_dir)
print(model.transcribe(["audio.wav"], source_lang="hi", target_lang="hi", pnc="yes")[0].text)
```

Nothing inside NeMo is modified, and the loader finds the checkpoint next to itself. If you
would rather not add anything to `sys.path`, copy `nemo/canary_multilingual_tokenizer.py` into
your NeMo install beside `canary_tokenizer.py` and `restore_from` the `.nemo` directly.

**Give it a language.** Pass any of the codes in *Full list of language codes* below as both
`source_lang` and `target_lang`:

```text
as  bho  bn  brx  doi  en  gu  hi  kn  kok  ks  mai  ml  mni
mr  ne  or  pa  sa  sat  sd  ta  te  ur
```

The checkpoint keeps one shared sub-tokenizer for all of them, and the class above routes every
code to it. Without it, stock NeMo raises `RuntimeError: Unsupported language: 'ml'`. This
checkpoint writes each language in its native script.

<h3 style="color:#FFD21E;">Command line</h3>

```bash
pip install "nemo_toolkit[asr]"

MODEL_DIR=$(python -c 'from huggingface_hub import snapshot_download; print(snapshot_download("bodhan-ai/indic-transcribe-core"))')

python "$MODEL_DIR/nemo/test_nemo.py" audio.wav hi          # check the install
python "$MODEL_DIR/nemo/inference_nemo.py" audio.wav --lang hi
python "$MODEL_DIR/nemo/inference_nemo.py" long_call.wav --lang ta   # chunked automatically
python "$MODEL_DIR/nemo/inference_nemo.py" *.wav --lang bn --batch-size 8
```

<h3 style="color:#FFD21E;">Long audio</h3>

Audio over 30 s is cut at natural pauses into pieces of at most 30 s and decoded piece by
piece -- the same splitter, cap and repetition guard the Hugging Face model uses, so both
paths cut audio identically. `inference_nemo.py` does it automatically; in code:

```python
from long_form_nemo import transcribe_long_nemo

print(transcribe_long_nemo(model, "long_audio.wav", lang="hi", batch_size=8))
```

Batching the pieces makes this path the faster one for long audio: a 10-minute file takes
8 s at `batch_size=8` against 24 s at 1, and an hour of audio runs in 48 s (77x realtime,
9.2 GiB of GPU memory). Pass `lang` -- this path has no language identification of its own,
and a wrong language gives you the wrong script rather than an error.

---

<h2 id="inputs" style="color:#FFD21E;">Input(s)</h2>

| Field | Details |
| :--- | :--- |
| **Input Type(s)** | Audio, Language ID |
| **Input Format(s)** | `.wav`, `.flac`, `.mp3`; string language code |
| **Input Parameters** | One-dimensional (1D) audio; one-dimensional (1D) language ID |
| **Other Properties** | 16 kHz mono; audio is resampled automatically if it differs. Single speaker. |

---

<h2 id="output" style="color:#FFD21E;">Output</h2>

| Field | Details |
| :--- | :--- |
| **Output Type(s)** | Text string in the input language |
| **Output Format(s)** | String |
| **Output Parameters** | One-dimensional (1D) |
| **Other Properties** | Native-script rendering; optional detected-language tag. |

---


<h2 id="supported-language-codes" style="color:#FFD21E;">Supported Language Codes</h2>

Pass these to `lang`. Omit `lang` for automatic language identification.

| Example | Value |
| --- | --- |
| Hindi | `lang="hi"` |
| Tamil | `lang="ta"` |
| Bengali | `lang="bn"` |
| Indian English | `lang="en"` |
| Auto-detect | omit `lang` |

All 25 languages use standard ISO 639-1 / 639-3 codes (also listed in the `language:` field at the top of this card).

<details>
<summary>Full list of language codes (25)</summary>

| Language | Code | Script | Group |
| --- | --- | --- | --- |
| English (Indian) | `en` | Latin | Indian-accented English |
| Assamese | `as` | Bengali–Assamese | Scheduled |
| Bengali | `bn` | Bengali | Scheduled |
| Bodo | `brx` | Devanagari | Scheduled |
| Dogri | `doi` | Devanagari | Scheduled |
| Gujarati | `gu` | Gujarati | Scheduled |
| Hindi | `hi` | Devanagari | Scheduled |
| Kannada | `kn` | Kannada | Scheduled |
| Kashmiri | `ks` | Perso-Arabic / Devanagari | Scheduled |
| Konkani | `kok` | Devanagari | Scheduled |
| Maithili | `mai` | Devanagari | Scheduled |
| Malayalam | `ml` | Malayalam | Scheduled |
| Manipuri | `mni` | Bengali / Meetei Mayek | Scheduled |
| Marathi | `mr` | Devanagari | Scheduled |
| Nepali | `ne` | Devanagari | Scheduled |
| Odia | `or` | Odia | Scheduled |
| Punjabi | `pa` | Gurmukhi | Scheduled |
| Sanskrit | `sa` | Devanagari | Scheduled |
| Santali | `sat` | Ol Chiki | Scheduled |
| Sindhi | `sd` | Perso-Arabic / Devanagari | Scheduled |
| Tamil | `ta` | Tamil | Scheduled |
| Telugu | `te` | Telugu | Scheduled |
| Urdu | `ur` | Perso-Arabic | Scheduled |
| Bhojpuri | `bho` | Devanagari | Hindi dialect |
| Bhili | `bhb` | Devanagari | Low resource |

</details>

---

<h2 id="limitations" style="color:#FFD21E;">Limitations</h2>

- **Native script only.** This model transcribes into the language's own script. It does not produce mixed-script/ITN or romanized output — spoken numbers stay as words, and English words inside Indic speech are rendered in the native script. Apply your own inverse text normalization or transliteration downstream if you need it.
- **Single-speaker audio.** The model is trained for single-speaker recordings. For multi-speaker scenarios, pair it with a diarization module and transcribe each speaker turn separately.
- **Automatic language ID is uneven — do not rely on it for Hindi-belt languages.** Accuracy varies widely by language, and Bhojpuri, Maithili and Urdu are absorbed by Hindi far too often to be trusted. Pass `lang` explicitly whenever you have it.

---

<h2 id="license--terms-of-use" style="color:#FFD21E;">License / Terms of Use</h2>

Released under [Indic Open Model License v1.0](Bodhan_AI_Open_Model_License.md).

The base model, [nvidia/canary-1b-v2](https://huggingface.co/nvidia/canary-1b-v2), carries its own license terms — ensure your use complies with both.

*If you find the license difficult to understand, here is a plain-language guide to the Indic Open Model License.*

Broad, no-cost access for research, government, nonprofit, and commercial use — with a few conditions attached.

> **This deed is a human-readable summary of the license, not a substitute for it.** Where the two disagree, the full **Indic Open Model License** governs.

---

## You're free to

No cost, no royalty, worldwide — for research, government, nonprofit, and commercial use, at any scale.

- ✅ **Run it** — for inference, in a product, in research, however you like.
- ✅ **Change it** — fine-tune, distill, quantize, merge, or otherwise build on it.
- ✅ **Self-host it** — power your own product or service with it, commercial or not.
- ✅ **Share it** — pass on copies of the model or your own version of it.

---

## As long as you

Five conditions cover almost everything. The rest of the license is these, spelled out in legal detail.

### 1. Give credit

Wherever you ship the model or a derivative to anyone else, say where it came from — and don't strip out existing notices.

```
"Built with [Model Name] from Bodhan AI / AI4Bharat."
```

### 2. Pass it on the same way

If you give your fine-tuned or derived version to anyone else — hand it over, or run it as a service for them — it carries this exact license. You can't relicense it on different terms.

### 3. Ask before hosting it for others

Self-hosting is free. But if you're going to run it as an API or hosted service that *other people or companies* call directly, that needs Bodhan AI's written sign-off first — unless you're a nonprofit, government, or academic user, or you publicly release an equally capable open version within 90 days.

### 4. Don't use it to cause harm

No exceptions — not even for nonprofit or research use. That means no:

- child sexual abuse material, or content that sexualizes minors
- weapons development, including chemical, biological, radiological, or nuclear
- mass surveillance or social-scoring systems
- disinformation campaigns, including election manipulation
- automated decisions that affect someone's legal rights without human oversight
- deepfakes or voice clones of real people without their consent
- robocalls, auto-dialers, or voice-phishing scams
- AI companion products designed to simulate romance or foster emotional dependency

### 5. Talk to us if your product gets huge

If your own product built on this — not through hosting it for others, that's covered above — crosses either threshold, you'll need a separate commercial license. Doesn't apply to nonprofit, government, or academic users.

| Threshold | |
|---|---|
| **500M+** | monthly active users |
| | *or* |
| **$250M+** | annual revenue |

---

## Good to know

- **No warranty.** The model is provided as-is. It isn't tested or certified for safety-critical use — medical, aviation, nuclear, or similar — so test thoroughly before relying on it in high-stakes settings.
- **You handle your own compliance.** Export controls, sanctions, and data-protection law (including India's DPDP Act, where it applies) are on you, not Bodhan AI.
- **This deed doesn't replace the license.** It leaves out most of the legal detail — termination, dispute resolution, confidentiality, and more all live in the full text. Read that before you rely on anything here.

---

<h2 id="use-case" style="color:#FFD21E;">Use Case</h2>

Native-script transcription of multilingual and code-mixed Indian-language audio, plus language identification.

---

<h2 id="deployment-geography" style="color:#FFD21E;">Deployment Geography</h2>

Global

---

<h2 id="citation" style="color:#FFD21E;">Citation</h2>

```bibtex
@misc{indictranscribe2026,
  title  = {Indic-Transcribe: Built for the way India actually speaks},
  author = {Bodhan AI, AI4Bharat},
  year   = {2026},
  url    = {https://bodhan.ai/research/blogs/indic-transcribe}
}
```

---

<h2 id="ethical-considerations" style="color:#FFD21E;">Ethical Considerations</h2>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Developers should work with their team to ensure this model meets requirements for the relevant industry and use case, and addresses unforeseen product misuse.