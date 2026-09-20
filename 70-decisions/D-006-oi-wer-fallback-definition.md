---
type: decision
id: D-006
title: "OI-WER: use a normalization-tolerant, multi-reference fallback, not the vendor's definition"
status: accepted
date: 2026-09-20
updated: 2026-09-20
---

# D-006 — OI-WER fallback definition

## Context

[[oi-wer]] flagged an open pitfall from the start: "is there a public reference
implementation of OI-WER, and does 'documented variants' mean a published
variant table we can reuse? If none exists: fall back to standard WER plus our
normalization-tolerant scoring." Before publication, `REPORT.md` §C5 compared
whitespace WER (22.0%) against the vendor's self-reported OI-WER (8.7%) —
different metrics on different corpora, acknowledged in the report as a gap
that "does not transfer."

Checked directly (2026-09-20): the vendor has not published an OI-WER
reference implementation. The suite's `reference_variants` manifest field
(`50-dataset/annotation-schema.md`) is populated for 57/80 EXP-A rows, but
inspection shows these are punctuated restatements of the primary reference
(original FLEURS/source text with punctuation retained), not a curated table
of documented spelling/transliteration alternatives.

## Decision

Implement OI-WER as the registry's own documented fallback:
NFKC normalization, casefold, cross-script digit folding, punctuation
stripping, and multi-reference scoring (min WER over reference ∪ variants).
Code: `code/metrics/oi_wer.py`. Label all results from this implementation as
**"project OI-WER"**, explicitly distinct from the vendor's OI-WER, in every
place they are reported.

## Consequences

- + Closes the metric-pending TODO in `REPORT.md` §4/§7 (C5) without
  fabricating a variant table we don't have.
- + Gives an honest, if partial, apples-to-apples adjustment: normalization
  tolerance closes ~2 of the ~13-point gap between our slice (19.9%) and the
  vendor's reported average (8.7%), strengthening rather than weakening C5.
- − Still not the vendor's own metric or corpus — C5 remains "does not
  transfer," now on firmer ground rather than a metric mismatch.
- − Multi-reference scoring currently has near-zero effect (57/80 variants are
  near-duplicates of the primary reference after normalization) — real value
  requires a genuinely curated variant table, not built here.

**Upgrade path:** if a curated spelling/transliteration variant table is ever
built, `oi_wer()` already supports it via `reference_variants` — no interface
change needed.

Related: [[oi-wer]] · [[METRICS]] · `REPORT.md` §5.7
