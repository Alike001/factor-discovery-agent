# Phase 2 Autonomous rToken Factor Research

Snapshot: 2026-09-28

## Decision

Phase 2 is complete. Five autonomous Qwen research cycles ran against trusted Bitget Reality data. All five factors were rejected by deterministic historical gates. This zero-survivor result is retained without changing thresholds. Paper trading has not started.

## Frozen protocol

Protocol `fdp-v1` freezes the core eight-symbol Reality universe, June 2 certification floor, OHLC/session-only inputs, disabled volume, safe AST limits, fixed lookbacks and thresholds, 30-day OOS rule, assumed 0.05% fee plus 0.025% slippage per fill, deterministic permutation seed, global trial semantics, and Qwen budget.

The live budget was capped at 20 HTTP attempts and 50,000 tokens. Phase 2 used 11 attempts and 18,224 measured tokens. The failed first half of one repaired lifecycle request did not retain provider usage, so it is explicitly `UNMEASURED` and conservatively charged 900 tokens; budget consumption is therefore 19,124. No reasoning content was stored or displayed.

## Qwen runtime

| Role | Model | Endpoint/profile | Attempts | Input | Output | Reasoning | Total |
|---|---|---|---:|---:|---:|---:|---:|
| Proposer | `qwen3.8-max` | `/chat/completions`, low reasoning, JSON object, 2,400 max | 5 | 4,875 | 5,886 | 4,454 | 10,761 |
| Lifecycle | `qwen3.8-max` | `/responses`, verified lifecycle profile | 6 | 4,898 | 2,565 | 2,126 | 7,463 |

There were ten logical calls. Cycle 2's lifecycle response required the one permitted repair, producing eleven HTTP attempts overall. The failed attempt's token usage is `UNMEASURED`, never zero. There were no empty-final-content failures.

## Autonomous trials

| Trial | Factor | One-line thesis | Result |
|---:|---|---|---|
| 1 | Overnight relative mean reversion RNVDA vs RQQQ | Positive overnight NVDA-vs-QQQ return divergence may mean-revert. | REJECTED |
| 2 | Weekend close-return reversal RAAPL vs RQQQ | A sharp negative weekend AAPL relative return may bounce during the following weekend bars. | REJECTED |
| 3 | Cross-rToken close divergence mean-reversion | Positive regular-session TSLA-vs-QQQ return divergence may revert. | REJECTED |
| 4 | Semiconductor after-hours relative momentum divergence | AMD after-hours relative strength versus NVDA may extend over a short horizon. | REJECTED |
| 5 | Pre-market relative momentum divergence RMSFT vs RQQQ | Microsoft pre-market relative strength versus QQQ may continue over subsequent bars. | REJECTED |

Lifecycle totals: 5 rejected, 0 inconclusive, 0 candidate, 0 certified. No duplicate appeared in the five live proposals.

## Gate results

Across 50 gate rows: 21 PASS, 10 FAIL, and 19 INCONCLUSIVE.

The main rejection pattern was honest rather than tuned:

- Four factors generated no qualifying fills under their proposed conditions and failed the positive-after-cost floor.
- Trial 1 traded, but returned -2.87% net, had only four OOS fills, failed its same-window baseline, and had a 2,000-draw permutation p-value of 0.5952.
- Exact Deflated Sharpe and the full symbol/session stability battery remain `INCONCLUSIVE_NOT_IMPLEMENTED`; neither is presented as green evidence, and certification is blocked.

## Persistence, recovery, and integrity

- Proposal and Qwen run are committed before evaluation.
- Trial numbers 1 through 5 were allocated transactionally.
- Canonical commutative equivalence and database duplicate-experiment tests pass.
- Duplicate proposals remain hypotheses but suppress a second performance experiment.
- Cycle 1 deliberately encountered a post-commit evaluator fault. Rerunning the same idempotency key resumed without recalling the proposer and returned the original manifest on subsequent rerun.
- PostgreSQL advisory lock allows one research owner.
- Evidence verification passes across 107 append-only events; chain head is `6b4362e6a48a8794ab3c7c6783286ccc7c008f30aa35798c05b7c7eae03b3252`.

## Product surfaces

- `/lab` shows the latest real autonomous proposal, fixed OOS boundary, historical metrics, full gate stack, and research funnel.
- `/factors` exposes all rejected factors in the Graveyard.
- `/factors/[id]` shows each factor's expression, data contract, metrics, gate reasons, and proof hashes.
- The UI explicitly says research-only and no paper positions. No Paper page, portfolio actor, orders, fills, or paper tables were added.

## Limitations

- Stock MCP remains degraded, so Phase 2 uses trusted Bitget rToken OHLC and cross-rToken references only.
- Volume remains disabled because provenance is unresolved.
- Account fee remains unverified; 0.05% is labeled an assumed published baseline.
- Reality Demo remains unverified and execution mode remains `local_paper`, though no paper execution occurs in Phase 2.
- The full cross-symbol/session stability battery and exact Deflated Sharpe are not implemented; both correctly block certification.
- Research evidence is exported from the persistent local PostgreSQL gate database. A managed Neon deployment is still required for public hosting.

## Recommendation

Do not begin Phase 4 paper trading yet. The next reviewed increment should be Phase 3 evidence hardening: complete stability/replication and Deflated Sharpe or another frozen, numerically validated multiple-testing method. Preserve the five rejected trials and global trial counter when advancing the protocol.
