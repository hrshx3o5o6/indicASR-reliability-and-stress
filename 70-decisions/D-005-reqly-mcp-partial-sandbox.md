---
type: decision
id: D-005
title: "Expose reqly as an opencode MCP server — partial, tool-level sandboxing"
status: accepted
date: 2026-09-19
updated: 2026-09-19
---

# D-005 — Reqly MCP in opencode (partial sandbox)

## Context

Full in-sandbox execution (the agent brain and all its tools inside reqly) is a
larger build. Meanwhile opencode supports local MCP servers, and reqly already
ships a stdio MCP server (`reqly/src/mcp.ts`) exposing `reqly_create_sandbox`,
`reqly_exec`, `reqly_write_file`, `reqly_read_file`, `reqly_list_files`,
`reqly_destroy_sandbox`. It was requested at
`/Users/harsha/Downloads/ventures_hacks_projects_backup/reqly`.

## Decision

Register reqly as a **local MCP server** in the opencode global config
(`~/.config/opencode/opencode.json`):

```json
"reqly": {
  "type": "local",
  "command": ["bash", "-lc", "cd <reqly> && exec ./node_modules/.bin/tsx src/mcp.ts"],
  "environment": { "REQLY_API_URL": "http://localhost:3100", "REQLY_API_KEY": "dev-only-key" },
  "enabled": true
}
```

(`tsx` directly rather than `npm run mcp`, so npm's script banner cannot pollute
the JSON-RPC stdout stream.)

Ralph's `exec: sandbox` tasks should prefer these tools, and run their **receipt**
inside the sandbox so the proof originates there.

## Consequences

- + Usable today: opencode gains real sandbox verbs without a new driver.
- + Receipts can be made to originate in isolation (create → upload → exec → read → destroy).
- + Consistent with [[D-004-sandboxed-thin-clients|D-004]] and
  [[D-003-model-as-service|D-003]] (no weights/secrets in the sandbox).
- − **Partial only.** Built-in `bash`/`edit`/`read` still run on the host; the
  session is not a security boundary. Requires agent discipline.
- − Requires reqly up (`localhost:3100`) with managed/E2B and `E2B_API_KEY`.
- − Config is loaded once at startup: opencode must be **restarted** to pick it up.
- − MCP exec returns text; the 1 MiB output cap and 60-min TTL still apply.

**Upgrade path:** a future pass should route all `exec: sandbox` work (agent + receipt)
through a persistent per-pass sandbox session (`scripts/ralph_sandbox.py --sandbox-id`),
or run the loop itself inside the sandbox. Until then this is explicitly partial.

Related: [[D-004-sandboxed-thin-clients]] · [[D-003-model-as-service]] · [[INFRA-NOTES]]
