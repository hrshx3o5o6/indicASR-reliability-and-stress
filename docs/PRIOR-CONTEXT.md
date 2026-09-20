# PRIOR-CONTEXT — continuity digest

> Distilled so a stateless agent (or a returning human) can continue without replaying
> `freebuff-chat-transcript.json`. Source: the 2026-09-10/11 freebuff session plus the
> vault state through 2026-09-19.

## What the freebuff session established (2026-09-10/11)

- Built the vault and the operating contract (`README.md`): "Obsidian is the IDE, the
  LLM is the programmer, the wiki is the codebase."
- Fetched the real vendor model cards and wrote the dossiers. Key intel: `return_lid`
  returns ranked top-k; `allowed_langs` is a hard filter that reassigns; 45 s cap.
- Verified HF access (both models gated), then vendored + audited Core code at
  `4d29eeb7a099`, producing [[F-002-vendor-lid-internals]]: `hne` is the biggest LID
  sink (not Hindi), hi/ur declared inseparable, no useful default confidence threshold.
- Started the ~4.6 GB Core weight download; it stalled at ~53% on flaky DNS/CDN and
  was the last recorded action of that session. **Superseded:** the model later
  downloaded, loaded, and every experiment (A–E) ran on 09-14…09-17.

## What happened after (state as of 2026-09-19)

- EXP-A…E complete; findings [[F-001-hindi-belt-lid-absorption|F-001]],
  [[F-003-oracle-turns-fail-diarbench|F-003]], [[F-004-flex-mixed-critical-values|F-004]].
- `REPORT.md` (claim ledger C1–C6) and `docs/REPRODUCE.md` written.
- Freebuff is **not** a pending thread; it is context. The real open items are the
  roadmap tail: publication hardening, the sandboxed Ralph loop, and EXP-F.

## Decisions currently in force

- [[D-001-layer-not-model|D-001]] trust layer, not a model.
- [[D-002-core-as-baseline|D-002]] Core is the baseline; Flex is an instrument.
- [[D-003-model-as-service|D-003]] Core/Flex served as a pinned HTTP service.
- [[D-004-sandboxed-thin-clients|D-004]] reqly/E2B sandboxes agent code; tasks route
  `compute: none | model`.

## How to resume

1. Read `RALPH.md`, `.ralph/state.json`, `.ralph/tasks.json`.
2. `scripts/ralph.sh` runs one task per fresh pass; receipts decide success.
3. Blockers and their statuses live in [[INFRA-NOTES]] (P-1…P-16).
