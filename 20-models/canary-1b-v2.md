---
type: model
updated: 2026-09-10
hf: "nvidia/canary-1b-v2"
role: "base architecture"
---

# [[canary-1b-v2]]

NVIDIA Canary multilingual ASR — FastConformer encoder + Transformer decoder, task-token driven. Both [[indic-transcribe-core]] and [[indic-transcribe-flex]] are fine-tunes of it.
Reference: [HF](https://huggingface.co/nvidia/canary-1b-v2). Leads HF Open ASR Leaderboard (6.67% avg WER, English-centric runs, vendor-reported).

**Why it matters here:** task tokens select language/mode at *decode* time — that mechanism is what makes cheap multi-hypothesis decoding plausible later (Exp C): same encoder pass, different language tokens → candidate transcripts to score.

Not studied directly in phase 1. Revisit if Exp C requires NeMo-level access to decoder internals (token logprobs, forced decoding).
