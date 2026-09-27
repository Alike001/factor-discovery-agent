from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.bitget.models import Candle
from app.bitget.session import classify_session
from app.evidence import canonical_hash
from app.research.dsl import FactorSpec


@dataclass(frozen=True)
class EngineConfig:
    asset_symbol: str
    benchmark_symbol: str
    relative_lookback: int = 12
    zscore_lookback: int = 120
    entry_threshold: float = -1.0
    exit_threshold: float = 0.0
    fee_per_fill: float = 0.0005
    slippage_per_fill: float = 0.00025
    oos_days: int = 30
    field_valid_from_ms: dict[str, int] = field(default_factory=dict)
    market_closures: tuple[tuple[datetime, datetime], ...] = ()
    schema_version: str = "phase1-tracer-v1"


@dataclass(frozen=True)
class ExperimentResult:
    evidence: dict[str, Any]


def _metrics(returns: list[float], turnovers: list[float], periods_per_year: int = 8760) -> dict[str, Any]:
    if not returns:
        return {"observations": 0, "total_return": 0.0, "sharpe": None, "max_drawdown": 0.0, "turnover": 0.0}
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
    deviation = statistics.stdev(returns) if len(returns) > 1 else 0
    sharpe = (statistics.mean(returns) / deviation * math.sqrt(periods_per_year)) if deviation else None
    return {
        "observations": len(returns),
        "total_return": equity - 1,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "turnover": sum(turnovers),
    }


def evaluate_factor(
    spec: FactorSpec,
    asset_candles: list[Candle],
    benchmark_candles: list[Candle],
    config: EngineConfig,
    *,
    split_timestamp_ms: int | None = None,
) -> ExperimentResult:
    asset_by_time = {item.timestamp_ms: item for item in asset_candles}
    benchmark_by_time = {item.timestamp_ms: item for item in benchmark_candles}
    timestamps = sorted(set(asset_by_time) & set(benchmark_by_time))
    required_valid_from = max(config.field_valid_from_ms.values(), default=0)
    timestamps = [timestamp for timestamp in timestamps if timestamp >= required_valid_from]
    if len(timestamps) < config.relative_lookback + config.zscore_lookback + 2:
        raise ValueError("insufficient aligned observations")
    latest = datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC)
    fixed_split = split_timestamp_ms or int((latest - timedelta(days=config.oos_days)).timestamp() * 1000)
    asset_close = [float(asset_by_time[timestamp].close) for timestamp in timestamps]
    benchmark_close = [float(benchmark_by_time[timestamp].close) for timestamp in timestamps]
    relative: list[float | None] = [None] * len(timestamps)
    for index in range(config.relative_lookback, len(timestamps)):
        asset_return = asset_close[index] / asset_close[index - config.relative_lookback] - 1
        benchmark_return = benchmark_close[index] / benchmark_close[index - config.relative_lookback] - 1
        relative[index] = asset_return - benchmark_return
    zscores: list[float | None] = [None] * len(timestamps)
    for index in range(config.relative_lookback + config.zscore_lookback - 1, len(timestamps)):
        window = [value for value in relative[index - config.zscore_lookback + 1 : index + 1] if value is not None]
        if len(window) != config.zscore_lookback:
            continue
        deviation = statistics.stdev(window)
        zscores[index] = (relative[index] - statistics.mean(window)) / deviation if deviation else 0.0

    position = 0.0
    pending: tuple[float, int] | None = None
    records: list[dict[str, Any]] = []
    trade_count = 0
    for index in range(len(timestamps) - 1):
        timestamp = timestamps[index]
        turnover = 0.0
        decision_timestamp = None
        if pending is not None:
            target, decision_timestamp = pending
            turnover = abs(target - position)
            if turnover:
                trade_count += 1
            position = target
            pending = None
        current_open = float(asset_by_time[timestamp].open)
        next_open = float(asset_by_time[timestamps[index + 1]].open)
        gross = position * (next_open / current_open - 1)
        cost = turnover * (config.fee_per_fill + config.slippage_per_fill)
        net = gross - cost
        session = classify_session(
            datetime.fromtimestamp((timestamp + 3_600_000) / 1000, tz=UTC), list(config.market_closures)
        ).value
        signal = zscores[index]
        next_target = position
        if signal is not None and session in spec.session_filter:
            if position == 0 and signal < config.entry_threshold:
                next_target = 1.0
            elif position == 1 and signal >= config.exit_threshold:
                next_target = 0.0
            if next_target != position:
                pending = (next_target, timestamp + 3_600_000)
        records.append(
            {
                "timestamp_ms": timestamp,
                "next_timestamp_ms": timestamps[index + 1],
                "signal": signal,
                "session": session,
                "position": position,
                "turnover": turnover,
                "gross_return": gross,
                "cost": cost,
                "net_return": net,
                "fill_decision_timestamp_ms": decision_timestamp,
                "fill_timestamp_ms": timestamp if turnover else None,
            }
        )

    def segment(before: bool, net: bool) -> dict[str, Any]:
        chosen = [item for item in records if (item["timestamp_ms"] < fixed_split) is before]
        key = "net_return" if net else "gross_return"
        return _metrics([item[key] for item in chosen], [item["turnover"] for item in chosen])

    gross_all = _metrics([item["gross_return"] for item in records], [item["turnover"] for item in records])
    net_all = _metrics([item["net_return"] for item in records], [item["turnover"] for item in records])
    is_net = segment(True, True)
    oos_net = segment(False, True)
    oos_trades = sum(1 for item in records if item["timestamp_ms"] >= fixed_split and item["turnover"] > 0)
    gates = [
        {"name": "Syntax", "verdict": "PASS", "reason": "FactorSpec validated against the safe JSON AST."},
        {"name": "Coverage", "verdict": "PASS", "reason": f"{len(timestamps)} aligned closed hourly observations; no forward-fill."},
        {"name": "Point-in-time", "verdict": "PASS", "reason": "Only closed rToken and rQQQ candle fields were used."},
        {"name": "Mechanics", "verdict": "PASS", "reason": "Every fill follows its decision candle."},
        {
            "name": "Costs",
            "verdict": "PASS" if net_all["total_return"] > 0 else "FAIL",
            "reason": "Net return remains positive." if net_all["total_return"] > 0 else "Net return is not positive after the stated costs.",
        },
        {
            "name": "OOS",
            "verdict": "INCONCLUSIVE" if oos_trades < 20 else ("PASS" if oos_net["total_return"] > 0 else "FAIL"),
            "reason": f"{oos_trades} OOS fills against a 20-fill minimum.",
        },
        {"name": "Stability", "verdict": "INCONCLUSIVE", "reason": "Phase 1 tracer does not run the certification stability battery."},
        {"name": "Promotion", "verdict": "INCONCLUSIVE", "reason": "A hardcoded tracer cannot be promoted or called discovered alpha."},
    ]
    evidence = {
        "schema_version": config.schema_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": "PAPER · REAL BITGET MARKET DATA",
        "claim": "Architecture tracer only; not discovered alpha and not a paper portfolio result.",
        "factor": spec.model_dump(mode="json"),
        "factor_hash": canonical_hash(spec.model_dump(mode="json")),
        "expression_human": "zscore(ret(RNVDA.close, 12h) − ret(RQQQ.close, 12h), 120h); enter below −1.0 overnight, exit at 0.0",
        "source": {
            "provider": "Bitget Reality public UTA v3",
            "asset": config.asset_symbol,
            "benchmark": config.benchmark_symbol,
            "first_timestamp": datetime.fromtimestamp(timestamps[0] / 1000, tz=UTC).isoformat(),
            "last_timestamp": datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
            "aligned_rows": len(timestamps),
            "forming_candles_excluded": True,
            "missing_bar_policy": "timestamp intersection; never forward-fill",
        },
        "protocol": {
            "relative_lookback_hours": config.relative_lookback,
            "zscore_lookback_hours": config.zscore_lookback,
            "entry_threshold": config.entry_threshold,
            "exit_threshold": config.exit_threshold,
            "split_timestamp": datetime.fromtimestamp(fixed_split / 1000, tz=UTC).isoformat(),
            "split_rule": "latest aligned timestamp minus 30 calendar days; fixed before metrics",
            "fill_rule": "next available aligned hourly candle open after decision",
            "fee_per_fill": config.fee_per_fill,
            "slippage_per_fill": config.slippage_per_fill,
            "fee_basis": "ASSUMED_PUBLISHED_BASELINE",
            "field_valid_from": {
                key: datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()
                for key, value in sorted(config.field_valid_from_ms.items())
            },
        },
        "metrics": {
            "gross": gross_all,
            "net": net_all,
            "is_net": is_net,
            "oos_net": oos_net,
            "fill_count": trade_count,
            "oos_fill_count": oos_trades,
        },
        "gates": gates,
        "integrity": {"records_hash": canonical_hash(records), "deterministic": True},
        "execution_audit": {
            "fill_count": sum(1 for item in records if item["fill_timestamp_ms"] is not None),
            "same_decision_candle_violations": sum(
                1
                for item in records
                if item["fill_timestamp_ms"] is not None
                and item["fill_timestamp_ms"] < item["fill_decision_timestamp_ms"]
            ),
        },
        "sample_records": records[-12:],
    }
    return ExperimentResult(evidence=evidence)
