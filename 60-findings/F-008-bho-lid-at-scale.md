---
type: finding
id: F-008
title: "At 64x the sample, Core's Bhojpuri auto-LID is 0/644 while Flex's is 371/644 — and it is not the padding"
status: verified
confidence: "high (n=644 real clips, 100 speakers, 3 districts; Wilson CIs below)"
metric: lid-reliability
updated: 2026-10-21
---

# F-008 — Bhojpuri LID re-measured at scale on unpadded audio

**Claim.** The EXP-A Bhojpuri headline (Core 0/10, Flex 4/10; 4 independent
clips) holds and sharpens on 644 real, unpadded clips. Core never identifies
Bhojpuri; Flex does so ~58% of the time. The failure is Bhojpuri-specific: the
same 100 speakers' Hindi is identified at 97-99.5% by both models.

**Evidence.** `code/results/v2/bho-lid-{core,flex}.jsonl`, summaries
`code/results/v2/bho-lid-{core,flex}-summary.txt`, manifest
`code/results/v2/bho-lid-manifest.jsonl`, scripts `code/scripts/v2/lid_v2.py`,
`analyze_lid.py`. Source: `ai4bharat/Rural_Women_Bhojpuri` (CC-BY-SA-4.0),
`benchmark` (444, read, no speaker IDs) + `train_real` (200 bho + 200 hi,
100 speakers). Models pinned: Core `e083ab7d`, Flex `c0db6b2b`. CPU, `identify(topk=5)`.

| | Core | Flex |
|---|---|---|
| benchmark bho | 0/444, Wilson [0, 0.9]% | 247/444 = 55.6% [51.0, 60.2] |
| train_real bho (100 spk) | 0/200 [0, 1.9]% | 124/200 = 62.0% [55.1, 68.4] |
| train_real hi (same spk) | 199/200 = 99.5% | 195/200 = 97.5% |
| bho wrong -> | mai 345, hi 270 | mai 134, hi 114 |
| true bho in top-3 | 322/644 | 604/644 |
| wrong answers at p>=0.9 | 55% | 29% |

Core ranks the true language 3rd-4th typically (benchmark: 2nd 16, 3rd 181,
4th 104, 5th 28, outside top-5 115), median P(bho) = 1e-4.

**Provenance.** `exp-a v2` (this pass).

**Interpretation.**
- The EXP-A ~50 s padding (data-expansion-v2 section 10) is **not** the
  cause: the bare 7.45 s source utterance is also misidentified.
- C1/C7/C9 are upgraded from n=10 to n=644. The Core/Flex asymmetry is a
  property of the checkpoints, not small-sample noise.
- **EXP-C's top-K headroom does not transfer to Core on Bhojpuri.** EXP-C
  saw truth in top-3 for 10/10 padded clips; at scale Core has it for only
  half, at negligible probability. An arbiter for Core must decode a fixed
  belt candidate set (hi/mai/bho), not Core's own top-K. Flex's top-3 holds
  the truth 94% of the time, so top-K reranking stays viable on Flex.

**Status.** verified.

**Limits.** One source (rural women, eastern UP districts); benchmark split is
read speech without speaker IDs; LID only (no WER in this pass).
