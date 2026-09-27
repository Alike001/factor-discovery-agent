from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.bitget.audit import iso
from app.bitget.models import Candle
from app.bitget.session import SessionLabel, classify_session


PUBLIC_RTOKEN_LAUNCH = datetime(2026, 6, 2, tzinfo=UTC)
DOCUMENTED_VOLUME_START = datetime(2026, 7, 9, tzinfo=UTC)


def certification_start_ms(instrument_launch_ms: int) -> int:
    return max(instrument_launch_ms, int(PUBLIC_RTOKEN_LAUNCH.timestamp() * 1000))


def first_at_or_after(candles: list[Candle], timestamp_ms: int) -> Candle | None:
    return next((item for item in candles if item.timestamp_ms >= timestamp_ms), None)


def first_weekend(candles: list[Candle]) -> Candle | None:
    for candle in candles:
        local = candle.timestamp.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York"))
        if local.weekday() >= 5:
            return candle
    return None


def provenance_summary(symbol: str, launch_ms: int, hourly: list[Candle], fifteen_minute: list[Candle]) -> dict[str, Any]:
    june_ms = int(PUBLIC_RTOKEN_LAUNCH.timestamp() * 1000)
    july_ms = int(DOCUMENTED_VOLUME_START.timestamp() * 1000)
    volume_items = [item for item in hourly if item.volume is not None]
    weekend = first_weekend(hourly)
    return {
        "symbol": symbol,
        "instrument_launch_time": iso(launch_ms),
        "first_returned_1h_candle": iso(hourly[0].timestamp_ms if hourly else None),
        "first_returned_15m_candle": iso(fifteen_minute[0].timestamp_ms if fifteen_minute else None),
        "first_non_empty_volume_candle": iso(volume_items[0].timestamp_ms if volume_items else None),
        "first_weekend_candle": iso(weekend.timestamp_ms if weekend else None),
        "first_candle_on_or_after_2026_06_02": iso(
            (item.timestamp_ms if (item := first_at_or_after(hourly, june_ms)) else None)
        ),
        "first_candle_on_or_after_2026_07_09": iso(
            (item.timestamp_ms if (item := first_at_or_after(hourly, july_ms)) else None)
        ),
        "first_candle_before_instrument_launch": bool(hourly and hourly[0].timestamp_ms < launch_ms),
        "first_candle_before_public_rtoken_launch": bool(hourly and hourly[0].timestamp_ms < june_ms),
        "hourly_bars_before_2026_06_02": sum(item.timestamp_ms < june_ms for item in hourly),
        "hourly_bars_on_or_after_2026_06_02": sum(item.timestamp_ms >= june_ms for item in hourly),
        "bars_before_2026_07_09_with_non_empty_volume": sum(
            item.timestamp_ms < july_ms and item.volume is not None for item in hourly
        ),
        "trusted_certification_start": iso(certification_start_ms(launch_ms)),
        "volume_valid_from": iso(max(certification_start_ms(launch_ms), july_ms)),
        "provenance_conclusion": "AMBIGUOUS_BEFORE_TRUSTED_CERTIFICATION_START",
    }


def gap_semantics(
    symbol: str,
    hourly: list[Candle],
    certification_ms: int,
    trading_periods: set[str],
    weekend_tradable: bool,
    closures: list[tuple[datetime, datetime]],
) -> dict[str, Any]:
    eligible = [item for item in hourly if item.timestamp_ms >= certification_ms]
    if not eligible:
        return {"symbol": symbol, "status": "NO_DATA"}
    actual = {item.timestamp_ms for item in eligible}
    first_hour = ((certification_ms + 3_599_999) // 3_600_000) * 3_600_000
    last_hour = eligible[-1].timestamp_ms
    observed_expected = 0
    expected_open_missing = 0
    expected_closed = 0
    observed_during_expected_closed = 0
    longest = 0
    current = 0
    missing_examples = []
    session_counts: dict[str, dict[str, int]] = {}
    timestamp = first_hour
    while timestamp <= last_hour:
        midpoint = datetime.fromtimestamp((timestamp + 1_800_000) / 1000, tz=UTC)
        label = classify_session(midpoint, closures).value
        is_open = label in trading_periods or (label == SessionLabel.WEEKEND.value and weekend_tradable)
        present = timestamp in actual
        bucket = session_counts.setdefault(label, {"expected": 0, "observed": 0, "missing": 0})
        if is_open:
            bucket["expected"] += 1
            if present:
                observed_expected += 1
                bucket["observed"] += 1
                current = 0
            else:
                expected_open_missing += 1
                bucket["missing"] += 1
                current += 1
                longest = max(longest, current)
                if len(missing_examples) < 20:
                    missing_examples.append(iso(timestamp))
        else:
            expected_closed += 1
            current = 0
            if present:
                observed_during_expected_closed += 1
        timestamp += 3_600_000
    expected = observed_expected + expected_open_missing
    return {
        "symbol": symbol,
        "status": "PASS" if expected_open_missing == 0 else "DEGRADED",
        "certification_start": iso(certification_ms),
        "actual_bars_after_certification_start": len(eligible),
        "expected_open_bars": expected,
        "observed_expected_open_bars": observed_expected,
        "expected_open_missing_bars": expected_open_missing,
        "intentional_closed_hours": expected_closed,
        "observed_during_expected_closed": observed_during_expected_closed,
        "longest_unexplained_gap_hours": longest,
        "percent_completeness": observed_expected / expected if expected else 0.0,
        "missing_examples": missing_examples,
        "session_breakdown": session_counts,
        "classification": ["OBSERVED", "EXPECTED_OPEN_MISSING", "EXPECTED_CLOSED"],
    }


def _distribution(values: list[Decimal | None]) -> dict[str, Any]:
    present = [float(value) for value in values if value is not None]
    positive = [value for value in present if value > 0]
    return {
        "rows": len(values),
        "null_or_empty": len(values) - len(present),
        "zero": sum(value == 0 for value in present),
        "positive": len(positive),
        "min_positive": min(positive) if positive else None,
        "median_positive": statistics.median(positive) if positive else None,
        "max_positive": max(positive) if positive else None,
    }


def volume_summary(symbol: str, hourly: list[Candle], closures: list[tuple[datetime, datetime]]) -> dict[str, Any]:
    july_ms = int(DOCUMENTED_VOLUME_START.timestamp() * 1000)
    before = [item for item in hourly if item.timestamp_ms < july_ms]
    after = [item for item in hourly if item.timestamp_ms >= july_ms]
    regular = [item for item in hourly if classify_session(item.timestamp, closures) == SessionLabel.REGULAR]
    overnight = [item for item in hourly if classify_session(item.timestamp, closures) == SessionLabel.OVERNIGHT]
    return {
        "symbol": symbol,
        "before_2026_07_09": {
            "base_volume": _distribution([item.volume for item in before]),
            "quote_turnover": _distribution([item.turnover for item in before]),
        },
        "on_or_after_2026_07_09": {
            "base_volume": _distribution([item.volume for item in after]),
            "quote_turnover": _distribution([item.turnover for item in after]),
        },
        "regular_session_base_volume": _distribution([item.volume for item in regular]),
        "overnight_base_volume": _distribution([item.volume for item in overnight]),
        "provenance": "UNESTABLISHED",
        "dsl_status": "DISABLED",
    }
