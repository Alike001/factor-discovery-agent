# Genesis Season 2 Track Primer

Research snapshot: 2026-09-27.

## The simplest distinction

Alpha Factory = build a trading rule and prove with numbers that it has an edge.

Agentic Trading = build a robot trader where the LLM makes trading decisions and the system executes them.

AI Trading Desk = build a research copilot where AI does analysis and a human makes the final trading decision.

## Common S2 setting

Season 2 focuses on AI + US-stock trading, especially rTokens and related contracts that can keep trading outside normal US-equity market hours. A safe layman model is: a crypto-venue instrument linked to US-stock exposure or pricing that can keep moving while the traditional stock market is closed. Exact legal and redemption structure depends on the specific instrument.

## Track 1 — Alpha Factory

Think: quant lab.

The strategy itself is the product. AI can help generate hypotheses, write code, optimize parameters or mine factors, but judges care about whether the strategy works after costs and outside the data used to design it.

Typical shapes:
- arbitrage
- after-hours information pricing
- pairs/correlation trading
- momentum or mean reversion
- factor strategies
- macro/risk-on-risk-off rotation
- execution-aware alpha

Official evidence:
- runnable strategy code
- at least 60 days of backtest data
- at least 30 days out of sample
- Sharpe, Sortino, drawdown, turnover and stability
- pure quantitative scoring

Web3 analogies:
- Hummingbot arbitrage, market making, stat-arb, grid, DCA and TWAP strategies
- CEX/DEX price-arbitrage bots
- factor/signal research systems judged by forward returns

Mental model:
DATA -> RULE -> BACKTEST -> COSTS -> OUT-OF-SAMPLE -> TRADE

## Track 2 — Agentic Trading

Think: robot trader.

The LLM is the primary decision-maker. The system watches data/events, reasons, selects an action, passes hard risk controls and executes.

Typical shapes:
- event-driven agent
- sentiment agent
- earnings agent
- cross-asset execution agent
- factor-discovery agent
- autonomous hedge/rebalance agent

A fixed-rule strategy with an LLM explanation on top is weak fit. The model must materially influence the trade decision.

Official evidence:
- runnable demo
- event -> decision -> execution flow
- paper-trading log from competition period
- two weeks recommended
- 50% quantitative + 50% judge scoring

Web3 analogies:
- Hummingbot Condor-style autonomous trading agents
- Coinbase agentic-wallet systems where an agent can trade or move value under constraints
- treasury/rebalancing/liquidity agents that sense state and act without a human click on each step

Mental model:
EVENT/DATA -> LLM -> RISK GATE -> EXECUTION -> MONITOR -> NEXT DECISION

## Track 3 — AI Trading Desk

Think: AI Bloomberg/Nansen workstation.

The AI retrieves information, summarizes it, compares scenarios, stress-tests a proposed trade and gives the trader an actionable view. The human keeps final authority.

Typical shapes:
- earnings/filing research desk
- natural-language market intelligence terminal
- personalized watchlist/research workspace
- pre-trade stress tester
- portfolio exposure copilot
- post-trade reviewer
- order-splitting/slippage assistant

Official evidence:
- accessible demo
- one complete research flow from question to actionable insight
- pure judge scoring around depth, research quality, data/Skill integration, natural-language UX and thesis

Web3 analogies:
- Nansen-like conversational Smart Money and portfolio research
- on-chain data copilots
- natural-language research terminals and portfolio risk explainers

Mental model:
QUESTION -> DATA/TOOLS -> AI ANALYSIS -> STRESS TEST -> HUMAN DECISION

## Timing note

The official Bitget landing page says submissions closed September 21, 2026. The current GitBook handbook says September 27, 2026 UTC+8. These official sources conflict.

At 2026-09-27 17:39 in Lagos, it is 2026-09-28 00:39 UTC+8, so even the later handbook deadline has technically passed. Verify the actual Google Form/community status before assuming a fresh Season 2 entry is still accepted.
