---
type: metric
updated: 2026-09-10
metric: critical-value-accuracy
direction: "higher is better"
---

# [[critical-value-accuracy]] — numbers · dates · currency · time

One metric family for the content types whose errors are **semantically massive but WER-small**:

| Type | Reference | Hypothesis | WER impact | Real impact |
| --- | --- | --- | --- | --- |
| currency | ₹50,000 | ₹5,000 | 1 word | 10× amount error |
| number | 25,000 | 2,500 | 1 word | 10× quantity error |
| date | 10 Sep 2026 | 10 Sep 2025 | 1 word | year error |
| time | 5:00 pm | 5:30 pm | 1 word | meeting missed |

## Definition

- Extract each value from reference and hypothesis (annotation pre-annotates in refs; extraction from hyps is scripted), normalize both (digit forms), compare.
- Report: **exact-match accuracy** per type + **relative magnitude error** for numeric/currency (50,000→5,000 is worse than 50,000→50,005) + **component breakdown** for dates (year/month/day separately — 2026→2025 outranks a day-name slip).
- ⚠️ to-verify: Core outputs spoken numbers **as words in native script** ("पांच हज़ार"). Comparison requires scripted word→digit normalization for each language in our set — this is exactly Exp-D machinery pulled forward. For Exp A, evaluate on **Flex `mixed` mode** (ITN built in) *and* Core-with-our-minimal-normalizer, and record which path we use per table row.

## Guard

This metric doubles as the acceptance test for any normalization ([[semantic-slot-accuracy]] for the broader check): if our normalizer "improves" WER but breaks a number here, the normalizer is rejected ([[THESIS]] rule 4).
