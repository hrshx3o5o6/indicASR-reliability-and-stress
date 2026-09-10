---
type: metric
updated: 2026-09-10
metric: selective-prediction
direction: "lower risk at higher coverage is better"
---

# [[selective-prediction]] — abstention done honestly

The system may return `accept | warn | abstain`. Measuring only accuracy on accepted answers invites gaming (abstain on everything hard). So:

| Quantity | Definition |
| --- | --- |
| **Coverage** | fraction of examples answered (accept or warn) |
| **Selective OI-WER** | [[oi-wer]] computed **only on answered** examples |
| **Selective accuracy** | 1 − risk on answered examples |
| **Risk–coverage curve** | risk vs coverage as threshold sweeps; report AURC |
| **AUROC** | reliability score separating acceptable vs unacceptable transcripts |
| **Abstention quality** | error rate of *abstained* examples should exceed answered error rate — if abstained examples are no harder than answered ones, the detector is useless |

## Reporting contract

Always report **(coverage, selective risk) pairs**, never one without the other. "Selective WER 3.2% @ 70% coverage" is a result; "selective WER 3.2%" is marketing.

## Decision-engine tie-in

Thresholds on the reliability score map to accept/warn/abstain; they are chosen from the risk–coverage curve on held-out data, never a priori ([[PIPELINE]]). The curve from Exp B is the artifact that justifies (or kills) the whole abstention thesis (P6 in [[THESIS]]).
