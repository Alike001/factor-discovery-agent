from decimal import Decimal

import pytest

from app.bitget.audit import audit_candles
from app.bitget.client import closed_candles
from app.bitget.models import Candle, CandleSeries


def candle(timestamp_ms: int) -> Candle:
    return Candle(timestamp_ms=timestamp_ms, open=Decimal("1"), high=Decimal("1"), low=Decimal("1"), close=Decimal("1"))


def test_forming_candle_cannot_be_used() -> None:
    items = [candle(0), candle(3_600_000)]
    assert [item.timestamp_ms for item in closed_candles(items, "1H", now_ms=7_199_999)] == [0]


def test_duplicate_timestamps_detected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        CandleSeries(candles=[candle(0), candle(0)])
    audit = audit_candles("RTESTUSDT", "1H", [candle(0), candle(0)], now_ms=10_000_000)
    assert audit.duplicate_timestamps == [0]

