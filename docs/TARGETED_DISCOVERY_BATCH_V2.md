# Targeted Discovery Batch — fdp-v2

## Decision

Final recommendation: `RESEARCH_PROTOCOL_REVIEW`.

The targeted batch stopped at its frozen hard token budget. It did not produce a candidate or certified factor, did not start paper trading, and did not create a replacement for the uncalled third slot.

## Frozen plan

`evidence/targeted-batch-v2/BATCH_PLAN.json` was written and hash-chained before the first Qwen request.

- Plan hash: `8bc4a3924b835ce01933efcfb10867557f1c41747782b7833e8ec5cef3e33e5a`
- Protocol: immutable `fdp-v2`
- Search program: `rtoken-session-alpha-v1`
- Starting search N: 5
- Planned slots: A cross-sectional ranking, B session transition, C residual/beta/dispersion
- Costs, IS/OOS rules, thresholds, and candidate gates: unchanged
- Automatic revision children: disabled

## What occurred

| Slot | Search trial | Unvalidated Qwen thesis | Result | FIRST_HARD_FAIL |
|---|---:|---|---|---|
| A — Cross-sectional ranking | 6 | “Overnight Gap Reversal Rank” | REJECTED_STRUCTURAL after one repair | Syntax |
| B — Session transition | 7 | “Overnight Mean-Reversion from After-Hours Dispersion” | REJECTED_STRUCTURAL after one repair | Syntax |
| C — Residual/beta/dispersion | — | No Qwen request made | NO_RUN_BUDGET_EXHAUSTED | — |

The quoted names identify unvalidated model outputs, not executable factors or discovered alpha. Slot A still emitted malformed `source` nodes after repair. Slot B still emitted malformed `dispersion` nodes after repair. Each output was allocated and permanently recorded; neither received a hidden replacement.

After the two proposer logical calls and their permitted repairs, the provider reported 26,090 measured tokens across four HTTP attempts. This exceeded the frozen 25,000-token cap by 1,090 tokens within the atomic second call. The system therefore blocked Slot C and all lifecycle calls. The cap was not raised, and no further Qwen request was made.

## Search and gates

- Global search N: 5 → 7
- Planned new trials: 3
- Committed new trials: 2
- Qwen logical calls: 2
- Qwen HTTP attempts: 4
- Measured tokens: 26,090
- Conservative tokens: 26,090
- Gate distribution: 2 FAIL, 18 INCONCLUSIVE
- Candidates: 0
- Certified: 0
- Diversity acceptance: FAIL; no structurally valid fdp-v2 factor was available to measure

Changing protocol versions did not reset search history. The two committed structural failures remain in `rtoken-session-alpha-v1`; Slot C did not increment N because no hypothesis was requested or committed.

## Integrity and limitations

- Exact Qwen prompts, responses, validation failures, usage, and attempt counts remain in PostgreSQL.
- The required batch JSON artifacts preserve the plan, trials, gate summary, budget, diversity result, and decision.
- The provider can consume more total tokens than a pre-call reserve predicts because usage is known only after an atomic response. This batch proves that future protocols need shorter schemas/prompts or a provider-side total-token ceiling.
- No historical performance evaluation was run for either malformed proposal. Cost, OOS, DSR, and stability are correctly `INCONCLUSIVE`, not inferred.
- No lifecycle interpretation was requested after the hard budget breach.
- No paper portfolio, order, fill, or paper decision exists.

## Verification

- Python/PostgreSQL: 48 tests passed.
- Frontend ESLint: passed without warnings.
- TypeScript: passed.
- Next.js production build: passed; 10 static pages generated.
- Evidence chain: PASS across 149 events; head `4b5707aca24bc6cfd49365813775c1eaf5da4dd29c772022ee04fdf1813ffa12`.
