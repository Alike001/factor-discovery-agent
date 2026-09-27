# Codex Kickoff Prompt — Phase 0 + Phase 1 Only

Paste this prompt into Codex from the EMPTY project folder.

---

We are building a Bitget AI Base Camp S2 Agentic Trading / Factor Discovery product.

The current working deadline is October 8, 2026 at 23:59 UTC+8, confirmed by the live official submission form.

You have a context package named `bitget-agent-hub-context-v8`. Read it before writing code.

Read these files first, in this exact order:

1. `00_README_V8.md`
2. `20_HOSTILE_FACTOR_DISCOVERY_FEASIBILITY.md`
3. `21_DIRECTION_DECISION_AFTER_HOSTILE_PASS.md`
4. `22_UX_RESEARCH_AND_DESIGN_DIRECTION.md`
5. `23_FINAL_BUILD_SPEC.md`
6. `24_PHASE0_PREFLIGHT.md`

Then use earlier files only when those six reference them.

The product direction is frozen:

An autonomous Qwen researcher for Bitget rTokens that proposes session-aware factor hypotheses, runs deterministic anti-overfit validation, rejects weak ideas, paper-trades survivors on real Bitget market data, and retires factors when forward evidence decays.

Do not broaden the product.

Do not add a landing page, social features, wallet UI, copy trading, games, generic chat, smart contracts, or real-money execution.

## Git rules

If this folder is not a Git repo:
- `git init`
- create `.gitignore`
- create `README.md`
- use `main`

Create `BUILD_STATUS.md`.

Commit after Phase 0.
Commit after Phase 1.

Use clear commit messages.

Never commit:
- `.env`
- API keys
- Bitget secrets
- Qwen secrets
- generated large market datasets

Small JSON evidence artifacts MAY be committed if they contain no secrets.

## Phase 0

Implement the actual live preflight described in `24_PHASE0_PREFLIGHT.md`.

Create:

```text
backend/
  app/
    config.py
    bitget/
    qwen/
    mcp/
    evidence/
  tests/
scripts/
docs/
evidence/preflight/
```

Use Python 3.12.

Recommended:
- httpx
- pydantic v2
- pytest
- python-dotenv only for local loading if needed

### Public Bitget checks

Call current official UTA v3 endpoints directly.

Do not rely on a copied S2 repo's cached response.

At minimum verify:
- SPOT instruments and `isReality`
- stock-info
- market states
- market calendar
- 1H candles
- recent 15m candles

Produce machine-readable preflight artifacts.

### Candle audit

For the core candidate universe:
NVDA, AAPL, TSLA, MSFT, AMZN, META, AMD, QQQ
then optionally SPY, COIN, HOOD, MSTR.

Select only symbols actually returned as online Reality instruments.

Measure:
- first timestamp
- last timestamp
- row count
- gaps
- duplicates
- volume non-empty coverage
- most recent closed candle

Do not silently forward-fill missing bars.

### Stock MCP

Connect to:
`https://agent.bitget.com/mcp`

Discover its live tool schema first.

Do not hardcode a tool name from memory.

Test:
- one current quote
- one historical query
for NVDA and AAPL.

If it fails or the timestamp semantics are unclear:
mark the capability degraded and keep Phase 1 rToken-only.

### Qwen

Use:
- base URL `https://hackathon.bitgetops.com/v1`
- model `qwen3.8-max`
- key from `BITGET_QWEN_API_KEY`

Never print or persist the key.

Test three strict local schemas:
- FactorProposal
- LifecycleDecision
- PortfolioDecision

Ask the model to return JSON only.
Validate locally with Pydantic.

Do not assume the provider supports OpenAI JSON-schema response format until proven live.

If the key is missing:
record BLOCKED_KEY and continue public-data preflight.
Do not fake a model result.

### Fee

If Bitget authenticated credentials are present, call UTA account fee-rate for one live rToken SPOT symbol.

If no credentials:
record ACCOUNT_FEE_UNVERIFIED and use 0.05% baseline in Phase 1, clearly labeled ASSUMED_PUBLISHED_BASELINE.

### Demo

Only if Demo credentials are configured.

Probe Reality spot using `paptrading: 1`.

Record the exact outcome.
If unsupported, set:
`EXECUTION_MODE=local_paper`.

A Demo failure is NOT a Phase 0 failure.

### Deployment architecture

For this hackathon, implement research/paper jobs as idempotent one-shot commands suitable for GitHub Actions + Neon.

Do not introduce Celery.

### Required Phase 0 artifacts

```text
evidence/preflight/
  reality-universe.json
  core-universe.json
  candle-coverage.json
  reality-stock-info.json
  market-states.json
  market-calendar.json
  stock-mcp.json
  qwen.json
  fees.json
  reality-demo.json
  preflight.json
```

If a capability cannot be tested, still write the artifact with explicit BLOCKED / UNVERIFIED status.

Write:
`docs/PHASE0_DECISION.md`

Summarize what was measured, not what was expected.

Update `BUILD_STATUS.md`.

Run tests.

Commit:
`chore: complete Bitget Phase 0 preflight`

Stop and show me the Phase 0 report before you change the product spec materially.

## Phase 1

Only proceed if Phase 0 has no hard blocker to real public Reality candle research.

Build one vertical tracer bullet.

### Backend

Implement:
- normalized candle model
- data snapshot
- safe JSON AST FactorSpec
- parser/validator
- one hardcoded tracer factor
- deterministic backtest
- fixed IS/OOS split
- fee/slippage cost layer
- gate report
- evidence JSON export

Tracer factor:
`Overnight Relative Return Z-Score`

The tracer exists only to prove architecture.
Do not optimize parameters.
Do not call it discovered alpha.

No arbitrary Python factor code.

### Frontend

Create a Next.js App Router application.

Root redirects to `/lab`.

Build ONLY the Lab page needed for the tracer bullet.

The page must show:
- `PAPER · REAL BITGET MARKET DATA`
- source timestamp
- tracer factor thesis
- human-readable factor expression
- IS/OOS boundary
- gross vs net metrics
- cost assumption
- PASS / FAIL / INCONCLUSIVE gate rows
- link to raw evidence JSON

Use the UX rules in `22_UX_RESEARCH_AND_DESIGN_DIRECTION.md`.

Do not spend Phase 1 on full visual polish.

### Tests

At minimum:
- forming candle cannot be used
- duplicate timestamps detected
- FactorSpec rejects unknown operators
- future/lookahead field impossible
- signal cannot fill on its own decision candle
- fee changes net performance
- OOS boundary fixed
- same input -> same output

### Phase 1 exit

A browser page must display a real Bitget-data experiment from end to end.

The data path must be:

Bitget Reality
-> normalized dataset
-> FactorSpec
-> deterministic evaluation
-> evidence artifact
-> `/lab`

Commit:
`feat: complete Reality factor tracer bullet`

Update `BUILD_STATUS.md`.

Then stop.

Report:
- exact commit hashes
- test output
- build output
- preflight status
- selected core universe
- tracer metrics
- limitations
- anything that contradicted the specification

Do not start Phase 2 until I review the output.
