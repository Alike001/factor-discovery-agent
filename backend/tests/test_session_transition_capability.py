from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.bitget.models import Candle
from app.bitget.session import NEW_YORK
from app.research.recipes import FactorRecipe, ast_hash, compile_recipe, recipe_hash
from app.research.session_transition import (
    ANCHOR_INTERVAL_MS,
    CalendarWindow,
    TransitionStatus,
    contract_hash,
    enumerate_events,
    evaluate_transition_recipe,
    event_availability,
    expected_event,
    resolve_transition,
)


def calendar(start: date = date(2026, 1, 1), end: date = date(2026, 12, 31),
             closures: tuple[tuple[datetime, datetime], ...] = ()) -> CalendarWindow:
    return CalendarWindow(closures=closures, available_from=start, available_through=end,
                          as_of=datetime(2026, 12, 31, tzinfo=UTC))


def candle(timestamp_ms: int, price: float) -> Candle:
    value = Decimal(str(price))
    return Candle(timestamp_ms=timestamp_ms, open=value, high=value, low=value, close=value)


def recipe(transition: str = "pre_market_to_regular", *, normalization: str = "none") -> FactorRecipe:
    from_session, to_session = transition.split("_to_")
    feature = "transition_return_zscore" if normalization == "zscore" else "transition_return"
    nested = {"kind": "session_transition", "transition": transition, "feature": feature,
              "normalization": normalization, "threshold": 0.0, "direction": "continuation"}
    if normalization == "zscore":
        nested["feature_lookback"] = 6
    return FactorRecipe.model_validate({
        "schema_version": "factor-recipe-v1", "name": "Golden transition fixture",
        "thesis": "An exact session boundary return can be evaluated without using future prices.",
        "family": "session_transition", "universe": ["RNVDAUSDT"],
        "session_contract": {"kind": "transition", "from_session": from_session, "to_session": to_session},
        "recipe": nested, "horizon_bars": 6, "rebalance_bars": 6, "direction": "long_flat",
        "expected_signal_frequency": "low", "economic_mechanism": "Session boundary repricing may persist.",
        "why_not_duplicate": "Exact transition anchors differ from rolling beta residuals.",
        "why_costs_should_not_dominate": "One eligible observation per transition limits turnover.",
    })


def bars_for_event(day: date, transition: str) -> tuple[list[Candle], int]:
    event = expected_event(day, transition)
    rows = []
    for index in range(27):
        timestamp = event.from_anchor_ms + index * ANCHOR_INTERVAL_MS
        rows.append(candle(timestamp, 100 + index * .1))
    return rows, rows[-1].timestamp_ms + ANCHOR_INTERVAL_MS


def test_allowed_transition_enum_only_and_invalid_pair_rejected() -> None:
    with pytest.raises(ValidationError):
        recipe("regular_to_pre_market")
    value = recipe().model_dump(mode="json")
    value["session_contract"] = {"kind": "transition", "from_session": "regular", "to_session": "after_hours"}
    with pytest.raises(ValidationError, match="must match"):
        FactorRecipe.model_validate(value)


def test_dst_safe_boundaries_use_historical_new_york_offset() -> None:
    winter = expected_event(date(2026, 1, 12), "pre_market_to_regular")
    summer = expected_event(date(2026, 7, 13), "pre_market_to_regular")
    assert datetime.fromtimestamp(winter.boundary_ms / 1000, tz=UTC).hour == 14
    assert datetime.fromtimestamp(summer.boundary_ms / 1000, tz=UTC).hour == 13
    assert datetime.fromtimestamp(winter.boundary_ms / 1000, tz=UTC).astimezone(NEW_YORK).strftime("%H:%M") == "09:30"
    assert datetime.fromtimestamp(summer.boundary_ms / 1000, tz=UTC).astimezone(NEW_YORK).strftime("%H:%M") == "09:30"


def test_holiday_weekend_and_stale_calendar_are_unavailable() -> None:
    holiday_start = datetime(2026, 7, 2, 20, tzinfo=NEW_YORK)
    holiday_end = datetime(2026, 7, 3, 20, tzinfo=NEW_YORK)
    assert event_availability(expected_event(date(2026, 7, 3), "pre_market_to_regular"),
                              calendar(closures=((holiday_start, holiday_end),))) == TransitionStatus.TRANSITION_UNAVAILABLE
    assert event_availability(expected_event(date(2026, 7, 4), "pre_market_to_regular"), calendar()) == TransitionStatus.TRANSITION_UNAVAILABLE
    assert event_availability(expected_event(date(2027, 1, 4), "pre_market_to_regular"), calendar()) == TransitionStatus.SESSION_CALENDAR_UNAVAILABLE


def test_missing_anchors_never_fall_back() -> None:
    event = expected_event(date(2026, 7, 13), "pre_market_to_regular")
    exact = {event.from_anchor_ms: candle(event.from_anchor_ms, 100), event.to_anchor_ms: candle(event.to_anchor_ms, 101),
             event.next_fill_ms: candle(event.next_fill_ms, 102)}
    missing_from = dict(exact)
    missing_from.pop(event.from_anchor_ms)
    missing_from[event.from_anchor_ms - ANCHOR_INTERVAL_MS] = candle(event.from_anchor_ms - ANCHOR_INTERVAL_MS, 99)
    result = resolve_transition(event, missing_from, as_of_ms=event.observable_ms, calendar=calendar())
    assert result["status"] == "MISSING_EXPECTED_ANCHOR" and result["missing"] == "from_anchor"
    missing_to = dict(exact)
    missing_to.pop(event.to_anchor_ms)
    missing_to[event.to_anchor_ms + ANCHOR_INTERVAL_MS] = candle(event.to_anchor_ms + ANCHOR_INTERVAL_MS, 102)
    result = resolve_transition(event, missing_to, as_of_ms=event.observable_ms, calendar=calendar())
    assert result["status"] == "MISSING_EXPECTED_ANCHOR" and result["missing"] == "to_anchor"


def test_forming_anchor_and_missing_next_bar_fail_closed() -> None:
    event = expected_event(date(2026, 7, 13), "regular_to_after_hours")
    values = {event.from_anchor_ms: candle(event.from_anchor_ms, 100), event.to_anchor_ms: candle(event.to_anchor_ms, 101)}
    assert resolve_transition(event, values, as_of_ms=event.observable_ms - 1, calendar=calendar())["status"] == "FORMING_TO_ANCHOR"
    assert resolve_transition(event, values, as_of_ms=event.observable_ms, calendar=calendar())["status"] == "NO_NEXT_EXECUTABLE_BAR"


@pytest.mark.parametrize("transition", [
    "after_hours_to_overnight", "overnight_to_pre_market", "pre_market_to_regular", "regular_to_after_hours",
])
@pytest.mark.parametrize("day", [date(2026, 1, 12), date(2026, 7, 13)])
def test_all_golden_transitions_compile_and_evaluate_in_two_dst_regimes(transition: str, day: date) -> None:
    factor = recipe(transition)
    compiled = compile_recipe(factor)
    bars, as_of_ms = bars_for_event(day, transition)
    report = evaluate_transition_recipe(factor, compiled, bars, calendar=calendar(), as_of_ms=as_of_ms)
    assert report["expected_transition_events"] == 1
    assert report["valid_anchors"] == 1
    assert report["no_lookahead_violations"] == 0
    assert report["records"][0]["fill_timestamp_ms"] >= report["records"][0]["observable_timestamp_ms"]
    assert report["search_trial_number"] is None
    assert report["promotion_eligible"] is False


def test_compile_and_hashes_are_stable() -> None:
    factor = recipe(normalization="zscore")
    assert recipe_hash(factor) == recipe_hash(FactorRecipe.model_validate(factor.model_dump(mode="json")))
    assert ast_hash(compile_recipe(factor)) == ast_hash(compile_recipe(factor))
    assert contract_hash() == contract_hash()


def test_event_enumeration_skips_closed_days() -> None:
    start = int(datetime(2026, 7, 3, tzinfo=UTC).timestamp() * 1000)
    end = int(datetime(2026, 7, 7, tzinfo=UTC).timestamp() * 1000)
    closures = ((datetime(2026, 7, 2, 20, tzinfo=NEW_YORK), datetime(2026, 7, 3, 20, tzinfo=NEW_YORK)),)
    events = enumerate_events(start, end, "pre_market_to_regular", calendar(closures=closures))
    assert [event.local_date for event in events] == [date(2026, 7, 6)]


def test_stale_transition_data_rejected() -> None:
    factor = recipe()
    compiled = compile_recipe(factor)
    bars, as_of_ms = bars_for_event(date(2026, 7, 13), "pre_market_to_regular")
    with pytest.raises(ValueError, match="STALE_TRANSITION_DATA"):
        evaluate_transition_recipe(factor, compiled, bars, calendar=calendar(), as_of_ms=as_of_ms + 10 * ANCHOR_INTERVAL_MS)
