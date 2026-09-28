from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Any, Iterable, Literal

from app.bitget.models import Candle
from app.bitget.session import NEW_YORK
from app.evidence import canonical_hash
from app.research.protocol_v2 import PROTOCOL_V2, PROTOCOL_V2_HASH, SEARCH_PROGRAM_ID

ANCHOR_INTERVAL_MS = 900_000
CONTRACT_VERSION = "session-transition-v1"
SUPPORTED_TRANSITIONS = (
    "after_hours_to_overnight",
    "overnight_to_pre_market",
    "pre_market_to_regular",
    "regular_to_after_hours",
)
Transition = Literal[
    "after_hours_to_overnight",
    "overnight_to_pre_market",
    "pre_market_to_regular",
    "regular_to_after_hours",
]

TRANSITION_PARTS: dict[str, tuple[str, str, time]] = {
    "after_hours_to_overnight": ("after_hours", "overnight", time(20)),
    "overnight_to_pre_market": ("overnight", "pre_market", time(4)),
    "pre_market_to_regular": ("pre_market", "regular", time(9, 30)),
    "regular_to_after_hours": ("regular", "after_hours", time(16)),
}


class TransitionStatus(StrEnum):
    READY = "READY"
    MISSING_EXPECTED_ANCHOR = "MISSING_EXPECTED_ANCHOR"
    STALE_TRANSITION_DATA = "STALE_TRANSITION_DATA"
    SESSION_CALENDAR_UNAVAILABLE = "SESSION_CALENDAR_UNAVAILABLE"
    TRANSITION_UNAVAILABLE = "TRANSITION_UNAVAILABLE"
    FORMING_TO_ANCHOR = "FORMING_TO_ANCHOR"
    NO_NEXT_EXECUTABLE_BAR = "NO_NEXT_EXECUTABLE_BAR"


SESSION_TRANSITION_CONTRACT: dict[str, Any] = {
    "version": CONTRACT_VERSION,
    "timezone": "America/New_York",
    "calendar_source": "Bitget Reality market calendar",
    "anchor_resolution": "15m",
    "anchor_interval_ms": ANCHOR_INTERVAL_MS,
    "research_resolution": "15m for transition architecture tracer",
    "supported_transitions": list(SUPPORTED_TRANSITIONS),
    "boundaries_local": {
        "after_hours_to_overnight": "20:00:00",
        "overnight_to_pre_market": "04:00:00",
        "pre_market_to_regular": "09:30:00",
        "regular_to_after_hours": "16:00:00",
    },
    "anchor_rules": {
        "timestamp_semantics": "candle open timestamp",
        "tolerance_ms": 0,
        "from_anchor_open_offset_ms": -ANCHOR_INTERVAL_MS,
        "from_anchor_close_offset_ms": 0,
        "to_anchor_open_offset_ms": 0,
        "to_anchor_close_offset_ms": ANCHOR_INTERVAL_MS,
        "price_field": "close",
        "fallback": "forbidden",
    },
    "feature": {
        "operator": "transition_return",
        "formula": "to_anchor.close / from_anchor.close - 1",
        "observable_at": "to_anchor close timestamp",
    },
    "execution": {
        "earliest_fill": "next exact 15m bar open after observable_at",
        "same_anchor_fill": "forbidden",
        "horizon_unit": "1H",
    },
    "failure_statuses": [
        "MISSING_EXPECTED_ANCHOR",
        "STALE_TRANSITION_DATA",
        "SESSION_CALENDAR_UNAVAILABLE",
    ],
    "closures": "weekends and specificConfig intervals make affected transitions unavailable",
    "cost_model": PROTOCOL_V2["cost_model"],
    "split_rule": PROTOCOL_V2["split_rule"],
}


def contract_hash() -> str:
    return canonical_hash(SESSION_TRANSITION_CONTRACT)


@dataclass(frozen=True)
class TransitionEvent:
    transition: str
    local_date: date
    boundary_ms: int
    from_anchor_ms: int
    to_anchor_ms: int
    observable_ms: int
    next_fill_ms: int


@dataclass(frozen=True)
class CalendarWindow:
    closures: tuple[tuple[datetime, datetime], ...]
    available_from: date
    available_through: date
    as_of: datetime


def expected_event(local_day: date, transition: str) -> TransitionEvent:
    if transition not in TRANSITION_PARTS:
        raise ValueError(f"unsupported transition: {transition}")
    _, _, boundary_time = TRANSITION_PARTS[transition]
    boundary = datetime.combine(local_day, boundary_time, tzinfo=NEW_YORK)
    boundary_ms = int(boundary.astimezone(UTC).timestamp() * 1000)
    return TransitionEvent(
        transition=transition,
        local_date=local_day,
        boundary_ms=boundary_ms,
        from_anchor_ms=boundary_ms - ANCHOR_INTERVAL_MS,
        to_anchor_ms=boundary_ms,
        observable_ms=boundary_ms + ANCHOR_INTERVAL_MS,
        next_fill_ms=boundary_ms + ANCHOR_INTERVAL_MS,
    )


def _overlaps_closure(start: datetime, end: datetime, closures: Iterable[tuple[datetime, datetime]]) -> bool:
    return any(start < closure_end and end > closure_start for closure_start, closure_end in closures)


def event_availability(event: TransitionEvent, calendar: CalendarWindow) -> TransitionStatus:
    if event.local_date < calendar.available_from or event.local_date > calendar.available_through:
        return TransitionStatus.SESSION_CALENDAR_UNAVAILABLE
    boundary = datetime.fromtimestamp(event.boundary_ms / 1000, tz=UTC).astimezone(NEW_YORK)
    if boundary.weekday() >= 5:
        return TransitionStatus.TRANSITION_UNAVAILABLE
    if event.transition == "after_hours_to_overnight" and boundary.weekday() == 4:
        return TransitionStatus.TRANSITION_UNAVAILABLE
    start = datetime.fromtimestamp(event.from_anchor_ms / 1000, tz=UTC).astimezone(NEW_YORK)
    end = datetime.fromtimestamp(event.observable_ms / 1000, tz=UTC).astimezone(NEW_YORK)
    if _overlaps_closure(start, end, calendar.closures):
        return TransitionStatus.TRANSITION_UNAVAILABLE
    return TransitionStatus.READY


def enumerate_events(start_ms: int, end_ms: int, transition: str, calendar: CalendarWindow) -> list[TransitionEvent]:
    start_day = datetime.fromtimestamp(start_ms / 1000, tz=UTC).astimezone(NEW_YORK).date() - timedelta(days=1)
    end_day = datetime.fromtimestamp(end_ms / 1000, tz=UTC).astimezone(NEW_YORK).date() + timedelta(days=1)
    events: list[TransitionEvent] = []
    day = start_day
    while day <= end_day:
        event = expected_event(day, transition)
        if start_ms <= event.from_anchor_ms and event.next_fill_ms <= end_ms and event_availability(event, calendar) == TransitionStatus.READY:
            events.append(event)
        day += timedelta(days=1)
    return events


def resolve_transition(
    event: TransitionEvent,
    candles: dict[int, Candle],
    *,
    as_of_ms: int,
    calendar: CalendarWindow,
    require_next_bar: bool = True,
) -> dict[str, Any]:
    availability = event_availability(event, calendar)
    base = {
        "transition": event.transition,
        "local_date": event.local_date.isoformat(),
        "from_anchor_timestamp_ms": event.from_anchor_ms,
        "to_anchor_timestamp_ms": event.to_anchor_ms,
        "observable_timestamp_ms": event.observable_ms,
        "next_fill_timestamp_ms": event.next_fill_ms,
    }
    if availability != TransitionStatus.READY:
        return {**base, "status": availability.value}
    if calendar.as_of.astimezone(UTC).timestamp() * 1000 < event.observable_ms:
        return {**base, "status": TransitionStatus.SESSION_CALENDAR_UNAVAILABLE.value}
    if event.from_anchor_ms not in candles:
        return {**base, "status": TransitionStatus.MISSING_EXPECTED_ANCHOR.value, "missing": "from_anchor"}
    if event.to_anchor_ms not in candles:
        return {**base, "status": TransitionStatus.MISSING_EXPECTED_ANCHOR.value, "missing": "to_anchor"}
    if as_of_ms < event.observable_ms:
        return {**base, "status": TransitionStatus.FORMING_TO_ANCHOR.value}
    if require_next_bar and event.next_fill_ms not in candles:
        return {**base, "status": TransitionStatus.NO_NEXT_EXECUTABLE_BAR.value}
    from_price = float(candles[event.from_anchor_ms].close)
    to_price = float(candles[event.to_anchor_ms].close)
    if from_price <= 0:
        return {**base, "status": TransitionStatus.MISSING_EXPECTED_ANCHOR.value, "missing": "valid_from_price"}
    return {
        **base,
        "status": TransitionStatus.READY.value,
        "symbol": None,
        "from_price": from_price,
        "to_price": to_price,
        "transition_return": to_price / from_price - 1,
    }


def _metrics(values: list[float], fills: int) -> dict[str, Any]:
    equity = peak = 1.0
    max_drawdown = 0.0
    for value in values:
        equity *= 1 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
    deviation = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "observations": len(values),
        "total_return": equity - 1,
        "sharpe": statistics.mean(values) / deviation * math.sqrt(365) if deviation else None,
        "max_drawdown": max_drawdown,
        "fills": fills,
    }


def evaluate_transition_recipe(
    recipe: Any,
    compiled: Any,
    candles: list[Candle],
    *,
    calendar: CalendarWindow,
    as_of_ms: int,
    architecture_tracer: bool = False,
) -> dict[str, Any]:
    if not candles:
        raise ValueError("STALE_TRANSITION_DATA")
    ordered = sorted(candles, key=lambda candle: candle.timestamp_ms)
    if len({c.timestamp_ms for c in ordered}) != len(ordered):
        raise ValueError("duplicate candle timestamp")
    closed = [c for c in ordered if c.timestamp_ms + ANCHOR_INTERVAL_MS <= as_of_ms]
    if not closed or as_of_ms - closed[-1].timestamp_ms > 2 * ANCHOR_INTERVAL_MS:
        raise ValueError("STALE_TRANSITION_DATA")
    by_timestamp = {c.timestamp_ms: c for c in closed}
    events = enumerate_events(closed[0].timestamp_ms, closed[-1].timestamp_ms, recipe.recipe.transition, calendar)
    resolved = [resolve_transition(event, by_timestamp, as_of_ms=as_of_ms, calendar=calendar) for event in events]
    valid = [item for item in resolved if item["status"] == TransitionStatus.READY]
    lookback = recipe.recipe.feature_lookback or 1
    features: list[float | None] = []
    raw = [float(item["transition_return"]) for item in valid]
    for index, value in enumerate(raw):
        if recipe.recipe.normalization == "none":
            features.append(value)
            continue
        if index + 1 < lookback:
            features.append(None)
            continue
        window = raw[index - lookback + 1:index + 1]
        deviation = statistics.stdev(window) if len(window) > 1 else 0.0
        features.append((value - statistics.mean(window)) / deviation if deviation else 0.0)
    threshold = float(recipe.recipe.threshold)
    signals = [False if value is None else (value > threshold if recipe.recipe.direction == "continuation" else value < -threshold)
               for value in features]
    round_trip_cost = 2 * (PROTOCOL_V2["cost_model"]["fee_per_fill"] + PROTOCOL_V2["cost_model"]["slippage_per_fill"])
    horizon_15m = recipe.horizon_bars * 4
    rows: list[dict[str, Any]] = []
    gross_returns: list[float] = []
    net_returns: list[float] = []
    fills = 0
    no_lookahead_violations = 0
    for item, feature, signal in zip(valid, features, signals):
        fill_ms = int(item["next_fill_timestamp_ms"])
        exit_ms = fill_ms + horizon_15m * ANCHOR_INTERVAL_MS
        fill = by_timestamp.get(fill_ms)
        exit_bar = by_timestamp.get(exit_ms)
        executed = bool(signal and fill and exit_bar)
        if executed:
            gross = float(exit_bar.open / fill.open - 1)
            net = gross - round_trip_cost
            gross_returns.append(gross)
            net_returns.append(net)
            fills += 2
            if fill_ms < int(item["observable_timestamp_ms"]):
                no_lookahead_violations += 1
        rows.append({**item, "symbol": recipe.universe[0], "feature": feature, "signal": signal,
                     "fill_timestamp_ms": fill_ms if executed else None,
                     "exit_timestamp_ms": exit_ms if executed else None,
                     "gross": gross if executed else 0.0, "net": net if executed else 0.0})
    split_ms = closed[-1].timestamp_ms - 30 * 86_400_000
    is_values = [row["net"] for row in rows if row["fill_timestamp_ms"] and row["fill_timestamp_ms"] < split_ms]
    oos_values = [row["net"] for row in rows if row["fill_timestamp_ms"] and row["fill_timestamp_ms"] >= split_ms]
    gates = [
        {"name": "Syntax", "outcome": "PASS", "reason": "Compiled safe transition recipe."},
        {"name": "Coverage", "outcome": "PASS" if valid else "INCONCLUSIVE", "reason": f"{len(valid)} exact transition anchors."},
        {"name": "Point-in-time", "outcome": "PASS", "reason": "Closed exact 15m anchors only; no fallback."},
        {"name": "Mechanics", "outcome": "PASS" if no_lookahead_violations == 0 else "FAIL", "reason": "Feature is observed at to-anchor close; fills are next-bar only."},
        {"name": "Costs", "outcome": "PASS" if net_returns and sum(net_returns) > 0 else "FAIL", "reason": "Unchanged fee/slippage applied to both fills."},
        {"name": "OOS", "outcome": "INCONCLUSIVE" if len(oos_values) < 20 else ("PASS" if sum(oos_values) > 0 else "FAIL"), "reason": f"{len(oos_values)} OOS trades."},
        {"name": "Permutation", "outcome": "INCONCLUSIVE", "reason": "Architecture tracer is outside the search population."},
        {"name": "Baseline", "outcome": "INCONCLUSIVE", "reason": "Architecture tracer is not a promotion experiment."},
    ]
    report = {
        "label": "SESSION_TRANSITION_ARCHITECTURE_TRACER" if architecture_tracer else "SESSION_TRANSITION_GOLDEN_FIXTURE",
        "protocol_version": "fdp-v3-draft",
        "protocol_hash": PROTOCOL_V2_HASH,
        "search_program_id": SEARCH_PROGRAM_ID,
        "search_trial_number": None,
        "dsr_population_member": False,
        "promotion_eligible": False,
        "candidate": False,
        "certified": False,
        "contract_version": CONTRACT_VERSION,
        "contract_hash": contract_hash(),
        "compiler_version": compiled.compiler_version,
        "recipe_hash": canonical_hash(recipe.model_dump(mode="json")),
        "ast_hash": canonical_hash(compiled.model_dump(mode="json")),
        "dataset_hash": canonical_hash([c.model_dump(mode="json") for c in closed]),
        "split_timestamp": datetime.fromtimestamp(split_ms / 1000, tz=UTC).isoformat(),
        "expected_transition_events": len(events),
        "valid_anchors": len(valid),
        "missing_anchors": sum(item["status"] == TransitionStatus.MISSING_EXPECTED_ANCHOR for item in resolved),
        "signals": sum(signals),
        "fills": fills,
        "costs": round_trip_cost * (fills // 2),
        "no_lookahead_violations": no_lookahead_violations,
        "metrics": {
            "gross": _metrics(gross_returns, fills),
            "net": _metrics(net_returns, fills),
            "is_net": _metrics(is_values, len(is_values) * 2),
            "oos_net": _metrics(oos_values, len(oos_values) * 2),
        },
        "gates": gates,
        "anchor_results": resolved,
        "records": rows,
    }
    report["report_hash"] = canonical_hash(report)
    return report
