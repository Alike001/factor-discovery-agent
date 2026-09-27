# Reverse-Engineering Build Plan, Not Yet a Product Spec

Snapshot: 2026-09-27.

## Architecture patterns to borrow

From Microsoft RD-Agent/Qlib:
- researcher proposes hypotheses
- developer turns hypotheses into executable factor definitions
- experiment engine returns objective feedback
- memory carries failures/successes into next generation
- factor/model optimization is iterative

From quant-agent:
- safe factor DSL / AST validation
- adversarial hypothesis review
- orthogonality/diversity checks
- OOS diagnosis
- factor decay -> re-discovery
- checkpoint/resume

From RotorEdge:
- point-in-time universe
- no-look-ahead test
- fair baselines
- walk-forward/OOS
- realistic costs
- multiple-testing correction
- preserve negative results

From Gridora:
- one clear autonomous loop
- hard guardrails outside the model
- persistent operator product
- verifiable actions, not a slideware agent

From Guarded Alpha:
- separate score from confidence
- portfolio rotation rather than one-way buying
- scheduled unattended runner
- proof ledger and operator console

From Bitget t2-sentiment-agent:
- pre-register run configuration
- source health is logged
- every model decision is grounded against facts
- risk kernel only reduces/refuses exposure
- dry-run before execution
- reconcile with venue truth

## Things to explicitly avoid

- a generic multi-agent debate council
- letting the LLM write arbitrary Python and execute it
- hand-picking only winning factors for the demo
- using present-day fundamentals in historical rows
- optimizing thresholds on the final OOS period
- reporting backfilled paper trading as competition-period logs
- claiming every rToken is executable in Demo without probing it
- a dashboard that stops being useful after one demo click

## 30-second test for a possible final shape

Someone should be able to hear:
"An AI researcher continuously discovers trading factors in Bitget's 24/7 tokenized-stock market. It tests each idea on unseen data, rejects weak or overfit factors, then paper-trades only the survivors and retires them when their edge decays."

They should immediately understand:
- what it watches: Bitget rToken/stock/crypto data
- what AI does: discovers and judges factors
- what code does: validates them
- what happens next: paper trading
- why it stays useful: keeps discovering and retiring factors

This is still a research shape, not the locked product name or final feature set.
