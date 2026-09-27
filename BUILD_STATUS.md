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

## Phase 1 — cleared to start

The public Reality candle gate has no hard blocker. The tracer must use timestamp intersections and no forward-filling.
