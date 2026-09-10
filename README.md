---
type: moc
updated: 2026-09-10
---

# README — Operating Contract

> **Obsidian is the IDE. The LLM is the programmer and the researcher. The wiki is the codebase.**

This vault runs the **Indic ASR Reliability** project ([[THESIS]]). It is not a filing cabinet — it is a development environment where knowledge is source code, findings are test results, and decisions are git history.

---

## The three-way metaphor

| Layer | Role | Where |
| --- | --- | --- |
| **Obsidian = IDE** | Navigation (graph, backlinks), queries (Dataview = the build/lint system), scaffolding (templates), commit log (daily notes) | everything except `wiki/` |
| **LLM = programmer & researcher** | Designs experiments, writes `code/`, analyzes results, records findings and decisions, keeps the graph honest | works through notes in `10–70` |
| **Wiki = codebase** | Karpathy plugin *compiles* the source notes into `wiki/` entity + concept pages; conversational query = "grep the codebase" | `wiki/` (generated — never edit by hand) |

The loop: **write/edit source notes → Karpathy ingests → wiki rebuilds → query the wiki for cross-cutting answers → new insights go back into source notes.** Source notes are the single source of truth. The wiki is the compiled, linked, queryable artifact.

---

## Directory map

| Folder | Contents |
| --- | --- |
| `HOME.md` | Dashboard — start every session here |
| `README.md` | This contract |
| `00-meta/templates/` | Note templates (`tpl-*`) |
| `10-thesis/` | [[THESIS]] — claims, falsifiable predictions, anti-goals |
| `20-models/` | Model dossiers (verified facts + API surface + open questions) |
| `30-metrics/` | Metric registry — one note per metric, definitions + pitfalls |
| `40-pipeline/` | [[PIPELINE]] architecture, [[roadmap]], `experiments/` |
| `50-dataset/` | [[challenge-suite-spec]], [[annotation-schema]], `datasets/` |
| `60-findings/` | Empirical findings (`F-###`) + [[error-taxonomy]] |
| `70-decisions/` | Decision records (`D-###`), ADR style |
| `90-journal/` | Daily notes (auto-templated) |
| `code/` | Actual implementation — see `code/README.md` |
| `wiki/` | Karpathy-generated knowledge base. **Do not hand-edit.** |

---

## Conventions (the LLM MUST follow these)

### Frontmatter is the type system
Every content note carries YAML frontmatter. Dataview dashboards on [[HOME]] only render notes with correct frontmatter — **no frontmatter, invisible**.

- `type:` `model` · `metric` · `experiment` · `finding` · `decision` · `dataset` · `template` · `thesis` · `pipeline` · `moc`
- `id:` `F-001` / `D-001` / `EXP-A` …
- `status:` experiments → `planned | running | blocked | done | superseded`; findings → `vendor-reported | open | verified | rejected`; decisions → `proposed | accepted | rejected | superseded`
- `updated:` ISO date, bump on every edit

### The working loop
1. Read [[HOME]] and today's daily note first.
2. Never run an unregistered experiment — create it from [[00-meta/templates/tpl-experiment]] in `40-pipeline/experiments/` with `status: planned` before touching `code/`.
3. Every empirical claim becomes a finding note (`F-###`) with evidence and provenance, even (especially) negative results.
4. Every consequential choice becomes a decision record (`D-###`) — context, options, choice, consequences.
5. Update `status:` fields and [[roadmap]] checkboxes as work proceeds. The dashboards must never lie.

### Epistemic rules (non-negotiable, from [[THESIS]])
- Every factual claim is either **sourced** (link + fetch date) or marked **⚠️ to-verify**. Vendor-reported ≠ verified.
- Be critical. If a feature does not correlate with ASR error, delete it from the feature set and record that as a finding.
- If normalization or LLM "correction" improves surface metrics but changes meaning → reject, record.
- No LLM in the reliability loop before the baseline is understood ([[D-001]], [[PIPELINE]]).

### Karpathy wiki
- `watchedFolders` is configured to the content folders (`10-`–`70-`). On note changes the plugin offers ingestion; approve it to rebuild `wiki/`.
- Ask the wiki questions conversationally for cross-cutting lookups ("what do we know about LID calibration?").
- `wiki/` pages are *derived artifacts*. Fix knowledge at the source, re-ingest.

### Dataview
- Dashboards live on [[HOME]] and [[METRICS]] / [[DATASETS]]. Plain DQL, frontmatter-driven.
- When adding a new note type, extend the dashboards in the same edit.

### Templates
Core **Templates** plugin points at `00-meta/templates/`. New experiment / finding / decision / daily note → start from the template, always.

### Hygiene
- Audio, checkpoints, and large artifacts never enter the repo (see `.gitignore`); results JSONs and plots do.
- Wikilinks over plain text. One idea per note. Link liberally — the graph and the wiki are only as good as the link density.
