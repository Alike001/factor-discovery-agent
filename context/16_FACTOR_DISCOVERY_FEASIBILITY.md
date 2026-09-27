# Factor Discovery Feasibility on Bitget

Snapshot: 2026-09-27.

## Why this theme is technically feasible

Bitget's current Reality/rToken API gives enough building blocks for an autonomous factor-research product:

- rToken instruments, tickers and candlesticks through UTA market APIs.
- Historical candlesticks can be queried for periods older than 90 days, while each individual query window is capped at 90 days.
- rToken candle intervals support 1m, 5m, 15m, 1H, 4H and 1D.
- rToken volume/turnover before 2026-07-09 may be empty, so volume-based historical factors need a shorter honest start date or a fallback source.
- Public stock-reference endpoints identify the underlying stock and market session state.
- Bitget Reality basic-data endpoints expose company overview, valuation ratios, earnings forecasts, dividends, insider trades, executive holdings and major shareholders.
- rToken order-book depth and recent platform fills may require special access/whitelisting, so v1 should not make those mandatory.
- The Reality trading API supports rToken market/limit order placement, but Demo availability for every rToken must be verified separately at runtime.

## Data families a factor agent can work with

### rToken market-structure factors
- overnight / weekend return
- distance from rolling fair-value anchors
- volatility compression/expansion
- spread between rToken and stock-future proxy
- volume/turnover factors after 2026-07-09
- session-specific momentum or mean reversion
- weekend-vs-weekday behavior

### Underlying-stock factors
- valuation: P/E, P/B, P/S, EV/EBITDA, dividend yield
- earnings forecast revisions / expectation gaps
- 52-week location
- insider activity
- executive / major shareholder changes
- dividend and split events

### Cross-asset factors
- rToken return relative to BTC/ETH/Nasdaq proxy
- sector-stock vs crypto beta changes
- risk-on/risk-off rotation
- stock-future vs spot-rToken divergence

### Event/session factors
- pre-market / regular / after-hours / overnight
- market closure and holiday flags
- earnings / macro windows
- post-close information absorption

## Critical data caveats

1. Never pretend unavailable historical fields exist.
2. Keep raw source timestamps and point-in-time snapshots.
3. Current valuation/fundamental endpoint values are not automatically historical point-in-time series. A factor that backtests them needs archived snapshots or another genuinely historical source.
4. Volume/turnover before 2026-07-09 may be blank and should stay blank.
5. Stock splits and other corporate actions need adjusted-price handling or explicit exclusion.
6. Reality orderbook/fill endpoints can be access-limited, so orderbook factors are optional until access is confirmed.
7. Paper/Demo support must be probed per actual symbol before promising venue fills.

## Why this can be Agentic Trading rather than Alpha Factory

The product should make the LLM the research and promotion decision-maker:
- choose what market anomaly to investigate
- formulate a factor hypothesis
- select transformations and controls from an allowed DSL
- interpret validation failures
- decide whether to revise, retire or promote the factor
- decide which validated factor or factor basket controls the next target position

Deterministic code should:
- compile/validate the factor
- prevent look-ahead
- calculate metrics
- apply transaction costs
- split IS/OOS
- correct for multiple testing
- enforce risk limits
- execute/reconcile the paper order

That division keeps the LLM genuinely load-bearing while keeping financial arithmetic reproducible.

## Minimum validation engine

Every candidate factor should produce:
- hypothesis and economic intuition
- exact formula / feature graph
- allowed data sources
- training window
- untouched OOS window
- IC / rank-IC or strategy return metric
- Sharpe / drawdown / turnover after costs
- comparison against a simple baseline
- correlation against already accepted factors
- multiple-testing penalty
- regime/session breakdown
- failure reason if rejected

Promotion must be impossible when leakage, missing data or OOS decay crosses hard thresholds.

## Product loop

OBSERVE market anomaly
-> Qwen proposes hypothesis
-> safe factor DSL compiles it
-> deterministic research engine tests it
-> adversarial/falsification checks
-> untouched OOS
-> Qwen reviews evidence
-> promote / revise / reject
-> promoted factor enters paper portfolio
-> Agent Hub executes
-> monitor live factor decay
-> retire/evolve when evidence deteriorates

This loop is continuously useful after the hackathon, unlike a one-time backtest page.
