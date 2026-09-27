from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx

from .models import Candle


INTERVAL_MS = {"15m": 900_000, "1H": 3_600_000}


class BitgetAPIError(RuntimeError):
    pass


class BitgetPublicClient:
    def __init__(self, base_url: str = "https://api.bitget.com", timeout: float = 30.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def __aenter__(self) -> "BitgetPublicClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = await self._client.get(path, params=params)
                response.raise_for_status()
                payload = response.json()
                if payload.get("code") != "00000":
                    raise BitgetAPIError(f"{path}: {payload.get('code')} {payload.get('msg')}")
                return payload
            except (httpx.HTTPError, BitgetAPIError) as exc:
                last_error = exc
                if attempt == 3:
                    raise
                await asyncio.sleep(0.4 * (2**attempt))
        raise RuntimeError(str(last_error))

    async def instruments(self) -> dict[str, Any]:
        return await self._get("/api/v3/market/instruments", {"category": "SPOT"})

    async def stock_info(self) -> dict[str, Any]:
        return await self._get("/api/v3/reality/market/stock-info")

    async def market_states(self) -> dict[str, Any]:
        return await self._get("/api/v3/reality/market/states")

    async def market_calendar(self) -> dict[str, Any]:
        return await self._get("/api/v3/reality/market/calendar")

    async def recent_candles(self, symbol: str, interval: str, limit: int = 1000) -> list[Candle]:
        payload = await self._get(
            "/api/v3/market/candles",
            {"category": "SPOT", "symbol": symbol, "interval": interval, "type": "market", "limit": limit},
        )
        return [Candle.from_row(row) for row in payload["data"]]

    async def candle_page(
        self, symbol: str, interval: str, *, end_ms: int | None = None, limit: int = 1000
    ) -> list[Candle]:
        params: dict[str, Any] = {
            "category": "SPOT",
            "symbol": symbol,
            "interval": interval,
            "type": "market",
            "limit": limit,
        }
        if end_ms is not None:
            params["endTime"] = end_ms
        payload = await self._get("/api/v3/market/candles", params)
        return [Candle.from_row(row) for row in payload["data"]]

    async def complete_candle_history(
        self, symbol: str, interval: str, *, lower_bound_ms: int, max_pages: int = 500
    ) -> list[Candle]:
        by_timestamp: dict[int, Candle] = {}
        cursor: int | None = None
        for _ in range(max_pages):
            page = await self.candle_page(symbol, interval, end_ms=cursor, limit=1000)
            if not page:
                break
            for candle in page:
                if candle.timestamp_ms in by_timestamp:
                    raise ValueError(f"duplicate candle timestamp from source: {candle.timestamp_ms}")
                by_timestamp[candle.timestamp_ms] = candle
            oldest = min(candle.timestamp_ms for candle in page)
            if oldest <= lower_bound_ms:
                break
            cursor = oldest - 1
        return [by_timestamp[key] for key in sorted(by_timestamp) if key >= lower_bound_ms]

    async def earliest_candle(
        self, symbol: str, interval: str, *, lower_bound_ms: int, upper_bound_ms: int
    ) -> Candle | None:
        day_ms = 86_400_000
        low_day = lower_bound_ms // day_ms
        high_day = upper_bound_ms // day_ms
        while low_day < high_day:
            middle = (low_day + high_day) // 2
            page = await self.history_page(symbol, interval, (middle + 1) * day_ms - 1)
            if page:
                high_day = middle
            else:
                low_day = middle + 1
        end_ms = (low_day + 3) * day_ms - 1
        page = await self.candle_page(symbol, interval, end_ms=end_ms, limit=1000)
        eligible = [item for item in page if item.timestamp_ms >= low_day * day_ms]
        return min(eligible, key=lambda item: item.timestamp_ms) if eligible else None

    async def history_page(self, symbol: str, interval: str, end_ms: int | None = None) -> list[Candle]:
        params: dict[str, Any] = {
            "category": "SPOT",
            "symbol": symbol,
            "interval": interval,
            "type": "market",
            "limit": 100,
        }
        if end_ms is not None:
            params["endTime"] = end_ms
        payload = await self._get("/api/v3/market/history-candles", params)
        return [Candle.from_row(row) for row in payload["data"]]

    async def all_history(self, symbol: str, interval: str, launch_ms: int, max_pages: int = 40) -> list[Candle]:
        by_timestamp: dict[int, Candle] = {}
        end_ms: int | None = None
        for _ in range(max_pages):
            page = await self.history_page(symbol, interval, end_ms)
            if not page:
                break
            for candle in page:
                if candle.timestamp_ms in by_timestamp:
                    raise ValueError(f"duplicate candle timestamp from source: {candle.timestamp_ms}")
                by_timestamp[candle.timestamp_ms] = candle
            oldest = min(candle.timestamp_ms for candle in page)
            if oldest <= launch_ms or (end_ms is not None and oldest >= end_ms):
                break
            end_ms = oldest - 1
        return [by_timestamp[key] for key in sorted(by_timestamp) if key >= launch_ms - INTERVAL_MS[interval]]

    async def history_range_backward(
        self,
        symbol: str,
        interval: str,
        *,
        end_ms: int,
        lower_bound_ms: int,
        max_pages: int,
    ) -> list[Candle]:
        by_timestamp: dict[int, Candle] = {}
        cursor = end_ms
        for _ in range(max_pages):
            page = await self.history_page(symbol, interval, cursor)
            if not page:
                break
            for candle in page:
                if candle.timestamp_ms in by_timestamp:
                    raise ValueError(f"duplicate candle timestamp from source: {candle.timestamp_ms}")
                by_timestamp[candle.timestamp_ms] = candle
            oldest = min(candle.timestamp_ms for candle in page)
            if oldest <= lower_bound_ms:
                break
            cursor = oldest - 1
        return [by_timestamp[key] for key in sorted(by_timestamp) if key >= lower_bound_ms]


def closed_candles(candles: list[Candle], interval: str, now_ms: int | None = None) -> list[Candle]:
    current_ms = now_ms if now_ms is not None else int(datetime.now(UTC).timestamp() * 1000)
    duration = INTERVAL_MS[interval]
    return [candle for candle in candles if candle.timestamp_ms + duration <= current_ms]
