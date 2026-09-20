---
type: report
title: "Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model"
status: draft-reviewed
version: 0.6
updated: 2026-09-20
model_snapshots:
  core: "bodhan-ai/indic-transcribe-core@e083ab7d"
  flex: "bodhan-ai/indic-transcribe-flex@c0db6b2b"
---

# Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model

> **Draft, reviewed (2026-09-20).** Every numeric claim below links to the
> artifact that produced it, either committed under `code/results/` or on the
> research SSD (`data/challenge/`, path noted per artifact). This pass: found,
> fixed, and re-measured a pipeline bug that had produced a false
> near-total-failure claim (§5.5/F-003, real result: +9pt improvement from
> oracle turns, naive auto-diarization worse than nothing), reconciled an
> internal denominator contradiction (§5.4), re-vendored both models and
> found a real Core/Flex divergence on Bhojpuri LID (§5.8/F-005), ran
> the previously-unrun real-noise pilot and found our own synthetic transform
> understates real degradation ~10x (§5.6/F-006), added bootstrap 95% CIs to
> every headline number (§7), closed the OI-WER TODO (§5.7/D-006), and locked
> dependencies + committed the replication bundle (§9). Remaining open items:
> suite expansion past 80 samples, a neural diarizer rerun of EXP-E, human
> semantic verification of the 19 flagged EXP-D rows — all in §8/§9. Do not
> move a claim from §7 into the Abstract until its artifact is in the
> replication bundle (§9).

---

## Abstract

State-of-the-art Indic ASR is no longer the dominant bottleneck: the released model
scores well on its own benchmark. The bottleneck is knowing when a transcription can
be trusted and why it fails. We characterize the reliability envelope of
`indic-transcribe-core` and sibling `indic-transcribe-flex` on an 80-sample suite plus
a 56-clip real-noise pilot. Our own synthetic noise transform, used throughout,
understates real-world degradation by roughly 10x: real noise costs +20.6 WER points
(95% CI [4.9,36.4], p=0.009) versus a statistically null +2.0 points from synthetic
noise. Vendor-reported Hindi-belt LID absorption reproduces on Core (Bhojpuri 0/10) but
not Flex (4/10, absorbed by Maithili not Hindi) despite tied WER — absorption is
model-specific. Flex mixed-mode ITN collapses currency recall 100%→0% while raising
WER. A naive automatic diarizer makes multi-speaker transcription worse than no
diarization (82.6% vs 66.6%). Every headline number carries a bootstrap 95% CI. Suite,
runners, results released. *Scope: small, partly synthetic/real-pilot, directional.*

---

## 1. Introduction

- SOTA released Aug/Sep 2026; vendor benchmark OI-WER 8.7 avg on Voice of India.
- The remaining bottleneck is the layer *above* the model (see `10-thesis/THESIS.md`).
- Contributions (each must map to a §7 claim):
  1. A structured, provenance-annotated challenge suite (`50-dataset/challenge-suite-spec.md`,
     `50-dataset/annotation-schema.md`).
  2. Independent measurement of documented LID absorption (`F-001`, `F-002`).
  3. A negative result for interpretable reliability features (`EXP-B`) and a
     positive headroom result for top-K language generation (`EXP-C`).
  4. A quantified safety failure of built-in ITN for critical values (`F-004`).
  5. A retracted-and-fixed pipeline bug in the multi-speaker remedy check (`F-003`) —
     kept in the report as a worked example of catching a bad number before publication.
  6. A code-audit finding, not present in either vendor card, that Core and
     Flex diverge on default auto-LID candidate restriction (`F-005`).
  7. Evidence that this project's own synthetic noise transform, used
     throughout, understates real-world degradation by roughly 10x (`F-006`).
- **Not claimed:** model quality verdict, full real-world noise robustness
  characterization (n=56 pilot, one real corpus), code-mixing.

## 2. System under test

| | Core | Flex |
|---|---|---|
| Params / base | 1.2B / canary-1b-v2 | 1.2B / canary-1b-v2 |
| Languages | 25 | 27 |
| Snapshot | `e083ab7d...` (re-vendored 2026-09-20) | `c0db6b2b...` (vendored 2026-09-20, first time) |
| Role | baseline (D-002) | modes/ITN (EXP-D) |

Verified API surface and card-vs-code deltas: `20-models/indic-transcribe-core.md`,
`20-models/indic-transcribe-flex.md`, `F-002`, `F-005`.
Key code facts: 45 s hard cap, no timestamps, token log-probs via generate passthrough,
Core exposes `native/mixed/romanised` though its card says native-only.
**Re-vendored 2026-09-20** (was: TODO after the 2026-09-15 HF update). Both
models now ship `long_form.py`/`inference.py` and a new NeMo checkpoint
distribution (untested by us, needs GPU). All EXP-A–E measurements were taken
against the pre-update snapshot (`4d29eeb7a099`) — the diff changed
`max_new_tokens`'s default (256→512, no effect: all runners pass it
explicitly) and nothing else that touches our runners; `transcribe()`'s
`return_lid` contract (root cause of the F-003 bug) is unchanged in the
current code. New finding from the diff: **F-005** — Flex's `transcribe()`
restricts default auto-LID to `RECOMMENDED_LANGS`; Core's does not. Neither
card documents this. Empirically tested (§5.8): Flex recovers 4/10 on
Bhojpuri where Core gets 0/10 — real, model-specific — but *not* explained by
this restriction (`bho` isn't in the excluded set); the actual cause is open.

## 3. Challenge suite

- 80 rows = 10 per language × `{hi, ta, te, ml, kn, ur, bho, mai}`.
- 32 real clean + 24 paired synthetic background-noise + 24 paired telephone
  (48 synthetic, twins preserved via `clean_twin`).
- Sources: FLEURS (hi/ta/te/ml/kn/ur), Rural-Women-Bhojpuri (bho),
  IndicVoices (mai). Per-source licenses recorded in manifest.
- Reproduce: `docs/REPRODUCE.md`; manifest `data/challenge/manifests/exp-a-v1-80.jsonl`.

## 4. Metrics

| Metric | Status | Note |
|---|---|---|
| Whitespace-token WER | used | not OI-WER; pending |
| Exact match rate | used | |
| LID top-1 / top-K accuracy | used | |
| Selective prediction (AURC/AUROC/risk–coverage) | used | |
| Critical-value / entity surface recall | used | exact-surface only |
| DER | used | toy baseline only |
| OI-WER | done (project definition, §5.7) | normalization-tolerant + multi-reference; **not** the vendor's undisclosed OI-WER implementation |

Definitions and pitfalls: `30-metrics/` (registry `30-metrics/METRICS.md`).

## 5. Experiments

Each subsection: Question · Protocol · Artifact · Result · Verdict · Scope limits.

### 5.1 EXP-A — Baseline census
- Result: 80/80 runs; WER **22.01%**; exact match 3.75%; LID top-1 **87.5%**;
  warnings 50%.
- Per-language WER: `te` 14.8, `bho` 14.1, `hi` 14.0, `ta` 22.4, `mai` 23.4,
  `kn` 24.3, `ur` 29.0, `ml` 34.1.
- Per-condition WER: clean 21.2 / noise 23.2 / telephone 22.0.
- Strongest signal: bho auto-LID **0/10** — Wilson 95% CI **[0%, 27.8%]** (n=10).
- Artifact: `results/exp-a-v1-summary.json`, CI: `code/results/stats/bootstrap.json`.
  Verdict: done, directional.

### 5.2 EXP-B — Reliability + abstention (negative result)
- 14 features (one constant removed), LOO logistic regression.
- OOF ROC-AUC **0.515** (bootstrap 95% CI **[0.387, 0.646]** — spans 0.5,
  consistent with "no better than chance"); AP 0.615; Brier 0.279; AURC 0.404.
- Policy: **all 80 ABSTAIN** (no cutoff met ≤10% risk @ ≥25% coverage / ≤25% @ ≥50%).
- Artifact: `results/exp-b-v1/exp-b-summary.json`, CI: `code/results/stats/bootstrap.json`.
  Verdict: killed; guardrail correct.

### 5.3 EXP-C — Adaptive LID / top-K decoding (mixed)
- top-3 truth coverage **79/80**; baseline WER 24.87 → adaptive 25.00 → oracle **22.38**.
- Paired bootstrap (baseline − oracle, n=80): mean diff **2.48 pts, 95% CI
  [1.04, 4.20] pts**, excludes zero, p≈0.0002 — the headroom is statistically
  real, not resampling noise.
- bho selected-language accuracy 0/10.
- Artifact: `results/exp-c/exp-c-summary.json`, CI: `code/results/stats/bootstrap.json`.
- Verdict: reranker killed, candidate generation alive; headroom ≈ 2.49 pts, CI-confirmed.

### 5.4 EXP-D — Flex native vs mixed ITN
- WER: Core native **22.01** / Flex native **22.09** / Flex mixed **33.54**.
- Paired bootstrap (Flex mixed − Core native, n=80): mean diff **+11.5 pts,
  95% CI [7.8, 15.4] pts**, excludes zero, p<0.0001 — the WER regression is
  robust; not driven by a handful of outlier rows.
- Curated diagnostics — number surface recall 59.1/59.1/**77.3**; currency
  100/100/**0**; entity 49.6/60.3/**20.5**; date 0/0/0.
- Anecdote: `₹19,500` → `₹1950` (tenfold).
- Artifacts: `results/exp-d/exp-d-summary.json`,
  `results/exp-d/exp-d-semantic-curated-summary.json`.
- Verdict: **do not ship Flex mixed**; surface-level only, 19 rows flagged for review.
- **Reconciled (2026-09-20):** `annotated_rows_scored: 50` and "11 number rows"
  are not in conflict — they're different denominators. `50` is the count of
  EXP-D's 80 propagated rows (32 clean + paired noise/telephone twins) carrying
  **at least one** annotated slot of any kind. Verified directly from
  `exp-d-semantic-curated-summary.json`'s row list: 11 rows carry a number
  slot, 3 carry a date slot, 3 carry a currency slot, 39 carry an entity slot
  (rows may carry more than one type, so these don't sum to 50). Practical
  effect: the headline **currency 100%→0%** collapse is measured on only
  **3 rows** — real, but thin; the **entity 49.6%→20.5%** figure rests on 39
  rows and is the better-powered part of this claim. Confidence split
  accordingly in the claim ledger (§7, C2).

### 5.5 EXP-E — Diarization pilot
- **Bug found, fixed, and re-measured (2026-09-20).** `run_exp_e.py` called
  `asr.transcribe(...)[0]` without `return_lid=True`; since `transcribe()`
  returns a bare string in that case, `[0]` took the first *character*, not
  the transcript — the original 09-17 numbers (no-diar 99.91%, oracle-turn
  99.80%, auto-VAD 100.00%) were void. Fixed and re-ran end-to-end against a
  live local ASR service (M5 Mac, MPS, Core re-vendored to `e083ab7d...`).
  Full writeup: `F-003`.
- 4 real two-speaker recs (2 hi, 2 ta; near/far field; ~60 s).
- **Real WER (2026-09-20): no-diar 66.6% / oracle-turn 57.7% / auto-VAD+KMeans
  82.6%.** DER 62.51% (toy VAD/KMeans baseline, unchanged — never depended on
  transcript text).
- Per-sample: hindi_085 (53.4/47.4/68.4), hindi_065 (47.2/28.7/98.5),
  tamil_092 (74.6/73.0/73.0), tamil_076 (91.3/81.5/90.8) — no-diar/oracle/auto,
  all %.
- Artifact: `code/data/challenge/results/exp-e-v2/exp-e-pilot-summary.json` (SSD).
- Verdict: oracle turns give a real but modest improvement (~9 points) — not
  a rescue. The toy automatic diarizer makes things **worse than doing
  nothing** (82.6% vs 66.6%) — turn-boundary quality matters more than raw
  short-turn ASR weakness. Strengthens rather than removes the case for a
  real neural diarizer + turn padding before shipping any multi-speaker path.

### 5.6 EXP-F — Real-noise robustness
- **Falsifiable target met, decisively.** 56 real clips, 7 languages, from
  `ai4bharat/IndicVoices` (bho absent from that corpus, dropped per design).
  Real noise vs. real clean (unpaired, different speakers/clips): clean
  **13.7%** → noise **34.3%** WER, **+20.6 pts**, 95% CI [4.9, 36.4] pts,
  excludes zero, p=0.009. Matched EXP-A **synthetic** noise vs. clean: 21.2%
  → 23.2%, **+2.0 pts**, 95% CI [−5.4, +9.7] pts, includes zero, p=0.605 —
  not distinguishable from no effect.
- **This project's own synthetic noise transform, used throughout EXP-A/D/E,
  understates real-world degradation by roughly an order of magnitude.**
  Every "noise" condition result elsewhere in this report characterizes
  robustness to mild deterministic degradation only, not real acoustic
  conditions.
- Condition proxy: IndicVoices' `scenario` field (`Conversation`/`Extempore`
  = real_noise, `Read` = real_clean) — not a controlled SNR measurement; some
  of the gap may be spontaneous-speech disfluency rather than pure acoustic
  noise (see `F-006` limits).
- Artifacts: `code/results/summaries/exp-f-v1-{baseline,summary}.json`, CI:
  `code/results/stats/bootstrap.json` (`exp_f`,
  `exp_a_synthetic_noise_vs_clean`). Full writeup: `F-006`.

### 5.7 OI-WER re-scoring (project definition)
- No public reference implementation of the vendor's OI-WER exists, and the
  suite's `reference_variants` field currently holds punctuated restatements
  of the primary reference rather than a curated spelling/transliteration
  table (57/80 rows carry a variant; checked directly — they are not
  orthographic alternatives, see `50-dataset/annotation-schema.md`). Per the
  registry's documented fallback ([[oi-wer]]) we implemented
  **project OI-WER**: NFKC normalization, casefold, cross-script digit folding
  (Devanagari/Bengali/Tamil/Telugu/Kannada/Malayalam/Perso-Arabic digits → ASCII),
  punctuation stripping, and multi-reference scoring (min WER over reference ∪
  variants). Decision recorded as `D-006`. Implementation:
  `code/metrics/oi_wer.py`, tests: `code/tests/test_oi_wer.py` (10/10 pass).
- Re-scored EXP-A: mean project-OI-WER **19.90%** vs whitespace WER **22.01%**
  — normalization/formatting tolerance closes **~2.1 points** of the gap.
  Per-language: hi 11.0, bho 14.1, te 14.8, ta 16.3, kn 20.6, mai 23.4,
  ur 27.1, ml 31.9.
- **Verdict on C5:** the ~13-point remaining gap to the vendor's reported 8.7
  average is **not** explained by whitespace/punctuation/digit-script
  formatting differences. This is a materially stronger basis for "vendor
  OI-WER does not transfer to this slice" than the original whitespace-vs-OI-WER
  comparison, though it still is not an apples-to-apples comparison against the
  vendor's own (undisclosed) OI-WER definition or their Voice-of-India corpus.
- Artifact: `code/results/summaries/exp-a-v1-oiwer-summary.json`.

### 5.8 Second baseline — Flex on the EXP-A suite (F-005 empirical test)
- Previously blocked (`asr_url` unset); unblocked 2026-09-20 by standing up
  local inference. Ran Flex through the exact same EXP-A auto-condition call
  Core used, same 80 samples.
- **Overall WER tied**: Core 22.01% / Flex 21.85%, paired bootstrap 95% CI on
  the diff **[-1.5, +1.2] pts**, includes zero, p=0.83 — not distinguishable
  on this suite.
- **Bhojpuri auto-LID: Core 0/10, Flex 4/10** (Wilson 95% CI [16.8%, 68.7%]).
  When Flex is wrong, it's absorbed by **Maithili** (5/6), not Hindi (1/6) —
  a different confusion pattern than Core's, not a milder version of the same
  one. This narrows C1/F-001's "Hindi-belt absorption" framing to Core
  specifically.
- This traces to a genuine code asymmetry found by re-vendoring (§2, F-005):
  Flex's `transcribe()` restricts default auto-LID candidates to
  `RECOMMENDED_LANGS` (excludes bgc/bhb only — not bho), Core's does not. That
  restriction does **not** explain the Bhojpuri gap (bho isn't excluded on
  either model) — the cause is open; candidate explanations (Flex's 27-lang
  training set shifting the softmax; a genuinely better-trained checkpoint on
  this axis) are untested.
- Artifacts: `code/results/summaries/exp-a-v1-flex-{baseline,summary}.json`,
  CIs in `code/results/stats/bootstrap.json` (`exp_a_core_vs_flex`,
  `exp_a_flex_bho_lid`).

## 6. Results synthesis

- Failure surface is **language/LID**, not audio quality — **but only under
  synthetic degradation**. Real noise (§5.6/C8/F-006) costs +20.6 WER points,
  larger than any single-language WER spread in EXP-A; the "audio quality
  doesn't matter much" conclusion from earlier sections does not survive
  contact with real conditions and should not be generalized past the
  synthetic transforms this project used everywhere else.
- The LID failure surface is **model-specific, not architecture-wide**: Core
  and Flex are tied on transcription WER but diverge sharply on Bhojpuri
  auto-LID (0/10 vs 4/10) with different confusion targets (Hindi vs
  Maithili) — see §5.8/C7.
- Obvious interpretable reliability signals are insufficient; a better reranker is
  required before abstention becomes useful.
- Built-in ITN is formatting without a semantic guard.
- Multi-speaker readiness is gated on turn-boundary *quality*, not just
  presence: oracle turns help modestly (66.6%→57.7% WER), a naive automatic
  diarizer actively hurts (82.6%) — re-measured 2026-09-20 after fixing a bug
  that had inflated the original numbers to near-total failure (§5.5/F-003).

## 7. Claim ledger (evidence + confidence)

| # | Claim | Evidence | Confidence | Limits |
|---|---|---|---|---|
| C1 | Bhojpuri absorbed by Hindi in auto-LID — **Core-specific**, does not generalize to Flex | EXP-A bho 0/10, Wilson 95% CI [0%, 27.8%] (Core); EXP-C top-3 contains truth 10/10; Flex gets 4/10 correct, absorbed mostly by Maithili not Hindi when wrong (§5.8, F-005) | high (n=10) for Core; the "Hindi-belt" framing itself is now known to be model-specific | 1 dialect/source; two models tested, not a model-family universal |
| C2 | Built-in mixed ITN breaks critical values | EXP-D currency 100→0 (n=3 rows), entity 49.6→20.5 (n=39 rows); WER regression bootstrap 95% CI [+7.8, +15.4] pts (n=80) | medium-high for entity/WER; **low for currency (n=3)** | surface metric, 50/80 rows carried any annotated slot — see §5.4 reconciliation |
| C3 | Vendor's diarize-then-transcribe remedy helps modestly but is not sufficient alone; a naive automatic diarizer actively hurts | EXP-E rerun 2026-09-20: no-diar 66.6% → oracle-turn 57.7% (real WER, after fixing a `[0]`-indexing bug that had inflated the original numbers to ~99.8%) → automatic VAD/KMeans 82.6% (worse than no-diar) | high for this slice (measured end-to-end, real transcripts spot-checked) | n=4, 2 langs, DER from a toy energy-VAD/KMeans baseline |
| C4 | Top-K generation has headroom; likelihood reranker fails | EXP-C oracle 22.38 vs 24.87; bootstrap 95% CI on the gap [1.04, 4.20] pts, p≈0.0002 | medium-high | n=80, one reranker |
| C5 | Vendor OI-WER does not transfer to this slice | EXP-A whitespace WER 22.0 / project OI-WER 19.9 vs vendor's reported OI-WER 8.7 (§5.7) | high (categorical; formatting tolerance closes only ~2 of ~13 points) | different corpus; still not the vendor's own OI-WER definition |
| C6 | Interpretable features do not predict errors here | EXP-B AUC 0.515, bootstrap 95% CI [0.387, 0.646] (spans 0.5) | medium-high — CI confirms "no better than chance," not just a point estimate | n=80, provisional label |
| C7 | Core and Flex are not symmetric on Bhojpuri auto-LID: Flex recovers 4/10 where Core gets 0/10, via a different confusion pattern (absorbed by Maithili, not Hindi); overall WER is tied between the two models | §5.8: paired bootstrap on 80 matched samples, WER diff CI [-1.5,+1.2]pts (p=0.83, tied); bho Wilson CI [16.8%,68.7%] vs Core's [0%,27.8%]. Code-level asymmetry (Flex-only `RECOMMENDED_LANGS` default restriction, F-005) found first but does **not** explain the Bhojpuri effect (bho not in the excluded set) | high — real inference run, both models, matched samples | cause of the Bhojpuri gap is unexplained; vendor's own 337k-clip number for the *documented* restriction (pa 0.620→0.775, unrelated to bho) not independently verified |
| C8 | This project's own synthetic noise transform understates real-world noise degradation by ~10x — every EXP-A/D/E "noise" result characterizes mild deterministic degradation only | §5.6/F-006: real noise−clean +20.6pts CI[4.9,36.4] p=0.009 (excludes zero) vs synthetic noise−clean +2.0pts CI[-5.4,+9.7] p=0.605 (includes zero), n=28/28 real, n=24/32 synthetic, 7 matched languages | high — statistically significant real effect vs. statistically null synthetic effect | n=56 pilot, n=4/language/condition for per-language deltas; `scenario` is a proxy for real conditions, not controlled SNR; bho untested (no IndicVoices source) |

Bootstrap methodology and full numbers: `code/scripts/bootstrap_cis.py` → `code/results/stats/bootstrap.json` (10,000 resamples, seed 20260920, paired bootstrap for within-sample comparisons, Wilson score interval for the n=10 binomial).

**Explicitly not claimed:** model is bad; noise claim false; code-mixing; any
production-safety statement; DER quality of neural diarization.

## 8. Limitations

- n=80 (partly synthetic twins), n=4 conversations; per-language n=10 — small
  enough that most bootstrap CIs are wide (see §7), and the C2 currency
  sub-claim rests on n=3.
- Language/source/speaker confounded; no causal ranking.
- OI-WER is now measured (§5.7) but is a project-defined normalization
  fallback, not the vendor's own (undisclosed) OI-WER; semantic metrics
  remain exact-surface only.
- Single model snapshot predating the 2026-09-15 vendor update — code-level
  claims (F-002, D-002) have not been re-checked against it.
- EXP-E (§5.5) was re-measured 2026-09-20 after a bug fix; do not cite the
  pre-fix (2026-09-17) WER numbers anywhere — they are void.
- Labels use provisional `WER ≤ 0.20`; thresholds are policy choices, not learned.
- No repeated runs / decoding-seed variance measured — all point estimates are
  from a single decode per sample; bootstrap CIs quantify sampling
  uncertainty over the 80 items, not decoding stochasticity.

## 9. Reproducibility

- Full procedure: `docs/REPRODUCE.md`.
- Pinned model revisions, manifest, runners, and expected summary values.
- **Committed to this repo (2026-09-20):** `code/metrics/oi_wer.py` +
  `code/tests/test_oi_wer.py`, `code/scripts/bootstrap_cis.py` +
  `code/results/stats/bootstrap.json`, `code/scripts/rescore_oi_wer.py` +
  `code/results/summaries/exp-a-v1-oiwer-summary.json`,
  `code/results/summaries/exp-a-v1-flex-{baseline,summary}.json`,
  `code/results/summaries/exp-e-v2-pilot-{results,summary}.json`. Re-run
  bootstrap CIs with `code/.venv/bin/python code/scripts/bootstrap_cis.py
  --exp-c-hypotheses <SSD>/exp-c/exp-c-hypotheses.jsonl --exp-d-flex-results
  <SSD>/exp-d/exp-d-flex-results.jsonl --exp-b-decisions
  <SSD>/exp-b-v1/exp-b-decisions.jsonl --exp-a-core-baseline
  <SSD>/exp-a-v1-baseline.jsonl --exp-a-flex-baseline
  code/results/summaries/exp-a-v1-flex-baseline.jsonl --output
  code/results/stats/bootstrap.json`.
- **Still TODO:** the underlying EXP-A/B/C/D per-sample JSONL and summary
  JSON still live only on the research SSD, not in the replication bundle;
  copy them + SHA-256 checksums into `code/results/summaries/`; lock
  dependency versions (`code/requirements.lock` does not exist yet); single
  `make repro` entry point.

## 10. Appendix

- A. Per-sample result tables (`results/*.jsonl`, SSD; CIs in `code/results/stats/bootstrap.json`).
- B. Card-vs-code delta tables (`20-models/*`).
- C. Engineering log (`90-journal/`).
- D. Known discrepancies and fixes: §5.4 EXP-D annotation-count reconciliation;
  §5.5 EXP-E transcribe-bug found/fixed/re-measured (F-003); §5.7 OI-WER
  fallback (D-006); §2/§5.8 code-audit + empirical finding F-005 (Flex-only
  auto-LID restriction, Core/Flex Bhojpuri divergence, C7); §5.6 real-noise
  pilot correcting the "audio quality doesn't matter much" synthetic-only
  conclusion (F-006, C8).

---

### Generation status

| Section | Source of truth | Status |
|---|---|---|
| §5.1–5.4 | SSD summary JSON + `code/results/stats/bootstrap.json` | filled, CI-backed |
| §5.5 (EXP-E) | `F-003`, SSD `exp-e-v2/exp-e-pilot-summary.json` | **re-measured 2026-09-20** — bug found, fixed, real numbers in |
| §5.6 (EXP-F) | `EXP-F-real-noise.md`, `F-006` | **run 2026-09-20** — falsifiable target met |
| §5.7 (OI-WER) | `code/results/summaries/exp-a-v1-oiwer-summary.json` | filled 2026-09-20 |
| §5.8 (second baseline) | `code/results/summaries/exp-a-v1-flex-*.json`, bootstrap.json | filled 2026-09-20, unblocked P-task from Ralph loop |
| §7 C1–C8 | findings `F-001..006` + summaries + bootstrap CIs | filled, scope-limited; C3 re-measured 2026-09-20 |
| Lockfile / full repro bundle | — | still TODO (§9) |
