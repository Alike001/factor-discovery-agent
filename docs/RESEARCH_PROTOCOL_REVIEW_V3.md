# Research Protocol Review V3

## Decision

Final recommendation: `PROTOCOL_CAPABILITY_GAP_REMAINS`.

This was an offline protocol review. It made zero Qwen HTTP attempts, created zero hypotheses and trials, left global search N at 7, kept `fdp-v3-draft` inactive, and made no paper decision.

## Diagnosis and repair

The targeted batch asked Qwen to construct AST shapes whose economic semantics were not fully implemented. Schema-level operator support was mistaken for end-to-end capability. The repaired contract separates economic intent from execution:

1. Qwen emits `factor-recipe-v1`, never raw AST nodes.
2. `factor-recipe-compiler-v1` deterministically constructs validated AST.
3. The proposer prompt is generated from the same READY registry used by the compiler.
4. A family becomes READY only after compile and evaluation pass on offline golden fixtures.

Only `beta_residual` is READY. Cross-sectional ranking is NOT_READY because selection, basket holdings, attribution, and leave-one-symbol-out mechanics do not exist. Session transition is NOT_READY because exact expected anchors and `MISSING_EXPECTED_ANCHOR` execution semantics are not implemented. Generic dispersion and `spread_bps` are also hidden.

## Offline proof

Three beta-residual recipes compiled deterministically and evaluated without exceptions on fixed synthetic OHLC fixtures. Every repeated compilation produced the same recipe and AST hashes. Fixtures create no search trials.

The generated proposer prompt:

- exposes only `beta_residual` and legal recipe parameters;
- contains one valid recipe example;
- contains no raw AST grammar or unsupported primitive;
- is estimated at 464 input tokens using `ceil(characters / 4 × 1.25)`, below the 1,500-token target.

The draft uses schema `factor-recipe-v1`, compiler `factor-recipe-compiler-v1`, and prompt schema `factor-recipe-prompt-v1`.

## Hard-budget semantics

`postgres-conservative-pre-call-reservation-v1` persists reservations before each HTTP attempt.

- Estimated input: `ceil(characters / 4 × 1.25)`.
- Reserved input: the greater of that estimate and UTF-8 byte length.
- Reservation: reserved input plus maximum completion tokens.
- Admission: charged usage + outstanding reservations + proposed reservation must not exceed the hard limit.
- Measured responses replace reservations with actual usage.
- UNMEASURED responses charge the full reservation.
- A repair is a separately admitted attempt.
- PostgreSQL advisory and row locks serialize concurrent admission.
- Insufficient capacity returns `NO_RUN_PROJECTED_BUDGET_EXHAUSTED` before network activity.

Tests cover normal, maximum-reservation, unmeasured, repair, refusal, and concurrent admission paths.

## Draft status and limitations

`fdp-v3-draft` preserves the existing costs, evidence thresholds, provenance, lifecycle, and `rtoken-session-alpha-v1` search program. It records current N=7 and is explicitly inactive.

Remaining gaps:

- FactorRecipe transport has not been live-tested because this phase prohibited Qwen calls.
- Cross-sectional portfolios need real selection, holdings, symbol attribution, and robustness mechanics.
- Session transitions need exact calendar anchors and fail-closed missing-anchor evaluation.
- The 1,200-token draft completion cap is proposed from compact schema size but is not yet live-demonstrated.
- Beta residual currently supports one target and one reference, not a general multi-target residual portfolio.
