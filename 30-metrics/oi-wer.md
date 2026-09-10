---
type: metric
updated: 2026-09-10
metric: oi-wer
direction: "lower is better"
---

# [[oi-wer]] — Orthographically-Informed WER

WER variant that **accepts documented spelling/transliteration variants as correct**, scored against **multi-reference** transcripts. It matters for Indic scripts, where the same spoken word has many valid orthographies — plain WER punishes orthography, not recognition.

Vendor benchmark (Voice of India) reports OI-WER: [[indic-transcribe-core]] avg 8.7 (⚠️ vendor-reported, re-measure).

## Pitfalls / decisions

- ⚠️ to-verify: is there a public reference implementation of OI-WER, and does "documented variants" mean a published variant table we can reuse? If none exists: fall back to standard WER **plus** our normalization-tolerant scoring (compare after applying a fixed, versioned normalization to both hyp and ref) and record the deviation in a `D-###` decision.
- Multi-reference scoring requires our challenge set to carry the reference variants it accepts ([[annotation-schema]]).
- OI-WER is still a **bag-of-words** metric → it cannot see [[critical-value-accuracy]] or [[entity-accuracy]] failures. Never report it alone.
