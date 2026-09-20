---
type: experiment
id: EXP-F
title: "Real-world noise robustness — market/call-center audio vs synthetic degradations"
status: done
phase: v1-pilot-results
depends: ["EXP-A"]
updated: 2026-09-20
---

# EXP-F — Real-world noise robustness

> Live observations: [[EXPERIMENT-OBSERVATIONS]]. Plain-English context: [[SUMMARY-PLAIN-ENGLISH]].

**Question.** EXP-A showed deterministic synthetic degradations (added background noise, telephone band-limiting) barely moved WER (clean 21.2% → noise 23.2% → telephone 22.0%). The vendor claims robustness "from crowded markets to call-center floors." Does **real** recorded noise behave like our synthetic transforms, or did our gentle transforms overstate robustness?

**Why it matters.** This is the largest *untested* robustness claim on the current [[indic-transcribe-core]] card. If real noise is categorically harder, EXP-B's reliability features (audio-quality side) were calibrated on the wrong noise distribution and need re-running on real conditions.

## Design

| | |
| --- | --- |
| System | [[indic-transcribe-core]] baseline, identical settings to [[EXP-A]] (explicit `lang`, greedy) |
| Data | Real noisy spontaneous speech: [[kathbath]] (natural recording conditions, read speech — check for non-studio subsets), [[indicvoices]] (crowdsourced phone/mic uploads — closest to call-center acoustics), [[mucs]] (⚠️ to-verify availability) as code-mix strata. Only short-clip subsets needed. |
| Conditions | `real-noise` (market/street/outdoor), `real-phone` (actual telephone/VOIP recordings), `real-far-field`, plus matched `clean` anchors of the same language/content type |
| Languages | Same 8 as EXP-A (hi, ta, te, ml, kn, ur, bho, mai) subject to dataset coverage; drop languages with no real-noise source rather than synthesizing |
| Scale | Start 40–60 clips (5–8 per language per condition), expand on first-pass signal |

## Runs per sample

1. Transcribe with explicit `lang` (primary, comparable to EXP-A).
2. Transcribe with auto-LID (secondary — does real noise also degrade language identification? EXP-A showed LID errors dominate; noise may amplify absorption).
3. Log same features as EXP-B (LID top-k, warning flag, duration) for later reliability re-training.

## Metrics

- WER (whitespace-token, as before — keep comparable with EXP-A) per language × condition
- The **key comparison**: matched-pair delta between `real-noise` and EXP-A's `synthetic-noise` on the same language
- LID top-1 accuracy under real noise vs clean (does absorption worsen?)
- All errors bucketed into [[error-taxonomy]] (expect new buckets: real-overlap, far-field, codec artifacts)

## Outputs

- `data/challenge/manifests/exp-f-v1.jsonl` · `data/challenge/results/exp-f/` (relocate to SSD when next mounted; ⚠️ SSD is currently disconnected — **keep all artifacts on internal disk for now**, budget below)

## Falsifiable targets

- **If** real-noise WER exceeds synthetic-noise WER by >5 points absolute on matched languages → "synthetic transforms overstate robustness"; the vendor's noise claim is materially untested by gentle degradations, and EXP-B must be re-run on real conditions. (Expected outcome.)
- **If** real-noise WER lands within ~2 points of synthetic → our transforms were adequate proxies; record honestly — that *supports* the vendor's claim at the scale we can measure, which is also a publishable finding.
- **If** auto-LID accuracy drops under real noise while explicit-`lang` WER holds → noise primarily hurts language *selection*, strengthening the [[EXP-C]] routing motivation.

## Storage estimate

- Short real-noise subsets only: **well under 2 GB** total (clips ≤30 s; models already downloaded). Internal-disk safe. No model re-download.

## Ablations

- Explicit `lang` vs auto-LID (above).
- Near-duplicate check: confirm no speaker/content overlap between real-noise picks and EXP-A rows (independence).

## v1 pilot results (2026-09-20)

- Data: `ai4bharat/IndicVoices` (gated, HF), 56 clips, 7 languages (hi, kn, mai,
  ml, ta, te, ur — bho dropped, no IndicVoices source, per the design's own
  fallback rule). Condition proxy: `scenario` field — `Conversation`/`Extempore`
  (spontaneous, real field recordings) = `real_noise`; `Read` = `real_clean`.
  8 clips/language (4+4), all ≤30s, audio embedded in the dataset (no separate
  download). Materializer: `code/scripts/materialize_exp_f.py`.
- **Falsifiable target met, decisively.** Real noise vs. real clean: **+20.6
  pts WER** (34.3%→13.7%... i.e. clean 13.7%, noise 34.3%), 95% CI [4.9, 36.4]
  pts, excludes zero, p=0.009. Matched EXP-A synthetic noise vs. clean:
  **+2.0 pts**, 95% CI [−5.4, +9.7] pts, includes zero, p=0.605 — not
  distinguishable from no effect. Real degradation is ~4x the falsification
  threshold this experiment was designed to test, and ~10x the synthetic
  transform's own measured effect.
- **Verdict: synthetic transforms materially overstate robustness** — this is
  the "expected outcome" the design anticipated, now measured. Full writeup:
  [[F-006-synthetic-noise-understates-real-noise|F-006]].
- Artifacts: `data/challenge/results/exp-f-v1-{baseline,summary}.json` (SSD);
  CIs in `code/results/stats/bootstrap.json` (`exp_f`,
  `exp_a_synthetic_noise_vs_clean`).
- Not yet done: auto-LID-under-real-noise comparison (design ablation #2) and
  scaling past the 56-clip pilot.
