# Product Filter for Bitget S2

Every candidate idea must pass all gates before we build.

## Gate 1 — 30-second clarity
A non-trader should understand:
- who has the problem
- what the product watches
- what decision it makes
- what happens after the decision

Fail examples:
- "multi-agent alpha orchestration framework"
- "AI-powered adaptive market intelligence layer"

Pass style:
- "The agent finds new rToken trading factors, tests them on unseen data, and paper-trades only the ones that survive."

## Gate 2 — Product, not demo
Must have:
- repeatable loop
- persistent state
- user-visible history/results
- recoverable runtime
- real data
- real Bitget integration
- settings/controls
- useful behavior after the judge finishes clicking

A one-button mock flow fails.

## Gate 3 — Bitget-native
Removing Bitget should break the core product, not only remove a logo.

Strong dependencies:
- rToken / US-stock 7x24 market structure
- Bitget Agent Hub execution
- Agentic Account or Demo
- bitget-mcp-server / Bitget stock data
- bitget-signal
- Playbook where useful

## Gate 4 — Track fit
For Agentic Trading:
- LLM materially decides
- event/data -> decision -> execution is visible
- hard risk layer exists
- paper logs exist
- explainability exists

## Gate 5 — Real gap
Reject if a public S2 entry already owns the same 30-second pitch.

## Gate 6 — Evidence plan
Before coding, define:
- success metric
- baseline
- paper-trading metric
- failure condition
- ablation or counterfactual
- what evidence judges can reproduce

## Gate 7 — Buildability
The MVP must be finishable before the current live submission deadline shown in the official form.

## Gate 8 — Useful after hackathon
A trader should have a reason to keep it running.

## Gate 9 — Honest claims
No fabricated PnL, fake live data, silent fallbacks or backfilled "competition" paper logs.

## Gate 10 — Sponsor/chain requirement
Use Bitget AI tools as a load-bearing dependency. The official handbook specifically recommends Agent Hub + Agentic Account for execution and bitget-signal + US-stock MCP for perception in Agentic Trading.
