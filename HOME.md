---
type: moc
updated: 2026-09-10
---

# 🏠 Indic ASR Reliability — HOME

> **Thesis:** SOTA Indic ASR is no longer the primary bottleneck. The bottleneck is *knowing when a transcription can be trusted, why it may be unreliable, and converting it into an application-ready representation.*

New here → [[README]] (operating contract) → [[THESIS]].
**Any LLM agent: read [[README]] before touching anything.**

## System under study

| Model | Params | Languages | Role in project |
| --- | --- | --- | --- |
| [[indic-transcribe-core]] | 1.2B | 25 | **Baseline** (Exp A) |
| [[indic-transcribe-flex]] | 1.2B | 27 | Modes / ITN / romanization (Exp D onward) |

Vendor-reported Voice-of-India OI-WER: **Core 8.7 avg** — Hindi 3.5 … Bhojpuri 13.3, Chhattisgarhi 13.6. *The average is not the story; the variance is.*

## Experiments

```dataview
TABLE status AS Status, phase AS Phase, depends AS "Depends on", updated
FROM "40-pipeline"
WHERE type = "experiment"
SORT file.name ASC
```

## Findings board

```dataview
TABLE status, confidence, metric AS Metric, updated
FROM "60-findings"
WHERE type = "finding"
SORT updated DESC
```

## Decision log

```dataview
TABLE status, date
FROM "70-decisions"
SORT file.name ASC
```

## Dataset candidates

```dataview
TABLE priority, access, license
FROM "50-dataset/datasets"
SORT priority ASC
```

## Open threads

```dataview
TASK
FROM "40-pipeline" OR "90-journal"
WHERE !completed
GROUP BY file.link
```

## Map

- **Why** — [[THESIS]] · decisions: [[D-001-layer-not-model|D-001]], [[D-002-core-as-baseline|D-002]]
- **What** — [[PIPELINE]] · [[roadmap]] · experiments `40-pipeline/experiments/`
- **Measure** — [[METRICS]] registry · [[oi-wer]] · [[lid-reliability]] · [[selective-prediction]] · [[error-taxonomy]]
- **Data** — [[challenge-suite-spec]] · [[annotation-schema]] · [[DATASETS]]
- **Models** — [[indic-transcribe-core]] · [[indic-transcribe-flex]] · [[canary-1b-v2]]
- `wiki/` — compiled knowledge (Karpathy). `code/` — implementation (`code/README.md`)
