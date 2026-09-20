---
type: experiment
id: EXP-F
title: "Real-world noise robustness — market/call-center audio vs synthetic degradations"
status: planned
phase: ""
depends: ["EXP-A"]
updated: 2026-09-17
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
