# Phase 3 Evidence Hardening

## Decision

Phase 3 is complete. The recommendation is `TARGETED_DISCOVERY_BATCH`.

No existing factor qualifies for paper probation: all five autonomous `fdp-v1` trials first failed the cost gate, and all five remain terminally `REJECTED`. Phase 3 made zero Qwen HTTP attempts, generated no hypotheses, and started no paper trading.

## Frozen methods

The authoritative replay used method manifest `phase3-evidence-v3`, SHA-256 `4cadae3586196b315836f26651085ec73249e7ed6c6a086b5b69b676afe604ce`. Version 3 inherits the complete statistical policy and unchanged thresholds from the original pre-result freeze. It only corrects a diagnostic reason-string parser after an earlier pre-result abort.

The DSR implementation is derived from the published Bailey/López de Prado equations. It uses non-annualized per-eligible-bar strategy returns including flat bars, adjusted sample skewness, unbiased non-excess kurtosis, and the frozen 0.90 probability threshold. The search population is every unique committed autonomous `fdp-v1` trial: N=5. With expected mean Sharpe fixed at zero, cross-trial sigma=0.002273326182517314 and maxZ=1.192594001014789, the hurdle SR*=0.00271115516762.

Stability method `scope-aware-stability-v1` divides fixed OOS time into four contiguous calendar-time blocks. It requires at least three evaluable blocks, 60% payoff-sign agreement with full OOS, agreement between evaluable halves, and at most 60% absolute PnL contribution from one block. All five factors classify as `PAIR_RELATIVE_SESSION`; cross-symbol generalization was therefore not fabricated. Session purity was checked against the declared session using `America/New_York`.

## Replay integrity

The Phase 2 data manifest exposed a reproducibility defect: it did not persist the exact normalized merge after current recent candles were added. The first replay attempt aborted before producing factor results. A public-data recovery reconstructed that merge; every recovered records hash matched its persisted Phase 2 hash. The audit is in `evidence/phase3/recovery-audit.json`, while the recovered raw data remains gitignored.

A second attempt aborted before producing artifacts because the Phase 2 diagnostic string stored a permutation p-value with trailing punctuation. The parser was corrected and covered by a regression test. Both aborts and all method freezes remain in the append-only evidence chain. The single result-producing replay evaluated all five stored factors under v3 without modifying formulas, costs, splits, thresholds, or terminal lifecycle states.

## Results

| Trial | FIRST_HARD_FAIL | DSR | Probability | Stability |
|---|---|---|---:|---|
| 1 — Overnight relative mean reversion RNVDA/RQQQ | Costs | FAIL / DSR_THRESHOLD_NOT_MET | 0.3456345261 | PASS / STABILITY_THRESHOLDS_MET |
| 2 — Weekend close-return reversal RAAPL/RQQQ | Costs | INCONCLUSIVE / INCONCLUSIVE_DSR_NUMERICS | — | INCONCLUSIVE / INCONCLUSIVE_STABILITY_SAMPLE |
| 3 — Cross-rToken close divergence RTSLA/RQQQ | Costs | INCONCLUSIVE / INCONCLUSIVE_DSR_NUMERICS | — | INCONCLUSIVE / INCONCLUSIVE_STABILITY_SAMPLE |
| 4 — After-hours momentum divergence RAMD/RNVDA | Costs | INCONCLUSIVE / INCONCLUSIVE_DSR_NUMERICS | — | INCONCLUSIVE / INCONCLUSIVE_STABILITY_SAMPLE |
| 5 — Pre-market momentum divergence RMSFT/RQQQ | Costs | INCONCLUSIVE / INCONCLUSIVE_DSR_NUMERICS | — | INCONCLUSIVE / INCONCLUSIVE_STABILITY_SAMPLE |

Trial 1 had 3/4 evaluable blocks. Trials 2–5 produced no completed OOS fills, so their return variance and temporal sample were insufficient; those results remain explicitly inconclusive rather than fabricated failures or passes.

Across 50 hardened gate rows: PASS 22, FAIL 11, INCONCLUSIVE 17. The full measured-value matrix is documented in `docs/PHASE3_REJECTION_MATRIX.md` and `evidence/phase3/rejection-matrix.json`.

## Structural diversity

The audit used proposal structure only and no performance fields. The five trials cover five targets and five sessions, but only two families (`mean_reversion`, `continuation`). Four trials share the same operator multiset. Nearest-neighbor Jaccard similarity ranges from 0.625 to 0.6471. This supports a later, deliberately structurally diversified research batch rather than paper probation for a rejected factor.

## Limitations

- Four trials have zero OOS fills, leaving both DSR and stability inconclusive.
- N=5 is a small search population; the hurdle will evolve with future committed trials.
- The Phase 2 exact normalized merge had to be reconstructed from public Bitget candles. Hash equality verifies the reconstruction, but future cycles should persist the complete normalized dataset at evaluation time.
- Fee remains the explicitly assumed published baseline, not an authenticated account fee.
- Demo execution remains unverified and local paper remains the configured default; no execution was performed.
- Structural diversity is descriptive and was not added to the proposer during Phase 3.
