---
type: moc
updated: 2026-09-10
---

# METRICS registry

One note per metric. A metric is only used after its note exists (definition, pitfalls, tooling status). Rule from [[THESIS]]: **WER alone is never sufficient.**

| Metric | Notes | Guards against |
| --- | --- | --- |
| [[oi-wer]] | primary ASR metric, orthography-tolerant | punishing valid spelling variants |
| [[entity-accuracy]] | entity-level correctness | small-WER huge-harm name errors |
| [[critical-value-accuracy]] | numbers · dates · currency · time | ₹50,000→₹5,000 "one word" errors |
| [[lid-reliability]] | top-k acc, margin, entropy, calibration | trusting confident-but-wrong LID |
| [[semantic-slot-accuracy]] | structured fact preservation | normalization "fixing" meaning |
| [[selective-prediction]] | coverage, risk–coverage, AURC | abstention that abstains on everything |
| [[error-taxonomy]] | bucketing scheme for all failures | only reporting aggregates |

Cross-cutting: every metric is computed **stratified by language × condition**, never only in aggregate ([[THESIS]] P1, P4). See [[challenge-suite-spec]] for how conditions get attached, [[annotation-schema]] for the data format.

## Dashboard: results live here

```dataview
TABLE metric, updated
FROM "30-metrics"
WHERE type = "metric"
SORT file.name ASC
```

Result files land in `code/results/` and are summarized into experiment notes — this registry stays definitional.
