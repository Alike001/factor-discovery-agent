# Phase 1 Tracer Report

## Outcome

The vertical path is complete:

```text
Bitget Reality public UTA v3
-> normalized closed RNVDA/RQQQ hourly candles
-> immutable data snapshot hash
-> safe JSON AST FactorSpec
-> deterministic next-bar evaluation
-> gate/evidence artifact
-> /lab
```

The hardcoded `Overnight Relative Return Z-Score` is an architecture tracer. It was not proposed by Qwen, was not optimized, and is not discovered alpha.

## Frozen expression

`zscore(ret(RNVDA.close, 12h) - ret(RQQQ.close, 12h), 120h)`

- Session: overnight
- Entry: z-score below -1.0
- Exit: z-score at or above 0.0
- Direction: long/flat
- Decision: closed hourly candle
- Fill: next available aligned hourly candle open
- Missing bars: timestamp intersection only; no forward-fill
- OOS: newest 30 calendar days, fixed before metrics
- Fee: 0.05% per fill, `ASSUMED_PUBLISHED_BASELINE`
- Slippage: 0.025% per fill

## Measured run

- Aligned closed hourly observations: **2,497**
- Gross return: **-10.03%**
- Net return: **-13.21%**
- IS net return: **-7.06%**
- OOS net return: **-6.62%**
- Net max drawdown: **-16.24%**
- Total fills: **48**
- OOS fills: **16**

Gate outcome:

- Syntax: PASS
- Coverage: PASS
- Point-in-time: PASS
- Mechanics: PASS
- Costs: FAIL
- OOS: INCONCLUSIVE (16 fills vs 20 required)
- Stability: INCONCLUSIVE (not part of tracer certification)
- Promotion: INCONCLUSIVE (hardcoded tracers cannot be promoted)

Exact current values and source timestamps are in [`evidence/tracer/tracer-experiment.json`](../evidence/tracer/tracer-experiment.json).

## Limitations

- Qwen is blocked by a missing key and intentionally does not participate in Phase 1.
- The stock MCP is degraded and excluded; the tracer is rToken-only.
- Account-specific fees are unavailable.
- Metrics use aligned available bars, not a synthetic complete clock grid.
- Hourly Sharpe is annualized and should not be treated as forward evidence.
- No robustness, permutation, multiple-testing, certification, or paper portfolio logic is claimed in Phase 1.
- Python 3.12 is the declared target; verification here ran on Python 3.14 because 3.12 is not installed.
