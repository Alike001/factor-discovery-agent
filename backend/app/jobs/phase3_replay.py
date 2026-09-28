from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg

from app.bitget.models import Candle
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.research.dsl import FactorSpec
from app.research.phase3 import (
    nearest_neighbors,
    reconstruct_returns,
    structural_fingerprint,
    temporal_stability,
)
from app.research.statistics import deflated_sharpe, expected_maximum_sharpe, return_moments

ROOT = Path(__file__).resolve().parents[3]
PHASE2 = ROOT / "evidence/phase2"
OUTPUT = ROOT / "evidence/phase3"
RAW_HISTORY = ROOT / "evidence/raw/core-history-provenance-v2.json"
RECOVERED_HISTORY = ROOT / "evidence/raw/phase3-phase2-recovery.json"
GATE_ORDER = ["Syntax", "Coverage", "Point-in-time", "Mechanics", "Costs", "OOS",
              "Stability", "Permutation", "Multiple testing", "Baseline"]


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def _qwen_attempts(database_url: str) -> int:
    with psycopg.connect(database_url) as connection:
        return int(connection.execute("SELECT COALESCE(sum(attempt_count),0) FROM qwen_runs").fetchone()[0])


def _gate(name: str, outcome: str, reason_code: str, value: Any, threshold: Any,
          method: str) -> dict[str, Any]:
    return {"name": name, "outcome": outcome, "reason_code": reason_code,
            "measured_value": value, "threshold": threshold, "method_version": method}


def _phase2_gate(gates: list[dict[str, Any]], name: str, report: dict[str, Any]) -> dict[str, Any]:
    source = next(item for item in gates if item["name"] == name)
    values: dict[str, Any] = {
        "Syntax": {"schema_valid": True},
        "Coverage": {"calendar_days": (_ms(report["data_contract"]["end"]) - _ms(report["data_contract"]["start"])) / 86_400_000},
        "Point-in-time": {"certified_closed_ohlc_only": True},
        "Mechanics": {"records_hash": report["integrity"]["records_hash"]},
        "Costs": {"net_return": report["metrics"]["net"]["total_return"]},
        "OOS": {"fills": report["metrics"]["oos_net"]["fills"], "net_return": report["metrics"]["oos_net"]["total_return"]},
        "Baseline": {"factor_net": report["metrics"]["net"]["total_return"], "buy_hold": report["metrics"]["buy_hold"]},
    }
    thresholds: dict[str, Any] = {
        "Syntax": {"schema_valid": True}, "Coverage": {"minimum_calendar_days": 60},
        "Point-in-time": {"leakage": False}, "Mechanics": {"same_candle_fills": 0},
        "Costs": {"net_return_greater_than": 0},
        "OOS": {"minimum_fills": 20, "net_return_greater_than": 0},
        "Baseline": {"factor_net_greater_than_buy_hold": True},
    }
    return _gate(name, source["outcome"], f"PHASE2_{name.upper().replace('-', '_').replace(' ', '_')}_{source['outcome']}",
                 values[name], thresholds[name], "fdp-v1-phase2")


def _permutation_gate(gates: list[dict[str, Any]]) -> dict[str, Any]:
    source = next(item for item in gates if item["name"] == "Permutation")
    matched = re.search(r"p=([0-9]+(?:\.[0-9]+)?)", source["reason"])
    value = {"p_value": float(matched.group(1)) if matched else None, "draws": 2000}
    code = "PERMUTATION_THRESHOLD_NOT_MET" if source["outcome"] == "FAIL" else (
        "INCONCLUSIVE_PERMUTATION_SAMPLE" if source["outcome"] == "INCONCLUSIVE" else "PERMUTATION_THRESHOLD_MET")
    return _gate("Permutation", source["outcome"], code, value, {"candidate_p_max": 0.10}, "sign-flip-v1")


def run(database_url: str) -> dict[str, Any]:
    if (OUTPUT / "replay-summary.json").exists():
        raise RuntimeError("Phase-3 replay already exists; exactly one replay is permitted")
    base_methods = json.loads((OUTPUT / "METHODS-v2.json").read_text())
    amendment = json.loads((OUTPUT / "METHODS-v3.json").read_text())
    methods = {**base_methods, "method_version": amendment["method_version"],
               "frozen_at": amendment["frozen_at"], "supersedes": amendment["supersedes"]}
    method_hash = canonical_hash(amendment)
    with psycopg.connect(database_url) as connection:
        frozen = connection.execute(
            "SELECT 1 FROM evidence_events WHERE event_type='PHASE3_METHODS_FROZEN' AND payload_json->>'methods_hash'=%s",
            (method_hash,),
        ).fetchone()
    if not frozen:
        raise RuntimeError("PHASE3_METHODS_FROZEN evidence event is required before replay")
    attempts_before = _qwen_attempts(database_url)
    raw = json.loads(RAW_HISTORY.read_text())
    candles = {symbol: [Candle.model_validate(row) for row in payload["one_hour"]]
               for symbol, payload in raw.items()}
    recovered = json.loads(RECOVERED_HISTORY.read_text())
    for symbol, rows in recovered["symbols"].items():
        by_time = {item.timestamp_ms: item for item in candles[symbol]}
        by_time.update({item.timestamp_ms: item for item in (Candle.model_validate(row) for row in rows)})
        candles[symbol] = [by_time[key] for key in sorted(by_time)]
    trials: list[dict[str, Any]] = []
    for path in sorted(PHASE2.glob("cycle-*.json")):
        artifact = json.loads(path.read_text())
        spec = FactorSpec.model_validate(artifact["proposal"])
        report = artifact["experiment"]
        contract = report["data_contract"]
        replay = reconstruct_returns(
            spec, candles, start_ms=_ms(contract["start"]), end_ms=_ms(contract["end"]),
            split_ms=_ms(report["split_timestamp"]), fee=methods["cost_model"]["fee_per_fill"],
            slippage=methods["cost_model"]["slippage_per_fill"],
        )
        replay_hash = canonical_hash(replay["rows"])
        if replay_hash != report["integrity"]["records_hash"]:
            raise RuntimeError(f"Phase-2 deterministic replay mismatch for trial {report['trial_number']}")
        returns = [row["net"] for row in replay["rows"]]
        moments = return_moments(returns)
        trials.append({"trial_number": report["trial_number"], "name": spec.name, "thesis": spec.thesis,
                       "spec": spec, "report": report, "rows": replay["rows"],
                       "scope": replay["scope"], "session_purity": replay["session_purity"],
                       "returns": returns, "moments": moments,
                       "fingerprint": structural_fingerprint(spec)})
    if len(trials) != methods["search_population"]["expected_n"]:
        raise RuntimeError("search population does not match frozen METHODS.json")

    # Degenerate all-flat trials contribute zero to cross-trial search dispersion but remain
    # individually inconclusive because their return variance is zero.
    population_sharpes = [trial["moments"].sharpe or 0.0 for trial in trials]
    hurdle = expected_maximum_sharpe(population_sharpes, expected_mean=methods["dsr"]["expected_mean_sr"])
    if hurdle["status"] != "OK":
        raise RuntimeError("DSR search population is not measurable")
    matrix = []
    replay_factors = []
    diversity_items = []
    repository = ResearchRepository(database_url)
    for trial in trials:
        report = trial["report"]
        dsr = deflated_sharpe(
            trial["returns"], benchmark_sharpe=float(hurdle["sr_star"]), search_n=len(trials),
            sigma_sr=float(hurdle["sigma_sr"]), threshold=methods["dsr"]["threshold"],
        )
        stability = temporal_stability(
            trial["rows"], _ms(report["split_timestamp"]), _ms(report["data_contract"]["end"]),
            session_purity=trial["session_purity"],
        )
        gates = [_phase2_gate(report["gates"], name, report) for name in GATE_ORDER
                 if name not in {"Stability", "Permutation", "Multiple testing"}]
        gates.append(_gate("Stability", stability["status"], stability["reason_code"], stability,
                           stability["thresholds"], methods["stability"]["version"]))
        gates.append(_permutation_gate(report["gates"]))
        gates.append(_gate("Multiple testing", str(dsr["status"]), str(dsr["reason_code"]), dsr,
                           {"probability_minimum": methods["dsr"]["threshold"]}, methods["method_version"]))
        gates.sort(key=lambda item: GATE_ORDER.index(item["name"]))
        first = next((gate for gate in gates if gate["outcome"] == "FAIL"), None)
        first_hard_fail = first["name"] if first else None
        item = {"trial_number": trial["trial_number"], "name": trial["name"],
                "terminal_phase2_state": "REJECTED", "diagnostic_only": True,
                "scope": trial["scope"], "first_hard_fail": first_hard_fail,
                "dsr": dsr, "stability": stability, "gates": gates,
                "replay_records_hash": canonical_hash(trial["rows"]),
                "phase2_records_hash": report["integrity"]["records_hash"]}
        matrix.append(item)
        replay_factors.append({key: item[key] for key in ("trial_number", "name", "terminal_phase2_state",
                                                           "scope", "first_hard_fail", "dsr", "stability")})
        diversity_items.append({"trial_number": trial["trial_number"], "name": trial["name"],
                                "fingerprint": trial["fingerprint"]})
        repository.append_evidence(event_type="PHASE3_FACTOR_REPLAYED", entity_type="factor_version",
            entity_id=None, payload={"trial_number": trial["trial_number"], "methods_hash": method_hash,
                                     "result_hash": canonical_hash(item), "diagnostic_only": True})
    neighbors = nearest_neighbors(diversity_items)
    patterns = Counter(json.dumps(item["fingerprint"]["operator_multiset"], sort_keys=True) for item in diversity_items)
    diversity = {"method_version": methods["diversity"]["version"], "performance_fields_used": False,
                 "factor_count": len(diversity_items), "unique_families": sorted({item["fingerprint"]["family"] for item in diversity_items}),
                 "unique_targets": sorted({value for item in diversity_items for value in item["fingerprint"]["targets"]}),
                 "unique_sessions": sorted({value for item in diversity_items for value in item["fingerprint"]["sessions"]}),
                 "repeated_operator_patterns": [{"pattern": json.loads(pattern), "count": count}
                                                for pattern, count in patterns.items() if count > 1],
                 "factors": diversity_items, "nearest_neighbors": neighbors}
    counts = Counter(gate["outcome"] for item in matrix for gate in item["gates"])
    hard_fail_counts = Counter(item["first_hard_fail"] or "NONE" for item in matrix)
    attempts_after = _qwen_attempts(database_url)
    if attempts_after != attempts_before:
        raise RuntimeError("Qwen attempt count changed during Phase 3")
    summary = {"method_version": methods["method_version"], "methods_hash": method_hash,
               "qwen_http_attempts_phase3": attempts_after - attempts_before,
               "search_n": len(trials), "search_hurdle": hurdle, "factors": replay_factors,
               "gate_distribution": dict(sorted(counts.items())),
               "first_hard_fail_distribution": dict(sorted(hard_fail_counts.items())),
               "old_terminal_states_rewritten": False, "recommendation": "TARGETED_DISCOVERY_BATCH"}
    write_json(OUTPUT / "rejection-matrix.json", {"method_version": methods["method_version"], "factors": matrix})
    write_json(OUTPUT / "research-diversity.json", diversity)
    write_json(OUTPUT / "replay-summary.json", summary)
    repository.append_evidence(event_type="PHASE3_REPLAY_COMPLETE", entity_type="research_protocol",
        entity_id=None, payload={"methods_hash": method_hash, "summary_hash": canonical_hash(summary),
                                 "qwen_http_attempts": 0, "factor_count": len(trials)})
    return summary


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    print(json.dumps(run(database_url), indent=2))


if __name__ == "__main__":
    main()
