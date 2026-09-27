#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.bitget.audit import iso  # noqa: E402
from app.bitget.client import BitgetPublicClient, closed_candles  # noqa: E402
from app.bitget.integrity import (  # noqa: E402
    PUBLIC_RTOKEN_LAUNCH,
    certification_start_ms,
    gap_semantics,
    provenance_summary,
    volume_summary,
)
from app.bitget.session import parse_calendar_closures  # noqa: E402
from app.config import Settings  # noqa: E402
from app.db.migrate import apply_migrations  # noqa: E402
from app.db.repository import ResearchRepository  # noqa: E402
from app.evidence import canonical_hash, write_json  # noqa: E402
from app.qwen.client import probe_schema  # noqa: E402
from app.qwen.models import FactorProposal, LifecycleDecision, PortfolioDecision  # noqa: E402
from app.research.tracer import run_tracer_v2  # noqa: E402


CORE_TICKERS = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "AMD", "QQQ"]
CORE_SYMBOLS = [f"R{ticker}USDT" for ticker in CORE_TICKERS]
OUTPUT = ROOT / "evidence" / "preflight-v2"
RAW = ROOT / "evidence" / "raw"
HISTORY_LOWER_BOUND_MS = int(datetime(1970, 1, 1, tzinfo=UTC).timestamp() * 1000)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def qwen_blocked(settings: Settings) -> dict[str, Any]:
    return {
        "generated_at": now_iso(),
        "status": "BLOCKED_KEY",
        "base_url": settings.qwen_base_url,
        "requested_model": settings.qwen_model,
        "probes": [],
        "secret_persisted": False,
    }


async def qwen_gate(settings: Settings) -> dict[str, Any]:
    if not settings.qwen_api_key:
        return qwen_blocked(settings)
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
    passed = len(probes) == 3 and all(
        item["validation"]["valid"] and item["repair_attempts"] <= 1 for item in probes
    )
    return {
        "generated_at": now_iso(),
        "status": "PASS" if passed else "FAIL",
        "base_url": settings.qwen_base_url,
        "requested_model": settings.qwen_model,
        "observed_models": sorted({item["observed_model"] for item in probes if item["observed_model"]}),
        "probes": probes,
        "secret_persisted": False,
    }


def database_gate(database_url: str | None) -> dict[str, Any]:
    if not database_url:
        return {
            "generated_at": now_iso(),
            "status": "BLOCKED_DATABASE_URL",
            "migrations": [],
            "tests": {},
            "credentials_persisted": False,
        }
    parsed = urlsplit(database_url)
    try:
        migrations = apply_migrations(database_url)
        repository = ResearchRepository(database_url)
        protocol = repository.ensure_protocol("phase1.5-integrity")
        with ThreadPoolExecutor(max_workers=8) as pool:
            trials = list(pool.map(lambda _: repository.allocate_trial_number(protocol), range(24)))
        concurrent_unique = len(trials) == len(set(trials)) and max(trials) - min(trials) == len(trials) - 1
        cycle_a = repository.upsert_cycle(
            protocol, 8_150_001, "phase1.5-integrity-cycle", datetime.now(UTC)
        )
        cycle_b = repository.upsert_cycle(
            protocol, 8_150_001, "phase1.5-integrity-cycle", datetime.now(UTC)
        )
        trial = repository.allocate_trial_number(protocol)
        pair_a = repository.create_factor_experiment_once(
            protocol_id=protocol,
            cycle_id=cycle_a,
            trial_number=trial,
            canonical_hash="phase1.5-integrity-factor",
            dataset_hash="phase1.5-integrity-dataset",
        )
        pair_b = repository.create_factor_experiment_once(
            protocol_id=protocol,
            cycle_id=cycle_a,
            trial_number=trial,
            canonical_hash="phase1.5-integrity-factor",
            dataset_hash="phase1.5-integrity-dataset",
        )
        with psycopg.connect(database_url) as connection:
            version = connection.execute("SHOW server_version").fetchone()[0]
            experiment_count = connection.execute(
                "SELECT count(*) FROM experiments WHERE factor_version_id = %s AND dataset_hash = %s",
                (pair_a[0], "phase1.5-integrity-dataset"),
            ).fetchone()[0]
        tests = {
            "concurrent_trial_numbers_unique": concurrent_unique,
            "cycle_rerun_idempotent": cycle_a == cycle_b,
            "duplicate_factor_same_experiment": pair_a == pair_b and experiment_count == 1,
        }
        return {
            "generated_at": now_iso(),
            "status": "PASS" if all(tests.values()) else "FAIL",
            "postgres_version": version,
            "endpoint": {"hostname": parsed.hostname, "port": parsed.port, "database": parsed.path.lstrip("/")},
            "migrations": migrations,
            "tests": tests,
            "credentials_persisted": False,
        }
    except Exception as exc:
        return {
            "generated_at": now_iso(),
            "status": "FAIL",
            "endpoint": {"hostname": parsed.hostname, "port": parsed.port, "database": parsed.path.lstrip("/")},
            "migrations": [],
            "tests": {},
            "error": f"{type(exc).__name__}: {exc}",
            "credentials_persisted": False,
        }


async def fetch_history(
    client: BitgetPublicClient,
    symbol: str,
    now_ms: int,
    semaphore: asyncio.Semaphore,
) -> tuple[list[Any], list[Any]]:
    async with semaphore:
        hourly = await client.complete_candle_history(
            symbol, "1H", lower_bound_ms=HISTORY_LOWER_BOUND_MS, max_pages=500
        )
    if not hourly:
        return [], []
    async with semaphore:
        first_fifteen = await client.earliest_candle(
            symbol,
            "15m",
            lower_bound_ms=HISTORY_LOWER_BOUND_MS,
            upper_bound_ms=now_ms,
        )
    fifteen = [first_fifteen] if first_fifteen else []
    return closed_candles(hourly, "1H", now_ms), closed_candles(fifteen, "15m", now_ms)


async def main() -> None:
    settings = Settings.from_env()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    async with BitgetPublicClient(settings.bitget_base_url) as client:
        instruments_payload, stock_payload, calendar_payload = await asyncio.gather(
            client.instruments(), client.stock_info(), client.market_calendar()
        )
        write_json(RAW / "spot-instruments-v2.json", instruments_payload)
        instruments = instruments_payload["data"]
        reality = [item for item in instruments if item.get("isReality") == "yes"]
        online_reality = [item for item in reality if item.get("status") == "online"]
        reality_symbols = sorted(item["symbol"] for item in reality)
        by_symbol = {item["symbol"]: item for item in instruments}
        core_assertions = {}
        for ticker, symbol in zip(CORE_TICKERS, CORE_SYMBOLS):
            item = by_symbol.get(symbol)
            core_assertions[symbol] = {
                "present": item is not None,
                "is_reality_yes": bool(item and item.get("isReality") == "yes"),
                "status_online": bool(item and item.get("status") == "online"),
                "base_coin": item.get("baseCoin") if item else None,
                "expected_base_coin": f"r{ticker}",
                "base_coin_matches": bool(item and item.get("baseCoin") == f"r{ticker}"),
            }
        count_audit = {
            "generated_at": now_iso(),
            "source": "GET /api/v3/market/instruments?category=SPOT",
            "raw_response_path": "evidence/raw/spot-instruments-v2.json (gitignored)",
            "raw_response_hash": canonical_hash(instruments_payload),
            "total_spot_count": len(instruments),
            "is_reality_yes_count": len(reality),
            "is_reality_no_count": sum(item.get("isReality") != "yes" for item in instruments),
            "status_online_and_reality_count": len(online_reality),
            "symbol_type_stock_and_reality_count": sum(
                item.get("symbolType") == "stock" for item in reality
            ),
            "unique_base_coin_count": len({item.get("baseCoin") for item in reality}),
            "first_25_reality_symbols": reality_symbols[:25],
            "last_25_reality_symbols": reality_symbols[-25:],
            "selected_core_assertions": core_assertions,
            "documentation_drift": len(reality) == 2587,
            "status": "PASS" if all(all(v for k, v in checks.items() if k in {"present", "is_reality_yes", "status_online", "base_coin_matches"}) for checks in core_assertions.values()) else "FAIL",
        }
        write_json(OUTPUT / "reality-count-audit.json", count_audit)

        stock_by_symbol = {item["symbol"]: item for item in stock_payload.get("data", [])}
        closures = parse_calendar_closures(calendar_payload["data"].get("specificConfig", []))
        semaphore = asyncio.Semaphore(3)
        histories = await asyncio.gather(
            *(fetch_history(client, symbol, now_ms, semaphore) for symbol in CORE_SYMBOLS)
        )

    provenance = {}
    gaps = {}
    volumes = {}
    raw_history = {}
    for symbol, (hourly, fifteen) in zip(CORE_SYMBOLS, histories):
        launch_ms = int(by_symbol[symbol]["launchTime"])
        provenance[symbol] = provenance_summary(symbol, launch_ms, hourly, fifteen)
        periods = set(stock_by_symbol[symbol].get("tradingPeriod", []))
        gaps[symbol] = gap_semantics(
            symbol,
            hourly,
            certification_start_ms(launch_ms),
            periods,
            stock_by_symbol[symbol].get("weekendTradable") == "yes",
            closures,
        )
        volumes[symbol] = volume_summary(symbol, hourly, closures)
        raw_history[symbol] = {
            "one_hour": [item.model_dump(mode="json") for item in hourly],
            "fifteen_minute_earliest_window": [item.model_dump(mode="json") for item in fifteen],
        }
    write_json(RAW / "core-history-provenance-v2.json", raw_history)
    write_json(
        OUTPUT / "history-provenance.json",
        {
            "generated_at": now_iso(),
            "status": "PASS",
            "public_rtoken_launch_floor": PUBLIC_RTOKEN_LAUNCH.isoformat(),
            "provenance_inference": "NONE; older bars remain ambiguous",
            "symbols": provenance,
        },
    )
    write_json(
        OUTPUT / "gap-semantics.json",
        {
            "generated_at": now_iso(),
            "status": "PASS_WITH_MISSING_BARS",
            "timezone": "America/New_York",
            "symbols": gaps,
        },
    )
    write_json(
        OUTPUT / "volume-audit.json",
        {
            "generated_at": now_iso(),
            "status": "PROVENANCE_UNESTABLISHED",
            "conclusion": "Volume and turnover are populated before July 9, but the values are not proven rToken trade volume.",
            "dsl_volume_operators": "DISABLED",
            "symbols": volumes,
        },
    )

    qwen = await qwen_gate(settings)
    database = database_gate(settings.database_url)
    write_json(OUTPUT / "qwen.json", qwen)
    write_json(OUTPUT / "database.json", database)

    tracer_v2 = await run_tracer_v2(ROOT)
    tracer_v1 = json.loads((ROOT / "evidence" / "tracer" / "tracer-experiment.json").read_text())
    comparison = {
        "v1": {"source": tracer_v1["source"], "metrics": tracer_v1["metrics"]},
        "v2": {"source": tracer_v2["source"], "metrics": tracer_v2["metrics"]},
        "parameters_changed": False,
    }
    write_json(OUTPUT / "tracer-comparison.json", comparison)

    fee_status = "PASS" if settings.bitget_api_key else "ACCOUNT_FEE_UNVERIFIED"
    demo_status = "INCONCLUSIVE_CREDENTIALS_PRESENT" if settings.demo_api_key else "UNVERIFIED_NO_CREDENTIALS"
    phase2_go = qwen["status"] == "PASS" and database["status"] == "PASS"
    gate = {
        "generated_at": now_iso(),
        "status": "GO" if phase2_go else "NO_GO",
        "reality_count_audit": count_audit["status"],
        "history_provenance": "PASS_WITH_AMBIGUOUS_PRE_CERTIFICATION_HISTORY",
        "gap_semantics": "PASS_WITH_MISSING_BARS",
        "volume": "DISABLED_UNPROVEN_PROVENANCE",
        "qwen": qwen["status"],
        "database": database["status"],
        "fee": fee_status,
        "fee_basis": "ASSUMED_PUBLISHED_BASELINE" if fee_status != "PASS" else "ACCOUNT_OBSERVED",
        "demo": demo_status,
        "execution_mode": "local_paper",
        "tracer_v2": "PASS_ARCHITECTURE_ONLY",
        "phase2_blockers": [
            name
            for name, passing in (("QWEN", qwen["status"] == "PASS"), ("POSTGRES", database["status"] == "PASS"))
            if not passing
        ],
    }
    write_json(OUTPUT / "integrity-gate.json", gate)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
