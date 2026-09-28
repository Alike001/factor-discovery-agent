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

## Targeted fdp-v2 batch — stopped at hard budget, paper trading not started

- Frozen `BATCH_PLAN.json` before the first Qwen request; immutable `fdp-v2` belongs to global search program `rtoken-session-alpha-v1` with `fdp-v1`.
- Slot A became search trial 6 and Slot B became search trial 7; both remained structurally invalid after their single permitted repair and were rejected at Syntax.
- Two proposer calls plus repairs consumed 4 HTTP attempts and 26,090 measured tokens. The second atomic response crossed the 25,000-token cap by 1,090.
- Slot C was recorded as `NO_RUN_BUDGET_EXHAUSTED`; no hypothesis or replacement trial was fabricated.
- Search N advanced honestly from 5 to 7, not the planned 8.
- Outcomes: 2 rejected, 0 candidate, 0 certified; diversity acceptance failed.
- Final recommendation: `RESEARCH_PROTOCOL_REVIEW`.
- No lifecycle Qwen calls, paper portfolio, orders, fills, or paper execution occurred after the hard-budget stop.

## Research protocol review — complete, fdp-v3 remains inactive

- Replaced Qwen-authored raw ASTs with `factor-recipe-v1` plus deterministic `factor-recipe-compiler-v1`.
- Capability registry and generated prompt expose only end-to-end READY recipes.
- READY: `beta_residual`; three compile/evaluate golden fixtures pass.
- NOT_READY: cross-sectional rank/baskets, session transitions, dispersion, and spread-bps reference semantics.
- Added persistent conservative pre-call reservations with projected-overspend refusal and concurrent admission locking.
- Generated proposer prompt is estimated at 464 tokens; draft completion cap is 1,200 tokens but remains live-unverified.
- `fdp-v3-draft` is not active. Global search N remains 7.
- Qwen HTTP attempts in this review: 0. Paper trading remains unstarted.
- Recommendation: `PROTOCOL_CAPABILITY_GAP_REMAINS`.

## Session-transition capability closure — complete, fdp-v3 remains inactive

- Frozen `session-transition-v1` before evaluation; exact 15-minute, DST-aware `America/New_York` anchors have zero timestamp tolerance and no fallback.
- `factor-recipe-compiler-v2` compiles safe `session_transition` recipes; READY families are now `beta_residual` and `session_transition`.
- Eight valid EST/EDT fixtures and nine fail-closed fixtures pass.
- Real RNVDA architecture tracer: 7 expected events, 7 valid anchors, 0 missing anchors, 0 signals/fills, and 0 lookahead violations; the fixed threshold was not tuned.
- Qwen HTTP attempts in this phase: 0. Global search N remains 7. The tracer created no trial and is excluded from promotion and DSR.
- Cross-sectional rank/baskets, dispersion, and spread-bps remain NOT_READY.
- `fdp-v3-draft` is not active. Paper trading remains unstarted.
- Recommendation: `READY_FOR_FDP_V3_BATCH`.

## FDP-v3 controlled discovery — complete, no paper trading

- Activated immutable `fdp-v3` and froze exactly two slots before Qwen traffic; protocol hash `08c088b3f366b2a269a3193e3b8671e0480b6f351f967c3f554a86d37c2d6d46`.
- Global search N advanced honestly from 7 to 9 without resetting earlier protocols.
- Slot A produced a valid compiled beta-residual recipe and was rejected: FIRST_HARD_FAIL Stability; DSR FAIL at 0.629643, permutation FAIL, baseline FAIL, and zero OOS fills.
- Slot B was rejected at Syntax. Its initial session-transition response was invalid, and the repair was refused before HTTP because its projected reservation could not fit the hard budget.
- Qwen accounting: 3 logical calls, 5 HTTP attempts, 8,804 measured/charged tokens against 14,000; every attempt was pre-reserved.
- Outcomes: 0 candidates, 0 certified. No hidden replacement, revision child, third slot, paper activity, or follow-on research batch occurred.
- Recommendation: `PRODUCT_HARDENING_NO_CANDIDATE`.

## Product hardening — complete, frozen evidence product

- Final navigation: Lab, Factors, Paper, Ledger, System; judge story at `/proof`; Trial 8 stored-evidence replay at `/replay`.
- Search N remains 9; discovery is CLOSED; Candidate and Certified counts remain zero.
- Paper engine is `LOCKED_NO_CANDIDATE`; capital, positions, orders, and fills remain zero.
- Public evidence includes required summaries, Trial 8/9 proof, search budget, capabilities, source health, a sanitized 190-event ledger, replay, and hashed manifest.
- Trial 8's rationale/recipe mismatch is preserved; structured recipe fields alone define execution.
- Public mode is `READ_ONLY_EVIDENCE_SNAPSHOT`; live execution is disabled and no managed database is claimed.
