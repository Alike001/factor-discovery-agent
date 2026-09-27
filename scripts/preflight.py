#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.bitget.audit import audit_candles, iso  # noqa: E402
from app.bitget.client import BitgetPublicClient, INTERVAL_MS  # noqa: E402
from app.config import Settings  # noqa: E402
from app.evidence import canonical_hash, write_json  # noqa: E402
from app.mcp.client import StockMCPClient  # noqa: E402
from app.qwen.client import probe_schema  # noqa: E402
from app.qwen.models import FactorProposal, LifecycleDecision, PortfolioDecision  # noqa: E402


PRIMARY = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "AMD", "QQQ"]
SECONDARY = ["SPY", "COIN", "HOOD", "MSTR"]
OUTPUT = ROOT / "evidence" / "preflight"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def public_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": now_iso(),
        "source": "Bitget live public API",
        "response_hash": canonical_hash(payload),
        "response": payload,
    }


async def fetch_symbol_candles(
    client: BitgetPublicClient,
    symbol: str,
    launch_ms: int,
    now_ms: int,
    semaphore: asyncio.Semaphore,
) -> tuple[str, dict[str, Any], list[Any]]:
    async with semaphore:
        one_hour = await client.all_history(symbol, "1H", launch_ms)
    seven_days_ms = now_ms - 7 * 24 * 60 * 60 * 1000
    async with semaphore:
        recent_15m = await client.recent_candles(symbol, "15m", 1000)
    recent_15m = [item for item in recent_15m if item.timestamp_ms >= seven_days_ms]
    audit_1h = audit_candles(symbol, "1H", one_hour, now_ms).model_dump(mode="json")
    audit_15m = audit_candles(symbol, "15m", recent_15m, now_ms).model_dump(mode="json")
    first_ms = min((item.timestamp_ms for item in one_hour), default=None)
    closed_1h = [item for item in one_hour if item.timestamp_ms + INTERVAL_MS["1H"] <= now_ms]
    closed_15m = [item for item in recent_15m if item.timestamp_ms + INTERVAL_MS["15m"] <= now_ms]
    history_days = round((now_ms - first_ms) / 86_400_000, 2) if first_ms else 0
    latest_1h_age = (now_ms - closed_1h[-1].timestamp_ms - INTERVAL_MS["1H"]) if closed_1h else 10**15
    latest_15m_age = (now_ms - closed_15m[-1].timestamp_ms - INTERVAL_MS["15m"]) if closed_15m else 10**15
    status = "PASS" if history_days >= 60 else "DEGRADED" if history_days >= 30 else "FAIL"
    if audit_1h["duplicate_timestamps"] or audit_15m["duplicate_timestamps"]:
        status = "FAIL"
    # Reality instruments can have scheduled closures; freshness is checked with a 72h weekend/holiday grace.
    if latest_1h_age > 72 * 3_600_000 or latest_15m_age > 72 * 3_600_000:
        status = "FAIL"
    result = {
        "status": status,
        "history_calendar_days": history_days,
        "one_hour": audit_1h,
        "recent_15m": audit_15m,
        "freshness": {
            "one_hour_closed_age_ms": latest_1h_age,
            "recent_15m_closed_age_ms": latest_15m_age,
            "allowed_grace_hours": 72,
        },
        "missing_data_policy": "REPORTED_NOT_FILLED",
    }
    return symbol, result, one_hour


def choose_tool(tools: list[dict[str, Any]], words: tuple[str, ...]) -> dict[str, Any] | None:
    scored = []
    for tool in tools:
        haystack = f"{tool.get('name', '')} {tool.get('description', '')}".lower()
        score = sum(1 for word in words if word in haystack)
        if score:
            scored.append((score, tool))
    return max(scored, key=lambda item: item[0])[1] if scored else None


def tool_args(tool: dict[str, Any], ticker: str, historical: bool) -> dict[str, Any]:
    properties = tool.get("inputSchema", {}).get("properties", {})
    values: dict[str, Any] = {}
    today = datetime.now(UTC).date()
    for key, schema in properties.items():
        lowered = key.lower()
        if lowered in {"symbol", "ticker", "stock_code", "code"}:
            values[key] = ticker
        elif historical and lowered in {"start", "start_date", "startdate", "from"}:
            values[key] = str(today - timedelta(days=10))
        elif historical and lowered in {"end", "end_date", "enddate", "to"}:
            values[key] = str(today)
        elif historical and lowered in {"interval", "period", "resolution", "timeframe"}:
            enum = schema.get("enum", [])
            values[key] = next((v for v in enum if str(v).lower() in {"1d", "day", "daily"}), enum[0] if enum else "1d")
        elif historical and lowered in {"limit", "count", "size"}:
            values[key] = 10
    return values


async def stock_mcp_check(settings: Settings) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "generated_at": now_iso(),
        "endpoint": settings.stock_mcp_url,
        "status": "DEGRADED",
        "capability": "RTOKEN_ONLY_PHASE1",
        "catalog": [],
        "queries": [],
    }
    try:
        async with StockMCPClient(settings.stock_mcp_url) as mcp:
            status, initialized, _ = await mcp.initialize()
            artifact["initialize"] = {"http_status": status, "payload": initialized}
            if status != 200 or "error" in initialized:
                artifact["reason"] = initialized.get("error", {}).get("message", "initialize failed")
                return artifact
            _, listed, _ = await mcp.call("tools/list", {}, 2)
            tools = listed.get("result", {}).get("tools", [])
            artifact["catalog"] = tools
            quote_tool = choose_tool(tools, ("quote", "real-time", "realtime", "price"))
            history_tool = choose_tool(tools, ("histor", "kline", "candle"))
            artifact["selected_tools"] = {
                "quote": quote_tool.get("name") if quote_tool else None,
                "history": history_tool.get("name") if history_tool else None,
            }
            request_id = 10
            for ticker in ("NVDA", "AAPL"):
                for kind, tool in (("quote", quote_tool), ("history", history_tool)):
                    if tool is None:
                        continue
                    _, result, _ = await mcp.call(
                        "tools/call",
                        {"name": tool["name"], "arguments": tool_args(tool, ticker, kind == "history")},
                        request_id,
                    )
                    request_id += 1
                    artifact["queries"].append({"ticker": ticker, "kind": kind, "result": result})
            complete = len(artifact["queries"]) == 4 and all("error" not in item["result"] for item in artifact["queries"])
            artifact["status"] = "PASS" if complete else "DEGRADED"
            artifact["capability"] = "POINT_IN_TIME_REVIEW_REQUIRED" if complete else "RTOKEN_ONLY_PHASE1"
            if complete:
                artifact["reason"] = "Queries succeeded; timestamp semantics still require explicit review before historical use."
            return artifact
    except Exception as exc:
        artifact["reason"] = f"{type(exc).__name__}: {exc}"
        return artifact


async def qwen_check(settings: Settings) -> dict[str, Any]:
    if not settings.qwen_api_key:
        return {
            "generated_at": now_iso(),
            "status": "BLOCKED_KEY",
            "base_url": settings.qwen_base_url,
            "model": settings.qwen_model,
            "probes": [],
            "secret_persisted": False,
        }
    async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=90.0) as client:
        probes = []
        for schema, purpose in (
            (FactorProposal, "FactorProposal"),
            (LifecycleDecision, "LifecycleDecision"),
            (PortfolioDecision, "PortfolioDecision"),
        ):
            probes.append(
                await probe_schema(
                    client,
                    model=settings.qwen_model,
                    api_key=settings.qwen_api_key,
                    schema=schema,
                    purpose=purpose,
                )
            )
    return {
        "generated_at": now_iso(),
        "status": "PASS" if all(item["validation"]["valid"] for item in probes) else "FAIL",
        "base_url": settings.qwen_base_url,
        "model": settings.qwen_model,
        "probes": probes,
        "secret_persisted": False,
    }


def signed_headers(settings: Settings, path_with_query: str, demo: bool = False) -> dict[str, str]:
    key = settings.demo_api_key if demo else settings.bitget_api_key
    secret = settings.demo_api_secret if demo else settings.bitget_api_secret
    passphrase = settings.demo_api_passphrase if demo else settings.bitget_api_passphrase
    timestamp = str(int(time.time() * 1000))
    signature = base64.b64encode(
        hmac.new(secret.encode(), f"{timestamp}GET{path_with_query}".encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "ACCESS-KEY": key or "",
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": passphrase or "",
        **({"paptrading": "1"} if demo else {}),
    }


async def fee_check(settings: Settings, symbol: str) -> dict[str, Any]:
    if not all((settings.bitget_api_key, settings.bitget_api_secret, settings.bitget_api_passphrase)):
        return {
            "generated_at": now_iso(),
            "status": "ACCOUNT_FEE_UNVERIFIED",
            "symbol": symbol,
            "basis": "ASSUMED_PUBLISHED_BASELINE",
            "fee_per_fill": 0.0005,
            "stress_fee_per_fill": 0.001,
        }
    path = f"/api/v3/account/fee-rate?symbol={symbol}&category=SPOT"
    async with httpx.AsyncClient(base_url=settings.bitget_base_url, timeout=30.0) as client:
        response = await client.get(path, headers=signed_headers(settings, path))
    payload = response.json()
    return {
        "generated_at": now_iso(),
        "status": "PASS" if response.status_code == 200 and payload.get("code") == "00000" else "FAIL",
        "symbol": symbol,
        "http_status": response.status_code,
        "response": payload,
    }


async def demo_check(settings: Settings) -> dict[str, Any]:
    if not all((settings.demo_api_key, settings.demo_api_secret, settings.demo_api_passphrase)):
        return {
            "generated_at": now_iso(),
            "status": "UNVERIFIED_NO_CREDENTIALS",
            "execution_mode": "local_paper",
            "probe_attempted": False,
        }
    # A Demo mutation requires POST signing and a carefully priced/cancelled order. Keep the live preflight
    # fail-closed until that authenticated adapter is explicitly configured and exercised.
    return {
        "generated_at": now_iso(),
        "status": "INCONCLUSIVE",
        "execution_mode": "local_paper",
        "probe_attempted": False,
        "reason": "Demo credentials detected, but the safe order/cancel adapter is not enabled in Phase 0.",
    }


async def main() -> None:
    settings = Settings.from_env()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    async with BitgetPublicClient(settings.bitget_base_url) as client:
        instruments_payload, stock_payload, states_payload, calendar_payload = await asyncio.gather(
            client.instruments(), client.stock_info(), client.market_states(), client.market_calendar()
        )
        reality = [item for item in instruments_payload["data"] if item.get("isReality") == "yes"]
        compact_universe = []
        for item in reality:
            compact_universe.append(
                {
                    "symbol": item.get("symbol"),
                    "baseCoin": item.get("baseCoin"),
                    "status": item.get("status"),
                    "launchTime": item.get("launchTime"),
                    "precision": {
                        "price": item.get("pricePrecision"),
                        "quantity": item.get("quantityPrecision"),
                        "quote": item.get("quotePrecision"),
                    },
                    "minOrderAmount": item.get("minOrderAmount"),
                    "raw_response_hash": canonical_hash(item),
                }
            )
        write_json(
            OUTPUT / "reality-universe.json",
            {
                "generated_at": now_iso(),
                "status": "PASS",
                "source": "GET /api/v3/market/instruments?category=SPOT",
                "response_hash": canonical_hash(instruments_payload),
                "count": len(compact_universe),
                "instruments": compact_universe,
            },
        )
        write_json(OUTPUT / "reality-stock-info.json", public_artifact(stock_payload))
        write_json(OUTPUT / "market-states.json", public_artifact(states_payload))
        write_json(OUTPUT / "market-calendar.json", public_artifact(calendar_payload))

        stock_symbols = {item.get("symbol") for item in stock_payload.get("data", [])}
        online = {item["symbol"]: item for item in reality if item.get("status") == "online"}
        candidates = []
        for ticker in PRIMARY + SECONDARY:
            symbol = f"R{ticker}USDT"
            if symbol in online and symbol in stock_symbols:
                candidates.append((symbol, int(online[symbol]["launchTime"]), ticker in PRIMARY))
        semaphore = asyncio.Semaphore(3)
        results = await asyncio.gather(
            *(fetch_symbol_candles(client, symbol, launch, now_ms, semaphore) for symbol, launch, _ in candidates),
            return_exceptions=True,
        )

    coverage: dict[str, Any] = {}
    hourly_by_symbol: dict[str, list[Any]] = {}
    primary_flags = {symbol: primary for symbol, _, primary in candidates}
    for candidate, result in zip(candidates, results):
        symbol = candidate[0]
        if isinstance(result, Exception):
            coverage[symbol] = {"status": "FAIL", "error": f"{type(result).__name__}: {result}"}
        else:
            _, detail, candles = result
            coverage[symbol] = detail
            hourly_by_symbol[symbol] = candles
    selected = [symbol for symbol, detail in coverage.items() if detail.get("status") in {"PASS", "DEGRADED"}]
    selected_primary = [symbol for symbol in selected if primary_flags[symbol]]
    write_json(
        OUTPUT / "candle-coverage.json",
        {
            "generated_at": now_iso(),
            "status": "PASS" if len(selected_primary) >= 4 else "FAIL",
            "source": "Bitget live history-candles and candles endpoints",
            "forming_candles_excluded_from_latest_closed": True,
            "symbols": coverage,
        },
    )
    write_json(
        OUTPUT / "core-universe.json",
        {
            "generated_at": now_iso(),
            "status": "PASS" if len(selected_primary) >= 4 else "FAIL",
            "selection_rule": "online Reality + stock-info mapping + usable 1H history + recent closed 15m",
            "primary_selected": selected_primary,
            "secondary_selected": [symbol for symbol in selected if not primary_flags[symbol]],
            "excluded": {symbol: coverage[symbol] for symbol, _, _ in candidates if symbol not in selected},
        },
    )

    stock_mcp, qwen, fees, demo = await asyncio.gather(
        stock_mcp_check(settings),
        qwen_check(settings),
        fee_check(settings, selected_primary[0] if selected_primary else "RNVDAUSDT"),
        demo_check(settings),
    )
    write_json(OUTPUT / "stock-mcp.json", stock_mcp)
    write_json(OUTPUT / "qwen.json", qwen)
    write_json(OUTPUT / "fees.json", fees)
    write_json(OUTPUT / "reality-demo.json", demo)

    sixty_day = any(detail.get("history_calendar_days", 0) >= 60 for detail in coverage.values())
    public_research = len(selected_primary) >= 4 and sixty_day
    overall = "PASS_WITH_LIMITATIONS" if public_research else "FAIL"
    preflight = {
        "generated_at": now_iso(),
        "overall": overall,
        "phase1_public_reality_research": "GO" if public_research else "NO_GO",
        "submission_deadline": "2026-10-08T23:59:00+08:00",
        "reality_universe": {"status": "PASS", "count": len(reality)},
        "core_universe": {"status": "PASS" if len(selected_primary) >= 4 else "FAIL", "selected": selected_primary},
        "candles": {"status": "PASS" if public_research else "FAIL", "has_60_day_symbol": sixty_day},
        "stock_mcp": {"status": stock_mcp["status"], "phase1_dependency": False},
        "session_calendar": {"status": "PASS"},
        "qwen": {"status": qwen["status"], "phase1_tracer_dependency": False},
        "fees": {"status": fees["status"], "phase1_basis": fees.get("basis", "ACCOUNT_OBSERVED")},
        "demo_reality": {"status": demo["status"], "phase1_dependency": False},
        "database": {
            "status": "UNVERIFIED" if not settings.database_url else "CONFIGURED_NOT_MUTATED",
            "deployment_mode": "GitHub Actions idempotent one-shot jobs + Neon",
        },
        "execution_mode": "local_paper",
        "limitations": [
            "Gap counts are raw interval gaps and include scheduled market closures; no gaps were filled.",
            "Stock MCP is excluded from the Phase 1 rToken-only tracer unless timestamp semantics pass.",
            "Missing credentials are reported, never replaced with fixtures.",
        ],
    }
    write_json(OUTPUT / "preflight.json", preflight)
    print(json.dumps(preflight, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

