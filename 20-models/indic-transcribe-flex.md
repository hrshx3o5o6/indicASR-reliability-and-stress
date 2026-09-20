---
type: model
updated: 2026-09-20
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

## Card re-check 2026-09-17 (current card modified 2026-09-15 — NEWER than our snapshot)

Full re-fetch: `/tmp/flex-card.md` (verbatim copy, 2026-09-17). Card body largely unchanged from our 09-10 extract; LID accuracy table (bho 0.05 / hi 0.26 / mai 0.36 / ur 0.49 vs ml/ta 0.98) is still present. New since 09-10: the same **long-audio section** as Core (`long_form.py`, `inference.py` CLI) — re-vendor from the Flex repo before use.

| Card claim | Ours (EXP-A–E) | Verdict |
| --- | --- | --- |
| VOI OI-WER avg 11.3 + competitive table | Flex native WER 22.09% vs Core 22.01% on our slice — effectively tied | Not comparable (corpus/metric); consistent in *direction*: Flex ≤ Core in vendor table, tied in our slice |
| "mixed-script mode will occasionally get it wrong" (Limitations) | [[F-004]]: mixed WER 33.54%, currency surface 100%→0%, entity 49.6%→20.5% | **Confirmed and quantified** — "occasionally" understates critical-value failures; card's own advice ("native-script mode recommended, apply your own ITN downstream") matches our no-go verdict |
| Mixed mode = "native words in native script with English and numerals in Latin" | Mixed emitted digit-like tokens 15/80, Latin tokens 62/80; only mode with digit-form number recall (77.3%) | Confirmed as behavior; the ITN capability is real but unsafe on critical values |
| LID table bho 0.05 | Core EXP-A: bho 0/10 correct ([[F-001]]); vendor table is Flex's | Consistent — both checkpoints fail bho LID |
| "Noise robustness has limits … overlapped speech, far-field, very low SNR" | Untested on Flex (our degraded conditions ran on Core only) | ⚠️ Untested claim in our experiments |
| Modes also work on long audio via `transcribe_long` | Not tested; `long_form.py` missing from our vendored snapshot | ⚠️ to-verify after re-vendoring |

**Claimable statements:** see [[indic-transcribe-core]] re-check §claimable — the Flex mixed no-go ([[F-004]]) is the strongest Flex-specific evidence.

## Re-vendor + card re-check 2026-09-20

**First time Flex has been vendored** (previously only Core was — a real gap,
now closed). Current HF revision `c0db6b2b...`, text/code files only, see
`code/vendored/flex/REVISION`.

- Card diff vs the 09-17 fetch (`/tmp/flex-card.md`): only the new NeMo
  checkpoint section was added (same as Core — `nemo/` dir, `transcribe_long_nemo`,
  vendor-claimed 77x realtime / 9.2 GiB GPU for 1 hour audio, untested by us).
  Every other section (limitations, LID accuracy table, mode descriptions,
  competitive benchmark table) is byte-identical to the 09-17 capture.
- **F-005 (new): Flex's `transcribe()` restricts default auto-LID to
  `RECOMMENDED_LANGS` (excludes `bgc`, `bhb`); Core's does not.** Found by
  diffing `indic_transcribe.py` between the two now-vendored repos — this is
  new information, not in either card, not in our prior dossiers. The
  vendor's own inline comment discloses a quantified effect (pa 0.620→0.775
  on VOI over 337k clips, excluding sink languages), which we have not
  independently verified. Full writeup: [[F-005]]. Practical effect on this
  project: none of our existing measurements change (all our auto-LID runs
  used Core), but the "same wrapper" framing above needs this caveat, and any
  future Flex-vs-Core LID comparison must control for it.
- `TRAINED_LANGS` in `lid.py` is correctly 27 for Flex (vs Core's 25) —
  consistent with the card and with `20-models/indic-transcribe-core.md`'s
  correction of the earlier F-002 note (that note's "27" referred to the
  mode-validation `LANGUAGES` tuple, which is shared and identical on both
  models, not the LID-specific `TRAINED_LANGS`).

Related: [[indic-transcribe-core]] · [[canary-1b-v2]] · [[F-001-hindi-belt-lid-absorption|F-001]] · [[F-004-flex-mixed-critical-values|F-004]] · [[F-005-flex-only-auto-lid-restriction|F-005]] · [[lid-reliability]]
