# Next Research Steps Before Selecting a Build

## 1. Runtime capability capture

Install the latest published packages in a clean demo environment and record:

```text
bgc --version
bgc discover
bgc discover --domain trade
bgc discover --tool order
bgc discover --tool strategy_order
```

For MCP, enumerate the actual tool list under the 3.3.x release.

Goal: reconcile public source vs published runtime.

## 2. Pull published npm package contents

Compare `@bitget-ai/bitget-agent-mcp@3.3.0` and `@bitget-ai/bitget-agent-skill@3.3.1` against GitHub main to locate Agentic Account additions that are not visible in the 3.0.0 GitHub snapshot.

## 3. Inspect safety/risk classification

Map every write/high-risk operation and ask:

- Which writes execute immediately?
- Which destructive actions require confirm?
- Is leverage change ordinary write or high-risk?
- Are strategy orders and fund transfers bounded differently?

This will tell us where a policy governor adds the most value.

## 4. Inspect UTA WebSocket support separately

The Agent SDK inspected here is REST-oriented. Research Bitget's UTA WebSocket APIs and determine the smallest clean adapter needed for event-driven agents.

## 5. Explore current Builder S2 submissions

Bitget advertises 700+ trading agents. We should classify visible builds by:

- generic analyst/trader
- copy trading
- signal aggregation
- portfolio/rebalancing
- risk/security
- scheduling/automation
- multi-agent
- audit/compliance
- developer infrastructure

Goal: find the least crowded gap before choosing a product.

## 6. Candidate architecture test

For each shortlisted idea, write:

- missing primitive
- current workaround
- reusable API
- demo proof
- failure modes
- mergeable contribution path into Bitget-AI

Do not start implementation until this comparison is complete.
