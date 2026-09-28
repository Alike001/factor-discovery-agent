# Research Protocol Capability Matrix

The machine-readable source is `evidence/protocol-review-v3/capability-matrix.json`. `PROMPTED` means the capability may appear in the generated FactorRecipe prompt. Internal AST operators remain hidden from Qwen even when executable.

| Capability | Status | Prompted | Schema | Compiler | Evaluator | Data | UI | Reason |
|---|---|---:|---:|---:|---:|---:|---:|---|
| source | READY_INTERNAL | no | yes | yes | yes | yes | yes | Compiler emits closed-OHLC sources; Qwen cannot emit nodes. |
| ret | READY_INTERNAL | no | yes | yes | yes | yes | yes | Compiler-generated close returns are supported. |
| sma | READY_INTERNAL | no | yes | yes | yes | yes | yes | Executable, but no READY recipe requires it. |
| zscore | READY_INTERNAL | no | yes | yes | yes | yes | yes | Deterministically emitted by beta-residual compilation. |
| rank | NOT_READY | no | yes | no | no | yes | yes | Cross-sectional selection and portfolio semantics are missing. |
| group_mean | NOT_READY | no | yes | no | no | yes | yes | Scalar helper does not establish basket execution. |
| rolling_beta | READY_INTERNAL | no | yes | yes | yes | yes | yes | Supported inside deterministic residual evaluation. |
| residual | READY | yes | yes | yes | yes | yes | yes | Full recipe-to-evaluation path passes three fixtures. |
| spread_bps | NOT_READY | no | no | no | no | no | no | No point-in-time reference-price adapter. |
| abs | READY_INTERNAL | no | yes | yes | yes | yes | yes | Executable but hidden from recipe prompts. |
| sign | READY_INTERNAL | no | yes | yes | yes | yes | yes | Executable but hidden from recipe prompts. |
| clip | READY_INTERNAL | no | yes | yes | yes | yes | yes | Executable but hidden from recipe prompts. |
| add/sub/mul/div | READY_INTERNAL | no | yes | yes | yes | yes | yes | Safe arithmetic exists; Qwen cannot compose it directly. |
| session filter | READY | yes | yes | yes | yes | yes | yes | A single `America/New_York` session compiles and evaluates. |
| session transition | NOT_READY | no | yes | no | no | yes | yes | Exact phase anchors and fail-closed missing-anchor mechanics are absent. |
| multi-symbol references | READY_LIMITED | yes | yes | yes | yes | yes | yes | One target and one reference are supported for beta residual only. |
| universe/basket | NOT_READY | no | yes | no | no | yes | yes | Holdings, attribution, and leave-one-out semantics are absent. |
| dispersion | NOT_READY | no | yes | no | no | yes | yes | Scalar dispersion is not an executable portfolio definition. |

The Qwen-visible READY family is therefore only `beta_residual`. `cross_sectional_rank` and `session_transition` remain in the recipe schema for explicit rejection and future work, but are absent from generated prompts and rejected by the compiler.
