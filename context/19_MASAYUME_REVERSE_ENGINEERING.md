# Masayume Reverse Engineering for Bitget S2

Snapshot: 2026-09-27.

Repository:
https://github.com/Blockchain-Oracle/masayume

## What Masayume actually is

Masayume is a Somnia Shannon testnet product built around DreamDEX Event Contracts. It combines:
- short UP/DOWN price markets
- bounded trading agents
- copy/follow permissions
- X-based trade commands
- games
- strategy publication
- durable operator services

It was prepared for the Somnia Event Contracts hackathon. It is not a Bitget/rToken product and should not be ported directly.

## Why it matters to our Bitget work

The useful overlap is not the market type. The overlap is the architecture between probabilistic AI decisions and financial execution.

Masayume has strong patterns around:
- fresh market context
- model decisions
- deterministic decision gates
- bounded spending permissions
- durable decision persistence
- one-attempt-per-market execution
- ambiguous-send recovery
- settlement/provenance tracking
- honest acceptance evidence

These map well to Bitget Agentic Trading.

## Important source-level patterns

### 1. Fresh context before every AI decision

`packages/markets/src/strategies/agent-context.ts`

The agent reads:
- opening price
- current spot/EMA
- price history
- both sides of the live book
- elapsed/remaining time
- exact stake envelope

The read fails closed on stale/missing data.

Bitget translation:
- rToken candles
- US-stock reference data
- crypto/cross-asset data
- factor-state snapshot
- current account/portfolio
- current paper venue facts

A factor/paper decision should never reuse an old snapshot silently.

### 2. Hash the exact prompt

`packages/brain/src/agent-decide.ts`

Masayume hashes the exact system + user prompt shown to the model and stores the hash with the decision.

Bitget translation:
Every Qwen hypothesis, promotion, retirement and portfolio decision can record:
- exact input snapshot hash
- prompt hash
- model/version
- verdict
- deterministic gate result

This improves reproducibility and judge evidence.

### 3. Reserve before calling the model

`services/ops/src/actors/strategy-runner/agent.ts`

Before a model call, Masayume reserves the strategy/window decision in durable storage. If another process already reserved it, the second process does not call the model.

This prevents:
- duplicate inference
- conflicting simultaneous decisions
- duplicate bills
- two agents acting on the same event independently

Bitget translation:
Reserve a factor experiment / live decision cycle before Qwen runs.

### 4. Store the AI decision before execution

Masayume never hands an unstored model verdict to execution.

Sequence:
reserve decision
-> call model
-> deterministic gate
-> persist decision
-> only then expose an executable candidate

Bitget translation:
Qwen cannot directly send an Agent Hub order. A decision must exist in the ledger first.

### 5. Hold is a valid financial decision

Masayume treats HOLD as a first-class outcome, including when:
- confidence is too low
- data is stale
- the model fails
- limits are hit
- the live quote no longer supports the trade

Bitget translation:
Our factor agent must be rewarded for rejecting factors and staying flat, not forced to generate activity.

### 6. Bounded permission

Masayume grants include:
- total budget
- per-trade cap
- daily spending cap
- max open positions
- price cap
- expiration
- pause/revoke

Bitget translation:
Do not rebuild these as Solidity contracts.
Use:
- Agentic Account fund isolation
- deterministic risk policy
- max portfolio exposure
- per-factor allocation cap
- daily loss budget
- max concurrent positions
- kill switch

Bitget already owns the venue/account layer.

### 7. One durable attempt per market/window

`services/ops/src/actors/strategy-runner/execute.ts`

Before submission it persists an attempt keyed by:
strategy + market + owner.

If an attempt already exists, it does not resend.

Bitget translation:
Use unique execution IDs for:
factor-version + rebalance-cycle + symbol/account.

This is especially important if the process restarts after sending an order.

### 8. Unknown send means reconcile, not retry

Masayume records nonce/block/attempt state. If confirmation is unknown, it does not blindly send again.

`lifecycle.ts` later reconciles:
- receipts
- events
- holdings
- transaction status

Bitget translation:
After an Agent Hub/UTA timeout:
- query order history by client order ID
- query fills/positions
- reconcile
- only send a replacement when absence is proven

Never treat an RPC/API timeout as proof the order failed.

### 9. Restart-safe decision memory

Masayume warms decision state from persistent records after restart so it does not ask the model again for the same Window.

Bitget translation:
Factor-discovery and paper-trading state must survive redeploys:
- hypotheses
- tested formulas
- rejected candidates
- accepted factors
- factor versions
- open positions
- latest rebalance decision
- pending executions

### 10. Evidence ledger

Masayume maintains an acceptance ledger separating:
- implemented behavior
- local tests
- deployed behavior
- actual live/testnet outcomes
- failed or superseded findings

It retains a real losing AI trade rather than presenting only wins.

Bitget translation:
Maintain:
- experiment ledger
- paper-decision ledger
- execution ledger
- failure log
- data-source health
- rejected-factor archive
- forward paper scorecard

This is a strong hackathon practice.

## What NOT to copy into Bitget

Do not port:
- Somnia contracts
- DreamDEX Event Contracts
- UP/DOWN prediction Windows
- X trading
- arcade/games
- on-chain StrategyRegistry
- on-chain EventVault
- custom copy-trading permission contracts
- the whole strategy marketplace
- 20-contract product breadth

Reasons:
1. Bitget Agent Hub already supplies trading/account primitives.
2. Agentic Accounts already isolate agent capital.
3. Our 30-second pitch would become unclear.
4. Factor Discovery is a narrower product and should remain focused.

## Mapping Masayume into our Factor Discovery research shape

Masayume concept -> Bitget equivalent

Market Window
-> factor experiment / rebalance cycle

Agent market context
-> point-in-time rToken + stock + crypto snapshot

Agent spec/persona
-> research mandate + allowed factor DSL + portfolio objective

AI verdict
-> hypothesis / revise / reject / promote / retire / target weights

Prompt hash
-> experiment decision provenance

Decision reservation
-> one research/portfolio decision per cycle

Decision record
-> immutable research ledger

Bounded grant
-> Agentic Account + risk budget

Strategy attempt
-> Agent Hub order attempt with client ID

Receipt reconciliation
-> UTA order/fill/position reconciliation

Settlement
-> realized paper PnL + factor attribution

Strategy history
-> factor lifecycle and decay history

Copy strategy
-> possible future publish/follow feature, not MVP

## What Masayume adds to our current Bitget plan

Before this review, our Factor Discovery loop was:

observe
-> hypothesis
-> test
-> falsify
-> OOS
-> promote
-> paper trade
-> decay
-> retire/evolve

Masayume adds a production reliability spine:

reserve cycle
-> snapshot fresh data
-> hash prompt/input
-> Qwen decides
-> persist verdict
-> deterministic validation
-> reserve execution
-> Agent Hub order
-> reconcile venue truth
-> update paper portfolio
-> preserve evidence
-> resume safely after restart

That turns a research demo into a continuously running financial product.

## Recommended product boundary

For the Bitget hackathon, copy Masayume's reliability philosophy, not its feature count.

MVP should contain:
1. Factor Lab
2. Factor Library
3. Paper Portfolio
4. Decision/Execution Ledger
5. Risk Controls
6. Autonomous scheduler

Future product features can include:
- strategy publishing
- factor marketplace
- copy/follow
- user-created research mandates

Do not put those in v1 unless the core factor loop is already complete.

## 30-second clarity test

Good:
"An AI researcher finds trading factors in Bitget's 24/7 tokenized-stock market, tests them on unseen data, rejects weak ideas, and paper-trades only the survivors. Every AI decision and order is recorded so the system can recover safely and prove what happened."

Bad:
"A multi-agent permissioned strategy registry with durable factor orchestration, copy markets and execution attestations."

## Conclusion

Masayume strongly validates the architecture style we are pursuing:
AI decision-making above deterministic financial controls, durable state, explicit permissions, idempotent execution, recovery and evidence.

It does not invalidate the Factor Discovery direction because Masayume is not a factor-research system. Its agent loop decides trades on short event markets rather than autonomously generating, falsifying and lifecycle-managing factors.

Use Masayume as:
- reliability reference
- productization reference
- permission/risk reference
- judge-evidence reference

Do not use it as:
- direct product idea
- Bitget market model
- reason to add contracts/games/copy trading to the MVP
