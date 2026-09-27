# Phase 1.5 — Data Integrity, Credentials, and Persistence Gate

Snapshot: 2026-09-27

This phase exists because Phase 0/1 succeeded technically but surfaced several facts that must be resolved before autonomous Qwen research begins.

Do NOT begin Phase 2 until this file's exit criteria pass.

## Phase 0/1 facts carried forward

Phase 0 commit:
`1ac574ee14936254eede23fcd9aa4535fa9c263f`

Phase 1 commit:
`1dd13a99bf7b74001711e4c2f145e33e1320fc90`

Current tracer:
- 2,497 aligned hourly observations
- gross return: -10.03%
- net return: -13.21%
- IS net return: -7.06%
- OOS net return: -6.62%
- max drawdown: -16.24%
- 48 fills
- 16 OOS fills
- zero same-decision-candle fill violations

This tracer is architecture evidence only. It is not alpha.

## Why Phase 1.5 is necessary

### A. Reality count anomaly

The Phase 0 report says 2,587 Reality instruments were returned live.

Bitget's public rToken product page currently advertises 500+ tradable assets.

This may mean:
- 2,587 is the full SPOT instrument count before `isReality=yes` filtering;
- the endpoint now contains far more Reality instruments than the public product page;
- or the preflight report is labeling the count incorrectly.

We must resolve this with raw evidence.

### B. Pre-public-launch candle history

Phase 0 reports RNVDA has ~157.74 days of hourly history.

Bitget publicly launched Stocks 2.0 / rToken on June 2, 2026.

A 157-day lookback from Sep 27 reaches late April.

The existence of older API candles does NOT prove those bars were publicly tradable rToken history.

Possible explanations:
- prelaunch/internal Reality history
- inherited predecessor-product history
- synthetic/reference backfill
- early limited trading
- legitimate instrument history before broad public launch

Until provenance is established, bars before June 2 must not be used for certification.

### C. Volume semantics

Docs state pre-July-9 Reality volume/turnover may be empty and were not backfilled.

The preflight instead saw non-empty volume on every retrieved hourly row.

That can be legitimate if:
- endpoint semantics changed;
- the selected history starts after July 9;
- older rows came from another market lineage;
- fields are present but not true rToken trade volume.

Therefore volume must remain disabled in the factor DSL until provenance is tested.

### D. Qwen unavailable

`Qwen: BLOCKED_KEY`

Phase 2 cannot begin without Qwen because the Agentic Trading thesis requires the model to originate hypotheses and later make portfolio decisions.

### E. Persistent state unavailable

Database is unverified.

Autonomous research cannot safely begin without persistent:
- trial counter
- factor identity
- proposal ledger
- lifecycle state
- Qwen run records
- idempotency keys

Neon/Postgres must be live before Phase 2.

---

# 1. Reality universe audit

Re-fetch raw:

`GET /api/v3/market/instruments?category=SPOT`

Save complete raw response outside Git if very large.

Produce a summary artifact with these exact counts:

- `total_spot_count`
- `is_reality_yes_count`
- `is_reality_no_count`
- `status_online_and_reality_count`
- `symbol_type_stock_and_reality_count`
- `unique_base_coin_count`

Also list the first 25 and last 25 Reality symbols lexicographically.

Assertions:
- every selected core symbol must have `isReality == "yes"`
- every selected core symbol must have `status == "online"`
- selected symbol must map to expected `baseCoin`

Write:
`evidence/preflight-v2/reality-count-audit.json`

If `is_reality_yes_count == 2587`, preserve that result exactly and flag the public-page mismatch as documentation drift.
If not, fix `docs/PHASE0_DECISION.md` and any UI copy that says 2,587 Reality instruments.

---

# 2. History provenance audit

For each core symbol:

- record instrument `launchTime`
- first returned 1H candle
- first returned 15m candle where feasible
- first non-empty volume candle
- first weekend candle
- first candle on/after 2026-06-02T00:00:00Z
- first candle on/after 2026-07-09T00:00:00Z

Compute:

- `first_candle_before_instrument_launch`
- `first_candle_before_public_rtoken_launch`
- number of hourly bars before June 2
- number of hourly bars after June 2
- number of bars before July 9 with non-empty volume

Write:
`evidence/preflight-v2/history-provenance.json`

Do not infer provenance from the numbers alone.

For V1 certification, freeze:

`certification_start = max(
    2026-06-02T00:00:00Z,
    symbol-specific public/online start if later
)`

If evidence later proves a later launch for a symbol, use the later date.

For any volume-dependent factor:

`volume_start = max(certification_start, 2026-07-09T00:00:00Z)`

unless Bitget provides authoritative evidence that earlier values are genuine rToken trade volume.

The backtester must support a per-field `valid_from`.

---

# 3. Session integrity audit

Use Bitget Reality market state/calendar plus IANA `America/New_York`.

Create deterministic session labels:
- pre_market
- regular
- after_hours
- overnight
- weekend
- closed/holiday

Do not rely on the API string `EST` for DST arithmetic.

For 50 randomly selected historical timestamps, compare:
- our IANA classification
- expected market calendar behavior

No randomness in test fixtures. Use a fixed fixture list committed to the repo.

Required fixtures:
- June 2
- July 3 holiday
- Friday 16:00 ET boundary
- Friday 20:00 ET
- Saturday
- Sunday
- Monday pre-market
- September DST date

Add regression:
If a factor requires an underlying anchor and the expected session's bar is missing, return `MISSING_EXPECTED_ANCHOR`. Never fall back to an older bar.

---

# 4. Gap semantics audit

The Phase 0 report says raw gaps are substantial and symbol-dependent.

For each core symbol calculate:
- expected 1H bars by session/calendar
- actual bars
- missing bars during expected tradable periods
- intentional closures
- longest unexplained gap
- percent completeness after certification_start

Do NOT judge gaps by 24/7 wall-clock continuity if the symbol is not expected to print every hour.

Classify:
- `EXPECTED_CLOSED`
- `EXPECTED_OPEN_MISSING`
- `OBSERVED`

Factor engine behavior:
- expected closed period is not missing data
- expected open missing data is missing data
- no forward fill across expected-open missing gaps

Write:
`evidence/preflight-v2/gap-semantics.json`

---

# 5. Volume audit

For each core symbol:
- inspect base volume
- inspect quote turnover
- detect zeros vs null/empty
- summarize distribution before/after July 9
- compare obvious regular-session vs overnight scale

Do not make a market-quality conclusion yet.

V1 rule:
- leave volume operators disabled in the Qwen Factor DSL until this audit is reviewed
- Phase 2 proposals may only use OHLC/session/cross-asset price features initially

---

# 6. Qwen key gate

Before Phase 2, configure locally:

`BITGET_QWEN_API_KEY`

Never send the value in chat.
Never commit it.
Never print it.

Re-run the three probes:
- FactorProposal
- LifecycleDecision
- PortfolioDecision

Save redacted results:
`evidence/preflight-v2/qwen.json`

Pass:
- 3/3 schema-valid after <=1 repair
- model returned is recorded
- latency recorded
- raw response stored without secrets

If provider accepts another exact model name than expected, record the observed model and amend spec.

Phase 2 remains BLOCKED until Qwen PASS.

---

# 7. Postgres/Neon gate

Create the database now.

Implement migrations for only the Phase-2 minimum:

- `research_protocols`
- `research_cycles`
- `data_snapshots`
- `qwen_runs`
- `hypotheses`
- `factor_versions`
- `experiments`
- `gate_results`
- `factor_lifecycle_events`
- `evidence_events`

Paper tables can wait for Phase 4.

Required constraints:
- research cycle number unique
- factor canonical hash unique per protocol where appropriate
- trial number unique and monotonically allocated
- evidence sequence unique
- lifecycle transitions append-only

Create integration tests against a disposable Postgres database where feasible.

Test:
- two concurrent trial-number allocations cannot return same number
- duplicate canonical factor does not create a second experiment
- rerunning the same cycle job is idempotent

Neon credentials remain `.env` only.

Write:
`evidence/preflight-v2/database.json`

Phase 2 remains BLOCKED until DB PASS.

---

# 8. Fee and Demo status

Fees:
Not a Phase-2 blocker.

Keep:
`0.05% per fill = ASSUMED_PUBLISHED_BASELINE`

until account-specific fee endpoint is available.

Demo:
Not a Phase-2 blocker.

Keep:
`EXECUTION_MODE=local_paper`

until Reality Demo is personally verified.

Do not spend more than 30 minutes on Demo during Phase 1.5.

---

# 9. Amend the tracer dataset

Re-run Phase 1 tracer with:

`start >= certification_start`

Do not change factor parameters.

Generate:
`evidence/tracer-v2/tracer-experiment.json`

Compare v1 vs v2:
- sample count
- gross/net
- OOS
- fill count
- drawdown

The performance does not need to improve.

Purpose:
prove the engine can enforce evidence provenance windows.

If the tracer becomes worse, keep the worse result.

---

# 10. Phase 1.5 exit criteria

PASS only when:

- Reality count labeling is correct
- certification history begins no earlier than trusted public availability
- per-field valid_from exists
- gap semantics distinguish closure from missing
- volume remains disabled or is explicitly proven
- Qwen PASS
- Postgres PASS
- tracer-v2 honors certification_start
- worktree clean
- all tests pass

Stock MCP may remain DEGRADED.

Account fee may remain UNVERIFIED.

Reality Demo may remain UNVERIFIED.

Then Phase 2 may start.

---

# 11. Required report

Write:
`docs/PHASE1_5_INTEGRITY.md`

It must include:
- corrected Reality counts
- launchTime vs first-candle table
- trusted certification start by symbol
- gap-completeness table
- volume decision
- Qwen result
- DB result
- fee basis
- Demo status
- tracer-v1 vs tracer-v2
- spec amendments
- Phase 2 GO / NO-GO

Commit:
`chore: validate Reality research integrity`
