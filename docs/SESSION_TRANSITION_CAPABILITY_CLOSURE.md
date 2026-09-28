# Session Transition Capability Closure

Status: complete on 2026-09-28. Final recommendation: `READY_FOR_FDP_V3_BATCH`.

This phase made no Qwen request, created no research trial, did not activate `fdp-v3-draft`, and did not start paper trading. Total recorded Qwen HTTP attempts remained 15 and global search N remained 7.

## Frozen contract

- Version: `session-transition-v1`
- Hash: `3663cf1d7cd843b9a630d4d8c9c9ad7dc6f3f788270e97474b3e6ab2def687fa`
- Anchor resolution: exact 15-minute candles
- Time zone: `America/New_York`, including historical DST conversion
- Timestamp tolerance: zero milliseconds
- Feature: `to_anchor.close / from_anchor.close - 1`
- Observability: only when the destination anchor closes
- Earliest execution: the next exact 15-minute bar open
- Fallback for missing anchors: forbidden

The contract was written and the `SESSION_TRANSITION_CONTRACT_FROZEN` event was appended before either golden evaluation or real-history replay.

Supported adjacent transitions are:

- `after_hours_to_overnight`
- `overnight_to_pre_market`
- `pre_market_to_regular`
- `regular_to_after_hours`

Affected holidays, weekends, Friday 20:00 transitions, unavailable calendar coverage, forming bars, missing exact anchors, and a missing next executable bar all fail closed.

## Executable path

`SessionTransitionRecipe` accepts only an approved transition, transition-return feature, normalization/lookback, threshold, continuation or reversion direction, and bounded execution parameters. It contains no raw AST. `factor-recipe-compiler-v2` deterministically emits the safe `transition_return` operator and comparison nodes. The evaluator enumerates calendar events, resolves exact anchors, delays observability through the destination-bar close, executes next-bar only, and applies the existing 0.05% fee plus 0.025% slippage per fill without modification.

The inactive `fdp-v3-draft` now exposes exactly two READY families: `beta_residual` and `session_transition`. Cross-sectional rank/baskets, dispersion, and spread-bps remain NOT_READY and absent from the generated proposer prompt.

## Verification evidence

All eight valid golden fixtures passed: four transitions in both EST and EDT. All nine adverse fixtures passed: missing source anchor, missing destination anchor, holiday closure, weekend unavailability, DST-transition week, forming destination anchor, stale calendar coverage, absent exact boundary, and no next executable bar.

The non-search `SESSION_TRANSITION_ARCHITECTURE_TRACER` used 999 closed public Bitget RNVDA 15-minute candles from 2026-09-17 06:00 UTC through 2026-09-28 09:30 UTC. It found seven expected events, seven valid anchor pairs, zero missing anchors, and zero lookahead violations. The fixed pre-market-to-regular z-score recipe generated zero signals and therefore zero fills and zero cost. This result was preserved without parameter tuning; the tracer is not a trial, cannot be Candidate or Certified, and is excluded from the DSR population.

The generated two-family prompt is estimated at 886 input tokens. The persistent PostgreSQL conservative pre-call reservation policy remains unchanged. The final evidence chain passes with 152 events and head `a5ce6e68eca2452bbbebd6085d7d4d57a23ef9f76304c9dae62f90c954872d1d`.

## Remaining limitations

- The real-history tracer demonstrated exact feature construction but produced no executed trades under its fixed threshold; next-bar costed execution is covered by deterministic golden fixtures.
- Calendar correctness depends on the live Bitget Reality calendar coverage window. Events outside it fail closed.
- Session-transition certification still requires a future search batch and the unchanged statistical gates; capability readiness is not evidence of alpha.
- Fee remains the assumed published baseline, not an authenticated account fee.
- `fdp-v3-draft` remains inactive and paper trading remains off.

Machine-readable evidence is under `evidence/capability-closure-v4/`.
