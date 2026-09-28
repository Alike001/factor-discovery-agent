from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.bitget.client import BitgetPublicClient, closed_candles
from app.bitget.integrity import certification_start_ms
from app.bitget.models import Candle
from app.config import Settings
from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.qwen.client import factor_proposal_prompt, probe_factor_proposal_compat, probe_schema
from app.qwen.models import FactorProposal, LifecycleDecision
from app.research.canonical import factor_identity
from app.research.dsl import FactorSpec
from app.research.evaluator import evaluate_research_factor
from app.research.protocol import CORE_SYMBOLS, PROTOCOL, PROTOCOL_HASH, PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[3]
RAW_HISTORY = ROOT / "evidence/raw/core-history-provenance-v2.json"
OUTPUT = ROOT / "evidence/phase2"
PUBLIC = ROOT / "web/public/evidence"
MANDATES = (
    "Use RNVDAUSDT and RQQQUSDT in overnight. Test relative price-return mean reversion; do not copy the example.",
    "Use RAAPLUSDT and RQQQUSDT in weekend. Test price-return momentum or reversal; do not copy the example.",
    "Use RTSLAUSDT and RQQQUSDT in regular. Test a bounded cross-rToken price hypothesis; do not copy the example.",
    "Use RAMDUSDT and RNVDAUSDT in after_hours. Test semiconductor relative returns; do not copy the example.",
    "Use RMSFTUSDT and RQQQUSDT in pre_market. Test price-only relative returns; do not copy the example.",
)


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=lambda item: item.isoformat() if hasattr(item, "isoformat") else str(item)))


def _load_history() -> dict[str, list[Candle]]:
    if not RAW_HISTORY.exists():
        raise RuntimeError("trusted Phase 1.5 history artifact is unavailable")
    raw = json.loads(RAW_HISTORY.read_text())
    return {symbol: [Candle.model_validate(row) for row in raw[symbol]["one_hour"]] for symbol in CORE_SYMBOLS}


def _merge(base: list[Candle], recent: list[Candle]) -> list[Candle]:
    values = {item.timestamp_ms: item for item in base}
    values.update({item.timestamp_ms: item for item in recent})
    return [values[key] for key in sorted(values)]


def _allows(repository: ResearchRepository, protocol_id: Any) -> bool:
    used = repository.qwen_budget(protocol_id)
    cap = PROTOCOL["budget"]
    return used["attempts"] < cap["max_live_http_attempts"] and used["budget_tokens"] < cap["max_measured_total_tokens"]


def _event(repository: ResearchRepository, cycle_id: Any, kind: str, payload: dict[str, Any]) -> str:
    return repository.append_evidence(event_type=kind, entity_type="research_cycle", entity_id=cycle_id, payload=payload)


def _save_run(repository: ResearchRepository, cycle_id: Any, role: str, prompt: str,
              prompt_version: str, result: dict[str, Any], fallback_model: str) -> Any:
    valid = result["validation"]["valid"]
    return repository.save_qwen_run(
        cycle_id=cycle_id, role=role, model=result["observed_model"] or fallback_model,
        endpoint_path=result["endpoint_path"], prompt_text=prompt, prompt_version=prompt_version,
        request_hash=result["request_hash"], response_hash=result["response_hash"],
        final_text=result["final_text"], parsed_json=result["parsed_json"],
        status="PASS" if valid else (result["error_code"] or "INVALID"),
        token_usage=result["response_metadata"]["usage"], latency_ms=result["latency_ms"],
        attempt_count=1 + result["repair_attempts"],
    )


def _write_summary(repository: ResearchRepository, protocol_id: Any) -> None:
    summary = _jsonable(repository.phase2_summary(protocol_id))
    summary.update({"generated_at": datetime.now(UTC).isoformat(), "protocol_hash": PROTOCOL_HASH})
    write_json(OUTPUT / "summary.json", summary)
    write_json(PUBLIC / "phase2-summary.json", summary)


async def run_cycle(cycle_number: int, idempotency_key: str | None = None) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.database_url or not settings.qwen_api_key:
        raise RuntimeError("DATABASE_URL and BITGET_QWEN_API_KEY are required")
    apply_migrations(settings.database_url)
    repository = ResearchRepository(settings.database_url)
    protocol_id = repository.ensure_protocol(PROTOCOL_VERSION, PROTOCOL)
    key = idempotency_key or f"fdp-v1-cycle-{cycle_number}"
    with repository.worker_lock() as acquired:
        if not acquired:
            return {"status": "NO_RUN_LOCKED", "cycle_number": cycle_number}
        existing = repository.cycle(key)
        cycle_id = repository.upsert_cycle(protocol_id, cycle_number, key, datetime.now(UTC))
        if existing and existing["status"] == "COMPLETE":
            _write_summary(repository, protocol_id)
            return {"status": "COMPLETE", "cycle_number": cycle_number, "resumed": True,
                    "manifest_hash": existing["manifest_hash"]}
        if not existing:
            _event(repository, cycle_id, "cycle_created", {"cycle_number": cycle_number, "protocol": PROTOCOL_VERSION})
        if not _allows(repository, protocol_id):
            repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_BUDGET_EXHAUSTED")
            _event(repository, cycle_id, "cycle_no_run", {"error_code": "NO_RUN_BUDGET_EXHAUSTED"})
            return {"status": "NO_RUN_BUDGET_EXHAUSTED", "cycle_number": cycle_number}

        async with BitgetPublicClient() as bitget:
            instruments, *sets = await asyncio.gather(
                bitget.instruments(), *(bitget.recent_candles(symbol, "1H", 1000) for symbol in CORE_SYMBOLS)
            )
        instrument_map = {item["symbol"]: item for item in instruments["data"]}
        now_ms = int(datetime.now(UTC).timestamp() * 1000)
        recent = {symbol: closed_candles(rows, "1H", now_ms) for symbol, rows in zip(CORE_SYMBOLS, sets)}
        latest = {symbol: rows[-1].timestamp_ms if rows else None for symbol, rows in recent.items()}
        if any(value is None for value in latest.values()):
            repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_STALE_DATA")
            return {"status": "NO_RUN_STALE_DATA", "cycle_number": cycle_number}
        snapshot = {"as_of": datetime.now(UTC).isoformat(), "source": "Bitget Reality public UTA v3",
                    "eligible_universe": list(CORE_SYMBOLS), "latest_closed_candle_ms": latest,
                    "enabled_fields": PROTOCOL["enabled_fields"], "protocol_hash": PROTOCOL_HASH}
        snapshot_hash = canonical_hash(snapshot)
        repository.save_snapshot(cycle_id, datetime.now(UTC), snapshot, snapshot_hash)
        _event(repository, cycle_id, "snapshot_committed", {"snapshot_hash": snapshot_hash, "latest": latest})

        hypothesis = repository.hypothesis_for_cycle(cycle_id)
        resumed = hypothesis is not None
        if hypothesis is None:
            mandate = MANDATES[(cycle_number - 1) % 5] + f" Autonomous cycle {cycle_number}; do not claim performance."
            prompt = factor_proposal_prompt(FactorProposal, mandate)
            _event(repository, cycle_id, "qwen_request", {"role": "proposer", "prompt_hash": canonical_hash(prompt)})
            async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
                result = await probe_factor_proposal_compat(
                    client, model=settings.qwen_model, api_key=settings.qwen_api_key,
                    schema=FactorProposal, max_repair_attempts=1, research_mandate=mandate,
                )
            run_id = _save_run(repository, cycle_id, "proposer", prompt, "factor-proposer-v1", result, settings.qwen_model)
            _event(repository, cycle_id, "qwen_response", {"role": "proposer", "response_hash": result["response_hash"], "valid": result["validation"]["valid"]})
            if not result["validation"]["valid"]:
                repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_INVALID_MODEL_OUTPUT")
                return {"status": "NO_RUN_INVALID_MODEL_OUTPUT", "cycle_number": cycle_number}
            proposal = FactorProposal.model_validate(result["parsed_json"])
            if not set(proposal.universe).issubset(CORE_SYMBOLS):
                repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_INVALID_MODEL_OUTPUT")
                return {"status": "NO_RUN_INVALID_MODEL_OUTPUT", "cycle_number": cycle_number}
            trial = repository.allocate_trial_number(protocol_id)
            identity = factor_identity(proposal)
            _, factor_id, duplicate = repository.commit_hypothesis(
                protocol_id=protocol_id, cycle_id=cycle_id, trial_number=trial,
                proposer_run_id=run_id, proposal=proposal.model_dump(mode="json"), canonical_hash=identity,
            )
            hypothesis = {"trial_number": trial, "proposal": proposal.model_dump(mode="json"),
                          "canonical_hash": identity, "duplicate_of": factor_id if duplicate else None,
                          "factor_version_id": factor_id}
            _event(repository, cycle_id, "hypothesis_committed", {"trial_number": trial, "canonical_hash": identity, "duplicate": duplicate})
        proposal = FactorSpec.model_validate(hypothesis["proposal"])
        factor_id = hypothesis["factor_version_id"]
        if hypothesis["duplicate_of"]:
            _event(repository, cycle_id, "cycle_complete", {"aggregate": "REJECTED", "reason": "DUPLICATE_SUPPRESSED"})
            repository.complete_cycle(cycle_id, "COMPLETE", hypothesis["canonical_hash"])
            return {"status": "COMPLETE", "cycle_number": cycle_number, "trial_number": hypothesis["trial_number"],
                    "aggregate": "REJECTED", "duplicate": True, "resumed": resumed}

        _event(repository, cycle_id, "dsl_formalized", {"canonical_hash": hypothesis["canonical_hash"]})
        base = _load_history()
        candles = {symbol: _merge(base[symbol], recent[symbol]) for symbol in CORE_SYMBOLS}
        valid_from = {f"{symbol}.close": certification_start_ms(int(instrument_map[symbol]["launchTime"])) for symbol in proposal.universe}
        report = evaluate_research_factor(proposal, candles, trial_number=hypothesis["trial_number"], field_valid_from_ms=valid_from).report
        experiment_id = repository.save_experiment(factor_version_id=factor_id, dataset_hash=report["dataset_hash"],
            data_contract=report["data_contract"], metrics=report, report_hash=report["report_hash"])
        repository.save_gates(experiment_id, report["gates"])
        repository.transition(factor_id, "COMMITTED", "FORMALIZED", "Safe FactorSpec validated.")
        repository.transition(factor_id, "FORMALIZED", "BACKTESTED", "Deterministic evaluation completed.", experiment_id=experiment_id)
        _event(repository, cycle_id, "experiment_completed", {"experiment_id": str(experiment_id), "report_hash": report["report_hash"]})
        for gate in report["gates"]:
            _event(repository, cycle_id, "gate_result", {"experiment_id": str(experiment_id), **gate})

        lifecycle_run_id = None
        if _allows(repository, protocol_id):
            detail = json.dumps({"proposal": proposal.model_dump(mode="json"), "aggregate": report["aggregate"],
                "metrics": report["metrics"], "gates": report["gates"],
                "instruction": "Interpret only this factor; deterministic gates own promotion."}, separators=(",", ":"))
            prompt = f"Return JSON only for LifecycleDecision. Evidence:{detail}"
            _event(repository, cycle_id, "qwen_request", {"role": "lifecycle", "prompt_hash": canonical_hash(prompt)})
            async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
                result = await probe_schema(client, model=settings.qwen_model, api_key=settings.qwen_api_key,
                    schema=LifecycleDecision, purpose="LifecycleDecision", prompt_detail=detail)
            lifecycle_run_id = _save_run(repository, cycle_id, "lifecycle", prompt, "lifecycle-v1", result, settings.qwen_model)
            _event(repository, cycle_id, "qwen_response", {"role": "lifecycle", "response_hash": result["response_hash"], "valid": result["validation"]["valid"]})
            lifecycle = LifecycleDecision.model_validate(result["parsed_json"]) if result["validation"]["valid"] else LifecycleDecision(action="ABANDON", reason="Invalid lifecycle output.", revision_intent=None)
        else:
            lifecycle = LifecycleDecision(action="ABANDON", reason="Qwen budget exhausted after evaluation.", revision_intent=None)
        final_state = report["aggregate"]
        reason = f"Deterministic aggregate {final_state}; Qwen action {lifecycle.action} cannot override gates."
        repository.transition(factor_id, "BACKTESTED", final_state, reason, qwen_run_id=lifecycle_run_id, experiment_id=experiment_id)
        _event(repository, cycle_id, "lifecycle_transition", {"to_state": final_state, "qwen_action": lifecycle.action})
        manifest = {"cycle_number": cycle_number, "trial_number": hypothesis["trial_number"],
                    "protocol_hash": PROTOCOL_HASH, "snapshot_hash": snapshot_hash,
                    "factor_hash": hypothesis["canonical_hash"], "report_hash": report["report_hash"],
                    "aggregate": final_state}
        manifest_hash = canonical_hash(manifest)
        manifest["manifest_hash"] = manifest_hash
        _event(repository, cycle_id, "cycle_complete", manifest)
        repository.complete_cycle(cycle_id, "COMPLETE", manifest_hash)
        artifact = {"generated_at": datetime.now(UTC).isoformat(), "manifest": manifest,
                    "proposal": proposal.model_dump(mode="json"), "experiment": report,
                    "lifecycle": lifecycle.model_dump(mode="json"), "resumed": resumed}
        write_json(OUTPUT / f"cycle-{cycle_number}.json", artifact)
        _write_summary(repository, protocol_id)
        return {"status": "COMPLETE", "cycle_number": cycle_number, "trial_number": hypothesis["trial_number"],
                "aggregate": final_state, "duplicate": False, "resumed": resumed, "manifest_hash": manifest_hash}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle-number", type=int, required=True)
    parser.add_argument("--idempotency-key")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run_cycle(args.cycle_number, args.idempotency_key)), indent=2))


if __name__ == "__main__":
    main()
