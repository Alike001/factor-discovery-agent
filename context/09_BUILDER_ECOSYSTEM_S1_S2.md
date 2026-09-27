# Bitget Builder Ecosystem Scan — S1 and S2

Research snapshot: 2026-09-27.

This is a competition-density map, not a complete census. Private projects, renamed repos, and submissions without searchable hackathon wording can be missing.

## Season 1 pattern

Bitget says S1 received 700+ AI-agent submissions. Its own Season 2 page highlights four recurring directions from S1: 24-hour tokenized-stock trading, trading safety/risk validation, LLMs as analysts rather than fortune tellers, and multi-agent systems with explicit responsibilities.

Representative public projects:

| Project | Product shape | Original gap overlap |
|---|---|---|
| BitgetBench | Leak-aware backtesting, paper sandbox, guardrails, hash-chained journal, public leaderboard | A, C, E |
| VEIL | Pre-execution verification, approve/block verdict, adversarial risk checks, audit trail | A, C, E |
| TradeAgent Flight Recorder | Strategy compiler, paper simulation, run monitor, risk scoring, audit record | A, C, E |
| AgentBus | Typed Redis pub/sub between signal, classifier and executor agents | D |
| Trading Council | Five specialist personas plus deterministic risk arbiter | A, D |
| Vector | Four signal channels, LLM reconciliation, risk guards, paper execution and journal | A, D, E |
| Glass Box | Post-trade signal attribution, confidence calibration and self-deception analysis | E |
| Adaptive Regime Switch | Regime classification, risk sizing, walk-forward tests and scheduled paper loop | A, B, E |
| SmartFlow AI | WebSocket whale monitor, AI interpretation, scheduler and Bitget execution | B |
| TradeMind AI | News + exchange data → LLM → risk-managed execution | A |
| BackTestBench | Strategy backtesting and AI diagnostics | E |

## Revised six-gap map

A. Stateful Policy Governor — crowded as a broad idea.
Simple max-loss, leverage, position-size, stop-loss, veto and kill-switch systems are common. A new project needs a narrower stateful policy problem.

B. Durable Watch / Trigger Runtime — partially covered.
Apps have cron, polling and WebSocket loops. Less visible is a reusable event runtime with persisted watches, deduplication, restart recovery, idempotent execution and explicit Agent Hub handoff.

C. Workflow Plan / Preflight / Receipt — crowded in generic safety.
Preflight, audit logs, replay and evidence capture already exist. Generic review-before-execute is weak differentiation.

D. Multi-Agent Portfolio Desk — crowded at council/message level.
AgentBus and Trading Council cover communication and role separation. Durable shared portfolio state, permissions, budgets and conflict resolution across agents remain less common.

E. Signal Evaluation / Shadow Trading — very crowded.
BitgetBench, BackTestBench, Glass Box and many agents cover backtesting, paper trading and evaluation.

F. SDK Version / Capability Inspector — niche, but weak S2 fit.
Useful tooling, but less directly tied to the trading outcome expected by Season 2.

## Public Season 2 scan

| Project | Track / theme | Product shape |
|---|---|---|
| MyDesk | AI Trading Desk | Human thesis → AI structured conditions → deterministic later verdict |
| Decis Analysis | AI Trading Desk | Earnings research, bull/bear/invalidation stress test, human final call |
| AfterHoursDesk | AI Trading Desk | Overnight US-equity/rToken research desk for Asia/EU users |
| Egress | AI Trading Desk / Execution Assistance | Estimates cost of exiting tokenized-stock positions at a chosen size |
| Weekend Desk | Alpha Factory / After-hours pricing | Tests weekend SPY-perp repricing as a predictor of the native-equity open |
| Veto | Agentic Trading / Earnings | Multi-pass LLM + deterministic signal + consensus + risk gate + paper execution |
| Divergent Agent Desk | Agentic Trading | Continuous signal → LLM/rules → risk gate → Bitget Demo UTA |
| VIGIL | Agentic Trading | rToken/crypto autonomous loop, portfolio limits, demo execution and signed decisions |

Public exact-phrase GitHub searches also surfaced several after-hours-pricing entries, an arbitrage project, a cross-market-correlation project and a cross-asset-execution project. This is only a visibility signal, not a complete count.

## Broad pitches to avoid

- AI trading agent with stop loss and risk limits
- AI safety layer for trading agents
- multi-agent council that votes on trades
- generic AI-agent backtester
- generic decision audit log
- news/sentiment bot that buys or sells
- generic personalized trading dashboard
- earnings agent with LLM + basic risk gate

## Areas that deserve deeper research

- persistent event execution where recovery/idempotency materially matter
- cross-asset state management rather than independent one-shot trades
- portfolio-aware decisions that change because of existing exposures
- factor discovery with mandatory falsification before deployment
- rToken execution-quality problems specific to 7×24 market structure
- measurable evidence for why an autonomous agent chose not to trade

## Sources

Official:
- https://www.bitget.com/activity-hub/hackathon
- https://bitget-ai.gitbook.io/bitgetai_hackathons2
- https://github.com/Bitget-AI/agent_hub
- https://github.com/Bitget-AI

Representative repos:
- https://github.com/OoJae/bitgetbench
- https://github.com/0xkinno/veil
- https://github.com/onehopeA10/tradeagent-flight-recorder
- https://github.com/Peesounds9/Agentbus
- https://github.com/cryptoduke01/vector
- https://github.com/captainebru84-sudo/bitget-trading-council
- https://github.com/NomadDigita/AutonomousSmartMoneyTracker
- https://github.com/lijianyuan10/MyDesk-for-Bitget-Hackathon-S2
- https://github.com/Mhiah/decis-analysis
- https://github.com/cryptorishu4436/AfterHoursDesk
- https://github.com/Ritapossible/Egress
- https://github.com/samixrd/weekend-desk
- https://github.com/GODGRACE07/veto
- https://github.com/scanner72/bitget-bot
