# External Open-Source and Winning-Project Patterns

Snapshot: 2026-09-27.

## BNB Hack AI Trading Agent winners

Official result reporting lists Guarded Alpha and Gridora among Autonomous Trading Agent winners, and RotorEdge among Strategy Skills winners.

### Gridora — 3rd place
Core product:
- adaptive grid trader
- Claude routes/tunes strategy
- hard deterministic guardrails
- local/non-custodial signing through Trust Wallet Agent Kit
- config committed onchain before trading
- outcomes and trades journaled onchain
- public read-only verifier

What to extract:
- one strategy, deeply productized
- a simple 30-second explanation
- precommit -> execute -> attest makes behavior verifiable
- model decides inside hard limits
- fallback keeps system alive

What to remove:
- grid-specific math
- BNB/Trust Wallet/onchain-attestation specifics unless they solve a Bitget need

### Guarded Alpha — winning Autonomous Trading Agent
Core product:
- score a constrained market universe
- Scout -> Quant -> Risk -> Executor -> Reviewer
- deterministic risk governor
- scheduled scanner
- portfolio rotations
- proof ledger
- operator console
- real BSC execution

What to extract:
- score is separate from confidence
- portfolio rotation instead of only buy/sell
- explicit mandate
- real execution + audit record
- "hold" and route failures are first-class states

What to remove:
- CoinMarketCap/BNB-chain-specific routing
- generic seven-voter scoring if it does not map to rTokens

### RotorEdge — winning Strategy Skill
Core product:
- cross-sectional momentum rotation
- point-in-time universe
- walk-forward out-of-sample validation
- costs and capacity
- survivorship-bias control
- ablations
- documented negative results
- deterministic reproduction

What to extract:
- evidence > marketing
- a fair benchmark
- no-look-ahead guarantees
- preserve negative results
- factor/strategy must survive costs and OOS

What to remove:
- BNB-token universe
- long-only altcoin assumptions

## Microsoft RD-Agent + Qlib

RD-Agent(Q) automates factor/model R&D:
hypothesis -> implementation -> experiment -> feedback -> next hypothesis.

Key patterns:
- separate proposer from developer/evaluator
- experiment feedback becomes memory for the next research cycle
- factor and model co-optimization
- session/checkpoint continuation
- Qlib provides the quantitative experiment substrate

Bitget mapping:
- replace Qlib equity universe with Bitget rToken + US-stock + crypto data
- constrain factor DSL to data available point-in-time
- use Qwen for hypothesis/research decisions
- use deterministic backtester for validation
- use Agent Hub paper execution only after a factor clears promotion rules

## quant-agent

Open-source factor factory pattern:
- LLM hypothesis generation
- adversarial review
- safe factor DSL / AST sandbox
- IC and OOS evaluation
- orthogonality/diversity checks
- composite-factor optimization
- decay monitoring
- feedback into the next discovery generation
- paper/live broker layer

This is very close to Bitget's Factor Discovery theme conceptually. The opportunity is productizing a much smaller, rToken-specific version rather than rebuilding a hedge-fund platform.

## TradingAgents

Multi-agent trading framework:
fundamentals + sentiment + news + technical -> bull/bear debate -> trader -> risk manager.

Lesson:
multi-agent role separation is now commodity. Do not use "many agents debate" as the product's novelty.

Useful patterns:
- structured roles
- checkpoint resume
- persistent decision log
- portfolio-aware runs
- point-in-time integrity

## Hummingbot Condor

Open-source harness connecting LLM decisions to deterministic trading across many exchanges.

Lesson:
"LLM connected to an exchange" is infrastructure, not enough product differentiation.

Useful patterns:
- deterministic execution below probabilistic reasoning
- deploy/manage autonomous agents
- shared accounts / fleets
- natural-language control

## Alpaca hackathon submissions

Strong examples include:
- Yield-paca: Temporal-based durable parent/child workflows, idempotent triggers, persistent plans/orders/fills
- SPECIES: evolutionary strategy population, validate survivors, promote to paper trading
- KIBA 0DTE: narrow strategy, aggressive measurable paper performance, code-enforced max loss

Reusable lesson:
winning/strong trading projects tend to own one measurable loop and make the evidence visible.
