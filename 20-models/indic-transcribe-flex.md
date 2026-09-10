---
type: model
updated: 2026-09-10
hf: "bodhan-ai/indic-transcribe-flex"
params: "1.2B"
languages: 27
base_model: "nvidia/canary-1b-v2"
license: "Indic Open Model License v1.0"
gated: true
role: "modes/ITN/romanization (Exp D), LID stats source"
---

# [[indic-transcribe-flex]]

**27-language sibling of [[indic-transcribe-core]] with three output modes.** Same FastConformer-Transformer (32L/811M encoder, 24L/419M decoder, 7,152-token BPE, 4.6 GB), `library_name: nemo` in card frontmatter vs `transformers` for Core — ⚠️ to-verify what that means for install ("model code ships in repo, no NeMo needed" claim is on both cards).
Source: [HF model card](https://huggingface.co/bodhan-ai/indic-transcribe-flex) (fetched 2026-09-10).

## The three transcription modes

| Mode | Example output | Use |
| --- | --- | --- |
| `native` | `मैंने कल पांच बजे तीन फाइलें अपलोड कीं` | recommended default |
| `mixed` (ITN) | `मैंने कल 5 बजे 3 files upload कीं` | digits + Latin English inline |
| `romanized` | `maine kal 5 baje 3 files upload kin` | search/index/UI |

API: `asr("audio.wav", lang="hi", mode="native" | "mixed" | "romanized")`; language param documented as `source_lang` in the codes section vs `lang` in examples — ⚠️ to-verify.

## Why Flex matters to this project

1. **Built-in ITN** = a *competitor* to our Exp-D normalization layer. If we build normalization, Flex `mixed` mode is the baseline to beat. The card itself warns: "mixed-script mode will occasionally get it wrong" (ITN ambiguity) → hypothesis: our semantics-preserving normalization + [[critical-value-accuracy]] metrics can expose where built-in ITN silently changes meaning. **P2-adjacent experiment.**
2. **Vendor-published LID accuracy table** (from card, per-language identify accuracy):

   | Lang | ml/ta | kn/bn | ur | mai | hi | bho |
   | --- | --- | --- | --- | --- | --- | --- |
   | acc | 0.98 | 0.96 | 0.49 | 0.36 | 0.26 | **0.05** |

   Each low-resource lang "absorbed by a close neighbour." Even *Hindi itself* is only identified 26% of the time as top-1 — presumably being split with its belt neighbours. ⚠️ These are Flex numbers; Core may differ → Exp A LID probe re-measures both.
3. Adds Chhattisgarhi (`hne`) + Haryanvi (`bgc`) vs Core — `hne` at 13.6 OI-WER is in our watch list but Core can't transcribe it; Flex can → condition set for Flex runs.

## Limitations (vendor-documented)

- Single speaker; no streaming in this tier ("use lite" — ⚠️ a `lite` model is referenced with 30 ms latency in a commented-out throughput section; status unclear)
- Romanization not standardized (model's own convention)
- Low-resource langs weak (bho, bhb)
- Noise robustness limits: overlapped speech, far-field, very low SNR

## Role in experiments

Exp A: LID-probe co-subject. Exp D: `mixed` mode as ITN baseline. Not the phase-1 baseline itself — Core is ([[D-002-core-as-baseline|D-002]]).

Related: [[indic-transcribe-core]] · [[canary-1b-v2]] · [[F-001-hindi-belt-lid-absorption|F-001]] · [[lid-reliability]]
