---
type: dataset
updated: 2026-09-10
---

# challenge-suite-spec — the structured stress test

**Not** a giant random test set. A deliberately structured challenge suite where every sample exists to answer a question. v0 = 50–100 samples, expand only after v0 proves its design ([[EXP-A]]).

## Condition taxonomy

**Audio conditions**
`clean` · `telephone` (bandpass + codec) · `background_noise` · `low_snr` · `reverberation` · `fast_speech` · `slow_speech` · `interruptions` · `multi_speaker`

**Content conditions**
`normal` · `code_mixed` · `heavy_code_mixed` · `english_terms` · `numbers` · `dates` · `times` · `currency` · `names` · `locations` · `organizations` · `technical`

**Combinations are the point** — the suite is built as (audio × content) pairs/cells, not a condition-per-sample list:
`noise+code_mixed` · `telephone+code_mixed` · `fast_speech+numbers` · `telephone+names` · `noise+names+code_mixed` · `code_mixed+technical` · `fast_speech+currency` · `multi_speaker+code_mixed` …

P4 of [[THESIS]]: interactions may be **non-additive** (clean 5% + noise 8% + code-mix 9% → combined 18%). The suite must contain cells that can prove or kill this.

## Design constraints

| Constraint | Value/reason |
| --- | --- |
| Languages | ta, hi, te, ml, kn, bho, mai, ur — confusion set {hi,bho,mai,ur} + strong non-Hindi {ta} + code-mixing room ([[THESIS]]) |
| Per cell | ≥3 samples minimum for v0; shared speakers across cells where possible (speaker control) |
| Sources | [[DATASETS]] registry — natural where possible, degraded-paired where needed, synthetic only if flagged |
| Degradations | Our own chain (ffmpeg/sox): documented, versioned, **paired** with the clean original — every degraded sample knows its clean twin |
| Balance | Don't let ta/hi dominate; bho/mai/ur must have enough mass to measure absorption ([[F-001-hindi-belt-lid-absorption|F-001]]) |
| Contamination | Prefer sources with no evidence the model trained on them; record `contamination_risk` field; flag rather than assume |

## Metadata contract

Every sample carries full provenance + annotation per [[annotation-schema]]. `source`, `source_id`, `degradation_chain`, `speaker_id`, `synthetic`, `contamination_risk` are mandatory — untraceable samples get dropped at review.
