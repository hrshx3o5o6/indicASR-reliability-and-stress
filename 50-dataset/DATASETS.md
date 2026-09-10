---
type: moc
updated: 2026-09-10
---

# DATASETS — sourcing strategy for the challenge suite

**Rule from [[challenge-suite-spec]]:** we are building a *deliberately structured* challenge suite (50–100 samples v0), not a giant random test set. Public datasets provide raw material; structure comes from our condition taxonomy.

## Strategy

1. **Natural speech with references** (IndicVoices, Kathbath, FLEURS, MUCS, Common Voice) → source audio + reference text, tagged by our conditions.
2. **Controlled degradation** → where no paired degraded audio exists, apply *our own* degradations (telephone bandpass, noise @ SNR, reverb, time-stretch) to clean sources. Paired clean/degraded = interaction analysis (P4) becomes possible.
3. **TTS-derived synthetic** ([[indic-tts-corpora|IndicTTS]] etc.) → *perfect references* + full condition control; always marked `synthetic: true` so results are never conflated with natural-speech results.
4. **Multi-speaker** ([[indic-diarbench|Indic DiarBench]]) → Exp E only, don't touch before then.

## Candidate registry

```dataview
TABLE priority, access, license, updated
FROM "50-dataset/datasets"
SORT priority ASC
```

Notes: [[indicvoices]] · [[kathbath]] · [[fleurs]] · [[mucs]] · [[indic-diarbench]] · [[indic-tts-corpora]]

Also considered: Mozilla Common Voice (CC-0, Indic coverage uneven — fallback), IndicVoices-R (successor, ⚠️ to-verify access). Voice of India: **methodological motivation only** — do not assume its full data is public.

## Selection criteria (per sample, enforced in [[annotation-schema]])

- reference quality known · provenance + license recorded · conditions assignable and honest · languages: ta, hi, te, ml, kn, bho, mai, ur ([[THESIS]] language rationale: confusion set + strong non-Hindi Dravidian + code-mixing playground)
