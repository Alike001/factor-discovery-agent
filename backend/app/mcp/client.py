from __future__ import annotations

import json
from typing import Any

import httpx


class StockMCPClient:
    def __init__(self, url: str, timeout: float = 30.0):
        self.url = url
        self.client = httpx.AsyncClient(timeout=timeout, headers={"Accept": "application/json, text/event-stream"})
        self.session_id: str | None = None

    async def __aenter__(self) -> "StockMCPClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.client.aclose()

    async def call(self, method: str, params: dict[str, Any], request_id: int) -> tuple[int, dict[str, Any], dict[str, str]]:
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        response = await self.client.post(
            self.url,
            headers=headers,
            json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
        )
        if response.headers.get("mcp-session-id"):
            self.session_id = response.headers["mcp-session-id"]
        text = response.text
        if text.startswith("event:"):
            data_lines = [line.removeprefix("data:").strip() for line in text.splitlines() if line.startswith("data:")]
            payload = json.loads(data_lines[-1]) if data_lines else {"raw": text}
        else:
            payload = response.json()
        return response.status_code, payload, dict(response.headers)

    async def initialize(self) -> tuple[int, dict[str, Any], dict[str, str]]:
        return await self.call(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "bitget-preflight", "version": "0.1.0"},
            },
            1,
        )

