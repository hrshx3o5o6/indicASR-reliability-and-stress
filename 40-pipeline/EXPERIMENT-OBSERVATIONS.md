---
type: experiment-dashboard
title: "Experiment observations and takeaways"
updated: 2026-09-17
---

# Experiment observations and takeaways

> **Source of truth.** Read this note first whenever you need to know what the experiments have established. It is updated after every material run, analysis, threshold decision, failure, or scope change. Detailed protocols remain in the linked EXP notes; raw artifacts live on the SSD.

## Current state

- **EXP-A v1:** complete for the 80-sample scope.
- **EXP-B v1:** complete for the 80-sample scope; conservative policy currently abstains on every sample.
- **EXP-C v1:** complete for the 80-sample scope; top-K has headroom, but the current reranker is not a win.
- **EXP-D v1:** complete with conservative agent-reviewed annotations; Flex mixed normalization is a no-go.
- **EXP-E pilot:** complete on 4 real recordings; a `[0]`-indexing bug inflated
  the original numbers to near-total failure (fixed and re-measured
  2026-09-20 — see below). Real result: oracle turns help modestly, a naive
  automatic diarizer hurts.
- **Execution commitment:** proceed through EXP-C, then EXP-D and EXP-E without waiting for another confirmation; each phase gets its own evidence-backed stop/go verdict.
- **Storage:** artifacts are on `/Volumes/Harshas ssd/Harshas Mac/work/bodhanai-asr-research`.

## What we observed

### EXP-A — Core baseline census

**Scope.** 80 samples, exactly 10 per `hi, ta, te, ml, kn, ur, bho, mai`:
32 real clean samples, 24 deterministic background-noise variants, and 24 deterministic telephone-bandwidth variants. The degraded rows preserve clean twins and are marked synthetic.

**Results.**

| Measure | Result |
| --- | ---: |
| Successful runs | 80 / 80 |
| Mean whitespace-token WER | 22.0% |
| Exact transcript match | 3.75% |
| Auto-LID top-1 accuracy | 87.5% (70/80) |
| Explicit-vs-auto LID agreement | 87.5% |
| Core-warning rate | 50.0% |

**Language WER.** `te` 14.8%, `bho` 14.1%, `hi` 14.0%, `ta` 22.4%, `mai` 23.4%, `kn` 24.3%, `ur` 29.0%, `ml` 34.1%.

**Condition WER.** `clean` 21.2%, `background_noise` 23.2%, `telephone` 22.0%. These are results for our deterministic transformations, not a claim about all real-world noise or telephony.

**Strongest finding.** Bhojpuri auto-LID was wrong on **10/10** samples, while the other seven languages were correct in this slice. This reproduces Hindi-belt absorption as a Core reliability problem.

### EXP-B — Reliability and abstention

**Scope.** 15 interpretable features: LID confidence/margin/entropy, explicit-vs-auto agreement, warnings, audio quality, duration, and transcript statistics. Constant script-consistency was removed automatically.

**Results.**

| Measure | Result |
| --- | ---: |
| OOF ROC-AUC | 0.515 |
| Average precision | 0.615 |
| Brier score | 0.279 |
| AURC | 0.404 |
| Default ACCEPT coverage | 0% |
| Default WARN coverage | 0% |

**Interpretation.** The feature set is only marginally better than random at ranking acceptable transcripts. No observed score cutoff met the safety targets, so the guardrail correctly returns `ABSTAIN` for all 80 samples. This is a useful safety result, not a usable production policy.

### EXP-C — Adaptive LID and multi-hypothesis decoding

**Scope.** The same 80 EXP-A v1 samples. A shared encoder pass generated top-3 language hypotheses; each candidate was decoded and scored with mean decoder token log-probability plus the LID prior.

| Measure | Result |
| --- | ---: |
| Top-3 truth coverage | 79/80 (98.75%) |
| Baseline auto-LID WER | 24.87% |
| Adaptive selected WER | 25.00% |
| Oracle top-3 WER | 22.38% |
| Selected language accuracy | 87.5% (70/80) |

**Interpretation.** The current reranker fails the EXP-C success criterion: it does not beat top-1 routing and slightly worsens WER. However, oracle top-3 decoding improves WER by 2.49 percentage points versus baseline, proving that candidate generation has useful headroom. The main failure remains Bhojpuri: 0/10 selected-language accuracy, despite the correct language appearing in the top-3 for those samples. Treat the likelihood-plus-LID scorer as killed, not the top-K routing idea.

### EXP-D — Flex native/mixed comparison

**Scope.** The same 80 EXP-A v1 samples, decoded with Core native, Flex native, and Flex mixed mode. Flex was downloaded to the SSD; no additional evaluation corpus was downloaded.

| Measure | Core native | Flex native | Flex mixed |
| --- | ---: | ---: | ---: |
| Mean whitespace-token WER | 22.01% | 22.09% | 33.54% |

Flex native improved over Core on 19/80 rows, tied 36/80, and worsened 25/80. Flex mixed improved on 9/80, tied 15/80, and worsened 56/80. It emitted digit-like tokens on 15/80 rows and Latin-script tokens on 62/80 rows. Those formatting changes are not semantic correctness measurements.

**Interpretation.** Flex native is effectively tied with Core in this slice. Flex mixed substantially worsens whitespace-token WER and cannot be accepted as a semantics-preserving normalization layer based on this evidence. Semantic-slot/entity scoring is still pending because the manifest annotations are empty.

**Annotation pass v1.** Curated labels now cover all 80 rows by annotating 32 unique clean references and propagating them to synthetic twins. The pass contains 11 number/identifier rows, 36 entity-bearing rows, and 19 rows conservatively flagged for human review. Conservative surface recall is Core native `0.591`, Flex native `0.591`, and Flex mixed `0.773`; digit-only recall is `0.00`, `0.00`, and `0.773`. This is not semantic-slot accuracy: the scorer accepts exact spoken phrases or digit values but does not handle transliteration or compositional number variants.

**EXP-D final v1 verdict.** The agent-reviewed pass now covers all 80 rows; 19 rows remain conservatively flagged for optional human review. Number surface recall is Core `59.1%`, Flex native `59.1%`, Flex mixed `77.3%`; currency surface recall is Core/Flex native `100%` versus Flex mixed `0%`; entity surface recall is Core `49.6%`, Flex native `60.3%`, Flex mixed `20.5%`. These are exact-surface diagnostics, not publication-grade semantic accuracy. The operational decision is nevertheless clear: do not ship Flex mixed normalization because it changes critical values and loses entity/currency surfaces.

### EXP-E — Multi-speaker pipeline pilot

**Scope.** Four real two-speaker conversations from Indic DiarBench: two Hindi and two Tamil recordings, near-field and far-field, each about one minute. The pilot compared full-conversation chunking, oracle annotated turns, and automatic energy-VAD plus spectral-feature KMeans clustering.

| Measure | Result (2026-09-17, VOID — see below) | Result (2026-09-20, real) |
| --- | ---: | ---: |
| No-diarization WER | ~~99.91%~~ | **66.6%** |
| Oracle-turn WER | ~~99.80%~~ | **57.7%** |
| Automatic VAD/cluster WER | ~~100.00%~~ | **82.6%** |
| Automatic DER | 62.51% | 62.51% (unchanged) |

**⚠️ 2026-09-20: the 09-17 numbers were a bug, not a model result.**
`run_exp_e.py`'s `transcribe_clip()` called `asr.transcribe(...)[0]` without
`return_lid=True`, truncating every transcript to ~1 character. Fixed, and
re-ran end-to-end against a live local ASR service.

**Interpretation (revised).** Oracle turn boundaries give a real but modest
improvement over no diarization (66.6%→57.7%, ~9 points) — not a rescue,
57.7% WER is still far from usable. The naive automatic VAD/KMeans diarizer
makes things **worse than doing nothing** (82.6% vs 66.6%) — 3 of 4
recordings got worse or flat under automatic segmentation. The 62.51% DER is
only the simple clustering baseline's result, not a claim about neural
diarization. The immediate engineering response is still turn padding/context
plus a neural diarizer, but the reason has sharpened: turn-boundary *quality*
is the bottleneck, and a naive baseline actively hurts rather than merely
under-delivering.

## Takeaways

1. Core is broadly usable but highly language-dependent; average WER hides substantial variance.
2. Auto-LID is the clearest current failure surface, specifically Bhojpuri/Hindi-belt confusion.
3. Core warnings are common enough to investigate, but they are not yet a calibrated reliability score.
4. The current reliability features do not identify safe outputs reliably. Do not loosen thresholds merely to produce ACCEPT decisions.
5. The 80-sample set is still small and partly synthetic; results are directional, not publication-grade.
6. The project should improve reliability/LID handling rather than train another ASR model.
7. Top-K language generation can expose recoverable errors, but reranking needs language-sensitive and semantic evidence; decoder likelihood alone favors the absorbed Hindi hypothesis.
8. Flex mixed mode changes formatting aggressively but increases WER from 22.01% to 33.54%; semantic-slot annotations are required before judging whether any apparent number/entity formatting is beneficial.
9. In the EXP-E pilot (re-measured 2026-09-20 after a bug fix), correct turn boundaries help modestly (66.6%→57.7% WER) but do not rescue Core; a naive automatic diarizer actively makes results worse (82.6%) — turn-boundary quality, not just presence, is the bottleneck.

## Known limitations

- Two source examples per language were expanded to four clean examples, then paired into synthetic degradations; degraded rows are not independent speakers.
- No real code-mixed, names, numbers, dates, currency, reverberation, or multi-speaker strata are included yet.
- WER uses whitespace-token comparison for now; OI-WER and critical-value/entity scoring are pending.
- EXP-B labels use provisional `WER <= 0.20`; this is not a final application-quality definition.
- Threshold targets (`≤10%` risk for ACCEPT and `≤25%` for WARN) are policy proposals, not data-derived truths.

## Model-card cross-check (2026-09-17)

Fetched the current HF cards (both modified **2026-09-15**, i.e. after our 09-10 snapshot — the repos now also ship `long_form.py`/`inference.py` that our vendored code lacks; re-vendor before further code claims). Full comparison tables live in the model dossiers ([[indic-transcribe-core]], [[indic-transcribe-flex]]); findings: [[F-001]] (promoted to `verified`), [[F-003]], [[F-004]].

**What we can claim (evidence-backed, scoped):**
1. Vendor's own Limitations on Hindi-belt LID are confirmed by measurement — bho 0/10 on our suite ([[F-001]]).
2. The vendor's multi-speaker remedy ("pair with diarization, transcribe each turn") is necessary but not sufficient — oracle turns fail ([[F-003]]).
3. Flex mixed ITN materially degrades critical-value surfaces, quantifying "occasionally wrong" ([[F-004]]) — supports the card's own native-mode recommendation and our no-go.
4. Vendor VOI OI-WER (Core 8.7) and our challenge-slice WER (22.0%) are not comparable — different corpora and metrics. We can claim non-transferability to our slice, not vendor error.
5. "Robust in noisy real-world conditions" and code-mixing claims remain **untested by us** — mild synthetic degradations barely moved WER, and no code-mixed strata exist yet.

## Claim hardening and infrastructure (2026-09-19)

Planning pass for publication + a sandboxed verification loop. Full detail in
[[DEPLOYMENT]] and [[INFRA-NOTES]]; decisions [[D-003-model-as-service]],
[[D-004-sandboxed-thin-clients]]; report `REPORT.md`; procedure `docs/REPRODUCE.md`.

- **Claim ledger C1–C6** recorded in `REPORT.md` §7, each tied to an SSD artifact
  and an explicit scope limit.
- **16 environment blockers** catalogued in [[INFRA-NOTES]] (P-1…P-16): weights vs
  4 GiB/60-min sandbox, loopback/secret constraints, download flakiness, the EXP-D
  annotation-count discrepancy (P-11), vendor card drift (P-12), repro gaps (P-14).
- **Architecture chosen:** model-as-a-service ([[D-003-model-as-service]]) +
  sandboxed thin clients routed `compute: none | model` ([[D-004-sandboxed-thin-clients]]).
  Inference is a service; agent code is sandboxed; state lives in git, never the sandbox.
- **Cache-first:** most claim re-scoring uses existing `results/*.jsonl` with zero
  model compute and is fully sandboxable today.
- **To build:** `code/asr_service.py`, `code/asr_client.py`, `.ralph/` state,
  `RALPH.md`, `scripts/ralph_step.sh`.

## Next actions

- **Immediate next experiment:** improve EXP-E with turn padding/context and a neural diarizer, then rerun on a larger stratified subset.
- **Registered, not started:** [[EXP-F-real-noise|EXP-F]] — real market/call-center audio vs EXP-A's synthetic degradations (matched-pair design). Currently the strongest test of the vendor's "robust in noisy real-world conditions" claim; SSD-independent (short-clip subsets < 2 GB, internal disk).
- **Re-vendor Core/Flex code:** the HF repos changed on 2026-09-15 (`long_form.py`, `inference.py` added; possibly `indic_transcribe.py`/`lid.py` diffs). Our snapshot `4d29eeb7a099` predates it — diff before drawing further code-level conclusions.
- **EXP-D follow-up (optional):** human-review the 19 flagged rows if publication-grade semantic metrics are needed; this does not change the current no-go decision for Flex mixed.
- **EXP-E immediate:** inspect Hindi/Tamil parquet schemas, sample conversations, validate speaker/turn/audio fields, then establish no-diarization and oracle-turn baselines.
- **EXP-E inventory:** Hindi 94 recordings / 10.74 hours / 8,665 segments; Tamil 93 recordings / 9.98 hours / 10,474 segments.
- Add semantic labels for names, numbers, dates, currency, and code-mixing.
- Add natural/noise-controlled validation data and speaker/source separation.
- Re-run EXP-B with critical-value-aware labels and sensitivity curves.
- Only then decide whether to build EXP-C adaptive LID routing.

## Data and model requirements

- **EXP-B:** no large download required. Use the 80-sample suite, add semantic annotations locally, and optionally add natural condition samples from already-available source shards.
- **EXP-C:** no new corpus required. It reuses the 80-sample audio and runs Core top-K language hypotheses; extra Hindi-belt natural audio is optional robustness evidence.
- **EXP-D:** requires the Flex checkpoint/code for the built-in `mixed`-mode comparison, plus locally annotated numbers, dates, currency, names, and organizations. No giant training corpus is required.
- **EXP-E:** requires a multi-speaker/diarization evaluation set such as Indic DiarBench, plus diarization/VAD dependencies. This is the only subsequent phase with a genuinely new dataset requirement.
- **EXP-F:** no new corpus download required up front. Reuse already-available [[kathbath]] / [[indicvoices]] short clips for real-noise/real-telephony strata; artifacts stay on internal disk (< 2 GB) until the SSD is next mounted. Move to SSD at next opportunity.
- **Current gate:** EXP-D v1 is complete with conservative exact-surface diagnostics; do not generalize them as publication-grade semantic accuracy.

## Execution order and time budget

- **Data/label improvement + EXP-B rerun:** approximately 2–4 hours of work; CPU baseline reruns are the dominant cost.
- **EXP-C adaptive LID:** approximately 4–8 hours including top-K decoding over the expanded set, scorer implementation, evaluation, and documentation.
- **EXP-D normalization/entities:** approximately 1–2 days because semantic annotations and a Flex comparison are required.
- **EXP-E diarization:** approximately 1–3 days because diarization data/tooling and DER evaluation must be validated separately.
- These are estimates, not promises; each phase stops when its success criterion is measured, killed, or blocked and records the reason here.

## Artifact index

- EXP-A manifest: `data/challenge/manifests/exp-a-v1-80.jsonl`
- EXP-A results: `data/challenge/results/exp-a-v1-baseline.jsonl`
- EXP-A summary: `data/challenge/results/exp-a-v1-summary.json`
- EXP-B features/decisions/summary: `data/challenge/results/exp-b-v1/`
- EXP-A protocol: [[EXP-A-baseline-census]]
- EXP-B protocol: [[EXP-B-reliability-abstention]]
- EXP-C protocol/results: [[EXP-C-adaptive-lid]]
- EXP-C hypotheses: `data/challenge/results/exp-c/exp-c-hypotheses.jsonl`
- EXP-C summary: `data/challenge/results/exp-c/exp-c-summary.json`
- EXP-D prerequisite note: [[EXP-D-normalization-entities]]
- EXP-D comparison: `data/challenge/results/exp-d/exp-d-flex-results.jsonl`
- EXP-D summary: `data/challenge/results/exp-d/exp-d-summary.json`
- EXP-D annotation candidates: `data/challenge/manifests/exp-d-v1-annotations.jsonl`
- EXP-D semantic diagnostic: `data/challenge/results/exp-d/exp-d-semantic-summary.json`
- EXP-D curated annotations: `data/challenge/manifests/exp-d-v1-annotations-curated.jsonl`
- EXP-D curated semantic diagnostic: `data/challenge/results/exp-d/exp-d-semantic-curated-summary.json`
- EXP-E dataset: `data/exp-e/indic-diarbench/`
- EXP-E runner: `code/run_exp_e.py`
- EXP-E pilot results (VOID, pre-bug-fix): `data/challenge/results/exp-e/exp-e-pilot-results.jsonl`
- EXP-E pilot results (real, 2026-09-20): `data/challenge/results/exp-e-v2/exp-e-pilot-results.jsonl`
- EXP-E pilot summary (real, 2026-09-20): `data/challenge/results/exp-e-v2/exp-e-pilot-summary.json`
- EXP-F protocol: [[EXP-F-real-noise]] (planned; no artifacts yet — run internally, migrate to SSD when next mounted)

## Maintenance rule

After every experiment, update this note with: scope, artifact path, metric table, observations, interpretation, limitations, and next action. If a result changes a claim, update the linked EXP note and add or revise an `F-###` finding; never leave the dashboard more optimistic than the evidence.
