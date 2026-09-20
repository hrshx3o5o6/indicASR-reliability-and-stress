---
type: moc
updated: 2026-09-17
---

# Plain-English project summary

> No-jargon version of [[HOME]] and [[EXPERIMENT-OBSERVATIONS]]. If a term appears in **bold**, it's defined where first used. The technical versions of everything here live in the linked notes.

## The project in one sentence

Someone released a very good speech-to-text AI for Indian languages ([[indic-transcribe-core]]). Instead of building a competing model, we're building the **quality inspector** that sits on top of it: figuring out *when* its transcriptions can be trusted, *why* they fail, and *how* to fix or format them without changing their meaning. They built the factory; we're building the quality-control department.

**Jargon used below — WER (word error rate):** if a sentence has 10 words and the model gets 2 wrong, WER is 20%. Lower is better. **LID (language identification):** the model's guess about which language is being spoken. **Oracle:** a cheating test where we hand the system the correct answer it's supposed to find, to see the best possible result.

## What we've done so far (5 experiments)

### EXP-A — How good is it really?

80 short audio clips across 8 languages: some clean, some made noisier, some squashed to sound like a phone call.

- On our clips, roughly **1 in 5 words is wrong** (22% average), swinging wildly by language — Hindi ~14%, Malayalam ~34%.
- Surprise: noise and phone-quality barely made things worse. **The language matters more than the audio quality.**
- Headline finding: the model guesses **Bhojpuri wrong 10 times out of 10** — it thinks Bhojpuri speakers are speaking Hindi. ([[F-001]])

### EXP-B — Can we predict when it's wrong?

We collected 15 side-clues (the model's own confidence, audio quality, clip length, …) and tried to build a small predictor: "this transcript is probably fine" vs "probably broken."

- The clues are **barely better than a coin flip**. So our safety switch currently refuses to approve *anything* — honest, but useless.
- This is an open problem, not a failure: we proved the obvious clues don't work, which tells us where *not* to look next.

### EXP-C — The language-guessing problem (expanded)

**The setup.** Before the model writes words down, it has to decide what language it's hearing. The vendor's own card admits this decision is unreliable for the Hindi-belt languages (Bhojpuri, Maithili, Urdu get absorbed by Hindi). Our EXP-A result agreed — Bhojpuri 0/10.

**The idea.** Instead of accepting the model's first guess, ask it: *"what are your three best candidates?"* Then transcribe the audio three times — once pretending it's each candidate language — and pick whichever transcript scores best.

**What we found, in three parts:**

1. **The right language is almost always on the shortlist.** In 79 of 80 samples, the true language appeared in the model's top-3. This is genuinely good news: Core's *hearing* is informative. When it's confused, it at least hedges with the correct answer on the list. The problem isn't listening — it's *deciding*.

2. **A perfect decider would pay off.** In the oracle test we forced the correct language for every clip and WER improved from 24.87% to 22.38%. That ~2.5-point gap is real headroom sitting on the table: the top-3 strategy contains better answers than the model's default choice produces.

3. **Our decider failed.** We scored each of the three candidate transcripts with the only tool we had: the model's own confidence in what it just wrote. Result: it picked Hindi essentially every time — Bhojpuri selected 0/10 — and overall WER got marginally *worse* (25.00% vs 24.87%).

**Why the decider failed (the important insight).** The scoring was circular. The model is more confident in its Hindi transcript partly *because* it believes the audio is Hindi — that belief is exactly the bias we were trying to correct. We asked a biased judge to referee its own bias, and it agreed with itself. The Bhojpuri hypothesis loses points for the crime of being Bhojpuri.

**Analogy.** A witness who can correctly list the three most likely suspects but always picks the famous one when asked to decide. The lineup is right; the choosing is wrong.

**Verdict.** The idea is alive, the current picker is dead. Next attempt needs a judge with *independent* evidence: does this transcript look like valid text in its claimed language? Is the script consistent? Do the numbers and names check out? — anything except "how confident does the model feel." (Technical detail in [[EXP-C]].)

### EXP-D — Is the auto-formatting mode safe?

The sibling model (Flex) has a **"mixed mode"**: it converts spoken numbers into digits and English words into Latin script — "five thousand rupees" becomes "₹5000". Sounds great.

- Result: it looks nicer but **destroys important values**. In our tests it got currency amounts right **0% of the time** (normal mode: 100%) and mangled names — including changing ₹19,500 into ₹1950, a tenfold error.
- One caveat on our own measurement: the 0% is not the scorer being picky about format — it happily accepts digit forms when the *value* is right (it credited mixed mode on 77% of plain numbers). The currency failures are genuinely wrong values.
- Verdict: **don't use it.** Pretty formatting isn't worth wrong numbers. ([[F-004]])

**Is this different from what the vendor claimed at release?** Close reading says: **no contradiction — but a big gap in emphasis.**

- The vendor's *launch messaging* (Aug 2026 posts, press coverage) sold mixed mode as a headline feature: three output modes, "your choice", "match the output to what your product expects". No public caveat about errors in the promotion.
- The vendor's *model card* (the fine print, under Limitations) already said: mixed-script mode "will occasionally get it wrong" and recommends native mode for production. We can't verify whether that caveat was present on release day — the card was last touched 2026-09-15 — but it's there now.
- So our finding doesn't contradict the vendor's own documented position — **it quantifies it**. "Occasionally wrong" turned out to mean "every currency amount in our slice." The vendor under-advertised the caveat, and we put a number on it.
- Best part for us: the card's advice — *"apply your own ITN downstream if you need it"* — is literally this project. We're building the layer they tell people to build, with the metrics to prove when the built-in one is unsafe.

### EXP-E — Does it work on conversations?

Real conversations have multiple people talking. We took 4 real multi-person recordings and tried: dumping the whole thing in, handing it perfect speaker boundaries (oracle), and auto-detecting speakers.

- **Everything failed** — near 100% word error *even with perfect boundaries*. On short conversational snippets the model outputs almost nothing.
- The vendor's own advice ("just add a speaker-splitter") is **not enough** — the model itself can't handle short turns. ([[F-003]])

## The model-card check

Vendors publish a **model card** — a spec sheet with benchmark scores and admitted weaknesses. We fetched the latest cards (they quietly updated them on Sep 15, after we started), compared every claim against our measurements, and recorded the results.

**What we can now claim:**

1. **"We independently confirmed the maker's own admission."** They say Hindi-belt languages get absorbed; we measured Bhojpuri 0/10.
2. **"The maker's multi-speaker recipe is incomplete."** Tested with perfect speaker splitting — still fails; short turns are the missing piece.
3. **"The auto-formatting mode is dangerous for critical values."** 0% currency accuracy; "occasionally" understates it.
4. **"Their published score doesn't transfer to harder conditions."** ⚠️ Careful: we can *not* claim their number is wrong — different dataset, different scoring method. Only: *it doesn't carry over to our slice.*

**What we canNOT claim:**

- "The model is bad" — our sample is tiny (80 clips, 4 conversations); results are directional, not a verdict.
- "Their noise-robustness claim is false" — we only made mild *fake* noise; real noise is untested (→ [[EXP-F-real-noise|EXP-F]]).
- Anything about Hinglish/code-mixing — their claim is untested by us; that's the biggest open item.

## Where this leaves us

The project has a legitimate, evidence-backed story already: *"SOTA models come with fine print. We measure the fine print, then build the trust layer."*

Next steps in plain English:

1. **Fix conversations** — give short clips more context, add a proper speaker-detection tool, rerun.
2. **Test real noise** — actual market/call-center audio ([[EXP-F-real-noise|EXP-F]]), since our fake noise was too gentle.
3. **Test Hinglish** — the biggest untested claim on the card.
4. **Re-download the vendor's code** — they changed it on Sep 15; our local copy is older.

## Related

[[HOME]] · [[THESIS]] · [[EXPERIMENT-OBSERVATIONS]] (technical source of truth) · [[roadmap]]
