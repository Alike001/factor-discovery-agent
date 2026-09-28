# Build Status

## Phase 0 — complete

- Public Reality research gate: `PASS_WITH_LIMITATIONS` / Phase 1 `GO`.
- Core universe: RNVDA, RAAPL, RTSLA, RMSFT, RAMZN, RMETA, RAMD, RQQQ (USDT pairs).
- Stock MCP: degraded (`Too many open sessions`), removed from Phase 1 dependency.
- Qwen: `BLOCKED_KEY`.
- Fee: `ACCOUNT_FEE_UNVERIFIED`; 0.05% per-fill baseline assumed and labeled.
- Demo: unverified; execution mode locked to `local_paper`.
- Database: unverified; deployment architecture remains one-shot GitHub Actions jobs + Neon.
- Local verification uses Python 3.14 because Python 3.12 is unavailable; metadata targets Python 3.12.

## Phase 1 — complete

- Real Bitget Reality data path completed: RNVDA + RQQQ closed 1H candles -> normalized snapshot -> FactorSpec -> deterministic evaluation -> evidence JSON -> `/lab`.
- Tracer verdict: failed costs; OOS inconclusive; never eligible for promotion.
- Evidence: `evidence/tracer/tracer-experiment.json`.
- Frontend: root redirect and Lab-only App Router product surface.
- Execution remains `local_paper`; Phase 1 does not place paper or real orders.
- Verification: 15 Python tests pass; frontend lint and production build pass; npm audit reports zero vulnerabilities.

## Stop point

Phase 3 is complete. Further autonomous discovery and paper trading await review.

## Phase 1.5 — complete, Phase 2 GO

- Reality counts verified: 3,169 total SPOT; 2,587 Reality; 2,587 online Reality.
- Pre-public-launch candles are inherited/ambiguous endpoint history and excluded from certification.
- Per-field `valid_from` enforcement added; tracer-v2 begins at 2026-06-02 UTC.
- Gap semantics now separate expected closures from expected-open missing bars.
- Volume and turnover DSL features remain disabled.
- PostgreSQL 16 persistence gate passes locally with migrations, concurrent trial allocation, deduplication, idempotency, and append-only lifecycle tests.
- Qwen final runtime gate passes 3/3 with zero repairs. FactorProposal uses `/chat/completions` with low reasoning and JSON object mode; lifecycle and portfolio keep `/responses`.
- Fees remain assumed; Demo remains unverified; execution remains `local_paper`.
- Phase 2 subsequently completed in its own implementation commit; paper trading remains unstarted.

## Phase 2 — complete, paper trading not started

- Frozen immutable research protocol: `fdp-v1`.
- Five autonomous Qwen cycles produced five unique committed trials on real Bitget Reality data.
- Outcomes: 5 rejected, 0 inconclusive, 0 candidate, 0 certified.
- Qwen usage: 10 logical runs, 11 HTTP attempts, 18,224 measured tokens; one failed repair attempt is `UNMEASURED` and budgeted conservatively.
- Evidence hash chain: PASS across 107 events.
- Resume/idempotency: PASS; a post-commit cycle recovery did not recall the proposer.
- Lab, Factors/Graveyard, and factor proof pages render the real Phase-2 evidence.
- Paper portfolio, portfolio actor, orders, fills, and paper execution remain unstarted pending review.

## Phase 3 — complete, paper trading not started

- Frozen evidence method: `phase3-evidence-v3`; all statistical thresholds remained unchanged after results.
- DSR implemented from published equations across all 5 unique committed `fdp-v1` trials; search hurdle SR*=0.00271115516762 at N=5.
- Scope-aware four-block OOS stability and session-purity checks completed.
- Outcomes remain 5 rejected, 0 candidate, 0 certified; every FIRST_HARD_FAIL is Costs.
- Hardened gates: 22 PASS, 11 FAIL, 17 INCONCLUSIVE.
- Qwen HTTP attempts in Phase 3: 0. No new factor was generated.
- Research diversity audit covers 2 families, 5 targets, and 5 sessions; 4 trials repeat one operator pattern.
- Recommendation: `TARGETED_DISCOVERY_BATCH` after review, not paper probation.
- Paper portfolio, orders, fills, and all paper execution remain unstarted.
