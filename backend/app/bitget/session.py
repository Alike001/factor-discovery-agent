from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo


NEW_YORK = ZoneInfo("America/New_York")


class AnchorStatus(StrEnum):
    READY = "READY"
    MISSING_ANCHOR = "MISSING_ANCHOR"


def is_market_holiday(day: date, closures: list[tuple[datetime, datetime]]) -> bool:
    noon = datetime.combine(day, time(12), tzinfo=NEW_YORK)
    return any(start <= noon <= end for start, end in closures)


def expected_last_regular_date(as_of: datetime, closures: list[tuple[datetime, datetime]] | None = None) -> date:
    closures = closures or []
    local = as_of.astimezone(NEW_YORK)
    candidate = local.date()
    if local.time() < time(16):
        candidate -= timedelta(days=1)
    while candidate.weekday() >= 5 or is_market_holiday(candidate, closures):
        candidate -= timedelta(days=1)
    return candidate


def validate_expected_anchor(expected: date, available_regular_dates: set[date]) -> AnchorStatus:
    return AnchorStatus.READY if expected in available_regular_dates else AnchorStatus.MISSING_ANCHOR

