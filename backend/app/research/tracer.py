from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.bitget.client import BitgetPublicClient, closed_candles
from app.evidence import canonical_hash, write_json
from app.research.dsl import FactorSpec
from app.research.engine import EngineConfig, evaluate_factor


TRACER_SPEC = {
    "name": "Overnight Relative Return Z-Score",
    "thesis": "A deeply negative hourly z-score of NVDA rToken return relative to QQQ during overnight trading may mean-revert.",
    "universe": ["RNVDAUSDT", "RQQQUSDT"],
    "session_filter": ["overnight"],
    "signal": {
        "op": "zscore",
        "lookback": 120,
        "args": [
            {
                "op": "sub",
                "args": [
                    {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RNVDAUSDT", "field": "close"}]},
                    {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RQQQUSDT", "field": "close"}]},
                ],
            }
        ],
    },
    "entry_condition": {"op": "lt", "threshold": -1.0, "args": [{"op": "signal"}]},
    "exit_condition": {"op": "gte", "threshold": 0.0, "args": [{"op": "signal"}]},
    "horizon_bars": 12,
    "rebalance_bars": 1,
    "direction": "long_flat",
    "rationale": "This fixed, unoptimized expression exists only to prove the safe data-to-evidence path.",
}


async def run_tracer(root: Path) -> dict:
    spec = FactorSpec.model_validate(TRACER_SPEC)
    async with BitgetPublicClient() as client:
        instruments = await client.instruments()
        launches = {item["symbol"]: int(item["launchTime"]) for item in instruments["data"]}
        asset = await client.all_history("RNVDAUSDT", "1H", launches["RNVDAUSDT"])
        benchmark = await client.all_history("RQQQUSDT", "1H", launches["RQQQUSDT"])
    asset = closed_candles(asset, "1H")
    benchmark = closed_candles(benchmark, "1H")
    candle_payload = {
        "asset": [item.model_dump(mode="json") for item in asset],
        "benchmark": [item.model_dump(mode="json") for item in benchmark],
    }
    normalized = {"generated_at": datetime.now(UTC).isoformat(), **candle_payload}
    data_path = root / "evidence" / "market-data" / "tracer-candles.json"
    write_json(data_path, normalized)
    snapshot = {
        "generated_at": normalized["generated_at"],
        "source": "Bitget Reality public UTA v3 history-candles",
        "dataset_hash": canonical_hash(candle_payload),
        "asset_rows": len(asset),
        "benchmark_rows": len(benchmark),
        "local_dataset_path": "evidence/market-data/tracer-candles.json (gitignored)",
    }
    result = evaluate_factor(spec, asset, benchmark, EngineConfig(asset_symbol="RNVDAUSDT", benchmark_symbol="RQQQUSDT"))
    evidence = {**result.evidence, "data_snapshot": snapshot}
    output = root / "evidence" / "tracer" / "tracer-experiment.json"
    public = root / "web" / "public" / "evidence" / "tracer-experiment.json"
    write_json(output, evidence)
    write_json(public, evidence)
    write_json(root / "evidence" / "tracer" / "data-snapshot.json", snapshot)
    return evidence
