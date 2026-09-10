---
type: pipeline
updated: 2026-09-10
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
- Streaming (engineering first, then: *can reliability be estimated online mid-utterance?*)

## Standing rule
Each phase ends with findings + decisions updated and the [[HOME]] dashboards truthful. No experiment runs unregistered.
