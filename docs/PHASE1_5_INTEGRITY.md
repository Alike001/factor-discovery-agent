# Phase 1.5 Integrity Gate

Snapshot: 2026-09-27

## Decision

**Phase 2: NO-GO.** Public-data integrity and PostgreSQL persistence pass, but Qwen is `BLOCKED_KEY`. Autonomous factor generation has not started.

## Reality universe

| Measurement | Count |
|---|---:|
| Total SPOT instruments | 3,169 |
| `isReality=yes` | 2,587 |
| `isReality!=yes` | 582 |
| Online Reality | 2,587 |
| Stock-typed Reality | 2,587 |
| Unique Reality base coins | 2,587 |

The Phase 0 count was correctly filtered. The discrepancy with Bitget's public 500+ copy is documentation drift. The selected core universe remains RNVDAUSDT, RAAPLUSDT, RTSLAUSDT, RMSFTUSDT, RAMZNUSDT, RMETAUSDT, RAMDUSDT, and RQQQUSDT. Every symbol is Reality, online, and mapped to its expected `r` base coin.

## History provenance and certification floor

| Symbol | Instrument `launchTime` | First 1H returned | First 15m returned | Trusted certification start |
|---|---|---|---|---|
| RNVDAUSDT | 2026-04-23 03:22:32.903Z | 2007-02-22 13:00Z | 2026-04-02 03:45Z | 2026-06-02 00:00Z |
| RAAPLUSDT | 2026-06-01 14:00Z | 2007-04-02 14:00Z | 2026-05-11 14:30Z | 2026-06-02 00:00Z |
| RTSLAUSDT | 2026-06-01 14:20:52.017Z | 2010-06-29 15:00Z | 2026-04-01 10:45Z | 2026-06-02 00:00Z |
| RMSFTUSDT | 2026-06-01 14:00Z | 2007-04-02 15:00Z | 2026-05-11 15:15Z | 2026-06-02 00:00Z |
| RAMZNUSDT | 2026-06-01 14:00Z | 2007-04-02 15:00Z | 2026-05-11 15:30Z | 2026-06-02 00:00Z |
| RMETAUSDT | 2026-06-01 14:00Z | 2022-06-09 10:00Z | 2026-05-11 15:30Z | 2026-06-02 00:00Z |
| RAMDUSDT | 2026-06-02 06:55:11.140Z | 2007-04-03 12:00Z | 2026-05-12 04:15Z | 2026-06-02 06:55:11.140Z |
| RQQQUSDT | 2026-06-01 14:00Z | 2011-03-23 10:00Z | 2026-05-11 13:00Z | 2026-06-02 00:00Z |

The older bars prove only that the endpoint exposes older lineage under current rToken symbols. They do not prove public rToken tradability. Certification now enforces `max(2026-06-02T00:00:00Z, instrument launchTime)` per symbol and field.

## Gap completeness after certification start

Core stock-info marks every selected symbol weekend-tradable. Expected-open calculations therefore include weekends and exclude only the live calendar's explicit closures.

| Symbol | Expected open | Observed | Missing expected-open | Completeness | Longest missing run |
|---|---:|---:|---:|---:|---:|
| RNVDAUSDT | 2,757 | 2,654 | 103 | 96.26% | 47h |
| RAAPLUSDT | 2,757 | 2,415 | 342 | 87.60% | 47h |
| RTSLAUSDT | 2,757 | 2,559 | 198 | 92.82% | 47h |
| RMSFTUSDT | 2,757 | 2,308 | 449 | 83.71% | 47h |
| RAMZNUSDT | 2,757 | 2,195 | 562 | 79.62% | 48h |
| RMETAUSDT | 2,757 | 2,298 | 459 | 83.35% | 47h |
| RAMDUSDT | 2,747 | 2,268 | 479 | 82.56% | 47h |
| RQQQUSDT | 2,757 | 2,507 | 250 | 90.93% | 48h |

The 72 explicitly closed hours are not missing bars. Expected-open omissions are missing data and are never forward-filled. The API also returned some bars inside declared closure windows; those are preserved and flagged rather than used to redefine the calendar.

## Volume audit

Every core symbol has populated base volume and quote turnover years before public rToken launch. Pre-July-9 median volumes are also orders of magnitude larger than many post-July-9 values and resemble older underlying-market lineage. This is evidence of ambiguous semantics, not proof of genuine rToken trade volume.

Decision: **volume/turnover operators remain disabled**. Phase 2 proposals, once unblocked, are restricted to OHLC, session, and cross-asset price features. The earliest possible volume `valid_from` remains `max(certification_start, 2026-07-09T00:00:00Z)`, subject to authoritative provenance.

## Qwen, database, fees, and Demo

- Qwen: `BLOCKED_KEY`; zero probes were fabricated. Phase 2 remains blocked.
- PostgreSQL: PASS on isolated PostgreSQL 16.15 at localhost port 55432 with a persistent named volume. Migration `001_phase2_minimum.sql` created only the ten Phase-2 tables.
- Database checks: concurrent trial numbers unique and contiguous; cycle rerun idempotent; duplicate canonical factor returns the same experiment; lifecycle/evidence tables are append-only.
- Fee: `ACCOUNT_FEE_UNVERIFIED`; 0.05% per fill remains `ASSUMED_PUBLISHED_BASELINE`.
- Demo: `UNVERIFIED_NO_CREDENTIALS`; execution remains `local_paper`.

## Tracer v1 vs v2

Factor parameters were not changed. V2 adds the certification floor and corrected holiday/weekend session semantics.

| Metric | V1 | V2 |
|---|---:|---:|
| Aligned rows | 2,497 | 2,487 |
| First eligible bar | 2026-06-01 13:00Z | 2026-06-02 00:00Z |
| Gross return | -10.03% | -9.39% |
| Net return | -13.21% | -11.67% |
| IS net return | -7.06% | -9.87% |
| OOS net return | -6.62% | -2.00% |
| Net max drawdown | -16.24% | -14.61% |
| Fills | 48 | 34 |
| OOS fills | 16 | 12 |

Both versions remain failing/inconclusive architecture evidence, not alpha.

## Spec amendments

- Clarified exact SPOT vs Reality counts and documented public-page drift.
- Added symbol/field `valid_from` and the June 2 public-availability floor.
- Disabled volume/turnover until authoritative provenance exists.
- Required `America/New_York` session conversion and explicit closure/missing classifications.
- Renamed fail-closed anchor result to `MISSING_EXPECTED_ANCHOR`.
- Made Qwen PASS and persistent PostgreSQL PASS mandatory before Phase 2.

Machine-readable evidence is under `evidence/preflight-v2/` and `evidence/tracer-v2/`. Complete raw API responses are gitignored under `evidence/raw/`.
