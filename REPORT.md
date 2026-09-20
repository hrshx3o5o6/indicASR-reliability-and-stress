---
type: report
title: "Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model"
status: draft-reviewed
version: 0.2
updated: 2026-09-20
model_snapshots:
  core: "bodhan-ai/indic-transcribe-core@4d29eeb7a099"
  flex: "bodhan-ai/indic-transcribe-flex (revision TBD)"
---

# Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model

> **Draft, reviewed once (2026-09-20).** Every numeric claim below links to the
> artifact that produced it, either committed under `code/results/` or on the
> research SSD (`data/challenge/`, path noted per artifact). This pass: found
> and fixed a pipeline bug that had produced a false near-total-failure claim
> (§5.5/F-003, now retracted), reconciled an internal denominator
> contradiction (§5.4), added bootstrap 95% CIs to every headline number
> (§7), and closed the OI-WER TODO with a documented fallback definition
> (§5.7/D-006). Remaining open items: EXP-F not run, single model snapshot
> predating the 2026-09-15 vendor update, no dependency lockfile yet — all in
> §8/§9. Do not move a claim from §7 into the Abstract until its artifact is
> in the replication bundle (§9).

---

## Abstract (draft)

State-of-the-art Indic ASR is no longer the dominant bottleneck: the released model
scores well on its own benchmark. The bottleneck is knowing *when* a transcription can
be trusted and *why* it fails. We characterize the reliability envelope of
`indic-transcribe-core` (1.2B, 25 languages) and its sibling `indic-transcribe-flex`
on a deliberately structured 80-sample challenge suite spanning 8 languages and three
audio conditions. We reproduce the vendor's documented Hindi-belt language-identification
absorption (Bhojpuri auto-LID 0/10), show that top-3 candidate generation contains
recoverable headroom (oracle WER 22.38% vs 24.87% baseline) while likelihood-based
reranking fails, demonstrate that Flex's built-in mixed-mode ITN collapses currency
surface recall from 100% to 0% (n=3 currency-bearing rows), and report a
retracted finding: an initial claim that the vendor's diarize-then-transcribe
remedy fails even with oracle boundaries turned out to be a pipeline bug
(a string-indexing error truncated every EXP-E transcript to ~1 character),
found and fixed during review — the real result is unmeasured pending a rerun.
A project-defined, normalization-tolerant OI-WER (no public vendor definition
exists) narrows but does not close the gap to the vendor's reported average
(19.9% vs 8.7%), and every headline comparison carries a bootstrap 95%
confidence interval. We release the suite, runners, and per-sample results.
*Scope: small, partly synthetic, directional.*

**TODO:** tighten to ≤150 words once §7 is frozen.

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
- **Not claimed:** model quality verdict, real-world noise robustness, code-mixing.

## 2. System under test

| | Core | Flex |
|---|---|---|
| Params / base | 1.2B / canary-1b-v2 | 1.2B / canary-1b-v2 |
| Languages | 25 | 27 |
| Snapshot | `4d29eeb7a099` | TODO |
| Role | baseline (D-002) | modes/ITN (EXP-D) |

Verified API surface and card-vs-code deltas: `20-models/indic-transcribe-core.md`,
`20-models/indic-transcribe-flex.md`, `F-002`.
Key code facts: 45 s hard cap, no timestamps, token log-probs via generate passthrough,
Core exposes `native/mixed/romanised` though its card says native-only.
**TODO:** re-vendor after the 2026-09-15 HF update (`long_form.py`, `inference.py` now ship).

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
- **⚠️ RETRACTED (2026-09-20): the WER numbers below were a pipeline bug, not a
  model result.** `run_exp_e.py` called `asr.transcribe(...)[0]` without
  `return_lid=True`; since `transcribe()` returns a bare string in that case,
  `[0]` took the first *character*, not the transcript. Confirmed directly on
  the per-sample records: a 60 s clip's transcript was `"य उ"` (one character
  per chunk), and oracle-turn token counts matched segment counts exactly
  (23/23, 12/12, 30/30, 27/27) regardless of segment duration (some 5–27 s).
  Bug fixed in code; **not re-run** (needs the ASR service, currently
  offline). Full writeup: `F-003`.
- 4 real two-speaker recs (2 hi, 2 ta; near/far field; ~60 s).
- ~~WER: no-diar 99.91 / oracle-turn 99.80 / auto-VAD+KMeans 100.00~~ — void, see above.
- DER 62.51 (toy VAD/KMeans baseline) is unaffected by the bug (computed from
  segment timing, not transcript text) and may still be cited directionally.
- Artifact: `results/exp-e/exp-e-pilot-summary.json` (WER fields invalid).
- Verdict: **pilot result unknown** until re-run with fixed code; DER-only
  signal says diarization-quality work (turn padding + neural diarizer) is
  still needed regardless of the WER retraction.

### 5.6 EXP-F — Real-noise robustness (registered, not run)
- Design and falsifiable targets: `EXP-F-real-noise.md`. No artifact yet.

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

## 6. Results synthesis

- Failure surface is **language/LID**, not audio quality, in this slice.
- Obvious interpretable reliability signals are insufficient; a better reranker is
  required before abstention becomes useful.
- Built-in ITN is formatting without a semantic guard.
- Multi-speaker readiness: **unknown**, not "gated on turn-context handling" — the
  original claim rested on a pipeline bug (§5.5/F-003), retracted pending rerun.

## 7. Claim ledger (evidence + confidence)

| # | Claim | Evidence | Confidence | Limits |
|---|---|---|---|---|
| C1 | Bhojpuri absorbed by Hindi in auto-LID | EXP-A bho 0/10, Wilson 95% CI [0%, 27.8%]; EXP-C top-3 contains truth 10/10 | high (n=10) | 1 dialect/source |
| C2 | Built-in mixed ITN breaks critical values | EXP-D currency 100→0 (n=3 rows), entity 49.6→20.5 (n=39 rows); WER regression bootstrap 95% CI [+7.8, +15.4] pts (n=80) | medium-high for entity/WER; **low for currency (n=3)** | surface metric, 50/80 rows carried any annotated slot — see §5.4 reconciliation |
| C3 | ~~Vendor diarize-then-transcribe insufficient as stated~~ **RETRACTED** | EXP-E WER numbers were a `[0]`-string-indexing bug, not a model result (F-003) | none — claim withdrawn | n=4, 2 langs; rerun pending live ASR service |
| C4 | Top-K generation has headroom; likelihood reranker fails | EXP-C oracle 22.38 vs 24.87; bootstrap 95% CI on the gap [1.04, 4.20] pts, p≈0.0002 | medium-high | n=80, one reranker |
| C5 | Vendor OI-WER does not transfer to this slice | EXP-A whitespace WER 22.0 / project OI-WER 19.9 vs vendor's reported OI-WER 8.7 (§5.7) | high (categorical; formatting tolerance closes only ~2 of ~13 points) | different corpus; still not the vendor's own OI-WER definition |
| C6 | Interpretable features do not predict errors here | EXP-B AUC 0.515, bootstrap 95% CI [0.387, 0.646] (spans 0.5) | medium-high — CI confirms "no better than chance," not just a point estimate | n=80, provisional label |

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
- EXP-E (§5.5) is unmeasured pending a rerun after the 2026-09-20 bug fix;
  do not cite its pre-fix WER numbers.
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
  `code/results/summaries/exp-a-v1-oiwer-summary.json`. Re-run bootstrap CIs
  with `code/.venv/bin/python code/scripts/bootstrap_cis.py --exp-c-hypotheses
  <SSD>/exp-c/exp-c-hypotheses.jsonl --exp-d-flex-results
  <SSD>/exp-d/exp-d-flex-results.jsonl --exp-b-decisions
  <SSD>/exp-b-v1/exp-b-decisions.jsonl --output code/results/stats/bootstrap.json`.
- **Still TODO:** the underlying EXP-A/B/C/D/E per-sample JSONL and summary
  JSON still live only on the research SSD, not in the replication bundle;
  copy them + SHA-256 checksums into `code/results/summaries/`; lock
  dependency versions (`code/requirements.lock` does not exist yet); single
  `make repro` entry point.

## 10. Appendix

- A. Per-sample result tables (`results/*.jsonl`, SSD; CIs in `code/results/stats/bootstrap.json`).
- B. Card-vs-code delta tables (`20-models/*`).
- C. Engineering log (`90-journal/`).
- D. Known discrepancies and fixes: §5.4 EXP-D annotation-count reconciliation;
  §5.5 EXP-E transcribe-bug retraction (F-003); §5.7 OI-WER fallback (D-006).

---

### Generation status

| Section | Source of truth | Status |
|---|---|---|
| §5.1–5.4 | SSD summary JSON + `code/results/stats/bootstrap.json` | filled, CI-backed |
| §5.5 (EXP-E) | `F-003` | **retracted pending rerun** — bug found and fixed 2026-09-20 |
| §5.6 (EXP-F) | `EXP-F-real-noise.md` | not run — needs live ASR service |
| §5.7 (OI-WER) | `code/results/summaries/exp-a-v1-oiwer-summary.json` | filled 2026-09-20 |
| §7 C1–C6 | findings `F-001..004` + summaries + bootstrap CIs | filled, scope-limited, C3 withdrawn |
| Lockfile / full repro bundle | — | still TODO (§9) |
