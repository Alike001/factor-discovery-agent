from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Candle(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    turnover: Decimal | None = None

    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=UTC)

    @classmethod
    def from_row(cls, row: list[Any]) -> "Candle":
        def optional_decimal(index: int) -> Decimal | None:
            if len(row) <= index or row[index] in (None, ""):
                return None
            return Decimal(str(row[index]))

        return cls(
            timestamp_ms=int(row[0]),
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=optional_decimal(5),
            turnover=optional_decimal(6),
        )


class CandleAudit(BaseModel):
    symbol: str
    interval: str
    row_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    duplicate_timestamps: list[int] = Field(default_factory=list)
    gap_count: int
    gaps: list[dict[str, Any]] = Field(default_factory=list)
    volume_non_empty_count: int
    volume_non_empty_coverage: float
    volume_non_empty_start: str | None
    most_recent_closed_candle: str | None


class CandleSeries(BaseModel):
    candles: list[Candle]

    @model_validator(mode="after")
    def timestamps_are_unique(self) -> "CandleSeries":
        timestamps = [item.timestamp_ms for item in self.candles]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("duplicate candle timestamps detected")
        return self

