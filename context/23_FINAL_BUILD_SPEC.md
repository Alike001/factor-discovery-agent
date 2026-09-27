# Final Build Specification

Working category: Autonomous Session-Alpha Researcher for Bitget rTokens
Track: Agentic Trading
Sub-theme: Factor Discovery Agent
Snapshot: 2026-09-27
Status: Build-ready specification with Phase 1.5 integrity amendment

This document is the product and implementation source of truth. Codex should not invent product scope outside this file without an explicit amendment.

---

# 1. Product definition

## 1.1 One sentence

An autonomous Qwen researcher for Bitget's 24/7 tokenized US stocks that proposes factor hypotheses, tries to falsify them on unseen data and after costs, rejects weak ideas, promotes survivors into a forward paper portfolio, and retires factors when their forward evidence decays.

## 1.2 30-second explanation

Bitget rTokens trade 24/7 while traditional US equities move through regular hours, after-hours, overnight, weekends, and holidays. That creates a new market structure with very little history and a high risk of overfitting.

The product runs an autonomous research loop. Qwen proposes a bounded factor hypothesis. Deterministic code tests it on real Bitget data, after costs and on held-out periods. Most ideas are rejected. Survivors enter a small forward paper portfolio. Every proposal, test, Qwen decision, position, and failure is stored in an evidence ledger. A factor that stops working is retired.

## 1.3 What we are building

A continuously running factor-research system with five visible product surfaces:

- Research Lab
- Factor Library and Graveyard
- Paper Portfolio
- Evidence Ledger
- System Health

## 1.4 What we are not building

This V1 is not:
- a generic trading chatbot
- a manual no-code strategy builder
- a strategy marketplace
- a copy-trading product
- a social trading feed
- an RSI/MA bot
- an overnight arbitrage guarantee
- a real-money trading system
- a multi-agent debate system
- a blockchain protocol
- a 500-symbol terminal

---

# 2. Exact target user

## 2.1 Primary user

A crypto-native systematic trader or very small quant team, usually 1 to 3 people, already interested in Bitget tokenized US equities.

Profile:
- capital they may eventually automate: roughly $10k to $250k
- risk appetite: moderate
- holding period: hourly to multi-day
- market: Bitget rTokens first
- technical comfort: can read Sharpe, drawdown, OOS, and factor logic, but does not want to hand-run dozens of research experiments
- current workflow: spreadsheets, notebooks, fixed bots, Playbooks, or ad hoc AI prompts

## 2.2 Primary job to be done

"Continuously search the new 24/7 rToken market for session-specific effects, but keep me from fooling myself with short-history backtests."

## 2.3 Secondary post-hackathon user

A strategy publisher or small systematic PM who wants to turn a factor that survived research and forward paper validation into a Bitget Playbook or bounded Agentic Account strategy.

---

# 3. User problem

The problem is not a lack of indicators.

rTokens are new. They trade through market phases that do not exist in the same way for the traditional underlying shares. Historical depth is limited. Some fields have shorter reliable coverage than price itself. Public S2 projects have already shown that bad clocks, stale stock anchors, mismatched return windows, or naive cost assumptions can manufacture convincing fake alpha.

Existing products cover pieces:
- Bitget Playbook can author, backtest, publish, and paper-run a user-specified strategy.
- Bitget offers simple automated bots and portfolio automation.
- Generic quant frameworks can search huge factor spaces.
- Generic LLM agents can generate strategy code.

The missing product is an autonomous research process that:
- originates its own bounded hypotheses
- records every trial
- cannot grade itself
- treats insufficient evidence as a real result
- keeps failed factors
- moves survivors into forward paper validation
- can retire a factor later

---

# 4. Hackathon fit

The official S2 handbook describes Factor Discovery Agent as:

"How does the Agent autonomously propose hypotheses, discover alpha factors, and translate into tradable decisions?"

The example flow is autonomous hypothesis proposal, iterative factor mining/backtesting, then autonomous trading after validation.

Official Agentic Trading requirements include:
- runnable demo
- event -> decision -> execution flow
- paper-trading log
- compliant X post

Judging focus:
- paper trading Sharpe
- max drawdown
- win rate
- decision explainability
- agent architecture quality
- risk control effectiveness

Scoring:
- 50% quantitative
- 50% judge

Official handbook:
https://bitget-ai.gitbook.io/bitgetai_hackathons2

Current operational deadline:
- October 8, 2026 at 23:59 UTC+8, confirmed by the live official submission form viewed by the builder.
- public handbook/landing-page dates are stale and must not override the live form for scheduling.
- keep a screenshot of the live form in the final evidence pack.

---

# 5. Core product loop

The long-running loop has two cadences.

## 5.1 Research cadence

Default V1:
- one discovery cycle every 6 hours
- manual admin `Run cycle` available
- only one research cycle may own the worker lease at a time

Cycle:

1. PRECHECK
2. SNAPSHOT
3. PROPOSE
4. COMMIT
5. FORMALIZE
6. EVALUATE
7. GATE
8. INTERPRET
9. LIFECYCLE
10. PAPER ELIGIBILITY
11. EVIDENCE CLOSE

### PRECHECK

Before asking Qwen:
- source health acceptable
- minimum core universe available
- latest required bars closed
- clock/session source current
- database writable
- no unresolved prior cycle that must be reconciled

A failed precheck writes a NO_RUN event. It does not call Qwen.

### SNAPSHOT

Create immutable research snapshot:
- as-of timestamp
- current Reality universe
- coverage by symbol
- latest closed bars
- underlying reference coverage
- session state
- current factor library identities
- current trial count
- structural rejection categories
- data-source timestamps

Hash the canonical snapshot JSON.

### PROPOSE

Qwen Proposer receives a deliberately blinded context.

It can see:
- market structure description
- allowed DSL grammar
- available fields
- available symbols
- current session context
- already evaluated canonical factor identities
- structural failure classes such as "volume unavailable" or "duplicate"
- total trials so far

It cannot see:
- Sharpe of previous factors
- ranking of previous factors
- PnL of previous factors
- best factor
- raw success/failure score leaderboard
- "directions that worked"

This prevents a feedback loop that repeatedly hill-climbs the same backtest.

Qwen outputs one FactorProposal JSON.

### COMMIT

Before evaluation:
- save exact Qwen request
- save exact Qwen response
- hash prompt
- hash response
- assign trial number
- save canonical proposal
- save proposal timestamp

This happens before any performance metric is computed.

### FORMALIZE

Parse the proposal into the safe Factor DSL.

No arbitrary Python.
No SQL.
No shell.
No dynamically imported model code.

Invalid syntax becomes REJECTED_STRUCTURAL and remains in the ledger.

### EVALUATE

The deterministic engine computes:
- raw signal
- trades
- gross results
- costs
- net results
- IS/OOS
- stability
- placebo/permutation
- multiple-testing adjustment
- evidence sufficiency

Qwen never calculates financial metrics.

### GATE

The gate engine returns:
- PASS
- FAIL
- INCONCLUSIVE

for every gate.

The aggregate lifecycle result can be:
- REJECTED
- INCONCLUSIVE
- CANDIDATE
- CERTIFIED

### INTERPRET

A separate Qwen lifecycle prompt can read the current experiment report.

Allowed actions:
- ABANDON
- EXPLAIN
- REVISE

It may recommend PROMOTE, but the deterministic gate owns promotion.

If Qwen proposes a revision:
- revision receives a new factor version
- new canonical hash
- new trial number
- full evaluation from zero

### LIFECYCLE

Persist the exact lifecycle transition.

No factor can skip states.

### PAPER ELIGIBILITY

A CANDIDATE or CERTIFIED factor may enter forward paper probation under different size caps.

No real capital.

### EVIDENCE CLOSE

Write final cycle manifest with hashes of all artifacts.

## 5.2 Paper cadence

Default:
- evaluate portfolio decisions on each closed 1H bar
- mark positions every 15 minutes where 15m data is available
- daily decay review

Event -> decision -> execution:

1. New closed market bar
2. Build current factor signal packet
3. Qwen Portfolio Actor sees eligible factor signals, current paper book, source health, and risk envelope
4. Qwen chooses HOLD / OPEN / REDUCE / CLOSE and target size from a bounded set
5. deterministic risk gate can only reduce or veto
6. paper engine executes exactly once
7. ledger records decision, risk verdict, order, fill, and new book state
8. forward factor evidence updates

This is the load-bearing LLM trading path for Agentic Trading.

---

# 6. Factor lifecycle

Enum:

```text
PROPOSED
COMMITTED
FORMALIZED
BACKTESTED
COST_CHECKED
OOS_TESTED
ROBUSTNESS_TESTED
MULTIPLE_TEST_GATED
CANDIDATE
CERTIFIED
PAPER_PROBATION
ACTIVE
DECAYED
RETIRED
REJECTED
INCONCLUSIVE
```

Rules:
- REJECTED and INCONCLUSIVE can be reached from any evaluation state
- no transition can skip a mandatory gate
- RETIRED is permanent for that version
- a revised expression is a new version
- factor identity is the canonical expression + universe + session + horizon + rebalance contract, not the human name

Meaning:
- CANDIDATE: passed minimum safety and OOS checks, eligible for tiny forward paper probation
- CERTIFIED: passed the complete historical anti-overfit gate
- PAPER_PROBATION: has entered forward paper validation
- ACTIVE: forward evidence met the pre-registered activation rule
- DECAYED: forward behavior breached the pre-registered decay rule
- RETIRED: removed from portfolio and archived

UI copy must say "historically certified" where needed. Historical certification is not a promise of future returns.

---

# 7. Safe Factor DSL V1

## 7.1 Design goal

Qwen should have enough language to express genuine rToken-session hypotheses without being able to emit arbitrary executable code.

The DSL is JSON AST, validated by Pydantic.

## 7.2 FactorSpec

Conceptual schema:

```json
{
  "name": "Semiconductor Overnight Residual Reversion",
  "thesis": "When semiconductor rTokens lag their benchmark during overnight hours, the lag partially reverses before the next regular session.",
  "universe": ["RNVDAUSDT", "RAMDUSDT"],
  "session_filter": ["overnight"],
  "signal": {},
  "entry_condition": {},
  "exit_condition": {},
  "horizon_bars": 6,
  "rebalance_bars": 1,
  "direction": "long_flat",
  "rationale": "..."
}
```

## 7.3 Data sources available to expressions

V1 market fields:
- rToken close
- rToken open
- rToken high
- rToken low
- rToken volume only after provenance is authoritatively established; currently disabled
- underlying close/history when point-in-time data is available
- benchmark close/history
- session phase
- hours since regular close
- hours until next regular open

V1 benchmark set:
- rQQQ or QQQ reference
- rSPY or SPY reference
- BTCUSDT where explicitly used as a cross-asset reference

Do not include current analyst targets, current fundamentals, or current news in historical factor backtests unless a point-in-time historical source is implemented.

## 7.4 Numeric operators

Allowed:
- `ret(source, lookback)`
- `vol(source, lookback)`
- `sma(expr, lookback)`
- `zscore(expr, lookback)`
- `rank(expr, universe)`
- `group_mean(expr, universe)`
- `rolling_beta(asset_return, benchmark_return, lookback)`
- `residual(asset_return, benchmark_return, lookback)`
- `spread_bps(token_price, reference_price)`
- `abs`
- `sign`
- `clip`
- `add`
- `sub`
- `mul`
- `div`

## 7.5 Boolean operators

Allowed:
- `gt`
- `gte`
- `lt`
- `lte`
- `and`
- `or`
- `not`
- `session_in`
- `data_available`

## 7.6 Fixed lookback set

V1 lookbacks are selected from:

```text
1, 3, 6, 12, 24, 48, 120, 168
```

expressed in the factor's base bar unit.

Qwen cannot invent arbitrary 37-bar windows.

This reduces search degrees of freedom and keeps the multiple-testing count honest.

## 7.7 DSL constraints

- max AST depth: 6
- max total nodes: 40
- max distinct lookbacks: 3
- max cross-asset references: 2
- max universe size in one factor: core universe size
- no dynamic symbol names outside approved universe
- no current forming candle
- no future fields
- no arbitrary constants except a small approved threshold set
- division uses safe denominator guard
- volume primitive automatically invalid before reliable volume coverage
- every expression canonicalized before evaluation
- duplicate canonical expressions are suppressed, but the duplicate proposal remains logged

## 7.8 Approved threshold set

V1:
```text
-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0
```

For percentage/bps comparisons, use explicit normalized functions instead of arbitrary raw constants where possible.

---

# 8. Research universe

## 8.1 Initial target

Seed list:
- rNVDA
- rAAPL
- rTSLA
- rMSFT
- rAMZN
- rMETA
- rAMD
- rQQQ

Secondary after coverage audit:
- rSPY
- rCOIN
- rHOOD
- rMSTR

## 8.2 Runtime eligibility

Never hardcode "supported" only from this document.

At startup and daily:
1. fetch Reality instruments
2. keep `isReality=yes`
3. intersect with seed list
4. check candle coverage
5. check reference coverage
6. check latest timestamp
7. check field coverage
8. mark symbol researchable or degraded

A factor may only use symbols whose required fields satisfy its data contract.

---

# 9. Data layer

## 9.1 Core Bitget inputs

Use official Bitget Reality/UTA market data for:
- Reality instrument discovery
- rToken tickers
- rToken candles
- session/reference state where available
- fee/precision metadata

Reality documentation:
https://www.bitget.com/docs/uta/reality-trading-guide

## 9.2 Underlying US stock data

Preferred:
`bitget-mcp-server`

Use only endpoints that have been live-tested and whose historical semantics are understood.

Do not historical-backtest current-only snapshots.

## 9.3 Optional enrichment

`bitget-signal` may be added only after live reliability is measured.

It must never be required for the minimum viable factor engine.

## 9.4 Data storage

Persist raw normalized bars in Postgres.

Recommended tables:
- `instruments`
- `market_bars`
- `reference_bars`
- `market_sessions`
- `source_health`
- `data_snapshots`

Every row has:
- source
- observed_at
- source_timestamp
- ingested_at
- payload_hash

## 9.5 Time rules

All persisted timestamps are UTC.

The session service is responsible for:
- US regular session
- pre-market
- after-hours
- overnight
- weekend
- holiday
- expected last regular close
- next regular open

No strategy code computes market sessions ad hoc.

## 9.6 Missing-data rule

Missing data never becomes zero.

The value states are:
- present
- missing
- stale
- structurally unavailable

A factor requiring a missing field becomes INCONCLUSIVE or is skipped.

## 9.7 Phase 1.5 integrity amendment — 2026-09-27

Live measurements require these binding rules before autonomous research:

- The live SPOT response contained 3,169 instruments: 2,587 `isReality=yes` and 582 not Reality. All 2,587 Reality instruments were online and stock-typed in this snapshot. This is documentation drift from the public 500+ product copy, not a filtering error.
- rToken-symbol hourly endpoints expose history years before instrument `launchTime` and the June 2 public rToken launch. This older lineage is ambiguous and must never be described as publicly tradable rToken history.
- Certification uses a symbol/field data contract. Price `valid_from` is `max(2026-06-02T00:00:00Z, instrument launchTime)`. A later authoritative public/online start overrides both.
- Volume and turnover operators are disabled. If later enabled, their minimum `valid_from` is `max(price certification start, 2026-07-09T00:00:00Z)` and authoritative provenance is still required.
- Historical session arithmetic uses IANA `America/New_York`, never the API's fixed `EST` label.
- Gap checks distinguish `EXPECTED_CLOSED`, `EXPECTED_OPEN_MISSING`, and `OBSERVED`. Expected-open missing bars are never forward-filled.
- Missing required underlying anchors return `MISSING_EXPECTED_ANCHOR`; older bars are not substituted.
- Phase 2 cannot start without both 3/3 schema-valid Qwen probes and a passing persistent PostgreSQL gate.

---

# 10. Qwen responsibilities

Use Qwen through the Bitget hackathon gateway if credentials work.

Recommended model from current handbook:
`qwen3.8-max`

## 10.1 Qwen Proposer

Purpose:
originate one falsifiable factor hypothesis.

Input:
- safe DSL schema
- market structure
- current eligible universe
- current structural snapshot
- previous factor identities
- structural failure categories
- trial count

Output:
strict `FactorProposal`.

Proposer never sees prior performance leaderboard.

## 10.2 Qwen Lifecycle Analyst

Purpose:
interpret one experiment after deterministic evaluation.

Input:
- proposal
- gate report
- failures
- current data limitations

Output:
- `ABANDON`
- `REVISE`
- `PROMOTE_RECOMMENDATION`
- explanation

A promotion recommendation cannot bypass code.

## 10.3 Qwen Portfolio Actor

Purpose:
make the actual Agentic Trading decision from eligible factor signals.

Input:
- eligible factor versions
- current signal values
- current book
- current source health
- risk envelope
- allowed actions

Output:
strict JSON:

```json
{
  "action": "HOLD|OPEN|REDUCE|CLOSE",
  "symbol": "RNVDAUSDT|null",
  "factor_version_id": "...|null",
  "target_weight": 0.0,
  "reason": "...",
  "invalidation": "..."
}
```

Target weights V1 can only be:
- 0
- 0.025
- 0.05

Qwen cannot request leverage.

Qwen cannot request a symbol not in the supplied eligible list.

## 10.4 Model failure behavior

Malformed JSON:
- one repair retry using the original response + schema error
- if still invalid, ABSTAIN/HOLD

Timeout:
- no blind trade fallback
- HOLD

Truncation:
- retry original prompt with larger output budget if the API indicates length truncation

Provider unavailable:
- HOLD
- log model outage

## 10.5 Qwen accounting

Every call stores:
- purpose
- model
- prompt version
- started/finished
- request hash
- response hash
- tokens if returned
- latency
- success/failure
- exact raw response

---

# 11. Anti-overfit and evidence gates

The system must be able to say INCONCLUSIVE.

No gate should be tuned after seeing a factor result without creating a versioned protocol amendment.

## 11.1 Gate 0 - syntax and canonical identity

Checks:
- schema valid
- AST limits
- approved fields/operators
- canonical hash
- duplicate detection

## 11.2 Gate 1 - data contract

Checks:
- required fields exist
- minimum history
- current forming bar excluded
- session labels available
- volume not used where volume history is structurally missing
- no current-only external snapshot leaked into history

FAIL for leakage.
INCONCLUSIVE for insufficient data.

## 11.3 Gate 2 - minimum independent evidence

Use time-block evidence, not raw row count.

Initial rule:
- total history target >= 60 calendar days where available
- OOS target >= 30 calendar days where available
- at least 12 independent time blocks for robustness tests
- at least 20 OOS trade events for performance certification

If not met:
INCONCLUSIVE for certification, though the factor may still be kept as a research candidate.

## 11.4 Gate 3 - backtest mechanics

- signal at closed bar t
- trade can execute no earlier than next observable bar/quote
- costs applied to each fill
- no overlapping future label leakage
- deterministic replay

## 11.5 Gate 4 - costs

Baseline cost:
- current Bitget rToken fee snapshot
- configured slippage model

Stress cost:
- 2x baseline slippage
- fee remains current published/observed rate

Report both gross and net.

A factor that exists only gross is rejected.

## 11.6 Gate 5 - fixed IS/OOS split

The split date is fixed by protocol before running the candidate.

Preferred:
- oldest available portion = IS
- newest >=30 days = OOS

Do not move the split to improve results.

Report:
- IS Sharpe
- OOS Sharpe
- decay ratio
- returns
- max drawdown
- turnover
- trade count

## 11.7 Gate 6 - OOS decay

Use the handbook's Alpha Factory alert as a sanity reference:

`OOS Sharpe < 0.5 * IS Sharpe`

For historical CERTIFIED:
- if IS Sharpe > 0, OOS must be >= 0.5 * IS
- OOS Sharpe must be > 0
- otherwise fail

For CANDIDATE paper probation:
- OOS net return positive
- no catastrophic drawdown
- no leakage
- enough trade events for paper interpretation

The candidate tier allows forward paper collection without calling weak history "certified".

## 11.8 Gate 7 - symbol/session stability

Report result by:
- symbol
- first/second half
- session subset

A population result carried entirely by one symbol is not certified.

Initial certification rule:
- same payoff sign in at least 60% of eligible symbols with enough observations
- no single symbol contributes >50% of total net PnL
- first/second half signs agree

If the factor is explicitly single-symbol, replace cross-symbol rule with time-block stability and label the factor single-symbol.

## 11.9 Gate 8 - placebo/permutation

Shuffle factor timing within safe blocks or sign-flip block payoffs.

Initial:
- 2,000 permutations
- one-sided p <= 0.10 for CANDIDATE
- p <= 0.05 for CERTIFIED

Store seed and method.

## 11.10 Gate 9 - split-half/block replication

Independent halves of time blocks must reproduce the payoff direction.

If too few blocks:
INCONCLUSIVE.

## 11.11 Gate 10 - multiple testing

Every unique committed hypothesis increments the global research trial counter.

Use Deflated Sharpe / equivalent multiple-testing adjustment.

Initial historical certification:
- DSR probability >= 0.90

Do not reset the trial counter because a research direction changed.

## 11.12 Gate 11 - baseline comparison

Compare to simple baselines:
- cash
- buy-and-hold rToken during same eligible windows
- simple session-only exposure if relevant
- one fixed simple momentum/reversion baseline if the proposed factor belongs to that family

A complicated factor must show incremental behavior over the simpler explanation.

## 11.13 Aggregate states

REJECTED:
- leakage
- structural invalidity
- cost failure
- clear OOS failure
- robustness failure

INCONCLUSIVE:
- insufficient independent evidence
- required source missing
- test cannot be evaluated honestly

CANDIDATE:
- safe mechanics
- positive net OOS
- enough evidence for forward paper probation
- not full certification yet

CERTIFIED:
- all historical certification gates pass

---

# 12. Paper engine

## 12.1 Purpose

Produce honest forward evidence using real Bitget market data while avoiding any claim of rToken Demo execution until verified.

Global V1 mode:

`PAPER_EXECUTION_REAL_BITGET_MARKET_DATA`

## 12.2 Starting account

Default:
- starting equity: 10,000 USDT virtual
- no leverage
- long/cash only in V1

This keeps the execution model aligned with rToken spot.

## 12.3 Risk envelope

Initial, pre-registered:

- max one symbol target: 5% equity
- CANDIDATE max symbol target: 2.5%
- CERTIFIED max symbol target: 5%
- max total exposure: 25%
- max open symbols: 5
- max one factor exposure: 10%
- no leverage
- daily loss halt: 2% of start-of-day equity
- total drawdown halt: 5%
- stale-data rule: no new exposure
- source-health failure: HOLD or reduce only

The risk layer may only:
- allow
- reduce
- close
- block

It may never create or enlarge an exposure the Qwen decision did not request.

## 12.4 Execution timing

For a decision made after closed bar `t`:
- earliest fill is next observable quote or next bar open
- never fill at the signal bar close if that price was not knowable before decision completion

Fallback deterministic model:
- next 15m bar open
- apply side-aware slippage
- apply fee

## 12.5 Slippage

Preferred:
- use bid/ask if public and reliable
- baseline = half-spread + configured buffer

If depth is unavailable:
- conservative fixed slippage configured in protocol
- stress run at 2x
- UI states that depth was unavailable

Do not invent market impact from fake order books.

## 12.6 Idempotency

Every intended order gets:

`paper_order_key = factor_version_id + cycle_id + symbol + target_version`

Unique DB constraint.

A repeated worker call returns the original order/fill state.

## 12.7 Unknown execution state

For local paper execution this should be rare, but persistence still follows Masayume's useful rule:
- persist intent before fill mutation
- on restart, reconcile open intent
- never create a second fill for the same key

## 12.8 Paper tables

- `paper_accounts`
- `paper_decisions`
- `paper_orders`
- `paper_fills`
- `paper_positions`
- `portfolio_marks`
- `factor_allocations`
- `risk_events`

## 12.9 Forward evidence

For each factor:
- number of paper decisions
- number of fills
- net return attribution
- turnover
- win rate
- max drawdown contribution
- realized expectancy
- days active
- divergence from historical expectation

---

# 13. Forward activation and decay

These rules are protocol versioned before observing the forward outcome.

## 13.1 Paper probation

CANDIDATE or CERTIFIED factor can enter PAPER_PROBATION.

Candidate cap: 2.5%.
Certified cap: 5%.

## 13.2 ACTIVE

V1 activation requires:
- at least 10 closed paper trades or equivalent independent forward events
- cumulative net expectancy > 0
- forward drawdown <= 1.5x historical OOS drawdown
- no risk-limit breach
- data/recovery integrity clean

If sample is too small:
remain PAPER_PROBATION.

## 13.3 DECAYED

After at least 10 independent forward events, decay if:
- cumulative net expectancy <= 0 for 3 consecutive review checkpoints, or
- forward drawdown > 2x historical OOS drawdown, or
- factor violates its own structural data assumptions

DECAYED factor:
- cannot open new exposure
- existing exposure can only reduce/close
- Qwen receives the decay report
- factor may become RETIRED or spawn a new revision

No threshold is changed to save a decaying factor.

---

# 14. Data model

Use PostgreSQL.

## 14.1 Core tables

### `research_cycles`

- id UUID
- cycle_number bigint unique
- status
- trigger
- as_of
- started_at
- completed_at
- snapshot_id
- worker_id
- protocol_version
- error_code
- manifest_hash

### `data_snapshots`

- id
- as_of
- source_health_json
- universe_json
- session_json
- coverage_json
- snapshot_json
- sha256

### `qwen_runs`

- id
- cycle_id
- role
- model
- prompt_version
- prompt_text
- prompt_hash
- response_text
- response_hash
- parsed_json
- status
- token_usage
- latency_ms
- created_at

### `hypotheses`

- id
- cycle_id
- trial_number
- name
- thesis
- proposer_run_id
- canonical_identity_hash
- created_at

### `factor_versions`

- id
- hypothesis_id
- version
- parent_factor_version_id nullable
- canonical_spec_json
- canonical_hash unique
- lifecycle_state
- universe
- session_filter
- horizon_bars
- created_at
- retired_at nullable

### `experiments`

- id
- factor_version_id
- dataset_hash
- protocol_version
- IS_start/end
- OOS_start/end
- metrics_json
- trades_artifact_path
- report_hash
- created_at

### `gate_results`

- id
- experiment_id
- gate_name
- outcome
- value_json
- reason
- protocol_version

### `factor_lifecycle_events`

- id
- factor_version_id
- from_state
- to_state
- reason
- qwen_run_id nullable
- experiment_id nullable
- created_at

### `source_health`

- id
- source
- capability
- status
- observed_at
- latest_source_timestamp
- latency_ms
- detail_json

### paper tables

As specified in section 12.

### `evidence_events`

Append-only event table:
- id
- seq bigint unique
- event_type
- entity_type
- entity_id
- payload_json
- previous_hash
- event_hash
- created_at

Hash chain:
`event_hash = sha256(previous_hash || canonical_payload)`

The hash chain is evidence integrity, not a blockchain claim.

---

# 15. Architecture

## 15.1 Repo layout

```text
project/
  web/
    src/app/
    src/components/
    src/features/
    src/lib/
  backend/
    app/
      api/
      bitget/
      qwen/
      research/
        dsl/
        proposer.py
        evaluator.py
        gates.py
        lifecycle.py
        protocol.py
      paper/
        allocator.py
        risk.py
        engine.py
        ledger.py
      data/
      db/
      worker/
      evidence/
    tests/
  scripts/
    preflight.py
    fetch_history.py
    run_cycle.py
    run_paper_tick.py
    export_evidence.py
  docs/
    PRODUCT.md
    ARCHITECTURE.md
    DATA_CONTRACT.md
    FACTOR_DSL.md
    EVIDENCE.md
    DEMO_SCRIPT.md
  evidence/
    README.md
  docker-compose.yml
  README.md
  LICENSE
```

## 15.2 Technology

Frontend:
- Next.js App Router
- TypeScript
- Tailwind
- shadcn/ui or Base UI primitives
- lightweight-charts or Recharts for compact charts
- TanStack Query

Backend:
- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- psycopg
- pandas or Polars
- numpy/scipy where needed
- httpx

Database:
- PostgreSQL

Scheduler:
- APScheduler in one worker process for V1
- PostgreSQL advisory lock prevents duplicate scheduler ownership
- every job is independently idempotent

No Celery in V1.

## 15.3 Process model

V1 can run two processes:
1. API
2. Worker

For lowest-cost hackathon deployment they may run in the same service with one replica, but code boundaries remain separate.

Post-hackathon:
split worker into its own service.

## 15.4 Service flow

```text
Bitget Reality + US data
          |
          v
     Data adapters
          |
          v
   Snapshot builder
          |
          v
    Research worker
     |          |
     |          +--> Qwen
     v
 Safe Factor DSL
     |
     v
 Backtest/Evidence engine
     |
     v
 Deterministic gates
     |
     +--> Graveyard
     |
     v
 Eligible factor library
     |
     v
 Qwen Portfolio Actor
     |
     v
 Deterministic Risk Gate
     |
     v
 Local Paper Engine
     |
     v
 Postgres + Evidence Chain
     |
     v
 Next.js product
```

---

# 16. API contract

Public read-only routes:

- `GET /api/status`
- `GET /api/universe`
- `GET /api/lab/current`
- `GET /api/lab/cycles`
- `GET /api/lab/cycles/{id}`
- `GET /api/factors`
- `GET /api/factors/{id}`
- `GET /api/factors/{id}/evidence`
- `GET /api/paper`
- `GET /api/paper/positions`
- `GET /api/paper/decisions`
- `GET /api/ledger`
- `GET /api/ledger/{seq}`
- `GET /api/proof`
- `GET /api/evidence/manifest`

Optional stream:
- `GET /api/lab/current/stream` SSE

Protected admin:
- `POST /api/admin/research/run`
- `POST /api/admin/research/pause`
- `POST /api/admin/research/resume`

No public mutation endpoints.

---

# 17. UX implementation specification

Detailed UX source:
`22_UX_RESEARCH_AND_DESIGN_DIRECTION.md`

## 17.1 Navigation

Desktop:
- left rail: Lab / Factors / Paper / Ledger / System

Mobile:
- bottom nav with the same five items

Root:
- redirect to `/lab`

No marketing gate.

## 17.2 Global status strip

Always visible:
- Bitget Reality
- US market phase
- eligible universe count
- worker state
- last cycle
- paper mode

## 17.3 Mandatory pages

### `/lab`
live autonomous cycle and current experiment

### `/factors`
factor lifecycle and graveyard

### `/factors/[id]`
factor logic + historical/forward evidence

### `/paper`
paper book with factor attribution

### `/ledger`
append-only audit stream

### `/system`
source/worker/Qwen/data health

### `/proof`
judge evidence page

## 17.4 Design law

- one brand accent
- semantic success/fail/warn colors
- dark-first
- hairline borders
- minimal shadow
- tabular numbers
- mono metadata
- state never conveyed by color only
- explicit source timestamp
- explicit paper/live label
- no decorative AI gradients as the primary identity
- no fake terminal look
- no glassmorphism everywhere

---

# 18. Day-0 blockers

Do these before feature building.

## Blocker 0 - submission status — RESOLVED

The live official submission form viewed by the builder states:
October 8, 2026 at 23:59 UTC+8.

Preserve a screenshot of the live form in the final evidence pack.

Public handbook/landing-page dates are stale and should not be used for build scheduling.

## Blocker 1 - current Reality universe

Run actual instrument discovery.

Output:
`evidence/preflight/reality-universe.json`

Need:
- symbol
- status
- isReality
- precision
- fee fields
- latest ticker availability

## Blocker 2 - candle coverage

For every core symbol:
- fetch 1H history
- fetch 15m recent history
- record first/last bar
- missing intervals
- duplicate timestamps
- volume coverage start
- obvious zero/empty fields

Output:
`evidence/preflight/candle-coverage.json`

## Blocker 3 - underlying reference history

Live test `bitget-mcp-server` or the chosen official US data source.

Need:
- history for core symbols
- exact timestamp semantics
- corporate-action behavior
- response latency
- failure behavior

## Blocker 4 - market session/calendar

Verify:
- current session
- last regular close
- next regular open
- holiday behavior

Add regression test for missing expected last session bar.

## Blocker 5 - Qwen

Run structured-output smoke test:
- one FactorProposal
- one lifecycle response
- one portfolio decision

Record:
- latency
- token count
- schema validity
- timeout behavior

## Blocker 6 - fees

Capture current Reality symbol fee metadata.

Do not carry a fee assumption from another project without rechecking.

## Blocker 7 - Demo Reality execution

If Demo credentials are available:
- test a minimum safe Reality spot order in Demo
- record exact response
- cancel if accepted
- never use real capital for this check

If unsupported:
lock V1 to local paper execution.

## Blocker 8 - deployment worker

Verify chosen host can:
- stay awake
- reach Bitget
- reach Qwen
- reach Postgres
- survive restart
- persist worker lease

---

# 19. Preflight script

`scripts/preflight.py`

Output one machine-readable report.

Example:

```json
{
  "generated_at": "...",
  "submission_form": "MANUAL_CHECK_REQUIRED",
  "reality_universe": {"status": "PASS", "eligible": 8},
  "candles_1h": {"status": "PASS"},
  "candles_15m": {"status": "PASS"},
  "underlying_history": {"status": "PASS"},
  "session_calendar": {"status": "PASS"},
  "qwen": {"status": "PASS", "latency_ms": 8200},
  "fees": {"status": "PASS"},
  "demo_reality": {"status": "UNVERIFIED"},
  "database": {"status": "PASS"},
  "overall": "PASS_WITH_LIMITATIONS"
}
```

The `/system` page renders this report.

---

# 20. Development phases

Because deadline status is ambiguous, build vertically. Do not spend a full day on isolated infrastructure before one complete loop exists.

## Phase 0 - preflight

Exit condition:
- exact available data known
- core universe frozen
- Qwen structured output works
- paper execution mode chosen
- deployment target chosen

Commit.

## Phase 1 - tracer bullet

Build one end-to-end path:

real Bitget history
-> one hardcoded FactorSpec
-> safe DSL parse
-> deterministic backtest
-> one OOS split
-> one gate report
-> one factor detail API
-> one minimal `/lab` UI

Exit:
judge can see real factor evidence in browser.

Commit.

## Phase 2 - autonomous research

Add:
- Qwen Proposer
- proposal commit-before-evaluation
- trial counter
- duplicate suppression
- lifecycle Qwen interpretation
- factor graveyard
- protocol versioning

Exit:
Qwen can autonomously propose one factor and the system can reject it without human intervention.

Commit.

## Phase 3 - full evidence gate

Add:
- cost model
- stability
- permutation
- split/block replication
- DSR / multiple testing
- baselines
- CANDIDATE / CERTIFIED logic

Exit:
every proposed factor ends with a complete evidence packet.

Commit.

## Phase 4 - paper agent

Add:
- Qwen Portfolio Actor
- deterministic risk gate
- long/cash paper engine
- idempotency
- positions/equity
- 15m marks
- factor attribution
- decay/probation counters

Exit:
event -> Qwen decision -> risk -> paper execution -> ledger works unattended.

Commit immediately and start forward run.

## Phase 5 - product UX

Build final surfaces in this order:
1. Lab
2. Factor detail
3. Factors/Graveyard
4. Paper
5. Ledger
6. System
7. Proof

Do not start with a landing page.

## Phase 6 - evidence hardening

Add:
- evidence export
- restart test
- stale-data test
- no-lookahead tests
- Qwen failure tests
- duplicate execution test
- source outage fixture
- docs
- public README

## Phase 7 - demo/submission polish

- public deployment
- no login
- seeded "replay latest complete cycle" path if live worker happens to be idle
- exact demo script
- screenshots
- video
- X post
- form text

---

# 21. Deployment

## 21.1 V1

Frontend:
Vercel

Database:
Neon Postgres or equivalent managed Postgres

Hackathon scheduler/runtime:
GitHub Actions may run the research/paper jobs as idempotent one-shot Python commands because the core decision cadence is hourly/multi-hour. Persist all state in Postgres.

Optional API:
FastAPI may be deployed separately only if the read API cannot be served cleanly from Next.js.

Post-hackathon:
move the same job functions into an always-on worker/scheduler without changing research semantics.

Constraints:
- server location must reach Bitget APIs
- one worker scheduler owner
- Postgres advisory lock
- health endpoint
- automatic restart

## 21.2 Public demo

No login.

Public read endpoints.

Admin write endpoints protected by a long random token and not linked in UI.

## 21.3 Environment variables

- `DATABASE_URL`
- `BITGET_QWEN_API_KEY`
- `BITGET_QWEN_BASE_URL`
- `QWEN_MODEL`
- optional Bitget Demo credentials
- `ADMIN_TOKEN`
- execution mode
- protocol version

Never expose API secrets to Next.js public env vars.

---

# 22. Forward-run plan

Start as soon as Phase 4 passes.

## 22.1 Cadence

- research proposal: every 6 hours
- paper decision: every closed 1H bar
- paper mark: every 15 minutes
- source health: every 15 minutes
- decay review: daily
- evidence export: daily

## 22.2 Logs

Every paper decision must include:
- timestamp
- symbol
- factor
- side/action
- target weight
- observed price
- fill price
- quantity/notional
- fee
- slippage
- equity before/after
- Qwen reason
- risk verdict
- source timestamps

## 22.3 Baseline

Maintain one simple fixed-rule shadow book only if implementation is cheap.

Preferred baseline:
- simple 24h momentum long/cash
or
- buy-and-hold equal-weight rToken basket

Freeze baseline before comparing.

Do not add five baselines to manufacture a win.

---

# 23. Evidence plan

The product should be able to generate a judge pack automatically.

`scripts/export_evidence.py`

Output:

```text
evidence/latest/
  MANIFEST.json
  PREFLIGHT.json
  PROTOCOL.json
  UNIVERSE.json
  SOURCE_HEALTH.json
  RESEARCH_FUNNEL.json
  LATEST_CYCLE.json
  REJECTED_FACTOR.json
  SURVIVOR_FACTOR.json
  PAPER_SUMMARY.json
  PAPER_DECISIONS.csv
  PAPER_FILLS.csv
  PORTFOLIO_MARKS.csv
  RECOVERY_TEST.json
  NO_LOOKAHEAD_TEST.json
  IDEMPOTENCY_TEST.json
```

## 23.1 Evidence rules

- every claim in README must point to an artifact
- rejected factors remain
- do not delete bad forward trades
- historical and forward metrics are visually separated
- observed vs targeted metrics explicitly labeled
- no screenshot-only evidence if JSON/CSV can be provided
- all exported files carry `generated_at`

## 23.2 Integrity

`MANIFEST.json`:
- filename
- sha256
- generated_at
- protocol version
- git commit

The evidence event table is hash-chained.

This is reproducibility evidence, not an on-chain attestation claim.

---

# 24. Test plan

## 24.1 DSL

- arbitrary code rejected
- unknown fields rejected
- depth limit
- node limit
- invalid lookback rejected
- division safe
- canonical duplicate stable

## 24.2 Data

- current forming bar excluded
- duplicate timestamps removed or fail
- missing expected last regular close blocks factor
- volume primitive refuses pre-coverage region
- stale source blocks new exposure

## 24.3 Backtest

- same input gives same output
- no signal can fill on the bar that created it
- fee applied
- slippage applied
- OOS boundary fixed
- benchmark uses same eligible windows

## 24.4 Multiple testing

- every unique committed factor increments trial count
- duplicate does not rerun performance
- protocol amendment does not reset history

## 24.5 Qwen

- invalid JSON -> repair then abstain
- timeout -> HOLD
- unapproved symbol -> rejected
- unapproved weight -> rejected
- prompt/response stored

## 24.6 Risk

- risk can only reduce
- max symbol
- max factor
- max gross
- drawdown halt
- daily halt
- stale-data close-only

## 24.7 Paper idempotency

- same order key twice => one fill
- crash after intent before fill => reconcile
- crash after fill before response => existing fill returned
- no duplicate equity mutation

## 24.8 UI

- no login
- mobile no horizontal overflow
- state readable without color
- backtest and paper labels cannot be confused
- source timestamps visible
- proof links work

---

# 25. Judging strategy

## 25.1 What judges should understand first

Within 30 seconds:

"rTokens trade 24/7, but this market is new and easy to overfit. Our Qwen agent continuously invents factor hypotheses, but deterministic tests reject most of them. Survivors enter forward paper probation. Every decision is reproducible."

## 25.2 What makes the Agent real

Do not demo a chatbot conversation.

Show:
- autonomous scheduled cycle
- Qwen proposal
- immutable committed factor
- deterministic rejection/promotion
- Qwen portfolio action
- risk layer
- paper fill
- forward ledger

## 25.3 What makes the architecture credible

Show one rejected factor before the survivor.

The key visual:
`34 proposed -> 25 rejected -> 6 inconclusive -> 2 testing -> 1 paper probation`

A low pass rate is credible.

## 25.4 Quantitative story

Report only what exists.

If paper history is short:
- say so
- show exact number of decisions/trades
- prioritize drawdown, turnover, and integrity over annualized Sharpe theater
- separate historical factor metrics from forward paper metrics

---

# 26. Three-minute demo story

## 0:00-0:20

Open `/proof` or `/lab`.

Say:

"Bitget rTokens trade 24/7, but the market only has months of history. That makes factor mining useful and dangerous. This agent is built to search, reject, and only paper-deploy what survives."

Show:
- source health
- current session
- paper mode

## 0:20-0:50

Replay latest cycle.

Show Qwen's factor proposal:
- thesis
- session
- universe
- expression tree
- trial number

Say:
"Qwen originates the hypothesis. It cannot see a leaderboard of previous Sharpe scores."

## 0:50-1:20

Show the gate stack.

Use a rejected factor first.

Say:
"This one looked profitable gross and died after costs/OOS. It stays in the graveyard."

Then open survivor.

## 1:20-1:50

Show survivor historical evidence:
- fixed OOS boundary
- cost stress
- multiple-testing penalty
- factor proof

Say:
"Qwen cannot promote around these gates."

## 1:50-2:20

Open Paper.

Show:
- Qwen portfolio decision
- risk verdict
- exact factor attribution
- real Bitget market timestamp
- paper fill

Say:
"Execution is paper-only and marked to real Bitget market data. We do not pretend this is an rToken Demo fill."

## 2:20-2:40

Open Ledger.

Show:
- prompt hash
- snapshot hash
- idempotency key
- event hash
- restart evidence

Say:
"A restart cannot silently create a second decision or fill."

## 2:40-3:00

Close on Factors/Graveyard.

Say:
"The product gets more valuable over time because the library records what failed, what survived, and when factors decayed. After the hackathon, validated factors can export into Playbook or controlled Agentic Account execution."

---

# 27. Submission description structure

Use the official six-part structure.

## Part 1 - Thesis

Focus on:
- 24/7 rToken market structure
- short history
- overfit risk
- autonomous research/falsification
- deterministic risk control

## Part 2 - Target user

Use the exact primary user from section 2.

## Part 3 - Validation

Include:
- historical factor sample
- IS/OOS
- fees/slippage
- research funnel
- paper period
- paper trades
- drawdown
- turnover
- observed vs targeted usage

## Part 4 - Progress

Built / not built / problems found / fixes.

## Part 5 - Deliverables

Direct links.

## Part 6 - Take on AI trading

Core statement:
LLMs should originate and choose among hypotheses, but deterministic systems should own measurement, risk limits, idempotency, and financial state.

---

# 28. Explicit features not to build in V1

Do not build any of these until the core loop is complete:

- real-money execution
- wallet connection
- social login
- strategy marketplace
- copy trading
- Telegram bot
- X command bot
- native mobile app
- options
- perpetual leverage
- short selling
- custom smart contracts
- blockchain evidence anchoring
- multi-agent debate
- 500-symbol support
- full L2 historical simulation
- news-driven trading
- earnings NLP
- fundamental factor library
- manual drag-and-drop strategy builder
- Playbook upload
- Agentic OAuth execution
- user billing
- team workspaces
- notifications
- public comments
- gamification

If there is spare time after `/proof` is excellent, the first stretch feature is Playbook export, not social features.

---

# 29. Product roadmap after the hackathon

V1:
autonomous rToken factor research + forward paper portfolio

V2:
user research mandates

Example:
"Search semiconductor overnight factors with max 8% historical drawdown."

V3:
Playbook export of a validated factor

V4:
controlled Agentic Account execution with bounded capital

V5:
private research libraries for teams

V6:
multi-venue tokenized-equity research

The defensible asset is the growing evidence library:
- hypotheses
- failures
- factor versions
- historical tests
- forward behavior
- decay events
- execution/recovery records

---

# 30. Build acceptance criteria

V1 is complete only when all are true:

1. Public demo opens without login.
2. Real Bitget Reality data is visible with timestamps.
3. Qwen autonomously proposes a valid factor.
4. Proposal is persisted before evaluation.
5. Safe DSL rejects arbitrary code.
6. One real historical experiment runs end to end.
7. IS/OOS and costs are visible.
8. Trial counter exists.
9. Multiple-testing gate exists.
10. At least one rejected factor is visible in Graveyard.
11. Candidate/Certified logic is deterministic.
12. Qwen portfolio actor produces HOLD/OPEN/REDUCE/CLOSE.
13. Deterministic risk layer can veto or reduce.
14. Paper fill occurs only after the decision time.
15. Paper position names its factor.
16. Duplicate worker execution cannot create duplicate fill.
17. Stale market data blocks new exposure.
18. `/ledger` exposes prompt/snapshot/integrity hashes.
19. `/system` exposes source and worker health.
20. `/proof` tells the whole story in under three minutes.
21. `pytest` passes.
22. frontend lint/typecheck/build passes.
23. evidence export command works.
24. README does not claim unverified Demo or live execution.
25. every major observed metric has a reproducible artifact.

---

# 31. First Codex instruction

When implementation begins, Codex should receive the entire context folder plus this file.

The first coding prompt should be limited to Phase 0 and Phase 1.

Required behavior:
- read all context
- do not broaden scope
- create Git repo if not already present
- commit after each completed phase
- never commit secrets
- write findings into `docs/`
- keep a `BUILD_STATUS.md`
- run tests before every phase commit
- stop and report if live Bitget behavior contradicts this specification
- do not fake unavailable integrations
- do not create the polished UI before the tracer bullet works

Phase 1 is successful when one real Bitget dataset produces one reproducible factor experiment that can be opened in `/lab`.

---

# 32. Authoritative current sources

Bitget S2 handbook:
https://bitget-ai.gitbook.io/bitgetai_hackathons2

Bitget S2 landing page:
https://www.bitget.com/activity-hub/hackathon

Bitget Reality guide:
https://www.bitget.com/docs/uta/reality-trading-guide

Bitget UTA quick start:
https://www.bitget.com/docs/uta/quick-start

GetAgent skill:
https://www.npmjs.com/package/@bitget-ai/getagent-skill

Masayume:
https://github.com/Blockchain-Oracle/masayume

QuantConnect Research Pipeline:
https://www.quantconnect.com/docs/v2/cloud-platform/research-pipeline

Composer:
https://www.composer.trade/
