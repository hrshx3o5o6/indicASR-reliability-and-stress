---
type: metric
updated: 2026-09-10
metric: entity-accuracy
direction: "higher is better"
---

# [[entity-accuracy]]

Fraction of reference entities transcribed correctly in the hypothesis. An entity error is an error **even when WER impact is tiny**: "Rahul Sharma" → "Rahul Verma" = 2 word errors, 100% entity failure.

## Definition

- Entities pre-annotated in references: `person | location | organization | product | technical` ([[annotation-schema]] `entities` field).
- Match rule: exact match first; ⚠️ to-verify whether transliteration-variant matching (à la [[oi-wer]]) should apply to entity names — decide in a `D-###` before Exp A reporting. Native-script Core output means English-origin names arrive transliterated ("Chennai" in Tamil script) — matching needs a policy, not vibes.
- Report per entity-type and per condition; expect conditions like `telephone + names` to crater ([[THESIS]] P4).

## Relation to other metrics

Feeds [[semantic-slot-accuracy]] (entities are slots) and the reliability feature set (entity confidence features, Exp B). [[critical-value-accuracy]] handles numbers/dates/currency — entities here are lexical, not numeric.
