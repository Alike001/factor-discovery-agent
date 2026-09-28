from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.bitget.models import Candle
from app.bitget.session import classify_session
from app.evidence import canonical_hash
from app.research.dsl import Expression, FactorSpec
from app.research.protocol import PROTOCOL, PROTOCOL_HASH, PROTOCOL_VERSION


@dataclass(frozen=True)
class ResearchEvaluation:
    report: dict[str, Any]


def _shift(values: list[Any], distance: int) -> list[Any]:
    return [None] * distance + values[:-distance] if distance else list(values)


def _rolling(values: list[float | None], lookback: int, fn: str) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    for index in range(lookback - 1, len(values)):
        window = values[index - lookback + 1 : index + 1]
        if any(value is None for value in window):
            continue
        numeric = [float(value) for value in window if value is not None]
        if fn == "sma":
            output[index] = statistics.mean(numeric)
        elif fn == "vol":
            output[index] = statistics.stdev(numeric) if len(numeric) > 1 else 0.0
        else:
            deviation = statistics.stdev(numeric) if len(numeric) > 1 else 0.0
            output[index] = (numeric[-1] - statistics.mean(numeric)) / deviation if deviation else 0.0
    return output


def _expression(
    node: Expression,
    fields: dict[tuple[str, str], list[float]],
    sessions: list[str],
    signal: list[Any] | None = None,
) -> list[Any]:
    size = len(sessions)
    if node.op == "source":
        return list(fields[(node.symbol or "", node.field or "")])
    if node.op == "signal":
        if signal is None:
            raise ValueError("signal reference is unavailable")
        return list(signal)
    args = [_expression(item, fields, sessions, signal) for item in node.args]
    if node.op == "session_in":
        allowed = set(node.sessions or [])
        return [item in allowed for item in sessions]
    if node.op == "data_available":
        return [value is not None for value in args[0]]
    if node.op == "ret":
        previous = _shift(args[0], int(node.lookback or 1))
        return [None if a is None or b in (None, 0) else a / b - 1 for a, b in zip(args[0], previous)]
    if node.op in {"sma", "vol", "zscore"}:
        return _rolling(args[0], int(node.lookback or 1), node.op)
    if node.op in {"abs", "sign", "clip", "not"}:
        output = []
        for value in args[0]:
            if value is None:
                output.append(None)
            elif node.op == "abs":
                output.append(abs(value))
            elif node.op == "sign":
                output.append(1.0 if value > 0 else (-1.0 if value < 0 else 0.0))
            elif node.op == "clip":
                output.append(max(-2.0, min(2.0, value)))
            else:
                output.append(not bool(value))
        return output
    if node.op in {"gt", "gte", "lt", "lte"}:
        threshold = float(node.threshold or 0)
        operations = {
            "gt": lambda value: value > threshold,
            "gte": lambda value: value >= threshold,
            "lt": lambda value: value < threshold,
            "lte": lambda value: value <= threshold,
        }
        return [None if value is None else operations[node.op](value) for value in args[0]]
    if node.op in {"add", "sub", "mul", "div", "and", "or"}:
        output = []
        for left, right in zip(args[0], args[1]):
            if left is None or right is None:
                output.append(None)
            elif node.op == "add":
                output.append(left + right)
            elif node.op == "sub":
                output.append(left - right)
            elif node.op == "mul":
                output.append(left * right)
            elif node.op == "div":
                output.append(0.0 if abs(right) < 1e-12 else left / right)
            elif node.op == "and":
                output.append(bool(left) and bool(right))
            else:
                output.append(bool(left) or bool(right))
        return output
    raise ValueError(f"unsupported operator: {node.op}")


def _metrics(returns: list[float], fills: int) -> dict[str, Any]:
    if not returns:
        return {"observations": 0, "total_return": 0.0, "sharpe": None, "max_drawdown": 0.0, "fills": fills}
    equity = peak = 1.0
    drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1)
    deviation = statistics.stdev(returns) if len(returns) > 1 else 0.0
    sharpe = statistics.mean(returns) / deviation * math.sqrt(8760) if deviation else None
    return {
        "observations": len(returns),
        "total_return": equity - 1,
        "sharpe": sharpe,
        "max_drawdown": drawdown,
        "fills": fills,
    }


def _permutation_p(trade_returns: list[float], seed: int, draws: int = 2000) -> float | None:
    if len(trade_returns) < 8:
        return None
    observed = sum(trade_returns)
    generator = random.Random(seed)
    exceed = 0
    for _ in range(draws):
        placebo = sum(value * generator.choice((-1, 1)) for value in trade_returns)
        exceed += placebo >= observed
    return (exceed + 1) / (draws + 1)


def evaluate_research_factor(
    spec: FactorSpec,
    candles: dict[str, list[Candle]],
    *,
    trial_number: int,
    field_valid_from_ms: dict[str, int],
) -> ResearchEvaluation:
    required_symbols = sorted({node.symbol for expression in (spec.signal, spec.entry_condition, spec.exit_condition) for node in expression.walk() if node.symbol})
    required_symbols = sorted(set(required_symbols) | set(spec.universe))
    common = set.intersection(*(set(item.timestamp_ms for item in candles[symbol]) for symbol in required_symbols))
    floor = max(field_valid_from_ms.get(f"{symbol}.close", 0) for symbol in required_symbols)
    timestamps = sorted(timestamp for timestamp in common if timestamp >= floor)
    if len(timestamps) < 3:
        raise ValueError("INCONCLUSIVE_DATA: insufficient aligned certified bars")
    by_symbol = {symbol: {item.timestamp_ms: item for item in candles[symbol]} for symbol in required_symbols}
    fields: dict[tuple[str, str], list[float]] = {}
    for symbol in required_symbols:
        for field in ("open", "high", "low", "close"):
            fields[(symbol, field)] = [float(getattr(by_symbol[symbol][timestamp], field)) for timestamp in timestamps]
    sessions = [classify_session(datetime.fromtimestamp((timestamp + 3_600_000) / 1000, tz=UTC)).value for timestamp in timestamps]
    signal = _expression(spec.signal, fields, sessions)
    entries = _expression(spec.entry_condition, fields, sessions, signal)
    exits = _expression(spec.exit_condition, fields, sessions, signal)
    primary = next((symbol for symbol in spec.universe if symbol != "RQQQUSDT"), spec.universe[0])
    opens = fields[(primary, "open")]
    split_ms = int((datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC) - timedelta(days=30)).timestamp() * 1000)
    position = 0.0
    pending: tuple[float, int] | None = None
    rows: list[dict[str, Any]] = []
    trade_returns: list[float] = []
    for index in range(len(timestamps) - 1):
        turnover = 0.0
        decision_at = None
        if pending:
            target, decision_at = pending
            turnover = abs(target - position)
            position = target
            pending = None
        gross = position * (opens[index + 1] / opens[index] - 1)
        cost = turnover * (PROTOCOL["cost_model"]["fee_per_fill"] + PROTOCOL["cost_model"]["slippage_per_fill"])
        net = gross - cost
        if position and net:
            trade_returns.append(net)
        if sessions[index] in spec.session_filter:
            target = position
            if position == 0 and entries[index] is True:
                target = 1.0
            elif position == 1 and exits[index] is True:
                target = 0.0
            if target != position:
                pending = (target, timestamps[index] + 3_600_000)
        rows.append({
            "timestamp_ms": timestamps[index], "gross": gross, "net": net, "turnover": turnover,
            "decision_timestamp_ms": decision_at,
            "fill_timestamp_ms": timestamps[index] if turnover else None,
        })
    all_fills = sum(row["turnover"] > 0 for row in rows)
    oos_fills = sum(row["turnover"] > 0 and row["timestamp_ms"] >= split_ms for row in rows)
    gross = _metrics([row["gross"] for row in rows], all_fills)
    net = _metrics([row["net"] for row in rows], all_fills)
    is_net = _metrics([row["net"] for row in rows if row["timestamp_ms"] < split_ms], all_fills - oos_fills)
    oos_net = _metrics([row["net"] for row in rows if row["timestamp_ms"] >= split_ms], oos_fills)
    buy_hold = opens[-1] / opens[0] - 1
    p_value = _permutation_p(trade_returns, seed=trial_number)
    days = (timestamps[-1] - timestamps[0]) / 86_400_000
    gates = [
        {"name": "Syntax", "outcome": "PASS", "reason": "Strict FactorSpec and safe AST validation passed."},
        {"name": "Coverage", "outcome": "PASS" if days >= 60 else "INCONCLUSIVE", "reason": f"{days:.1f} certified calendar days and {len(timestamps)} aligned closed bars."},
        {"name": "Point-in-time", "outcome": "PASS", "reason": "Only certified closed OHLC fields were used; volume remains disabled."},
        {"name": "Mechanics", "outcome": "PASS" if all(not row["fill_timestamp_ms"] or row["fill_timestamp_ms"] >= row["decision_timestamp_ms"] for row in rows) else "FAIL", "reason": "Signals execute no earlier than the next aligned bar."},
        {"name": "Costs", "outcome": "PASS" if net["total_return"] > 0 else "FAIL", "reason": f"Net return after fee and slippage is {net['total_return']:.4%}."},
        {"name": "OOS", "outcome": "INCONCLUSIVE" if oos_fills < 20 else ("PASS" if oos_net["total_return"] > 0 else "FAIL"), "reason": f"{oos_fills} OOS fills; net OOS return {oos_net['total_return']:.4%}."},
        {"name": "Stability", "outcome": "INCONCLUSIVE", "reason": "INCONCLUSIVE_NOT_IMPLEMENTED: full symbol/session replication is deferred; certification blocked."},
        {"name": "Permutation", "outcome": "INCONCLUSIVE" if p_value is None else ("PASS" if p_value <= 0.10 else "FAIL"), "reason": "Insufficient independent trade returns." if p_value is None else f"Deterministic 2,000 sign-flip p={p_value:.4f}."},
        {"name": "Multiple testing", "outcome": "INCONCLUSIVE", "reason": "INCONCLUSIVE_NOT_IMPLEMENTED: exact Deflated Sharpe is not claimed; certification blocked."},
        {"name": "Baseline", "outcome": "PASS" if net["total_return"] > buy_hold else "FAIL", "reason": f"Factor net {net['total_return']:.4%} versus same-window buy-and-hold {buy_hold:.4%}."},
    ]
    hard_fail = any(gate["outcome"] == "FAIL" for gate in gates if gate["name"] in {"Syntax", "Point-in-time", "Mechanics", "Costs", "OOS", "Permutation", "Baseline"})
    candidate = not hard_fail and all(next(g for g in gates if g["name"] == name)["outcome"] == "PASS" for name in ("Coverage", "Costs", "OOS", "Permutation", "Baseline"))
    aggregate = "REJECTED" if hard_fail else ("CANDIDATE" if candidate else "INCONCLUSIVE")
    contract = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_hash": PROTOCOL_HASH,
        "symbols": required_symbols,
        "start": datetime.fromtimestamp(timestamps[0] / 1000, tz=UTC).isoformat(),
        "end": datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
        "latest_included_timestamp": datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
        "field_valid_from_ms": field_valid_from_ms,
        "session_classification_version": PROTOCOL["session_classifier"],
        "cost_model_version": PROTOCOL["cost_model"]["version"],
    }
    report = {
        "protocol": PROTOCOL_VERSION,
        "trial_number": trial_number,
        "factor": spec.model_dump(mode="json"),
        "data_contract": contract,
        "dataset_hash": canonical_hash({
            "contract": contract,
            "timestamps": timestamps,
            "fields": {f"{symbol}.{field}": values for (symbol, field), values in sorted(fields.items())},
        }),
        "split_timestamp": datetime.fromtimestamp(split_ms / 1000, tz=UTC).isoformat(),
        "metrics": {"gross": gross, "net": net, "is_net": is_net, "oos_net": oos_net, "buy_hold": buy_hold},
        "gates": gates,
        "aggregate": aggregate,
        "integrity": {"records_hash": canonical_hash(rows), "permutation_seed": trial_number, "deterministic": True},
        "sample_records": rows[-12:],
    }
    report["report_hash"] = canonical_hash(report)
    return ResearchEvaluation(report)
