---
type: metric
updated: 2026-09-10
metric: error-taxonomy
---

# [[error-taxonomy]] — failure buckets

Every analyzed error gets exactly one primary bucket (primary cause, judged in context) plus optional secondary tags. Aggregate scores never substitute for bucket counts ([[THESIS]] style rule: be critical, find the real bottleneck).

| Bucket | Contains |
| --- | --- |
| `acoustic` | noise, telephone-band, reverb, clipping, low-SNR-driven deletions |
| `lid` | wrong-language decode, script mismatch with true language |
| `lexical` | ordinary word substitutions/insertions/deletions |
| `entity` | names, orgs, places ([[entity-accuracy]]) |
| `numeric` | numbers, currency, magnitudes ([[critical-value-accuracy]]) |
| `datetime` | dates, times, years |
| `code-mixing` | English-in-Indic or mixed-segment breakage |
| `script` | wrong script, transliteration chaos, mixed-script artifacts |
| `overlap` | multi-speaker, interruptions |
| `hallucination` | repeated/looped text, fluent text with no acoustic support |
| `normalization` | errors *introduced by* our own post-processing (self-inflicted — track honestly) |

## Outputs expected from Exp A

- bucket × language and bucket × condition heatmaps (the interaction table of [[THESIS]] P4)
- confusion matrix by language ([[lid-reliability]])
- `hallucination` + `normalization` buckets are tracked from day 1 so Exp-D regressions have a baseline

Bucketing procedure: automated alignment (WER diff) proposes, human/LLM-review confirms; disagreements logged. ⚠️ to-verify: define the review protocol before Exp A ends, in a `D-###`.
