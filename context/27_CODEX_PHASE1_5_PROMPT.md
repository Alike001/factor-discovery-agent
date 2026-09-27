# Codex Prompt — Phase 1.5 Integrity Gate

You completed:

Phase 0 commit:
`1ac574ee14936254eede23fcd9aa4535fa9c263f`

Phase 1 commit:
`1dd13a99bf7b74001711e4c2f145e33e1320fc90`

Do NOT start Phase 2.

Read:

1. `context/00_README_V9.md`
2. `context/23_FINAL_BUILD_SPEC.md`
3. `context/24_PHASE0_PREFLIGHT.md`
4. `context/26_PHASE1_5_DATA_INTEGRITY.md`

The Phase 0/1 output surfaced four issues that must be resolved before autonomous research:

1. The report says 2,587 Reality instruments. Verify whether this is actually the `isReality=yes` count or the full SPOT count.
2. RNVDA has ~157.74 days of candles even though rToken's broad public Stocks 2.0 launch was June 2, 2026. Audit launchTime vs first candle and do not use ambiguous pre-public-launch history for certification.
3. Volume is non-empty on all retrieved rows despite Bitget's warning that pre-July-9 volume may be empty/not backfilled. Audit it and keep volume DSL operators disabled unless provenance is established.
4. Qwen and Postgres are still blocked/unverified. Phase 2 requires both.

Implement exactly `26_PHASE1_5_DATA_INTEGRITY.md`.

Important rules:

- Do not optimize or change the tracer factor.
- Do not start autonomous factor generation.
- Do not build new product pages.
- Do not add Paper Portfolio yet.
- Do not claim older candles are tradable rToken history unless evidence proves it.
- Use `America/New_York` for historical session conversion.
- Treat missing expected-open bars differently from market closures.
- Keep volume operators disabled by default.
- Use Qwen key only from environment.
- Never display or commit secrets.
- Use Postgres as persistent Phase-2 state.
- Preserve failing evidence.
- Keep local paper execution as the default.
- Update the final spec if live measurements contradict it.

At the end:

1. run Python tests
2. run frontend lint/typecheck/build if touched
3. ensure worktree is clean
4. commit:
   `chore: validate Reality research integrity`

Then STOP.

Report:
- commit hash
- exact total SPOT count
- exact Reality count
- exact online Reality count
- selected core universe
- launchTime vs first candle for each core symbol
- trusted certification start for each core symbol
- gap completeness
- volume audit conclusion
- Qwen probe result
- Postgres result
- fee status
- Demo status
- tracer v1 vs v2 metrics
- tests/build output
- final Phase 2 GO or NO-GO
- any spec amendments
