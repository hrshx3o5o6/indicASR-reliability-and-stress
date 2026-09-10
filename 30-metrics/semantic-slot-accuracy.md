---
type: metric
updated: 2026-09-10
metric: semantic-slot-accuracy
direction: "higher is better"
---

# [[semantic-slot-accuracy]]

Compare **structured facts**, not text: extract semantic slots from reference and hypothesis independently, diff the structures.

```json
// ref: "Transfer ₹50,000 to Rahul tomorrow."
{"action": "transfer", "amount": 50000, "recipient": "Rahul", "date": "tomorrow"}
```

Slot accuracy = fraction of reference slots preserved exactly in the hypothesis' slots.

## Why it exists

- An LLM judge is **auxiliary only** — it can hallucinate agreement and hides its reasoning. Structured slots are checkable, deterministic, versioned.
- It is the **acceptance test for Exp-D normalization**: normalization that raises [[oi-wer]] but flips an amount or a recipient slot is rejected, full stop ([[THESIS]] rule 4).

## Scope

v1 slots: `action` (limited verb inventory), `amount`, `date`, `time`, `recipient`, `location`. ⚠️ to-verify: slot extraction will start pattern-based per language; keep the extractor versioned and pin it in every experiment record — extractor drift silently invalidates cross-experiment comparisons.
