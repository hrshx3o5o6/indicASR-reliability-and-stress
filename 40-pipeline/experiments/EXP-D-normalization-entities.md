---
type: experiment
id: EXP-D
title: "Semantics-preserving normalization + entity correction"
status: done
phase: results
depends: ["EXP-B"]
updated: 2026-09-16
---

# EXP-D — Normalization & entity correction

**Question.** Can Core's native-script output be converted to application-ready text (digits, dates, entities, mixed script) **without changing the speaker's meaning**? And does that layer beat Flex's built-in ITN?

## Two sub-systems

### 1. Normalization (numbers, dates, currency, units, technical terms)
- Word→digit normalization per language (Core outputs spoken numbers as words — see [[critical-value-accuracy]])
- **Acceptance test: [[semantic-slot-accuracy]] must not regress; [[critical-value-accuracy]] must improve.** A normalization that raises OI-WER but flips meaning is rejected ([[THESIS]] rule 4)
- Baseline to beat: Flex `mode="mixed"` (built-in ITN) — the Flex card itself admits mixed mode "will occasionally get it wrong"; measure both, compare on identical audio
- ⚠️ Normalizer versioned + pinned; self-inflicted errors go to the `normalization` bucket of [[error-taxonomy]]

### 2. Entity correction (conservative by design)
```
transcript → entity detection → candidate generation → contextual validation → correct ONLY at high confidence
```
- Never "correct" merely because a database form is more frequent
- Every correction logged with evidence; wrong corrections tracked as findings
- Cases: "Rahul Sharma"→"Rahul Verma" (must NOT fire), "Chennai IIT"→"IIT Madras" (may fire only with strong contextual evidence)

## Evaluation

Same suite as [[EXP-A]]; deltas reported per metric + per bucket; entity-correction precision/recall on the entity subset; ITN comparison table Core+ours vs Flex-mixed.

## Output

Normalization + entity layers gated behind the reliability engine (apply to accept/warn cases; abstain cases bypass or route to [[EXP-C]]).

## Prerequisite check (2026-09-15)

- **Flex checkpoint/code:** downloaded to the SSD and verified by a native/mixed smoke test.
- **Semantic annotations:** absent from the EXP-A v1 manifest; no defensible slot/entity accuracy comparison can be made from the current references alone.
- **Decision:** complete the model comparison, but keep semantic normalization and entity-correction claims gated until the annotation pass is versioned.
- **Operational update:** the external SSD is now mounted with approximately 814 GiB free. Flex download is active at `data/models/indic-transcribe-flex/`; no internal storage is being used for the model.

## Results (2026-09-15)

- Flex checkpoint download completed and passed a native/mixed smoke test.
- Full Core-native versus Flex-native versus Flex-mixed evaluation completed over the 80-row EXP-A v1 suite on CPU.
- Output: `data/challenge/results/exp-d/` on the SSD.

| Measure | Core native | Flex native | Flex mixed |
| --- | ---: | ---: | ---: |
| Mean whitespace-token WER | 22.01% | 22.09% | 33.54% |

Flex native improved over Core on 19/80 rows, tied 36/80, and was worse on 25/80. Flex mixed improved over Core on 9/80, tied 15/80, and was worse on 56/80. Mixed mode emitted digit-like tokens on 15/80 rows and Latin-script tokens on 62/80 rows, confirming that it changes formatting but not that it preserves meaning.

**Verdict.** Flex native is effectively tied with Core on this small slice; Flex mixed is not an acceptable drop-in normalization baseline by WER. Semantic-slot and entity accuracy remain uncomputed, so no semantics-preserving normalizer or entity-correction success claim is allowed. The next required step is annotation, not more model downloading.

## Annotation pass v1 (2026-09-16)

- Generated a conservative 80-row annotation-candidate file at `data/challenge/manifests/exp-d-v1-annotations.jsonl`.
- Curated `data/challenge/manifests/exp-d-v1-annotations-curated.jsonl` for all 80 rows by annotating 32 unique clean references and propagating labels to their synthetic twins.
- 11 rows contain high-confidence number/identifier labels; 36 rows contain entity labels; 22 rows remain flagged for human review.
- Current scorer measures conservative surface recall: Core native `0.591`, Flex native `0.591`, Flex mixed `0.773` across the 11 labeled rows; digit-only recall is `0.00`, `0.00`, and `0.773` respectively.
- This is **not** semantic-slot accuracy: it accepts exact spoken phrases or digit values but does not handle transliteration or compositional number variants.
- Full publication-grade semantic reporting remains optionally gated on human review of the 19 conservatively flagged rows and stronger language-aware scoring.

## Final v1 semantic diagnostics (2026-09-17)

The annotation set is agent-reviewed and covers all 80 rows; 19 rows remain conservatively flagged for possible human review. The scorer evaluates exact spoken surfaces or digit values and therefore undercounts transliteration-equivalent entities.

| Diagnostic | Core native | Flex native | Flex mixed |
| --- | ---: | ---: | ---: |
| Number surface recall (11 labeled rows) | 59.1% | 59.1% | 77.3% |
| Digit-only recall (11 labeled rows) | 0.0% | 0.0% | 77.3% |
| Currency surface recall | 100.0% | 100.0% | 0.0% |
| Entity surface recall | 49.6% | 60.3% | 20.5% |

**Final EXP-D verdict.** Do not ship Flex mixed as a normalization layer. It improves digit rendering in some cases but loses currency/entity surfaces and previously changed `19,500` to `1950`. Core native remains the safer default. No normalization or entity-correction layer is promoted from this experiment.

### Storage estimate

- **Required download:** `bodhan-ai/indic-transcribe-flex`, approximately **4.6 GB** for the model weights, plus a small amount for tokenizer/config/model code.
- **Safe working budget:** reserve **10 GB** to allow Hugging Face cache/temp duplication during download; remove duplicate cache copies afterward.
- **Required dataset download:** **0 GB**. EXP-D reuses the existing 80-sample EXP-A audio suite.
- **Local labels:** semantic-slot and entity annotations are authored locally; expected size is **well under 1 MB** for 80 rows.
- **Optional expansion:** additional natural entity/number audio is useful but not required for the first EXP-D run and should be budgeted separately.
