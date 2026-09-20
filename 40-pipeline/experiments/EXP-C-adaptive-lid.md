---
type: experiment
id: EXP-C
title: "Adaptive LID + multi-hypothesis decoding (next project seed)"
status: done
phase: results
depends: ["EXP-B"]
updated: 2026-09-15
---

# EXP-C — Adaptive LID & multi-hypothesis decoding

> Live observations and cross-experiment takeaways: [[EXPERIMENT-OBSERVATIONS]].

**Question.** When LID is uncertain (hi 0.48 / bho 0.44 / mai 0.06), does decoding top-K language hypotheses and scoring them on evidence beat trusting top-1? This is the *next project* — Exp-B's abstained cases are its input distribution.

## Design sketch (do not build until Exp A/B verdicts exist)

```
audio → identify() top-K (e.g. K=3, no allowed_langs filtering by default)
      → per-language decode (task-token switch = cheap, same encoder pass — [[canary-1b-v2]])
      → hypothesis scorer (features: LID prior × LM likelihood × script consistency ×
         [[critical-value-accuracy]]-style consistency checks × acoustic match)
      → best (language, transcript) + still-honest reliability score
```

Confusable set focus: {hi, bho, mai, ur} where absorption is documented ([[F-001-hindi-belt-lid-absorption|F-001]]).

## Prerequisites from Exp A/B

- Measured top-K LID: does the truth appear in top-K on the confused cases? (if top-1 wrong but top-3 right → multi-hypothesis has headroom; if truth absent from top-K entirely → routing can't save it — either verdict is a key finding)
- Hypothesis-scorer features validated on Exp-A per-sample records
- Abstained-case distribution from [[EXP-B]] = the test distribution

## Success criterion

Beat top-1-LID baseline OI-WER on the *confused subset* without degrading the confident subset. If the scorer just reproduces top-1, that's a killed hypothesis — record it.

## Results (2026-09-15)

- Input: EXP-A v1, 80 samples; top-3 truth coverage is 79/80.
- Decoder: Core shared-encoder top-3 hypotheses with mean decoder token log-probability plus LID prior.
- Output: `data/challenge/results/exp-c/` on the SSD.

| Measure | Result |
| --- | ---: |
| Top-3 truth coverage | 79/80 (98.75%) |
| Baseline auto-LID WER | 24.87% |
| Adaptive selected WER | 25.00% |
| Oracle top-3 WER | 22.38% |
| Selected language accuracy | 87.5% (70/80) |

The current scorer is a **killed hypothesis** for this benchmark: it essentially reproduces top-1 routing and slightly degrades WER. The result is still valuable because the oracle gap shows that candidate generation has headroom; the missing component is a better reranker, especially for Bhojpuri. Bhojpuri selected-language accuracy remained 0/10, while the other seven languages were 10/10 in this slice.

**Verdict.** Do not deploy this reranker. Retain top-K generation as a research primitive and require a stronger language-sensitive/semantic reranker before claiming an EXP-C win.
