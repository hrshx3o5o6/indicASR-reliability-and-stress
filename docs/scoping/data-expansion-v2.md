# Data expansion v2: scope

Status: scoping (2026-10-12). Supersedes the vague `expand-suite` Ralph task ("80 -> 300-500").
Serves three consumers: the published report, the **language arbiter** build, the **critical-value guard** build.

## 1. Why 80 -> 300-500 is the wrong target

Measured from `code/results/summaries/exp-a-v1-baseline.jsonl`:

| Language | Rows | Independent clean clips | Speakers |
|---|---|---|---|
| bho | 10 | **4** (rest are noise/telephone twins) | `unknown` |
| mai | 10 | **4** | **1** (`S4258920000324271`) |
| hi | 10 | 4 (FLEURS, studio read) | `unknown` |

So the report's headline LID result (Bhojpuri 0/10, Wilson CI [0, 27.8]) is **4 clips** with correlated twins; the CI understates uncertainty. Row count is the wrong unit. The target is **independent clips with speaker-disjoint splits**.

Other gaps the expansion must close:
- Only 11 number / 3 date / 3 currency rows exist in EXP-D: too few to build or validate a critical-value guard.
- bho has no real-noise data (EXP-F dropped it); FLEURS (hi/ta/te/ml/kn/ur) is studio read speech.
- No tune/holdout split exists; EXP-B/C scorers were developed and evaluated on the same 80 rows.

## 2. Targets (independent clean clips, each <= 30 s)

CI half-widths below are approximate, at p=0.5, normal approx. For 0/n, Wilson upper bound is about 3.84/(n+3.84).

| Stratum | Purpose | Tune | Holdout | Notes |
|---|---|---|---|---|
| bho | arbiter positive class | 60 | 60 | holdout 0/60 would bound the error at <6%; accuracy CI about +-12 pts |
| mai | arbiter positive class | 60 | 60 | need >= 10 speakers per split, not 1 |
| hi | belt "attractor" | 40 | 40 | add spontaneous IndicVoices-hi; FLEURS alone is too easy |
| ur | belt neighbour | 30 | 30 | |
| ta, te, ml, kn | do-no-harm controls | 20 each | 20 each | arbiter must not regress these |
| **Total clean** | | **~290** | **~290** | ~580 clips, of which ~240 are belt-language |
| Numbers / currency / dates / IDs (guard) | see section 4 | 60 | 60 | overlaps with the above where possible |
| Real-noise bho (optional) | closes EXP-F gap | 0 | 30 | only if a source exists |

Synthetic noise/telephone twins are **not** added at scale. Section 5 explains why: we already know they understate real degradation (F-006). Real-condition clips replace them.

## 3. Sources (see section 10 for the 2026-10-17 audit; the table below is the pre-audit plan)

| Language | Known source | Status |
|---|---|---|
| bho | Rural-Women-Bhojpuri (CC-BY-SA-4.0), used in EXP-A | Need: total clips, speaker IDs, size. If one source only, say so; speaker `unknown` makes a speaker-disjoint split impossible. |
| bho | other candidates (e.g. Vaani, Common Voice, news/radio sets) | **Unverified: check existence, license, bho coverage before relying on any.** IndicVoices has no bho (EXP-F). |
| mai | IndicVoices (CC-BY-4.0), used in EXP-A | Need: speaker count; EXP-A used 1 speaker. |
| hi, ur, ta, te, ml, kn | IndicVoices (spontaneous), Kathbath (read, numbers/names in prompts), FLEURS | Verified in project notes. |

Per-sample requirement (suite spec): `source`, `source_id`, `speaker_id`, `license`, `contamination_risk`, `synthetic`. Samples without a speaker ID get a pseudo-speaker only if the source guarantees one speaker per file; otherwise they can go in tune only and are excluded from holdout claims.

Contamination: IndicVoices and Kathbath are the vendor's own ecosystem. Record `contamination_risk` per source and report holdout results by source, so a source-specific effect is visible.

## 4. Guard-specific data

1. **Text-only (no audio, can start now).** A number-word parser needs unit cases: spoken form -> digits for hi/ta/te/ml/kn/ur/bho/mai (cardinals, lakh/crore, "dedh"/"dhai"-style irregulars, currency with rupee words, dates, digit-by-digit phone/ID readouts). Target 300+ cases written from grammar, plus every number row already in EXP-D.
2. **Audio.** >= 60 tune + 60 holdout clips each carrying numbers, currency, dates or IDs. Sources: Kathbath prompts and IndicVoices references. Slots are extracted by rule from the reference, then **human-checked on a sample**. This also resolves the 19 flagged EXP-D rows.
3. **Decodes needed per clip:** Core native, Flex native, Flex mixed. Metric = rate of *wrong digits accepted* vs *benign rewrites accepted*, not WER.

## 5. Split protocol

- **Speaker-disjoint, source-stratified** tune/holdout. A synthetic twin always stays with its clean parent.
- Tune is for building scorers and thresholds. **Holdout is run once**, after the arbiter and guard are frozen (commit hash recorded before the run).
- The v1 80-sample suite stays as an unmodified legacy set; v2 artifacts get new filenames. No v1 file is overwritten.
- Existing EXP-B/C results are re-reported on v2 holdout, since they were never held out.

## 6. Where each step runs

| Step | Runs | Needs |
|---|---|---|
| Source audit (clip counts, speakers, licenses) | Mac | HF access (gated IndicVoices token) |
| Materializer + split scripts | **here (script), Mac (run)** | pyarrow, soundfile |
| Core/Flex inference (auto-LID, top-K, native/mixed) | Mac (MPS) | local ASR service |
| Guard parser + unit tests, replay on cached EXP-D outputs | **here** | none (`compute: none`) |
| Arbiter scorer design on cached EXP-C top-K hypotheses | **here**, then re-eval on Mac | none until v2 data |
| Bootstrap/CI re-reporting | here | cached JSONL |

## 7. Order of work and gates

1. **Source audit** (Mac, about an hour): per-source clip and speaker counts, license check. *Gate:* bho has >= 60 tune + 60 holdout clips from >= 2 speakers per split; otherwise rescope bho claims to "single-source".
2. Write `materialize_v2.py` + `split_v2.py`; dry-run on the Mac.
3. In parallel here: guard parser and tests; replay on EXP-D cached outputs.
4. Run baselines on v2 (Core + Flex, auto-LID with topk saved) to re-measure EXP-A at proper n. *This alone may change the report's Bhojpuri headline; run it before finalising the report.*
5. Build arbiter on tune; freeze; run holdout once.

## 8. Risks

- **bho supply.** If no second bho source exists, the arbiter can still be built, but its bho result is single-source and must be labeled so.
- **Gated access / tokens** are on your side; I cannot reach HF from here.
- **Inference cost** scales with top-K decodes (about 4 per clip). Measure EXP-A's per-clip time on the M5 before committing to 580 clips x 4 decodes.
- **The headline may move.** A 4-clip finding re-measured at n=60 could shrink or hold; the report must be updated either way.

## 9. Decisions needed from you

1. Can you run the source audit and inference on the M5, and share the audit output (counts/speakers/licenses) back into the repo?
2. Is single-source bho acceptable as a stated limitation if no second source exists?
3. Publish the report after step 4 (re-measured at proper n) rather than before?

## 10. Source audit results (2026-10-17, run from the container, no HF token)

Method: Hub API listings + `datasets-server` row metadata. No audio downloaded. Gated repos' files (Bodhan models) still need `HF_TOKEN`, which is not set in this session.

**Bhojpuri: `ai4bharat/Rural_Women_Bhojpuri` is public (not gated), CC-BY-SA-4.0, and much bigger than EXP-A used.**

| Split | Rows | Notes |
|---|---|---|
| benchmark | 444 | Real, read, 0.5-23 s (median 10 s). **No speaker IDs** (all `None`); 3 districts (Mirzapur 177, Jaunpur 138, Bhadohi 129). Task domains: digital financial (177), health (129), government schemes (90), agriculture (48). |
| train_real | 400 | **100 speakers**, 4 rows each. 200 Bhojpuri + 200 *Hindi* (same speakers); Read/Extempore split 200/200. |
| train_synthetic | 77,967 | **Exclude** (synthetic). |

Consequences:
- Bhojpuri supply is not the bottleneck: 200 real Bhojpuri rows with speaker IDs allow a speaker-disjoint split (e.g. 50/50 speakers), plus up to 444 benchmark rows.
- **Same speakers record both Bhojpuri and Hindi**, which gives the arbiter a speaker-controlled bho-vs-hi test.
- Benchmark references are dense in numbers, currency, and card/account digit strings (e.g. "tirānbe hazār rupiya", digit readouts, "double zero"). This is a ready-made Bhojpuri set for the critical-value guard.
- Caveat: benchmark rows have no speaker IDs, so they can go in the tune set or be split by district only; holdout claims should rest on `train_real` speakers.
- `Devvrat024/Rural_Women_Bhojpuri` is an identical-schema copy (same splits and sizes); not an independent source.

**Other Bhojpuri audio on the Hub (unvetted):** `KonthouKabiAI/bhojpuri-lr-v3` (audio+sentence, about 30k rows, no license, no speaker field), `1rsh/speech-qa-bhojpuri-hi-karya` (390 rows, no license). Provenance and licensing unknown; treat as optional, not for holdout.

**Maithili:** `ai4bharat/IndicVoices` has a `maithili` folder (72 shards, 29.4 GB; gated "auto"; README readable, shards need the token). No Bhojpuri folder in IndicVoices, confirming EXP-F. Other Maithili speech sets found (`DataoceanAI/India_Maithili_Speech_Recognition_Corpus`, `mlwiseyak/raw_maithili_audio_data_new`) are unvetted. Per-speaker counts for IndicVoices Maithili still need a token to read the `speaker_id` column.

**Other IndicVoices languages present:** hindi, urdu, tamil, telugu, kannada, malayalam (all needed for controls and belt languages).

### Correction to section 1
The Bhojpuri/Maithili clean clips are 4 distinct source files each (distinct `source_id`), so "4 independent clips" stands. The source of the "unknown" Bhojpuri speaker is the benchmark split itself (no speaker IDs), not a pipeline loss. But the larger finding below changes how to read the EXP-A audio.

### New anomaly: EXP-A clean clips are padded to about 50 s
- `regional-bho-001` (reference "kirpa karke hamra debit card se tiranbe hazar rupiya ...") is **48.8 s** in EXP-A. The same utterance in the source benchmark (row 0) is **7.45 s**.
- Core's transcript covers just that one utterance (no tiling/repetition), so the extra length is most likely padding.
- Across all 8 languages EXP-A clean clips are 43-56 s (one 4 s outlier) regardless of reference length. The builder scripts (`materialize_regional_seed.py`, `build_exp_a_stratified.py`, `materialize_fleurs_seed.py`) do not pad, so the cause is upstream and undocumented.
- Why it matters: auto-LID may behave differently on a 7 s utterance in 41 s of padding than on the bare utterance. The Bhojpuri 0/10 result and the F-005/F-007 comparisons should be re-measured on **unpadded** clips before being published.
- Action: add to step 4 below: re-run Bhojpuri/Maithili auto-LID on unpadded originals, same model snapshot, and compare to the padded result.

### Updated gate for step 1
Bhojpuri: **passes** (>= 60 tune + 60 holdout clips from >= 2 speakers per split is achievable from `train_real`: 100 speakers, 200 clips; benchmark rows add volume without speaker IDs).
Maithili: **open** until an `HF_TOKEN` can read IndicVoices `speaker_id`.
