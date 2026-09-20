---
type: finding
id: F-007
title: "Bhojpuri is the only language either checkpoint is genuinely uncertain about — Core commits confidently to the wrong answer, Flex hedges and sometimes gets it right"
status: verified
confidence: "high for the qualitative entropy pattern (deterministic from stored topk); the Flex>Core entropy-on-bho comparison itself is directional only (n=10, CI includes zero)"
metric: lid-reliability
updated: 2026-09-20
---

# F-007 — Diagnosing the F-005 Bhojpuri gap: it's confidence, not code

**Question.** [[F-005]] found Flex resolves Bhojpuri auto-LID correctly on
4/10 clips where Core gets 0/10, and ruled out the one code-level asymmetry
found by re-vendoring (Flex's `RECOMMENDED_LANGS` default restriction — `bho`
isn't in the excluded set). This finding investigates the actual mechanism,
using only the LID top-k probability distributions already stored in the
committed EXP-A baseline artifacts (`compute: none`, no new inference).

**Method.** For every EXP-A sample, computed Shannon entropy of the model's
own top-k LID probability distribution (`auto.lid.topk`), for both Core and
Flex, across all 8 languages in the suite.

**Result — a clean, striking pattern.** For **both** checkpoints, mean LID
entropy is ≈0 for every language except the three Hindi-belt languages (bho,
mai-adjacent hi, ur), and by far the largest for bho specifically:

| Language | Core mean entropy | Flex mean entropy |
| --- | ---: | ---: |
| bho | **0.322** | **0.517** |
| hi | 0.001 | 0.014 |
| ur | 0.009 | 0.003 |
| kn / mai / ml / ta / te | 0.000 | 0.000 |

Both models "know" Bhojpuri is genuinely contested — it is the only language
in the suite where either model's own softmax spreads meaningful probability
mass across multiple candidates. Every other language (including the other
belt languages at the audio level, i.e. hi/mai/ur *as spoken*, not as
distractor) is decided with near-total confidence by both models.

**The Core/Flex difference is in what each model does with that uncertainty,
not whether it has it.** Per-sample topk for all 10 bho clips (`code/results/summaries/exp-a-v1-{baseline,flex-baseline}.jsonl`):
- **Core is overconfident in the wrong direction.** E.g. `regional-bho-003`:
  Core assigns `mai` 99.59% probability (essentially certain) — and is wrong.
  Core's bho probability is consistently ≤1.2% across all 10 clips (0.0001–
  0.0118) — bho is barely a candidate at all in Core's output, even though
  its own entropy number shows *some* residual uncertainty (spread between
  hi and mai, not toward bho).
- **Flex genuinely contests bho as the top candidate.** Same clip
  (`regional-bho-003`): Flex gives `mai` 63.4% vs `bho` 33.7% — a real
  three-way-ish contest, not a rounding error. Across all 10 clips Flex's
  `bho` probability ranges 1.3%–98.7%, regularly the #2 candidate by a wide
  margin even when wrong.
- Paired comparison (Flex entropy − Core entropy on the 10 bho clips): mean
  **+0.195 nats**, bootstrap 95% CI **[−0.083, 0.466]** — directionally
  consistent with "Flex is more uncertain about bho," but **not**
  statistically significant at this n=10; do not over-read the point estimate.

**Interpretation.** Core's bho failures are not hedged, uncertain guesses
that happened to land wrong — they are confident, wrong commitments (e.g.
99.6% on `mai`). Flex's bho behavior looks like a genuine, well-posed
three-way acoustic contest (bho/mai/hi) that it sometimes wins. This is
consistent with — though does not prove — a **calibration difference between
the two training runs specifically on the bho class**, rather than an
architectural or restriction-related cause. Two live hypotheses, both
untested here: (a) Flex's LID head saw more or cleaner bho-labeled training
data than Core's; (b) Flex's softmax is generally less sharp near true
class boundaries (would predict Flex should be more uncertain, not
necessarily more *accurate* — the fact that extra entropy correlates with
*better* top-1 accuracy here is the more interesting, harder-to-explain part).

**Status.** `verified` for the entropy pattern itself (deterministic
computation over already-committed data — no new claims about causation).
The causal question — *why* does Flex's softmax commit less confidently and
more often correctly on bho specifically — remains open. Next step to make
progress without new training: compare encoder embeddings for bho clips
across checkpoints (requires loading both models simultaneously, not done
here), or check whether Flex's larger training vocabulary (27 vs 25
languages) changed the LID head's output layer dimensionality/regularization
in a way that would generically soften near-boundary classes — testable by
checking entropy on other close-language pairs neither checkpoint currently
shows confusion on (would need a harder suite than this one, where only bho
shows any contest at all).

**Relation to [[EXP-B]]/C6.** This is a concrete mechanistic instance of why
EXP-B's interpretable reliability features failed to predict errors (AUC
0.515, indistinguishable from chance). `lid_top1_probability`/`lid_margin`
were in that feature set — but Core's confidently-wrong bho errors would
score *high* confidence on exactly those features, the opposite of a
warning sign. A feature set built from top-1 confidence alone cannot flag a
failure mode whose defining trait is high top-1 confidence.

**Card relation.** Neither vendor card documents per-language LID confidence/
entropy, only point-accuracy tables. This suggests a card improvement: report
entropy or a calibration curve for `identify()`, not just top-1 accuracy —
Core's case shows top-1 accuracy alone (0/10) hides that the model isn't
"confused," it's *confidently wrong*, which has different practical
implications (a confidence threshold would not have caught these errors;
Core's own LID probabilities never signaled distress on 9 of 10 bho clips).
