# Agentic Trading Reverse Engineering — Bitget S2

Snapshot: 2026-09-27.

## Official track contract

Agentic Trading requires the LLM to be the primary trading decision-maker. The product must sense the environment, make independent judgments, execute with risk controls, provide a runnable demo, show event -> decision -> execution, and keep paper-trading logs.

The five named themes are Event-Driven, Market Sentiment, Earnings-Driven, Cross-Asset Execution, and Factor Discovery, plus Open Theme.

## Public S2 competitors inspected

### Triad — Cross-Asset Execution Agent
30-second pitch: autonomous Apple-rToken/BTC spread trader.

Core:
- three signals: price divergence, event, sentiment
- LLM decision
- deterministic risk cage
- Bitget Agent Hub paper execution
- persistent position/risk state
- append-only decision log
- backtest + walk-forward harness

Weakness/opening:
- the rToken basket often acts as a signal while BTC is the fill leg
- limited true joint-portfolio optimization
- cross-asset relation is mostly a hand-defined divergence rule
- backtest trade count is thin

### Crossfire — Cross-Asset Execution Agent
30-second pitch: always-on dual-book agent for US-stock contracts and crypto perps.

Core:
- 5-minute heartbeat + event wakes
- LLM/policy decision
- Risk Cage
- shared book and paper sleeve
- append-only JSONL
- scorecard UI

Weakness/opening:
- much of the cross-asset logic is Mag7-vs-BTC divergence
- public/default mode can be signal-only
- portfolio objective is less explicit than the risk limits

### Gloaming — Agentic Trading + Desk
30-second pitch: trades the hours the US stock market cannot.

Core:
- fair-value model from native-share close + live proxies
- Qwen decisions every 15 minutes while NYSE is closed
- deterministic risk layer
- public, committed paper history
- GitHub Actions unattended runtime
- research desk on same data

Weakness/opening:
- highly focused on overnight fair-value/spread behavior
- fixed proxy blend rather than autonomous factor research
- each decision is mostly a signal-to-trade loop, not a research-to-factor lifecycle

### t2-sentiment-agent — Market Sentiment Agent
30-second pitch: Qwen turns live crowd positioning/news into a target book, then a reduce-only risk kernel and Agent Hub execute.

Core:
- event triggers
- Qwen target-book decision
- schema/grounding checks
- deterministic risk kernel that can only shrink/refuse
- dry-run then Demo execution through bgc
- reconciliation against venue truth
- hash-chained log
- published run metrics

This is a strong reference for evidence discipline and sponsor-stack integration.

### Chronos-Nexus — Event-Driven
30-second pitch: ORACLE reads news, SENTINEL vetoes unsafe setups, CHAIRMAN executes on Bitget Demo.

Core:
- RSS/event sensing
- Qwen thesis
- TA/risk veto
- Demo execution
- persistent logs
- Telegram console

This confirms event-driven + risk-veto is crowded.

## Competition density

### Event-Driven
Crowded. Many projects already do news/event -> LLM -> risk -> execution.

### Market Sentiment
Crowded. t2-sentiment-agent is already unusually rigorous.

### Earnings-Driven
Crowded enough that a basic earnings reader/trader is weak.

### Cross-Asset Execution
Moderately crowded. Triad, Crossfire, VIGIL and Gloaming already overlap. A new entry needs a genuinely portfolio-level or execution-level problem, not just "rToken + BTC."

### Factor Discovery
Publicly less crowded in S2. Mature open-source work exists outside Bitget, which gives strong patterns to adapt without copying a Bitget entry.

### Open Theme
Useful only if the product's trading output and LLM decision role are obvious.

## Best research wedge after this pass

Factor Discovery remains the clearest under-explored named Bitget theme.

A strong product in this theme should not be "LLM invents indicators." It should own an end-to-end lifecycle:

market anomaly -> hypothesis -> factor implementation -> leakage check -> cost-aware test -> out-of-sample falsification -> portfolio fit -> paper deployment -> decay monitor -> retire/evolve

The LLM owns hypothesis selection and promotion/retirement decisions. Deterministic code owns the math, anti-leakage checks, risk limits and execution constraints.
