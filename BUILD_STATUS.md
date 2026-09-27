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

Phase 2 has not started. Awaiting review.
