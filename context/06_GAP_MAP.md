# Gap Map - Underbuilt Product and Infrastructure Hypotheses

These are hypotheses based on public source + docs, not claims about Bitget's private/internal roadmap.

## Gap A - Stateful Policy Governor

### Missing primitive

A reusable pre-execution policy engine that sits between model intent and `agent-sdk` execution.

### Why current controls are insufficient

Current safety is mostly operation-scoped:

- read-only blocks all writes
- dry-run previews one request
- `high` risk asks for confirm
- Agentic Account limits the total fund pool

These do not express policy such as:

```text
BTC leverage <= 3x
no new positions after daily loss > 2%
ETH position <= 20% of NAV
only BTCUSDT and ETHUSDT
always attach stop loss before opening leveraged position
one strategy may spend <= 500 USDT/day
```

### Reusable artifact shape

- TypeScript middleware package around `safeInvoke`
- policy JSON/DSL
- decision result: allow / deny / require approval / mutate-with-bounds
- deterministic policy receipt
- optional MCP verb such as `preflight_trade`

## Gap B - Durable Watch/Trigger Runtime

### Missing primitive

A restart-safe condition engine for long-lived tasks.

Example:

```text
Until market close:
  watch BTC price + sentiment + news
  if all predicates become true:
      construct exact order plan
      policy-check
      execute once
```

### Why useful

The public product page advertises continuous monitoring examples, yet the inspected Agent Hub SDK is a REST tool layer. Public repo searches did not reveal a durable scheduler/WebSocket runtime.

### Reusable artifact shape

- persisted watch definitions
- WebSocket + REST fallback
- de-duplication/idempotency key
- restart recovery
- one-shot/recurring trigger semantics
- execution handoff to SDK

## Gap C - Workflow Plan / Preflight / Receipt

### Missing primitive

Move safety from single tool calls to multi-step execution plans.

Example:

```json
{
  "steps": [
    {"op":"setLeverage", "symbol":"BTCUSDT", "leverage":"3"},
    {"op":"placeOrder", "side":"buy", "qty":"..."},
    {"op":"placeStrategyOrder", "stopLoss":"..."}
  ],
  "invariants": [
    "positionNotional <= 500",
    "stopLossPresent == true"
  ]
}
```

Then:

```text
compile -> validate -> simulate -> approve -> execute -> verify -> receipt
```

### Reusable artifact shape

- plan schema
- static validator
- dry-run aggregation
- policy integration
- exact execution trace
- recovery plan if step N fails

## Gap D - Multi-Agent Portfolio Desk

### Missing primitive

Multiple specialized agents with explicit roles and shared bounded state.

Possible roles:

- researcher
- strategy proposer
- risk reviewer
- execution agent
- post-trade reviewer

### Needed primitives

- shared state store
- role permissions
- approval quorum
- policy inheritance
- conflict resolution
- per-agent subaccount/budget mapping

## Gap E - Signal Evaluation / Shadow Trading

### Missing primitive

A bridge from analysis to measurable strategy quality.

Pipeline:

```text
Signal output
 -> normalized thesis
 -> deterministic rule
 -> backtest/replay
 -> paper shadow mode
 -> live comparison
 -> drift/confidence report
```

This is more defensible than another analyst UI because Signal already supplies core research data.

## Gap F - Public-SDK Version / Capability Inspector

Smaller but mergeable infrastructure idea:

- runtime detects package versions
- compares SDK catalog vs docs/skill assumptions
- warns when a skill expects unavailable tools
- exports a capability manifest

This is motivated by real version drift observed during this research: GitHub main 3.0.0 metadata vs npm MCP/Skill 3.3.x, and 89/14 documentation claims vs a 109-operation/16-composite generated catalog on main.
