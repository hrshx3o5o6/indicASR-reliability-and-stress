---
type: finding
id: F-004
title: "Flex mixed-mode ITN degrades critical-value surfaces — vendor's 'occasionally wrong' is measurable and material"
status: verified
confidence: "medium-high — conservative exact-surface diagnostics on 80 rows"
metric: critical-value-accuracy
updated: 2026-09-17
---

# F-004 — Flex mixed mode fails critical-value surfaces

**Claim.** On our 80-sample suite, [[indic-transcribe-flex]] `mixed` (ITN) mode raises WER 22.01% → 33.54% and collapses **currency surface recall 100% → 0%** and **entity surface recall 49.6% → 20.5%** versus Core native. The card's *"mixed-script mode will occasionally get it wrong"* materially understates the failure mode on critical-value content in our slice.

**Evidence.** [[EXP-D]] final v1: `data/challenge/results/exp-d/exp-d-semantic-curated-summary.json` (SSD). Per-mode (Core native / Flex native / Flex mixed): number surface recall 59.1 / 59.1 / 77.3% · currency 100 / 100 / 0% · entity 49.6 / 60.3 / 20.5%. Mixed improved 9/80 rows, worsened 56/80, emitted digit-like tokens on 15/80 and Latin-script tokens on 62/80.

**Provenance.** `exp-d` (agent-reviewed conservative annotations, 2026-09-16/17). Exact-surface diagnostics — the scorer accepts the exact spoken phrase or digit value only, no transliteration or compositional variants. Not publication-grade semantic accuracy.

**Interpretation.** Quantifies a vendor-documented limitation. The card's own production advice — *"native-script mode is recommended, applying your own ITN downstream if you need it"* — is precisely this project's design point ([[D-001-layer-not-model]], [[EXP-D]]). Mixed mode's only surface win (digit-form number recall 77.3% vs 0.0% for native modes) shows what ITN *can* extract, but it trades critical-value integrity for formatting.

**Status.** `verified` in scope; operational decision recorded: **do not ship Flex mixed as a normalization layer** (19/80 rows remain conservatively flagged for optional human review — does not change the verdict). **If confirmed at scale:** strengthens the case for a semantics-preserving normalization layer with critical-value gates. **If refuted:** would require human-reviewed semantic labels showing mixed preserves meaning where it changes format — surface recall alone cannot settle it.

**Card relation.** The Flex card carries both a usage recommendation for mixed mode *and* a Limitations warning against it. Our evidence sides with the Limitations section.
