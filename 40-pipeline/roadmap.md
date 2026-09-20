---
type: pipeline
updated: 2026-09-17
---

# Roadmap — 3-day sprint, then next project

## Day 1 — baseline + failure census
- [ ] Accept licenses / get HF access to both gated models ([[indic-transcribe-core]], [[indic-transcribe-flex]])
- [ ] Local inference running ([[EXP-A]]); verify card API claims against repo code → resolve all `⚠️ to-verify` in [[indic-transcribe-core]]
- [ ] Probe available metadata: token probs, timestamps, decoder scores, `RECOMMENDED_LANGS` contents
- [ ] Build challenge suite v0: 50–100 samples ([[challenge-suite-spec]], [[annotation-schema]]) from [[DATASETS]]
- [ ] Run [[EXP-A]] baseline; compute WER, OI-WER (or fallback — see [[oi-wer]]), LID acc, [[entity-accuracy]], [[critical-value-accuracy]]
- [ ] Start [[error-taxonomy]] bucketing; record findings as `F-###`
- [ ] Confirm/kill P1–P4 evidence at first pass

## Day 2 — reliability model + abstention
- [ ] Audio features (SNR, rate, clipping…), LID features (top-1, margin, entropy), transcript features ([[EXP-B]])
- [ ] Reliability labels from Exp-A errors; train logistic regression → LightGBM
- [ ] Calibration analysis ([[lid-reliability]] ECE; reliability score calibration)
- [ ] ACCEPT/WARN/ABSTAIN thresholds from risk–coverage ([[selective-prediction]])
- [ ] AUROC/AURC reported; P5–P6 verdicts recorded

## Day 3 — normalization + demo + ablations
- [ ] Semantics-preserving normalization ([[critical-value-accuracy]] as acceptance test) ([[EXP-D]])
- [ ] Basic entity detect→validate→correct (conservative) ([[EXP-D]])
- [ ] Demo = [[PIPELINE]] contract output rendered ([[EXP-B]] output shape)
- [ ] Ablations + language×condition heatmaps ([[EXP-A]] analysis, [[error-taxonomy]])
- [ ] Failure-mode writeup; identify strongest bottleneck → next-project seed ([[EXP-C]])

## After the sprint (not before)
- [[EXP-C]] adaptive LID + multi-hypothesis decoding (the next *project*)
- [[EXP-E]] diarization (Indic DiarBench)
- [[EXP-F-real-noise|EXP-F]] real market/call-center noise — validate "robust in noisy real-world conditions" against actual recordings, not synthetic transforms
- Streaming (engineering first, then: *can reliability be estimated online mid-utterance?*)

## Phase 2 — claim hardening (publication)
- [ ] Reconcile EXP-D annotation count ([[INFRA-NOTES]] P-11)
- [ ] Implement [[oi-wer]]; re-score EXP-A/C/D
- [ ] Bootstrap CIs + paired significance tests on existing per-sample results
- [ ] Expand suite 80 → 300–500, real speakers, natural conditions; split tune/holdout
- [ ] Human-verify the 19 flagged EXP-D rows; inter-annotator agreement → true semantic accuracy
- [ ] Second baseline (vanilla `canary-1b-v2` / another Indic ASR) for context
- [ ] Independent clean-clone rerun on a second machine
- [ ] Re-vendor after the 2026-09-15 vendor update; pin both revisions
- [ ] Lock dependencies; commit summary JSONs + SHA-256; single `make repro`

## Phase 3 — infrastructure + sandboxed research loop
- [ ] [[D-003-model-as-service|D-003]]: `code/asr_service.py` + `code/asr_client.py`; `--asr-url` in runners
- [ ] Option A host: M5 + `cloudflared` tunnel; record URL in state
- [ ] [[D-004-sandboxed-thin-clients|D-004]]: reqly/E2B smoke with `E2B_API_KEY`
- [ ] Build `.ralph/` state + `RALPH.md` + `scripts/ralph_step.sh` (router)
- [ ] First cache-only pass (`lockfile` / `commit-artifacts`); prove one end-to-end pass
- [ ] Digest freebuff transcript → `docs/PRIOR-CONTEXT.md` for loop continuity
- [ ] Promote to GPU tier (Modal) when whole-model reruns return

## Standing rule
Each phase ends with findings + decisions updated and the [[HOME]] dashboards truthful. No experiment runs unregistered.
