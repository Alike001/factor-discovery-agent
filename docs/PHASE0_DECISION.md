# Phase 0 Decision

Generated from the live preflight on 2026-09-27. Evidence is in [`evidence/preflight/`](../evidence/preflight/).

## Decision

**GO for the rToken-only Phase 1 tracer, with limitations.** Public Bitget Reality candle research has no hard blocker. Qwen, authenticated account fees, Demo execution, Stock MCP, and Neon are not Phase 1 tracer dependencies and remain explicitly blocked, degraded, or unverified.

## Measured results

- Working deadline: **2026-10-08 23:59 UTC+8**, as supplied by the live-form context package.
- Reality discovery: **2,587** live-response instruments carried `isReality=yes`.
- Primary core universe selected: **RNVDAUSDT, RAAPLUSDT, RTSLAUSDT, RMSFTUSDT, RAMZNUSDT, RMETAUSDT, RAMDUSDT, RQQQUSDT**.
- Secondary audited symbols: **RSPYUSDT, RCOINUSDT, RHOODUSDT, RMSTRUSDT**.
- Hourly history: every audited target had at least **117.61 calendar days**; RNVDA had **157.74 days**.
- Hourly rows ranged from **2,156 to 3,251**. No duplicate timestamps were measured.
- Raw hourly missing-interval counts ranged from **231 to 679**. These counts include scheduled closures and symbol-specific missing bars. No missing interval was filled.
- Recent 15-minute rows ranged from **506 to 644** over the requested seven-day window. No duplicate timestamps were measured.
- The API returned non-empty volume for every retrieved hourly row. This is a current observation, not an assumption that older empty volume was backfilled.
- Latest closed 15-minute bars were between **2026-09-27 17:00 UTC and 20:15 UTC**, depending on symbol.
- Stock info, market states, and market calendar public endpoints returned success.
- The live states response reported `daylightType=standard` and `timeZone=EST`. Because that label is surprising for September, session conversion uses IANA `America/New_York` rules and preserves the raw response for review.

## Integration status

- Stock MCP: **DEGRADED**. `initialize` returned HTTP 503 / `Too many open sessions`; no tool name was hardcoded and no quote/history result was fabricated. Phase 1 is rToken-only.
- Qwen: **BLOCKED_KEY**. `BITGET_QWEN_API_KEY` was absent, so all three required schema probes are recorded as unrun.
- Account fee: **ACCOUNT_FEE_UNVERIFIED**. Standard authenticated credentials were absent. Phase 1 uses **0.05% per fill**, labeled `ASSUMED_PUBLISHED_BASELINE`.
- Reality Demo: **UNVERIFIED_NO_CREDENTIALS**. Demo credentials were absent. `EXECUTION_MODE=local_paper`.
- Database: **UNVERIFIED** because `DATABASE_URL` was absent. The hackathon architecture remains idempotent one-shot jobs for GitHub Actions + Neon; Phase 1 evidence is file-backed.

## Session safeguards

Regression tests cover normal weekday, Friday close, Saturday, holiday closure, DST conversion, and missing expected regular-session anchor. A missing anchor returns `MISSING_ANCHOR`; dependent factors must not fall back to an older bar.

## Spec amendments and contradictions

- No material product-direction amendment is required.
- The Phase 1 tracer is narrowed to aligned rToken/QQQ hourly timestamps because Stock MCP did not initialize.
- Raw bar gaps are too frequent to treat the dataset as a complete 24/7 grid. Evaluation must intersect timestamps and must never forward-fill.
- The provider's session response uses `EST`/`standard` in late September; this conflicts with normal US daylight-saving expectations and is treated as source metadata rather than a safe timezone conversion rule.

## Phase 1 constraints

- The tracer is architecture proof, not discovered alpha.
- Fixed IS/OOS boundary; no parameter tuning.
- Forming candles excluded.
- Decisions fill no earlier than the next available candle.
- Gross and net results shown separately with the assumed fee basis.

