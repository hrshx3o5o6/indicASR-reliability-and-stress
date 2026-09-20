---
type: report
title: "Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model"
status: draft-skeleton
version: 0.1
updated: 2026-09-19
model_snapshots:
  core: "bodhan-ai/indic-transcribe-core@4d29eeb7a099"
  flex: "bodhan-ai/indic-transcribe-flex (revision TBD)"
---

# Trust, but Verify: Measuring the Reliability Envelope of a SOTA Indic ASR Model

> **Draft skeleton.** Every numeric claim below links to the artifact that produced it
> under `data/challenge/` on the research SSD. Placeholders marked `TODO` are not yet
> measured. Do not move a claim from §7 into the Abstract until its artifact is in the
> replication bundle (§9).

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
surface recall from 100% to 0%, and show that the vendor's diarize-then-transcribe
remedy is insufficient on short conversational turns even with oracle boundaries.
We release the suite, runners, and per-sample results. *Scope: small, partly synthetic,
directional.*

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
  5. A measured qualification of the vendor's multi-speaker remedy (`F-003`).
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
| OI-WER | **pending** | required before publication claims about spelling fairness |

Definitions and pitfalls: `30-metrics/` (registry `30-metrics/METRICS.md`).

## 5. Experiments

Each subsection: Question · Protocol · Artifact · Result · Verdict · Scope limits.

### 5.1 EXP-A — Baseline census
- Result: 80/80 runs; WER **22.01%**; exact match 3.75%; LID top-1 **87.5%**;
  warnings 50%.
- Per-language WER: `te` 14.8, `bho` 14.1, `hi` 14.0, `ta` 22.4, `mai` 23.4,
  `kn` 24.3, `ur` 29.0, `ml` 34.1.
- Per-condition WER: clean 21.2 / noise 23.2 / telephone 22.0.
- Strongest signal: bho auto-LID **0/10**.
- Artifact: `results/exp-a-v1-summary.json`. Verdict: done, directional.

### 5.2 EXP-B — Reliability + abstention (negative result)
- 14 features (one constant removed), LOO logistic regression.
- OOF ROC-AUC **0.515**; AP 0.615; Brier 0.279; AURC 0.404.
- Policy: **all 80 ABSTAIN** (no cutoff met ≤10% risk @ ≥25% coverage / ≤25% @ ≥50%).
- Artifact: `results/exp-b-v1/exp-b-summary.json`. Verdict: killed; guardrail correct.

### 5.3 EXP-C — Adaptive LID / top-K decoding (mixed)
- top-3 truth coverage **79/80**; baseline WER 24.87 → adaptive 25.00 → oracle **22.38**.
- bho selected-language accuracy 0/10.
- Artifact: `results/exp-c/exp-c-summary.json`.
- Verdict: reranker killed, candidate generation alive; headroom ≈ 2.49 pts.

### 5.4 EXP-D — Flex native vs mixed ITN
- WER: Core native **22.01** / Flex native **22.09** / Flex mixed **33.54**.
- Curated diagnostics — number surface recall 59.1/59.1/**77.3**; currency
  100/100/**0**; entity 49.6/60.3/**20.5**; date 0/0/0.
- Anecdote: `₹19,500` → `₹1950` (tenfold).
- Artifacts: `results/exp-d/exp-d-summary.json`,
  `results/exp-d/exp-d-semantic-curated-summary.json`.
- Verdict: **do not ship Flex mixed**; surface-level only, 19 rows flagged for review.
- ⚠️ Data-integrity TODO: curated summary reports `annotated_rows_scored: 50`
  while notes cite 11 number rows / 80 rows — reconcile before publication.

### 5.5 EXP-E — Diarization pilot
- 4 real two-speaker recs (2 hi, 2 ta; near/far field; ~60 s).
- WER: no-diar **99.91** / oracle-turn **99.80** / auto-VAD+KMeans **100.00**;
  DER 62.51 (toy baseline).
- Artifact: `results/exp-e/exp-e-pilot-summary.json`.
- Verdict: pilot fails; next = turn padding + neural diarizer.

### 5.6 EXP-F — Real-noise robustness (registered, not run)
- Design and falsifiable targets: `EXP-F-real-noise.md`. No artifact yet.

## 6. Results synthesis

- Failure surface is **language/LID**, not audio quality, in this slice.
- Obvious interpretable reliability signals are insufficient; a better reranker is
  required before abstention becomes useful.
- Built-in ITN is formatting without a semantic guard.
- Multi-speaker readiness is gated on turn-context handling, not just diarization.

## 7. Claim ledger (evidence + confidence)

| # | Claim | Evidence | Confidence | Limits |
|---|---|---|---|---|
| C1 | Bhojpuri absorbed by Hindi in auto-LID | EXP-A bho 0/10; EXP-C top-3 contains truth 10/10 | high (n=10) | 1 dialect/source |
| C2 | Built-in mixed ITN breaks critical values | EXP-D currency 100→0, entity 49.6→20.5 | medium-high | surface metric, n=80 |
| C3 | Vendor diarize-then-transcribe insufficient as stated | EXP-E oracle-turn WER 99.80 | high for slice | n=4, 2 langs |
| C4 | Top-K generation has headroom; likelihood reranker fails | EXP-C oracle 22.38 vs 24.87 | medium-high | n=80, one reranker |
| C5 | Vendor OI-WER does not transfer to this slice | EXP-A 22.0 vs vendor 8.7 | high (categorical) | different corpus/metric |
| C6 | Interpretable features do not predict errors here | EXP-B AUC 0.515 | medium | n=80, provisional label |

**Explicitly not claimed:** model is bad; noise claim false; code-mixing; any
production-safety statement; DER quality of neural diarization.

## 8. Limitations

- n=80 (partly synthetic twins), n=4 conversations; per-language n=10.
- Language/source/speaker confounded; no causal ranking.
- Whitespace WER, not OI-WER; semantic metrics are exact-surface only.
- Single model snapshot predating the 2026-09-15 vendor update.
- Labels use provisional `WER ≤ 0.20`; thresholds are policy choices, not learned.

## 9. Reproducibility

- Full procedure: `docs/REPRODUCE.md`.
- Pinned model revisions, manifest, runners, and expected summary values.
- **TODO:** commit summary JSONs + SHA-256 to repo; lock dependency versions;
  single `make repro` entry point.

## 10. Appendix

- A. Per-sample result tables (`results/*.jsonl`).
- B. Card-vs-code delta tables (`20-models/*`).
- C. Engineering log (`90-journal/`).
- D. Known discrepancies and fixes (e.g., §5.4 annotation count).

---

### Generation status

| Section | Source of truth | Status |
|---|---|---|
| §5.1–5.5 | SSD summary JSON | filled |
| §5.6 | `EXP-F-real-noise.md` | not run |
| §7 C1–C6 | findings `F-001..004` + summaries | filled, scope-limited |
| Lockfile / repro bundle | — | TODO |
