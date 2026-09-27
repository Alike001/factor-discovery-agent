from datetime import UTC, datetime
from decimal import Decimal

from app.bitget.integrity import gap_semantics
from app.bitget.models import Candle


def make_candle(timestamp: datetime) -> Candle:
    value = Decimal("1")
    return Candle(
        timestamp_ms=int(timestamp.timestamp() * 1000),
        open=value,
        high=value,
        low=value,
        close=value,
    )


def test_expected_closure_is_not_counted_as_missing() -> None:
    start = datetime(2026, 7, 3, 0, 0, tzinfo=UTC)
    end = datetime(2026, 7, 3, 4, 0, tzinfo=UTC)
    result = gap_semantics(
        "RTESTUSDT",
        [make_candle(start), make_candle(end)],
        int(start.timestamp() * 1000),
        {"overnight", "pre_market", "regular", "after_hours"},
        True,
        [(start, end)],
    )
    assert result["intentional_closed_hours"] == 4
    assert result["expected_open_missing_bars"] == 0


def test_expected_open_missing_is_classified_separately() -> None:
    start = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    end = datetime(2026, 6, 2, 14, 0, tzinfo=UTC)
    result = gap_semantics(
        "RTESTUSDT",
        [make_candle(start), make_candle(end)],
        int(start.timestamp() * 1000),
        {"overnight", "pre_market", "regular", "after_hours"},
        True,
        [],
    )
    assert result["expected_open_missing_bars"] == 1
    assert result["longest_unexplained_gap_hours"] == 1
