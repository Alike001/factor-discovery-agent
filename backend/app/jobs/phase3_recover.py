from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from app.bitget.client import BitgetPublicClient, closed_candles
from app.bitget.models import Candle
from app.evidence import canonical_hash, write_json
from app.research.dsl import FactorSpec
from app.research.phase3 import reconstruct_returns
from app.research.protocol import CORE_SYMBOLS

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "evidence/raw/core-history-provenance-v2.json"
RECOVERED = ROOT / "evidence/raw/phase3-phase2-recovery.json"
OUTPUT = ROOT / "evidence/phase3/recovery-audit.json"


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def _merge(base: list[Candle], recent: list[Candle]) -> list[Candle]:
    values = {item.timestamp_ms: item for item in base}
    values.update({item.timestamp_ms: item for item in recent})
    return [values[key] for key in sorted(values)]


async def recover() -> dict[str, object]:
    async with BitgetPublicClient() as client:
        recent_sets = await asyncio.gather(*(client.recent_candles(symbol, "1H", 1000) for symbol in CORE_SYMBOLS))
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    recent = {symbol: closed_candles(rows, "1H", now_ms) for symbol, rows in zip(CORE_SYMBOLS, recent_sets)}
    raw_payload = {"retrieved_at": datetime.now(UTC).isoformat(),
                   "symbols": {symbol: [item.model_dump(mode="json") for item in rows]
                               for symbol, rows in recent.items()}}
    write_json(RECOVERED, raw_payload)
    base_raw = json.loads(BASE.read_text())
    merged = {symbol: _merge([Candle.model_validate(row) for row in base_raw[symbol]["one_hour"]], recent[symbol])
              for symbol in CORE_SYMBOLS}
    checks = []
    for path in sorted((ROOT / "evidence/phase2").glob("cycle-*.json")):
        artifact = json.loads(path.read_text())
        report = artifact["experiment"]
        contract = report["data_contract"]
        replay = reconstruct_returns(
            FactorSpec.model_validate(artifact["proposal"]), merged,
            start_ms=_ms(contract["start"]), end_ms=_ms(contract["end"]),
            split_ms=_ms(report["split_timestamp"]), fee=0.0005, slippage=0.00025,
        )
        actual = canonical_hash(replay["rows"])
        expected = report["integrity"]["records_hash"]
        checks.append({"trial_number": report["trial_number"], "expected_records_hash": expected,
                       "recovered_records_hash": actual, "match": actual == expected})
    result = {"status": "PASS" if all(item["match"] for item in checks) else "FAIL",
              "retrieved_at": raw_payload["retrieved_at"], "source": "Bitget UTA v3 recent closed 1H candles",
              "recovered_raw_path": "evidence/raw/phase3-phase2-recovery.json (gitignored)",
              "recovered_raw_hash": canonical_hash(raw_payload), "checks": checks}
    write_json(OUTPUT, result)
    return result


def main() -> None:
    result = asyncio.run(recover())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
