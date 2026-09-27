# Bitget-AI Organization Repository Map

Snapshot: 2026-09-27

Public repos confirmed during this research pass:

| Repo | Role | Key relationship |
|---|---|---|
| `Bitget-AI/agent_hub` | Ecosystem entrypoint and installer | Points users to the rest of the stack |
| `Bitget-AI/agent-sdk` | Foundation TypeScript SDK | CLI and MCP depend on it |
| `Bitget-AI/agent-cli` | `bgc` terminal interface | Depends on SDK |
| `Bitget-AI/agent-mcp` | MCP stdio adapter | Depends on SDK + MCP SDK |
| `Bitget-AI/agent-skill` | Trading instruction/skill package | Teaches terminal agents to use `bgc` |
| `Bitget-AI/bitget-signal` | Market-analysis skill bundle | Independent public data MCP path |

## agent_hub

Main responsibilities:

- ecosystem documentation
- install/upgrade/rollback meta-tool
- package discovery
- cross-repo onboarding

Do not treat it as the deepest source of current trading behavior. Execution logic moved into `agent-sdk` and the thin surfaces around it.

## agent-sdk

Most important repo for reverse engineering.

Key source areas:

- `openapi.yaml` - source API specification
- `scripts/generate-catalog.mjs` - catalog generation
- `src/generated/catalog.ts` - generated operation catalog
- `src/constants.ts` - modules and hidden-module policy
- `src/tools/build.ts` - tool surface assembly
- `src/tools/composites/` - intent verbs
- `src/tools/discover.ts` - progressive capability discovery
- `src/tools/raw.ts` - long-tail operation escape hatch
- `src/tools/safety.ts` - shared dry-run/read-only/confirm gate
- `src/tools/risk.ts` - operation risk classification
- `src/client/` - REST client/signing/rate-limit implementation
- `src/testing/` - mock/test utilities

The SDK is spec-driven, and the generated catalog is the closest thing to a capability source of truth in public GitHub.

## agent-cli

Thin terminal-native execution surface.

Design themes:

- JSON-friendly stdout/stderr
- progressive `discover`
- intent verbs instead of hundreds of commands
- deterministic flags rather than interactive safety prompts
- intended for Codex CLI, Claude Code, OpenClaw and other shell agents

## agent-mcp

Thin MCP adapter over the SDK.

Important caveat: published npm MCP has moved to 3.3.0 while GitHub `main` package metadata inspected here remains 3.0.0. Agentic/OAuth behavior is documented outside this older main snapshot.

## agent-skill

Markdown/instruction layer that teaches the model:

- when to call Bitget tools
- how to discover parameters
- how to confirm writes
- how to recover from errors

Published npm Skill is newer than the public `main` package metadata inspected here.

## bitget-signal

Five current analysis skills:

- macro-analyst
- market-intel
- sentiment-analyst
- technical-analysis
- news-briefing

Roadmap/public README also points to Bitget-exclusive signals:

- top-trader-flow
- derivatives-structure
- large-flow-detect

This makes generic "market intelligence" less open than it was early in 2026.
