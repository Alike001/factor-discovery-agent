# Phase 0 Preflight — Verified Facts, Live Checks, and Build Gate

Snapshot: 2026-09-27
Working submission deadline: 2026-10-08 23:59 UTC+8, confirmed by the live official submission form viewed by the builder.

Important:
The public handbook still shows the older September 27 deadline. For project planning, use the live submission form's October 8 deadline. Keep a screenshot of the form in the final evidence pack.

This document separates:
1. facts verified from current official documentation;
2. measurements reported by public S2 builders;
3. checks that MUST be executed locally in the new project before Phase 1.

---

# 1. Official facts already verified

## 1.1 Reality instrument discovery

Official endpoint:

`GET https://api.bitget.com/api/v3/market/instruments?category=SPOT`

Reality instruments are identified by:

`isReality == "yes"`

Relevant response fields:
- symbol
- baseCoin
- quoteCoin
- symbolType
- pricePrecision
- quantityPrecision
- quotePrecision
- minOrderAmount
- status
- launchTime
- isReality

Do not hardcode the active universe from old articles or screenshots. Fetch it at runtime.

Official docs:
https://www.bitget.com/api-doc/uta/public/Instruments

## 1.2 rToken candles

Official endpoints:

`GET /api/v3/market/candles`
`GET /api/v3/market/history-candles`

rToken constraints:
- category: SPOT
- type: market
- supported intervals: 1m, 5m, 15m, 1H, 4H, 1D
- current candles endpoint: up to 1000 rows
- history endpoint: up to 100 rows per request
- historical request window: max 90 days
- history older than 90 days can still be requested by paging windows
- Reality volume/turnover before 2026-07-09 may be empty and was not backfilled

Official docs:
https://www.bitget.com/docs/catalog/market/market-data
https://www.bitget.com/docs/uta/reality-trading-guide

## 1.3 Reality stock reference/session data

Public endpoints:

`GET /api/v3/reality/market/stock-info`
`GET /api/v3/reality/market/states`
`GET /api/v3/reality/market/calendar`

Stock info returns:
- rToken symbol
- native stock code
- company name
- supported trading periods
- weekendTradable

Market states describes:
- pre_market
- regular
- after_hours
- overnight
- daylight saving type

Market calendar returns:
- timezone
- special closures
- regular weekend closures

Official docs:
https://www.bitget.com/docs/catalog/reality/market-data

## 1.4 Reality order book / platform fills

Dedicated Reality orderbook and platform-fill endpoints require authentication and whitelist access.

These are NOT V1 dependencies.

The product must work without them.

## 1.5 Reality trading

Official rToken order endpoint:

`POST /api/v3/trade/place-reality-order`

Supports:
- SPOT or MARGIN category
- market or limit
- clientOid

Official docs:
https://www.bitget.com/docs/catalog/reality/trading

## 1.6 Demo environment

Official Demo:
- create a Demo API Key
- send `paptrading: 1`
- REST host remains `https://api.bitget.com`
- Demo WebSocket hosts use `wspap.bitget.com`

Official docs do NOT specifically guarantee Reality spot availability in Demo.

Official docs:
https://www.bitget.com/docs/uta/quick-start
https://www.bitget.com/docs/uta/demo-trading/rest-api

## 1.7 Fees

Bitget's 2026-08-06 rToken fee announcement states a baseline 0.05% maker / 0.05% taker rate for VIP 0-3, with lower rates for higher VIP tiers and BGB deduction.

Do not make this the sole source of truth for the user's account.

The authenticated UTA endpoint exists:

`GET /api/v3/account/fee-rate?symbol=RNVDAUSDT&category=SPOT`

It returns the account's actual maker/taker rates.

Official docs:
https://www.bitget.com/api-doc/uta/account/Get-Account-Fee-Rate

For development when account-auth is not configured:
- baseline research assumption: 0.05% per fill
- stress test: at least 2x baseline transaction-cost assumption
- UI must label fee as assumed until authenticated account fee is recorded

## 1.8 Qwen hackathon gateway

Current public handbook setup:

Base URL:
`https://hackathon.bitgetops.com/v1`

Recommended model:
`qwen3.8-max`

Environment variable:
`BITGET_QWEN_API_KEY`

Codex wire API:
`responses`

The backend should call Qwen directly through the same OpenAI-compatible gateway.

Do not assume structured-output extensions are supported.
For Phase 0:
- request strict JSON in the prompt
- parse it
- validate it locally against Pydantic
- record first-pass schema success/failure and latency

Official handbook:
https://bitget-ai.gitbook.io/bitgetai_hackathons2

## 1.9 Bitget US-stock MCP

Current handbook states the standalone read-only MCP endpoint is:

`https://agent.bitget.com/mcp`

It covers:
- real-time quotes and historical K-lines
- company profile
- financial statements
- ratios/valuation
- earnings calendar
- corporate actions
- insider trades
- 13F
- analyst estimates
- ETFs
- news/sentiment

No Bitget account/API key required.

Phase 0 must use MCP discovery (`tools/list`) before depending on any exact tool name.

Important:
Do not use current-only fundamentals in a historical factor unless historical point-in-time semantics are proven.

---

# 2. Public builder measurements worth treating as warnings, not as our live truth

## 2.1 Reality spot exists in public API

Public S2 projects have recorded live `RAAPLUSDT` / `RNVDAUSDT` instruments with `isReality=yes`.

One recorded `RNVDAUSDT` snapshot showed:
- category SPOT
- status online
- isReality yes
- price precision 2
- quantity precision 4
- min order amount 10

This is prior evidence only. Our own preflight must refetch current values.

## 2.2 Demo Reality spot has failed for other builders

Gloaming reports a live September 11 test where:
- Demo order on `RAAPLUSDT` returned `"Parameter RAAPLUSDT does not exist"`
- BTCUSDT progressed to ordinary order validation

WardenClaw separately reported Demo spot calls returning environment mismatch in its tested environment.

Conclusion:
Direct rToken Demo remains UNVERIFIED for us.

Default V1 execution stays:
`LOCAL PAPER ENGINE + REAL BITGET MARKET DATA`

Only change this after our own Phase 0 probe succeeds.

## 2.3 Session/reference bugs are a real product risk

Gloaming documented:
- inconsistent proxy lookback windows manufacturing multi-percent "spreads"
- a missing expected Friday stock bar causing the system to fall back to Thursday, creating false weekend dislocations and bad paper trades

Our session service must fail closed if the expected anchor bar is missing.

---

# 3. Local live checks that must run now

These are the only remaining Phase 0 gates.

## P0-A — Reality universe

Call live endpoint.

Write:
`evidence/preflight/reality-universe.json`

Fields per Reality symbol:
- symbol
- baseCoin
- status
- launchTime
- precision
- minOrderAmount
- raw response hash

Then create:
`evidence/preflight/core-universe.json`

Selection rule:
- intersect Reality online symbols with target tickers
- require valid stock-info mapping
- require 1H candles
- require latest 15m candles
- require enough history for the current factor family

Initial target ticker set:
NVDA, AAPL, TSLA, MSFT, AMZN, META, AMD, QQQ
Secondary:
SPY, COIN, HOOD, MSTR

Do not force eight symbols if some fail data quality.

## P0-B — Candle coverage

For every selected core symbol:

1H:
- find earliest retrievable bar
- count rows
- count gaps
- check duplicate timestamps
- record first/last timestamp
- record volume non-empty start

15m:
- fetch recent 7 days
- count gaps
- record last closed bar

Write:
`evidence/preflight/candle-coverage.json`

Fail conditions:
- duplicate timestamps unresolved
- latest expected closed bar missing by more than allowed grace
- <30 calendar days price history for a core symbol

Degraded:
- 30-59 days history

Pass for historical certification:
- >=60 days price history

Volume:
- never treat empty pre-2026-07-09 values as zero

## P0-C — Stock MCP

Connect to:
`https://agent.bitget.com/mcp`

Run:
- initialize
- tools/list
- save tool catalog
- discover one quote tool
- discover one history/K-line tool
- query NVDA and AAPL
- record timestamps and response shape

Write:
`evidence/preflight/stock-mcp.json`

Pass:
- history endpoint/tool exists
- exact timestamps are exposed or derivable
- at least NVDA/AAPL historical queries work

If history semantics are unclear:
- do not depend on native-stock history in Phase 1 factor
- use rToken-only tracer factor first

## P0-D — Session/calendar

Call Reality:
- stock-info
- states
- calendar

Validate current session service against these responses.

Regression fixtures:
- normal weekday
- Friday close
- Saturday
- US holiday
- DST state

Critical test:
If the expected last regular-session date has no bar, return MISSING_ANCHOR and block any factor that depends on it.

## P0-E — Qwen

Environment:
`BITGET_QWEN_API_KEY`

Call:
`https://hackathon.bitgetops.com/v1/responses`

Model:
`qwen3.8-max`

Run exactly three probes:
1. FactorProposal JSON
2. LifecycleDecision JSON
3. PortfolioDecision JSON

For every probe record:
- request hash
- response hash
- latency
- HTTP status
- raw text
- Pydantic validation result
- repair required yes/no

Pass:
- all three can produce schema-valid JSON with max one repair
- no secret appears in logs

If no key:
status is `BLOCKED_KEY`, not fake PASS.

## P0-F — Account fee

If standard/demo Bitget API credentials are available:
call:
`GET /api/v3/account/fee-rate?symbol=<first-core-symbol>&category=SPOT`

Write exact maker/taker.

If credentials absent:
record:
`ACCOUNT_FEE_UNVERIFIED`
and use published 0.05% baseline for tracer bullet.

## P0-G — Reality Demo

Only run if a Demo API key is available.

Steps:
1. authenticated Demo environment check
2. query/check Reality symbol availability
3. attempt a minimum notional Reality spot limit order with unique clientOid
4. record exact response
5. cancel if accepted
6. query order status

Output:
`evidence/preflight/reality-demo.json`

Outcomes:
- VERIFIED
- UNSUPPORTED_SYMBOL
- ENVIRONMENT_MISMATCH
- AUTH_FAILURE
- INCONCLUSIVE

Never let Phase 1 depend on VERIFIED.

## P0-H — Database + scheduler

For hackathon runtime use a low-cost architecture:

- Next.js frontend: Vercel
- Postgres: Neon
- scheduled research/paper jobs: GitHub Actions calling one-shot Python commands
- public API can run in Next.js for read-only DB queries OR a small FastAPI service if needed

Reason:
Our decision cadence is hourly / multi-hour, so an always-awake worker is not technically required for V1.

Required one-shot commands:
- `python -m app.jobs.research_cycle`
- `python -m app.jobs.paper_tick`
- `python -m app.jobs.mark_portfolio`
- `python -m app.jobs.daily_decay`
- `python -m app.jobs.export_evidence`

Every command must be:
- idempotent
- protected by Postgres advisory lock / unique DB keys
- restart-safe

Post-hackathon:
move the exact job functions into an always-on scheduler without changing research logic.

---

# 4. Phase 0 exit decision

Phase 0 is PASS when:
- Reality public data works for >=4 quality rTokens
- >=1 rToken has >=60 days price history OR the product explicitly downgrades certification to forward-paper-first
- Qwen schema-valid calls work
- stock MCP either works or is cleanly removed from the Phase 1 tracer
- session/calendar functions work
- database works
- fee assumption is recorded
- execution mode is explicitly determined

Reality Demo may fail without failing Phase 0.

A Demo failure locks:
`EXECUTION_MODE=local_paper`

The product remains valid.

---

# 5. Tracer bullet factor

Phase 1 must NOT ask Qwen to invent the first factor yet.

Use one hardcoded, boring factor only to prove infrastructure.

Tracer:
`Overnight Relative Return Z-Score`

Concept:
- one rToken
- compare its recent return to QQQ or its own rolling baseline during a valid session
- generate long/flat signal
- no claim that this is alpha

Purpose:
- prove data -> DSL -> backtest -> OOS -> costs -> report -> UI

After tracer works, Phase 2 turns on autonomous Qwen proposal.

Do not optimize the tracer.

Do not present tracer performance as the project thesis.

---

# 6. Phase 0 decision log template

At the end of Phase 0 write:

`docs/PHASE0_DECISION.md`

with:

- deadline status
- Reality symbols selected
- first/last price dates
- volume coverage
- stock MCP status
- Qwen status
- current fee basis
- Demo status
- execution mode
- deployment mode
- blockers
- spec amendments

If any finding contradicts `23_FINAL_BUILD_SPEC.md`, update the spec before Phase 1 and record why.
