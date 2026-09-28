# FDP-v3 Controlled Discovery Batch

Status: complete on 2026-09-28. Final recommendation: `PRODUCT_HARDENING_NO_CANDIDATE`.

## Frozen controls

- Protocol: `fdp-v3`
- Protocol hash: `08c088b3f366b2a269a3193e3b8671e0480b6f351f967c3f554a86d37c2d6d46`
- Search program: `rtoken-session-alpha-v1`
- Search N: `7 → 9`; protocol activation did not reset prior trials
- Frozen slots: A `beta_residual`, B `session_transition`
- Costs, IS/OOS split, DSR, stability, permutation, baseline, provenance, and next-bar mechanics remained unchanged
- Automatic revision children, hidden replacements, a third slot, and paper trading remained disabled

The immutable protocol activation and batch plan were appended as evidence events 153 and 154 before the first Qwen reservation or HTTP attempt.

## Model and budget accounting

- Logical Qwen calls: 3
- HTTP attempts: 5 of 6 maximum
- Measured tokens: 8,804
- Charged tokens: 8,804 of the 14,000 hard limit
- Cumulative reservation amounts: 21,292
- Maximum admitted `charged + outstanding reservation`: 13,730
- Outstanding reservations after closure: 0

Cumulative reservations can exceed the phase limit because unused reserved capacity is released at settlement. At every admission point, charged tokens plus the active reservation remained at or below 14,000. Slot B's proposed repair was refused before transport because its projected reservation would have exceeded that invariant.

Every HTTP request had a settled PostgreSQL reservation created first. Qwen database records retain only allowed metadata and hashes: prompt and response bodies are empty, parsed model content is not stored there, and no reasoning content is persisted.

## Slot A — beta residual

Search trial 8 produced a valid `factor-recipe-v1` recipe and compiled deterministically with `factor-recipe-compiler-v2`.

- Name: Semiconductor beta-residual mean reversion
- Thesis: When AMD's residual to QQQ diverges positively beyond its rolling norm, the dislocation tends to decay as sector-specific overpricing unwinds.
- Target/reference: `RAMDUSDT` / `RQQQUSDT`
- Session: regular
- Beta lookback: 120
- Signal lookback: 48
- Entry side: positive continuation
- Threshold: 1.5
- Horizon/rebalance: 48 / 12 hourly bars

Outcome: `REJECTED`. FIRST_HARD_FAIL: `Stability`.

- Coverage, syntax, point-in-time mechanics, and costs passed
- Net historical return after unchanged costs: 7.8369%
- OOS: inconclusive with zero OOS fills
- Stability: FAIL, `SESSION_PURITY_FAIL`
- Permutation: FAIL, p=0.2029
- DSR: FAIL, probability 0.629643 against the frozen 0.90 threshold at search N=9
- Baseline: FAIL; 7.8369% net versus 22.0073% same-window buy-and-hold
- Lifecycle: ABANDON after one repair; no revision child was created

The recipe's prose describes mean reversion while its executable enum requests positive continuation. The compiler correctly honored the structured enum. This semantic inconsistency is retained as a limitation rather than edited after results.

## Slot B — session transition

Search trial 9 did not produce a valid `FactorRecipe`. The initial model response was structurally invalid. The single permitted repair could not obtain a pre-call reservation within the remaining hard budget, so it was not sent.

Outcome: `REJECTED`. FIRST_HARD_FAIL: `Syntax` with `NO_RUN_PROJECTED_BUDGET_EXHAUSTED_AFTER_INVALID_OUTPUT`.

No compiled AST or deterministic market experiment exists for Slot B. Consequently transition anchor statistics, DSR, stability, signals, and fills are not applicable. No lifecycle call was made for this structural failure, and no replacement hypothesis or third slot was created.

## Final result

- Candidates: 0
- Certified: 0
- Evidence chain: PASS at 190 events, head `3393199128eccbffc99ff9554b205179202412c1eef4a484711390aec5fb216b`
- Paper trading: not started
- Additional research batch: not started

Machine-readable artifacts are in `evidence/fdp-v3-batch/`.

## Remaining limitations

- Only one of the two slots reached deterministic market evaluation.
- Slot A had no OOS fills and failed session purity, permutation, DSR, and baseline gates despite positive in-sample/net historical return.
- Slot B provides no transition-anchor evidence because it failed before compilation.
- The authenticated account fee remains unverified; evaluation retains the published 0.05% per-fill assumption plus frozen slippage.
- No factor is eligible for Paper under this batch outcome.
