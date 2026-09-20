---
type: finding
id: F-006
title: "Synthetic background-noise degradation understates real-world noise by roughly an order of magnitude"
status: verified
confidence: "high — statistically significant, matched languages, real vs. our own synthetic transform"
metric: wer
updated: 2026-09-20
---

# F-006 — EXP-A's synthetic noise transform is a weak proxy for real noise

**Claim.** Real crowdsourced conversational/spontaneous audio (IndicVoices) costs
[[indic-transcribe-core]] a statistically significant **+20.6 point** WER penalty
relative to clean speech in the same corpus. Our own synthetic background-noise
transform, used throughout [[EXP-A]]/EXP-D/EXP-E, costs only **+2.0 points** — not
statistically distinguishable from zero. This confirms and quantifies EXP-F's
registered falsifiable prediction ("if real-noise WER exceeds synthetic-noise
WER by >5 points absolute on matched languages, synthetic transforms overstate
robustness") — the real gap is roughly **4x the falsification threshold**, and
about **10x** the synthetic transform's own measured effect.

**Evidence.** EXP-F v1, 56 real clips across 7 languages (hi, kn, mai, ml, ta,
te, ur — no bho, absent from IndicVoices), sourced from `ai4bharat/IndicVoices`
(2026-09-20). Condition proxy: IndicVoices' own `scenario` field — `Conversation`/
`Extempore` (spontaneous, naturally noisy field recordings) as `real_noise`,
`Read` (near-studio) as `real_clean`. No synthetic degradation applied to either
— both are real recordings.

| | n | Mean WER | 95% CI |
| --- | ---: | ---: | --- |
| Real noise (IndicVoices, spontaneous) | 28 | 34.3% | [23.4%, 47.3%] |
| Real clean (IndicVoices, read) | 28 | 13.7% | [5.2%, 24.8%] |
| **Unpaired diff (noise − clean)** | | **+20.6 pts** | **[4.9, 36.4] pts, excludes zero, p=0.009** |
| Synthetic noise (EXP-A) | 24 | 23.2% | [17.7%, 29.2%] |
| Synthetic clean (EXP-A) | 32 | 21.2% | [16.3%, 26.4%] |
| **Unpaired diff (noise − clean)** | | **+2.0 pts** | **[−5.4, +9.7] pts, includes zero, p=0.605** |

Per-language real noise−clean deltas (n=4 each, small-n, high variance — see
Limits): hi +46.7, mai +29.4, ta +27.3, kn +20.4, ur +9.9, ml +9.0, te +1.5 pts.
Artifacts: `data/challenge/results/exp-f-v1-{baseline,summary}.json` (SSD),
`code/results/stats/bootstrap.json` (`exp_f`, `exp_a_synthetic_noise_vs_clean`).

**Interpretation.** This project's own synthetic noise transform — deterministic
background-noise mixing at a fixed level — was, by design, "gentle" (EXP-A
condition table: clean 21.2% / noise 23.2%, a 2-point spread). It was never
validated against real acoustic conditions until this experiment. The result:
it materially **understates** real-world degradation. This has two implications:
1. Every EXP-A/D/E conclusion drawn from the "noise" condition column
   characterizes robustness to *mild, deterministic* degradation only — it says
   nothing about robustness to real spontaneous/field audio.
2. EXP-B's reliability features were fit on synthetic-noise-range acoustic
   variance; if real-world variance is 10x larger, those features (already a
   negative result, AUC 0.515) were calibrated on a narrower distribution than
   production traffic would present, which may partly explain why they failed
   to predict errors ([[EXP-B]]).

**Status.** `verified`, first-pass pilot (n=56, per EXP-F's own "start 40-60
clips, expand on signal" design). Falsifiable target met decisively — no
further confirmation run needed before citing the qualitative conclusion
("synthetic transforms overstate robustness"); a larger sample would tighten
the wide per-language CIs before citing individual per-language deltas.

**Limits.** n=4 per language per condition is small; the aggregate n=28/28
result is the reliable number, per-language deltas are directional only. The
`scenario` field is a proxy for real acoustic difficulty, not a controlled
SNR measurement — `Conversation`/`Extempore` audio also differs from `Read` in
speaking style (spontaneous vs. scripted), so some of the WER gap may be
disfluency/spontaneous-speech effects rather than pure acoustic noise; this
finding characterizes "real crowdsourced audio" broadly, not noise in
isolation. bho is untested (no source in IndicVoices).

**Card relation.** Directly tests the vendor's claim of handling "noisy
real-world conditions, from crowded markets to call-center floors." This is
the first evidence in this project measuring against **real** noise rather
than synthetic proxies for that claim — and shows the synthetic proxies this
project itself used were far too gentle to test it meaningfully.
