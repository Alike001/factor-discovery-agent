# Existing Projects and Crowding Map

## Official stack already covers

- natural-language market queries
- spot/futures order placement
- order amendment/cancellation
- position and leverage management
- account and fund operations
- strategy orders / TP-SL-oriented strategy support
- crypto loans and tax reads
- hidden broker/institutional-loan API surfaces in SDK source
- paper trading
- dry-run
- read-only mode
- high-risk confirmation
- generic market analysis through 5 Signal skills
- Agentic Account OAuth/fund isolation in newer published flow
- US-stock/ETF/fundamental read-only MCP data

## Public community patterns observed in Bitget-AI issues/PRs

### BotIndex MCP integration proposal

Shape:

```text
external market intelligence -> agent -> Bitget execution
```

Signals discussed include funding arbitrage, cross-exchange divergence, launch monitoring, and correlation changes.

Takeaway: generic intelligence aggregation is already an obvious integration pattern and should not be treated as unexplored.

### AlgoVault MCP integration

Shape:

```text
composite verdict (signal/confidence/regime/factors) -> Bitget execution
```

Takeaway: "third-party signal engine + Bitget MCP" is already being built.

### Fly Marketing Agent PR

Shape:

```text
social/content automation + trading signals + Bitget integration
```

Takeaway: lateral AI-agent combinations around marketing/social are also represented.

### Earlier strategy / TP-SL work

Public issues/PRs in early 2026 asked for strategy bot visibility and TP/SL support. The current UTA-oriented docs/source now contain strategy-related operations, so do not assume these old requests are still open capability gaps.

## Official ecosystem direction

Bitget's 2026 messaging evolved from execution to analysis + execution and now to Agentic Accounts and runnable trading systems.

Bitget also advertises a Builder ecosystem with 700+ trading agents, 30+ ecosystem partners, and a 50K USDT reward pool on its current Agent Hub page.

Implication: a generic "AI trading agent" pitch is likely too broad and crowded. Stronger projects should add an infrastructure primitive, a safety/control layer, a new stateful runtime, or a uniquely provable workflow.
