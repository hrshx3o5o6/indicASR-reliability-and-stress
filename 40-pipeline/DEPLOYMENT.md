---
type: pipeline
title: "Target deployment architecture and real-world use cases"
status: planned
updated: 2026-09-19
---

# DEPLOYMENT — from experiment to a trust layer product

> Captures the **real-world use case** and the **future scope** surfaced while
> planning the sandboxed Ralph loop (2026-09-19). Engineering constraints and
> blockers live in [[INFRA-NOTES]]; the decisions are [[D-003-model-as-service]]
> and [[D-004-sandboxed-thin-clients]].

## The real-world use case

The vendor's own model card says: *"native-script mode is recommended, apply your
own ITN downstream if you need it."* This project **is that downstream layer**, with
the metrics to prove when it can be trusted. The product is not another ASR model
([[D-001-layer-not-model|D-001]]) but the layer that answers:

- Can this transcript be trusted? (`accept / warn / abstain`)
- Where exactly is it uncertain? (uncertain spans, critical values)
- Why? (LID absorption, short turns, code-mixing, low SNR)

Concrete applications (each with a different cost of a wrong transcript):

| Application | What a wrong transcript costs | Layer capability required |
| --- | --- | --- |
| Call-center QA / compliance | mis-scored agent, missed obligation | accept/warn/abstain + speaker turns |
| Government / healthcare voice intake | wrong name, amount, date | critical-value gates + normalization |
| Financial services (loan/insurance) | tenfold currency error, wrong ID | semantic-slot accuracy, no ITN drift |
| Education / assessment | unfair grading | language-aware reliability |
| Media / legal transcription | misattribution | diarization + uncertain spans |
| Field data collection (Bhojpuri/Maithili belts) | silent systematic error | LID routing / top-K, not auto top-1 |

The unifying pitch: *SOTA models come with fine print. We measure the fine print,
then build the trust layer.* Evidence for the fine print already exists in
[[F-001-hindi-belt-lid-absorption|F-001]], [[F-003-oracle-turns-fail-diarbench|F-003]],
[[F-004-flex-mixed-critical-values|F-004]].

## Target deployment architecture (Pattern 1)

Model inference is a **pure service**; untrusted/agent code is **sandboxed** and
talks to it over HTTPS. Weights and secrets never enter a sandbox.

```
                        persistent, heavy
   ┌─────────────────────────────────────────────┐
   │  ASR inference service (pinned revision)    │
   │  Core + Flex · weights cached · MPS/GPU     │
   │  /transcribe  /identify  /topk_decode       │
   └───────────────────▲─────────────────────────┘
                       │ HTTPS (public endpoint via tunnel)
     ┌─────────────────┼──────────────────┐
     │ reqly/E2B       │ reqly/E2B        │  ephemeral, ~1 GB, no GPU
     │ sandbox pass    │ sandbox pass     │  reads cached results, calls service
     └─────────────────┴──────────────────┘
                       │
        state + artifacts ──► git / object store (never the sandbox)
```

- **Service:** `code/asr_service.py` — FastAPI around the vendored wrapper,
  pinned revision `4d29eeb7a099`, echoes `{revision, dtype, decoding}` per response.
- **Client:** `code/asr_client.py` — runners take `--asr-url`; local loader stays
  as a fallback. One code path, two placements.
- **Sandboxes:** reqly managed/E2B, thin client only ([[D-004-sandboxed-thin-clients]]).
- **Interim host:** Apple M5 + `cloudflared` quick tunnel (option A, chosen
  2026-09-19). Later: serverless GPU (Modal) when reruns get heavy.

## Future scope (parking lot)

1. **Public inference endpoint** — move service from M5 tunnel to a hosted GPU;
   stable URL, auth, rate limits, batching.
2. **Reliability API** — wrap the [[PIPELINE]] contract (`accept/warn/abstain`,
   `uncertain_spans`, reasons) as a product endpoint over the ASR service.
3. **Semantics-preserving normalization layer** — the downstream ITN the vendor
   recommends; gated by [[semantic-slot-accuracy]] and [[critical-value-accuracy]].
4. **LID routing / reranker** — promote the [[EXP-C]] top-K primitive into a
   language-sensitive reranker (the current likelihood scorer is killed).
5. **Multi-speaker pipeline** — neural diarizer + turn padding ([[EXP-E]] iteration 2).
6. **Real-noise robustness** — [[EXP-F-real-noise|EXP-F]], real market/call-center strata.
7. **Code-mixing** — the largest untested vendor claim; Hinglish/MUCS strata.
8. **Streaming / online reliability** — estimate trust mid-utterance.
9. **Human-in-the-loop** — route `abstain` cases to review; measure review load.
10. **Sandboxed research loop** — the Ralph loop ([[INFRA-NOTES]] §Ralph) making
    every claim reproducible on demand.
11. **Certification / deployment hardening** — E2B isolation ownership, service
    auth, egress, quota, audit (see reqly's own security limitations).

## Non-goals (unchanged from [[THESIS]])

No ASR training/fine-tuning, no generic "Indic STT app", no LLM correction before
the baseline is understood, no claim of safety-critical production readiness.

## Open questions

- Who owns the inference service in production — us, or the customer's VPC?
- Does the reliability layer ship as a library, a sidecar, or a hosted API?
- How to price/measure the abstain→human-review loop.
- What is the SLA when the model service is down mid-pass (receipt semantics)?

Related: [[PIPELINE]] · [[THESIS]] · [[D-003-model-as-service]] · [[INFRA-NOTES]]
