from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import Iterable
from zoneinfo import ZoneInfo


NEW_YORK = ZoneInfo("America/New_York")


class AnchorStatus(StrEnum):
    READY = "READY"
    MISSING_EXPECTED_ANCHOR = "MISSING_EXPECTED_ANCHOR"


class SessionLabel(StrEnum):
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    OVERNIGHT = "overnight"
    WEEKEND = "weekend"
    CLOSED_HOLIDAY = "closed/holiday"


def parse_calendar_closures(items: Iterable[dict[str, str]]) -> list[tuple[datetime, datetime]]:
    closures = []
    for item in items:
        start = datetime.strptime(item["startTime"], "%Y-%m-%d %H:%M").replace(tzinfo=NEW_YORK)
        end = datetime.strptime(item["endTime"], "%Y-%m-%d %H:%M").replace(tzinfo=NEW_YORK)
        closures.append((start, end))
    return closures


def classify_session(timestamp: datetime, closures: list[tuple[datetime, datetime]] | None = None) -> SessionLabel:
    local = timestamp.astimezone(NEW_YORK)
    if any(start <= local < end for start, end in (closures or [])):
        return SessionLabel.CLOSED_HOLIDAY
    if local.weekday() >= 5 or (local.weekday() == 4 and local.time() >= time(20)):
        return SessionLabel.WEEKEND
    local_time = local.time()
    if time(4) <= local_time < time(9, 30):
        return SessionLabel.PRE_MARKET
    if time(9, 30) <= local_time < time(16):
        return SessionLabel.REGULAR
    if time(16) <= local_time < time(20):
        return SessionLabel.AFTER_HOURS
    return SessionLabel.OVERNIGHT


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
    return AnchorStatus.READY if expected in available_regular_dates else AnchorStatus.MISSING_EXPECTED_ANCHOR
