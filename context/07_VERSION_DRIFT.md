# Version Drift and Source-of-Truth Notes

Snapshot: 2026-09-27

## Observed mismatch 1 - package versions

Public GitHub `main` package metadata inspected:

- agent-sdk: 3.0.0
- agent-cli: 3.0.0
- agent-mcp: 3.0.0
- agent-skill: 3.0.0
- bitget-signal: 1.2.0

Public npm/web results observed:

- `@bitget-ai/bitget-agent-mcp`: 3.3.0
- `@bitget-ai/bitget-agent-skill`: 3.3.1

September 3, 2026 Agentic Account instructions require Agentic Skill >= 3.3.0.

Conclusion: published runtime behavior can be ahead of public GitHub `main`.

## Observed mismatch 2 - capability counts

Public docs/README commonly say:

- 89 UTA operations
- 14 curated intent verbs

Checked-in generated SDK source says:

- `CATALOG_OPERATION_COUNT = 109`
- 16 composite intent tool names in `src/tools/composites/index.ts`
- 8 modules in `src/constants.ts`
- 9 agent-facing domains in `src/tools/domains.ts`

Some of the extra surface is hidden/enterprise-oriented (`broker`, `instloan`), which may explain part of the public count difference, but 109 is the literal generated catalog count in public main.

## Rule for future work

Before coding:

1. Run the actual installed package version.
2. Run `discover` and capture the runtime manifest.
3. Compare it with the repository source being used.
4. Treat runtime discover output as authoritative for an installed environment.
5. Avoid hardcoding operation/verb counts from README text.
