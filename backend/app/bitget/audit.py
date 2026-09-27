from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from .client import INTERVAL_MS, closed_candles
from .models import Candle, CandleAudit


def iso(timestamp_ms: int | None) -> str | None:
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).isoformat()


def audit_candles(symbol: str, interval: str, candles: list[Candle], now_ms: int) -> CandleAudit:
    timestamps = [item.timestamp_ms for item in candles]
    duplicates = sorted(timestamp for timestamp, count in Counter(timestamps).items() if count > 1)
    unique = sorted({item.timestamp_ms: item for item in candles}.values(), key=lambda item: item.timestamp_ms)
    completed = closed_candles(unique, interval, now_ms)
    duration = INTERVAL_MS[interval]
    gaps: list[dict[str, Any]] = []
    for previous, current in zip(unique, unique[1:]):
        missing = max(0, (current.timestamp_ms - previous.timestamp_ms) // duration - 1)
        if missing:
            gaps.append(
                {
                    "after": iso(previous.timestamp_ms),
                    "before": iso(current.timestamp_ms),
                    "missing_intervals": missing,
                }
            )
    volume_items = [item for item in unique if item.volume is not None]
    return CandleAudit(
        symbol=symbol,
        interval=interval,
        row_count=len(unique),
        first_timestamp=iso(unique[0].timestamp_ms if unique else None),
        last_timestamp=iso(unique[-1].timestamp_ms if unique else None),
        duplicate_timestamps=duplicates,
        gap_count=sum(item["missing_intervals"] for item in gaps),
        gaps=gaps,
        volume_non_empty_count=len(volume_items),
        volume_non_empty_coverage=(len(volume_items) / len(unique) if unique else 0),
        volume_non_empty_start=iso(volume_items[0].timestamp_ms if volume_items else None),
        most_recent_closed_candle=iso(completed[-1].timestamp_ms if completed else None),
    )

