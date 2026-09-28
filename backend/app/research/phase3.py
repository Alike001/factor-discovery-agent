from __future__ import annotations

import math
import statistics
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from app.bitget.models import Candle
from app.bitget.session import classify_session
from app.research.dsl import Expression, FactorSpec
from app.research.evaluator import _expression

STABILITY_VERSION = "scope-aware-stability-v1"


def factor_scope(spec: FactorSpec) -> str:
    symbols = {node.symbol for expression in (spec.signal, spec.entry_condition, spec.exit_condition)
               for node in expression.walk() if node.symbol}
    if len(symbols) <= 1:
        return "SINGLE_SYMBOL_SESSION"
    if len(symbols) == 2:
        return "PAIR_RELATIVE_SESSION"
    return "MULTI_SYMBOL_CROSS_SECTIONAL"


def reconstruct_returns(
    spec: FactorSpec, candles: dict[str, list[Candle]], *, start_ms: int, end_ms: int,
    split_ms: int, fee: float, slippage: float,
) -> dict[str, Any]:
    symbols = sorted({node.symbol for expression in (spec.signal, spec.entry_condition, spec.exit_condition)
                      for node in expression.walk() if node.symbol} | set(spec.universe))
    by_symbol = {symbol: {item.timestamp_ms: item for item in candles[symbol]
                          if start_ms <= item.timestamp_ms <= end_ms} for symbol in symbols}
    timestamps = sorted(set.intersection(*(set(values) for values in by_symbol.values())))
    fields: dict[tuple[str, str], list[float]] = {}
    for symbol in symbols:
        for field in ("open", "high", "low", "close"):
            fields[(symbol, field)] = [float(getattr(by_symbol[symbol][timestamp], field)) for timestamp in timestamps]
    sessions = [classify_session(datetime.fromtimestamp((timestamp + 3_600_000) / 1000, tz=UTC)).value
                for timestamp in timestamps]
    signal = _expression(spec.signal, fields, sessions)
    entries = _expression(spec.entry_condition, fields, sessions, signal)
    exits = _expression(spec.exit_condition, fields, sessions, signal)
    primary = next((symbol for symbol in spec.universe if symbol != "RQQQUSDT"), spec.universe[0])
    opens = fields[(primary, "open")]
    position = 0.0
    pending: tuple[float, int] | None = None
    rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for index in range(len(timestamps) - 1):
        turnover = 0.0
        decision_at = None
        if pending:
            target, decision_at = pending
            turnover = abs(target - position)
            position = target
            pending = None
        gross = position * (opens[index + 1] / opens[index] - 1)
        net = gross - turnover * (fee + slippage)
        if sessions[index] in spec.session_filter:
            target = position
            if position == 0 and entries[index] is True:
                target = 1.0
            elif position == 1 and exits[index] is True:
                target = 0.0
            if target != position:
                pending = (target, timestamps[index] + 3_600_000)
                decisions.append({"timestamp_ms": timestamps[index], "session": sessions[index], "target": target})
        rows.append({"timestamp_ms": timestamps[index], "gross": gross, "net": net,
                     "turnover": turnover, "decision_timestamp_ms": decision_at,
                     "fill_timestamp_ms": timestamps[index] if turnover else None})
    purity = all(item["session"] in spec.session_filter for item in decisions)
    return {"rows": rows, "split_ms": split_ms, "decisions": decisions,
            "session_purity": purity, "scope": factor_scope(spec)}


def _block_metrics(rows: list[dict[str, Any]], start_ms: int, end_ms: int) -> dict[str, Any]:
    selected = [row for row in rows if start_ms <= row["timestamp_ms"] < end_ms]
    returns = [row["net"] for row in selected]
    fills = sum(row["turnover"] > 0 for row in selected)
    equity = peak = 1.0
    drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1)
    deviation = statistics.stdev(returns) if len(returns) > 1 else 0.0
    sharpe = statistics.mean(returns) / deviation * math.sqrt(8760) if deviation else None
    net_return = equity - 1
    return {
        "start": datetime.fromtimestamp(start_ms / 1000, tz=UTC).isoformat(),
        "end": datetime.fromtimestamp(end_ms / 1000, tz=UTC).isoformat(),
        "observations": len(selected), "fills": fills, "net_return": net_return,
        "sharpe": sharpe, "max_drawdown": drawdown,
        "payoff_sign": 1 if net_return > 0 else (-1 if net_return < 0 else 0),
        "evaluable": bool(selected) and fills >= 1,
    }


def temporal_stability(rows: list[dict[str, Any]], split_ms: int, end_ms: int,
                       *, session_purity: bool) -> dict[str, Any]:
    width = max(1, (end_ms + 3_600_000 - split_ms) // 4)
    boundaries = [split_ms + width * index for index in range(4)] + [end_ms + 3_600_000]
    blocks = [_block_metrics(rows, boundaries[index], boundaries[index + 1]) for index in range(4)]
    evaluable = [block for block in blocks if block["evaluable"]]
    if not session_purity:
        outcome, reason = "FAIL", "SESSION_PURITY_FAIL"
    elif len(evaluable) < 3:
        outcome, reason = "INCONCLUSIVE", "INCONCLUSIVE_STABILITY_SAMPLE"
    else:
        oos_rows = [row for row in rows if row["timestamp_ms"] >= split_ms]
        full_return = math.prod(1 + row["net"] for row in oos_rows) - 1
        full_sign = 1 if full_return > 0 else (-1 if full_return < 0 else 0)
        sign_share = sum(block["payoff_sign"] == full_sign for block in evaluable) / len(evaluable)
        absolute = sum(abs(block["net_return"]) for block in evaluable)
        max_contribution = max((abs(block["net_return"]) / absolute for block in evaluable), default=1.0) if absolute else 1.0
        first = math.prod(1 + row["net"] for row in oos_rows if row["timestamp_ms"] < boundaries[2]) - 1
        second = math.prod(1 + row["net"] for row in oos_rows if row["timestamp_ms"] >= boundaries[2]) - 1
        halves_agree = first != 0 and second != 0 and (first > 0) == (second > 0)
        passed = sign_share >= 0.60 and max_contribution <= 0.60 and halves_agree
        outcome, reason = ("PASS", "STABILITY_THRESHOLDS_MET") if passed else ("FAIL", "STABILITY_THRESHOLDS_NOT_MET")
    absolute = sum(abs(block["net_return"]) for block in evaluable)
    for block in blocks:
        block["absolute_pnl_contribution"] = abs(block["net_return"]) / absolute if absolute else None
    return {"status": outcome, "reason_code": reason, "scope_method": STABILITY_VERSION,
            "session_purity": session_purity, "evaluable_blocks": len(evaluable), "blocks": blocks,
            "thresholds": {"minimum_evaluable_blocks": 3, "sign_agreement": 0.60,
                           "maximum_absolute_pnl_contribution": 0.60, "halves_must_agree": True}}


def strategy_family(spec: FactorSpec) -> str:
    words = f"{spec.name} {spec.thesis}".lower()
    if any(word in words for word in ("reversion", "revert", "reversal", "bounce")):
        return "mean_reversion"
    if any(word in words for word in ("momentum", "continue", "continuation", "strength", "extension")):
        return "continuation"
    if "residual" in words:
        return "residual"
    if len(spec.universe) > 2:
        return "cross_sectional"
    return "other"


def structural_fingerprint(spec: FactorSpec) -> dict[str, Any]:
    nodes = [node for expression in (spec.signal, spec.entry_condition, spec.exit_condition) for node in expression.walk()]
    sources = [node.symbol for node in nodes if node.op == "source" and node.symbol]
    target = next((symbol for symbol in spec.universe if symbol != "RQQQUSDT"), spec.universe[0])
    return {"family": strategy_family(spec), "targets": [target],
            "references": sorted(set(sources) - {target}), "sessions": sorted(spec.session_filter),
            "operator_multiset": dict(sorted(Counter(node.op for node in nodes).items())),
            "lookbacks": sorted({node.lookback for node in nodes if node.lookback is not None}),
            "direction": spec.direction, "horizon": spec.horizon_bars}


def fingerprint_features(fingerprint: dict[str, Any]) -> set[str]:
    features = {f"family:{fingerprint['family']}", f"direction:{fingerprint['direction']}",
                f"horizon:{fingerprint['horizon']}"}
    for field in ("targets", "references", "sessions", "lookbacks"):
        features.update(f"{field}:{value}" for value in fingerprint[field])
    features.update(f"op:{key}:{value}" for key, value in fingerprint["operator_multiset"].items())
    return features


def nearest_neighbors(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for item in items:
        own = fingerprint_features(item["fingerprint"])
        candidates = []
        for other in items:
            if item["trial_number"] == other["trial_number"]:
                continue
            theirs = fingerprint_features(other["fingerprint"])
            score = len(own & theirs) / len(own | theirs)
            candidates.append((score, other["trial_number"]))
        score, trial = max(candidates) if candidates else (0.0, None)
        output.append({"trial_number": item["trial_number"], "nearest_trial": trial,
                       "jaccard_similarity": score})
    return output
