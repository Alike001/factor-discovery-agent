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
from app.research.phase3 import temporal_stability
from app.research.protocol_v2 import PROTOCOL_V2, PROTOCOL_V2_HASH, PROTOCOL_VERSION_V2, SEARCH_PROGRAM_ID
from app.research.statistics import deflated_sharpe
from app.research.targeted import ExpressionV2, FactorProposalV2

CANDIDATE_REQUIRED_GATES = frozenset({"Coverage", "Costs", "OOS", "Permutation", "Baseline"})


@dataclass(frozen=True)
class TargetedEvaluation:
    report: dict[str, Any]
    rows: list[dict[str, Any]]


def _shift(values: list[Any], distance: int) -> list[Any]:
    return [None] * distance + values[:-distance] if distance else list(values)


def _rolling(values: list[float | None], lookback: int, operation: str) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    for index in range(lookback - 1, len(values)):
        window = values[index - lookback + 1:index + 1]
        if any(value is None for value in window):
            continue
        numeric = [float(value) for value in window if value is not None]
        if operation == "sma":
            output[index] = statistics.mean(numeric)
        elif operation == "vol":
            output[index] = statistics.stdev(numeric) if len(numeric) > 1 else 0.0
        else:
            deviation = statistics.stdev(numeric) if len(numeric) > 1 else 0.0
            output[index] = (numeric[-1] - statistics.mean(numeric)) / deviation if deviation else 0.0
    return output


def _rolling_relation(left: list[Any], right: list[Any], lookback: int, *, residual: bool) -> list[float | None]:
    output: list[float | None] = [None] * len(left)
    for index in range(lookback - 1, len(left)):
        xs = right[index - lookback + 1:index + 1]
        ys = left[index - lookback + 1:index + 1]
        if any(value is None for value in xs + ys):
            continue
        x = [float(value) for value in xs]
        y = [float(value) for value in ys]
        variance = statistics.variance(x) if len(x) > 1 else 0.0
        beta = sum((a - statistics.mean(x)) * (b - statistics.mean(y)) for a, b in zip(x, y)) / ((len(x) - 1) * variance) if variance else 0.0
        output[index] = float(left[index]) - beta * float(right[index]) if residual else beta
    return output


def expression_v2(node: ExpressionV2, fields: dict[tuple[str, str], list[float]], sessions: list[str], signal: list[Any] | None = None) -> list[Any]:
    if node.op == "source":
        return list(fields[(node.symbol or "", node.field or "")])
    if node.op == "signal":
        if signal is None:
            raise ValueError("signal unavailable")
        return list(signal)
    args = [expression_v2(child, fields, sessions, signal) for child in node.args]
    if node.op == "session_in":
        allowed = set(node.sessions or [])
        return [session in allowed for session in sessions]
    if node.op == "data_available":
        return [value is not None for value in args[0]]
    if node.op == "ret":
        prior = _shift(args[0], int(node.lookback or 1))
        return [None if value is None or base in (None, 0) else value / base - 1 for value, base in zip(args[0], prior)]
    if node.op in {"sma", "vol", "zscore"}:
        return _rolling(args[0], int(node.lookback or 1), node.op)
    if node.op in {"rolling_beta", "residual"}:
        return _rolling_relation(args[0], args[1], int(node.lookback or 1), residual=node.op == "residual")
    if node.op in {"rank", "group_mean", "dispersion"}:
        output: list[float | None] = []
        for values in zip(*args):
            if any(value is None for value in values):
                output.append(None)
                continue
            numeric = [float(value) for value in values]
            if node.op == "group_mean":
                output.append(statistics.mean(numeric))
            elif node.op == "dispersion":
                output.append(statistics.stdev(numeric))
            else:
                ordered = sorted(range(len(numeric)), key=numeric.__getitem__)
                rank = ordered.index(0)
                output.append(2 * rank / (len(numeric) - 1) - 1)
        return output
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
        operations = {"gt": lambda x: x > threshold, "gte": lambda x: x >= threshold,
                      "lt": lambda x: x < threshold, "lte": lambda x: x <= threshold}
        return [None if value is None else operations[node.op](value) for value in args[0]]
    if node.op in {"add", "sub", "mul", "div", "and", "or"}:
        output = []
        for left, right in zip(args[0], args[1]):
            if left is None or right is None:
                output.append(None)
            elif node.op == "add": output.append(left + right)
            elif node.op == "sub": output.append(left - right)
            elif node.op == "mul": output.append(left * right)
            elif node.op == "div": output.append(0.0 if abs(right) < 1e-12 else left / right)
            elif node.op == "and": output.append(bool(left) and bool(right))
            else: output.append(bool(left) or bool(right))
        return output
    raise ValueError(f"unsupported fdp-v2 operator {node.op}")


def _metrics(returns: list[float], fills: int) -> dict[str, Any]:
    equity = peak = 1.0
    drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1)
    deviation = statistics.stdev(returns) if len(returns) > 1 else 0.0
    return {"observations": len(returns), "total_return": equity - 1,
            "sharpe": statistics.mean(returns) / deviation * math.sqrt(8760) if deviation else None,
            "max_drawdown": drawdown, "fills": fills}


def _permutation(values: list[float], seed: int, draws: int = 2000) -> float | None:
    if len(values) < 8:
        return None
    observed = sum(values)
    generator = random.Random(seed)
    exceed = sum(sum(value * generator.choice((-1, 1)) for value in values) >= observed for _ in range(draws))
    return (exceed + 1) / (draws + 1)


def evaluate_targeted_factor(proposal: FactorProposalV2, candles: dict[str, list[Candle]], *, trial_number: int,
                             field_valid_from_ms: dict[str, int]) -> TargetedEvaluation:
    symbols = sorted(set(proposal.universe))
    common = set.intersection(*(set(item.timestamp_ms for item in candles[symbol]) for symbol in symbols))
    floor = max(field_valid_from_ms.get(f"{symbol}.close", 0) for symbol in symbols)
    timestamps = sorted(timestamp for timestamp in common if timestamp >= floor)
    if len(timestamps) < 3:
        raise ValueError("INCONCLUSIVE_DATA")
    by_symbol = {symbol: {item.timestamp_ms: item for item in candles[symbol]} for symbol in symbols}
    fields = {(symbol, field): [float(getattr(by_symbol[symbol][timestamp], field)) for timestamp in timestamps]
              for symbol in symbols for field in ("open", "high", "low", "close")}
    sessions = [classify_session(datetime.fromtimestamp((timestamp + 3_600_000) / 1000, tz=UTC)).value for timestamp in timestamps]
    signal = expression_v2(proposal.signal, fields, sessions)
    entries = expression_v2(proposal.entry_condition, fields, sessions, signal)
    exits = expression_v2(proposal.exit_condition, fields, sessions, signal)
    primary = proposal.universe[0]
    opens = fields[(primary, "open")]
    split_ms = int((datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC) - timedelta(days=30)).timestamp() * 1000)
    position = 0.0
    pending: tuple[float, int, str] | None = None
    held = 0
    rows: list[dict[str, Any]] = []
    payoff_events: list[float] = []
    for index in range(len(timestamps) - 1):
        turnover = 0.0
        decision_at = None
        decision_session = None
        if pending:
            target, decision_at, decision_session = pending
            turnover = abs(target - position)
            position = target
            held = 0 if position else held
            pending = None
        gross = position * (opens[index + 1] / opens[index] - 1)
        cost = turnover * (PROTOCOL_V2["cost_model"]["fee_per_fill"] + PROTOCOL_V2["cost_model"]["slippage_per_fill"])
        net = gross - cost
        if position:
            held += 1
            payoff_events.append(net)
        transition_ok = True
        if proposal.slot == "B":
            transition_ok = index > 0 and sessions[index - 1] == proposal.transition_from and sessions[index] == proposal.transition_to
        decision_window = index % proposal.rebalance_bars == 0 and sessions[index] in proposal.session_filter and transition_ok
        target = position
        if position and held >= proposal.horizon_bars:
            target = 0.0
        elif decision_window:
            if position == 0 and entries[index] is True:
                target = 1.0
            elif position == 1 and exits[index] is True:
                target = 0.0
        if target != position:
            pending = (target, timestamps[index] + 3_600_000, sessions[index])
        rows.append({"timestamp_ms": timestamps[index], "gross": gross, "net": net, "turnover": turnover,
                     "signal": signal[index], "session": sessions[index], "decision_timestamp_ms": decision_at,
                     "decision_session": decision_session,
                     "fill_timestamp_ms": timestamps[index] if turnover else None})
    fills = sum(row["turnover"] > 0 for row in rows)
    oos_fills = sum(row["turnover"] > 0 and row["timestamp_ms"] >= split_ms for row in rows)
    gross = _metrics([row["gross"] for row in rows], fills)
    net = _metrics([row["net"] for row in rows], fills)
    is_net = _metrics([row["net"] for row in rows if row["timestamp_ms"] < split_ms], fills - oos_fills)
    oos_net = _metrics([row["net"] for row in rows if row["timestamp_ms"] >= split_ms], oos_fills)
    buy_hold = opens[-1] / opens[0] - 1
    p_value = _permutation(payoff_events, trial_number)
    days = (timestamps[-1] - timestamps[0]) / 86_400_000
    contract = {"protocol_version": PROTOCOL_VERSION_V2, "protocol_hash": PROTOCOL_V2_HASH,
                "search_program_id": SEARCH_PROGRAM_ID, "symbols": symbols,
                "start": datetime.fromtimestamp(timestamps[0] / 1000, tz=UTC).isoformat(),
                "end": datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
                "latest_included_timestamp": datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
                "field_valid_from_ms": field_valid_from_ms, "session_classification_version": PROTOCOL_V2["session_classifier"],
                "cost_model_version": PROTOCOL_V2["cost_model"]["version"]}
    gates = [
        {"name": "Syntax", "outcome": "PASS", "reason": "Strict fdp-v2 safe AST and slot validation passed."},
        {"name": "Coverage", "outcome": "PASS" if days >= 60 else "INCONCLUSIVE", "reason": f"{days:.1f} certified days and {len(timestamps)} aligned bars."},
        {"name": "Point-in-time", "outcome": "PASS", "reason": "Certified closed OHLC only; volume disabled."},
        {"name": "Mechanics", "outcome": "PASS" if all(not row["fill_timestamp_ms"] or row["fill_timestamp_ms"] >= row["decision_timestamp_ms"] for row in rows) else "FAIL", "reason": "Next-bar execution and rebalance controls enforced."},
        {"name": "Costs", "outcome": "PASS" if net["total_return"] > 0 else "FAIL", "reason": f"Net return after unchanged fee/slippage is {net['total_return']:.4%}."},
        {"name": "OOS", "outcome": "INCONCLUSIVE" if oos_fills < 20 else ("PASS" if oos_net["total_return"] > 0 else "FAIL"), "reason": f"{oos_fills} OOS fills; net OOS {oos_net['total_return']:.4%}."},
        {"name": "Permutation", "outcome": "INCONCLUSIVE" if p_value is None else ("PASS" if p_value <= .10 else "FAIL"), "reason": "Insufficient independent payoff events." if p_value is None else f"Deterministic 2,000 sign-flip p={p_value:.4f}."},
        {"name": "Baseline", "outcome": "PASS" if net["total_return"] > buy_hold else "FAIL", "reason": f"Factor net {net['total_return']:.4%} versus same-window primary buy-and-hold {buy_hold:.4%}."},
    ]
    report = {"protocol": PROTOCOL_VERSION_V2, "search_program_id": SEARCH_PROGRAM_ID, "trial_number": trial_number,
              "slot": proposal.slot, "factor": proposal.model_dump(mode="json"), "data_contract": contract,
              "dataset_hash": canonical_hash({"contract": contract, "timestamps": timestamps}),
              "split_timestamp": datetime.fromtimestamp(split_ms / 1000, tz=UTC).isoformat(),
              "metrics": {"gross": gross, "net": net, "is_net": is_net, "oos_net": oos_net, "buy_hold": buy_hold},
              "gates": gates, "integrity": {"records_hash": canonical_hash(rows), "permutation_seed": trial_number, "deterministic": True},
              "sample_records": rows[-12:]}
    return TargetedEvaluation(report, rows)


def finalize_evaluation(evaluation: TargetedEvaluation, *, benchmark_sharpe: float, search_n: int, sigma_sr: float) -> dict[str, Any]:
    report = dict(evaluation.report)
    proposal = FactorProposalV2.model_validate(report["factor"])
    split_ms = int(datetime.fromisoformat(report["split_timestamp"]).timestamp() * 1000)
    end_ms = int(datetime.fromisoformat(report["data_contract"]["end"]).timestamp() * 1000)
    purity = all(row["decision_session"] in proposal.session_filter for row in evaluation.rows if row["decision_timestamp_ms"] is not None)
    stability = temporal_stability(evaluation.rows, split_ms, end_ms, session_purity=purity)
    dsr = deflated_sharpe([row["net"] for row in evaluation.rows], benchmark_sharpe=benchmark_sharpe,
                          search_n=search_n, sigma_sr=sigma_sr, threshold=PROTOCOL_V2["gate_policy"]["dsr_probability"])
    gates = list(report["gates"])
    gates.extend([
        {"name": "Stability", "outcome": stability["status"], "reason": stability["reason_code"], "value": stability},
        {"name": "Multiple testing", "outcome": dsr["status"], "reason": dsr["reason_code"], "value": dsr},
    ])
    order = ["Syntax", "Coverage", "Point-in-time", "Mechanics", "Costs", "OOS", "Stability", "Permutation", "Multiple testing", "Baseline"]
    gates.sort(key=lambda gate: order.index(gate["name"]))
    hard = {"Syntax", "Point-in-time", "Mechanics", "Costs", "OOS", "Stability", "Permutation", "Baseline"}
    first_hard_fail = next((gate["name"] for gate in gates if gate["name"] in hard and gate["outcome"] == "FAIL"), None)
    candidate = first_hard_fail is None and all(next(g for g in gates if g["name"] == name)["outcome"] == "PASS" for name in CANDIDATE_REQUIRED_GATES)
    certified = candidate and all(gate["outcome"] == "PASS" for gate in gates)
    report["gates"] = gates
    report["first_hard_fail"] = first_hard_fail
    report["aggregate"] = "CERTIFIED" if certified else ("CANDIDATE" if candidate else ("REJECTED" if first_hard_fail else "INCONCLUSIVE"))
    report["report_hash"] = canonical_hash(report)
    return report


def structural_rejection(proposal: FactorProposalV2 | dict[str, Any], trial_number: int, errors: list[str], *, slot: str | None = None) -> dict[str, Any]:
    proposal_json = proposal.model_dump(mode="json") if isinstance(proposal, FactorProposalV2) else proposal
    resolved_slot = proposal.slot if isinstance(proposal, FactorProposalV2) else (slot or str(proposal.get("slot", "UNKNOWN")))
    gates = [{"name": name, "outcome": "FAIL" if name == "Syntax" else "INCONCLUSIVE",
              "reason": ",".join(errors) if name == "Syntax" else "Not evaluated after structural rejection."}
             for name in ["Syntax", "Coverage", "Point-in-time", "Mechanics", "Costs", "OOS", "Stability", "Permutation", "Multiple testing", "Baseline"]]
    report = {"protocol": PROTOCOL_VERSION_V2, "search_program_id": SEARCH_PROGRAM_ID, "trial_number": trial_number,
              "slot": resolved_slot, "factor": proposal_json, "data_contract": {}, "dataset_hash": canonical_hash({"structural": errors}),
              "metrics": {}, "gates": gates, "first_hard_fail": "Syntax", "aggregate": "REJECTED", "structural_errors": errors}
    report["report_hash"] = canonical_hash(report)
    return report
