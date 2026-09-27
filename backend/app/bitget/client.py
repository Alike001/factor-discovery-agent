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
                by_timestamp[candle.timestamp_ms] = candle
            oldest = min(candle.timestamp_ms for candle in page)
            if oldest <= launch_ms or (end_ms is not None and oldest >= end_ms):
                break
            end_ms = oldest - 1
        return [by_timestamp[key] for key in sorted(by_timestamp) if key >= launch_ms - INTERVAL_MS[interval]]


def closed_candles(candles: list[Candle], interval: str, now_ms: int | None = None) -> list[Candle]:
    current_ms = now_ms if now_ms is not None else int(datetime.now(UTC).timestamp() * 1000)
    duration = INTERVAL_MS[interval]
    return [candle for candle in candles if candle.timestamp_ms + duration <= current_ms]

