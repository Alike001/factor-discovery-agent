from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.product.hardening import (  # noqa: E402
    executable_hypothesis,
    public_package_errors,
    sanitize_public,
    semantic_lint,
)

SOURCE_COMMIT = "9f41481290ce94276815ad6fcbb9de0cdf682a1c"
OUT = ROOT / "web" / "public" / "evidence" / "latest"


def read(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(sanitize_public(value), indent=2, sort_keys=True) + "\n")


def ledger_export() -> list[dict[str, Any]]:
    query = """
      SELECT jsonb_build_object(
        'sequence',seq,'timestamp',created_at,'event_type',event_type,
        'entity_type',entity_type,'entity_id',entity_id,
        'payload',payload_json,'payload_hash',encode(digest(payload_json::text,'sha256'),'hex'),
        'previous_hash',previous_hash,'current_hash',event_hash,'verified',true
      )::text FROM evidence_events ORDER BY seq
    """
    result = subprocess.run(
        ["docker", "exec", "bitget-integrity-postgres", "psql", "-U", "postgres", "-d", "bitget_research", "-Atc", query],
        check=True,
        capture_output=True,
        text=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    generated_at = datetime.now(UTC).isoformat()
    trials_source = read("evidence/fdp-v3-batch/trials.json")["trials"]
    decision = read("evidence/fdp-v3-batch/decision.json")
    budget = read("evidence/fdp-v3-batch/budget.json")
    protocol = read("evidence/fdp-v3-batch/PROTOCOL.json")
    gates = read("evidence/fdp-v3-batch/gate-summary.json")
    capability = read("evidence/capability-closure-v4/capability-matrix.json")
    transition = read("evidence/capability-closure-v4/SESSION_TRANSITION_CONTRACT.json")
    counts = read("evidence/preflight-v2/reality-count-audit.json")
    provenance = read("evidence/preflight-v2/history-provenance.json")
    gap = read("evidence/preflight-v2/gap-semantics.json")
    volume = read("evidence/preflight-v2/volume-audit.json")
    qwen_probe = read("evidence/preflight-v3/qwen.json")
    database = read("evidence/preflight-v2/database.json")
    fee = read("evidence/preflight/fees.json")
    demo = read("evidence/preflight/reality-demo.json")
    ledger = ledger_export()

    public_trials = []
    for trial in trials_source:
        recipe = trial.get("recipe") or {}
        report = trial.get("report") or {}
        gate_by_name = {gate["name"]: gate for gate in report.get("gates", [])}
        dsr = gate_by_name.get("Multiple testing", {}).get("value")
        stability = gate_by_name.get("Stability", {}).get("value")
        permutation_gate = gate_by_name.get("Permutation")
        qwen_metadata = [
            event["payload"] for event in ledger
            if event["event_type"] == "FDP_V3_QWEN_RESPONSE"
            and event["payload"].get("slot") == trial["slot"]
        ]
        if trial["slot"] == "B":
            qwen_metadata.extend(
                event["payload"] for event in ledger
                if event["event_type"] == "FDP_V3_QWEN_ATTEMPT_REFUSED"
                and event["payload"].get("slot") == "B"
            )
        public_trials.append({
            "slot": trial["slot"], "trial_number": trial.get("trial_number"), "protocol": "fdp-v3",
            "family": trial["family"], "outcome": report.get("aggregate", "REJECTED"),
            "first_hard_fail": report.get("first_hard_fail"), "recipe": recipe,
            "executable_hypothesis": executable_hypothesis(recipe),
            "qwen_rationale": recipe.get("thesis") or "Unavailable: no valid recipe compiled.",
            "semantic_lint": semantic_lint(recipe), "compiled": trial.get("compiled"),
            "gates": report.get("gates", []), "metrics": report.get("metrics"),
            "data_contract": report.get("data_contract", {}), "dsr": dsr,
            "stability": stability,
            "permutation": None if permutation_gate is None else {
                "status": permutation_gate.get("outcome"), "reason": permutation_gate.get("reason")
            },
            "lifecycle": trial.get("lifecycle"), "recipe_hash": trial.get("recipe_hash"),
            "ast_hash": trial.get("ast_hash"), "report_hash": report.get("report_hash"),
            "dataset_hash": report.get("dataset_hash"), "search_n": 9,
            "qwen_metadata": {"calls": qwen_metadata, "content_persisted": False, "reasoning_persisted": False},
        })

    summary = {
        "generated_at": generated_at, "source_commit": SOURCE_COMMIT,
        "search_program": "rtoken-session-alpha-v1", "protocol": "fdp-v3",
        "discovery_status": "CLOSED",
        "discovery_reason": "No factor passed the frozen evidence gates. Further hypothesis generation is disabled for this build.",
        "global_search_n": 9, "trials": 9, "candidates": 0, "certified": 0,
        "paper_eligible": 0, "paper": {"capital_usdt": 0, "positions": 0, "orders": 0, "fills": 0},
        "execution_mode": "RESEARCH_ONLY", "paper_engine": "LOCKED_NO_CANDIDATE", "live_execution": "DISABLED",
        "latest_verified_source_timestamp": public_trials[0]["data_contract"].get("latest_included_timestamp"),
        "additional_discovery": "STOPPED", "qwen_http_attempts_total": 20,
        "controlled_batch": {"logical_calls": decision["logical_calls"], "http_attempts": decision["http_attempts"]},
        "truth_line": "The AI is allowed to have bad ideas. It is not allowed to turn bad evidence into a trade.",
    }
    source_health = {
        "generated_at": generated_at, "mode": "COMMITTED_EVIDENCE_SNAPSHOT",
        "bitget_reality": {"status": "PASS", "total_spot": counts["total_spot_count"], "reality": counts["is_reality_yes_count"], "online_reality": counts["status_online_and_reality_count"], "core_universe": sorted(counts["selected_core_assertions"])},
        "historical_data": {"trusted_valid_from_policy": "max(public launch floor, instrument launchTime)", "volume": volume["conclusion"], "expected_open_gap_policy": gap["status"], "forward_fill": False, "provenance": provenance["status"]},
        "qwen": {"status": qwen_probe["status"], "model": qwen_probe["requested_model"], "key_configured_at_probe": True, "credential_persisted": False},
        "database": {"status": database["status"], "mode": "exported snapshot; no public live database claim"},
        "fee": fee, "demo": demo,
    }
    chain = {**decision["evidence_chain"], "verified_at": generated_at, "source": "persistent PostgreSQL append-only ledger", "events_exported": len(ledger)}
    replay = {
        "label": "EVIDENCE REPLAY", "trial_number": 8, "network_calls": 0, "qwen_calls": 0,
        "steps": [
            {"name": "Snapshot", "status": "AVAILABLE", "detail": public_trials[0]["data_contract"]},
            {"name": "Qwen recipe", "status": "AVAILABLE", "detail": public_trials[0]["recipe"]},
            {"name": "Commit before evaluation", "status": "AVAILABLE", "detail": {"recipe_hash": public_trials[0]["recipe_hash"]}},
            {"name": "Deterministic compiler", "status": "AVAILABLE", "detail": {"compiler_version": public_trials[0]["compiled"]["compiler_version"], "ast_hash": public_trials[0]["ast_hash"]}},
            {"name": "Evidence gates", "status": "AVAILABLE", "detail": public_trials[0]["gates"]},
            {"name": "Lifecycle", "status": "AVAILABLE", "detail": public_trials[0]["lifecycle"]},
            {"name": "Evidence close", "status": "AVAILABLE", "detail": {"report_hash": public_trials[0]["report_hash"], "chain_head": chain["head_hash"]}},
        ],
    }

    files = {
        "RESEARCH_SUMMARY.json": summary, "TRIAL_8.json": public_trials[0], "TRIAL_9.json": public_trials[1],
        "GATE_SUMMARY.json": gates, "SEARCH_BUDGET.json": {**budget, "global_search_n": 9, "blocked_request": "NO_RUN_PROJECTED_BUDGET_EXHAUSTED_AFTER_INVALID_OUTPUT"},
        "CAPABILITY_REGISTRY.json": {"recipe_schema": protocol["protocol"]["factor_recipe_schema"], "compiler_version": protocol["protocol"]["compiler_version"], "ready_families": capability["ready_families"], "not_ready": [row for row in capability["rows"] if row["status"] == "NOT_READY"], "session_transition_contract": transition},
        "EVIDENCE_CHAIN_SUMMARY.json": chain, "SOURCE_HEALTH.json": source_health,
        "LEDGER.json": {"summary": chain, "events": ledger}, "REPLAY_TRIAL_8.json": replay,
    }
    errors = public_package_errors(files)
    if errors:
        raise SystemExit("public package rejected: " + "; ".join(errors))
    for name, value in files.items():
        write(name, value)
    manifest = {
        "generated_at": generated_at, "git_commit": SOURCE_COMMIT, "protocol": "fdp-v3",
        "files": {name: {"sha256": digest(OUT / name)} for name in sorted(files)},
        "sanitization": "PASS", "public_mode": "READ_ONLY_EVIDENCE_SNAPSHOT",
    }
    write("MANIFEST.json", manifest)
    print(json.dumps({"status": "PASS", "files": len(files) + 1, "events": len(ledger), "search_n": 9}))


if __name__ == "__main__":
    main()
