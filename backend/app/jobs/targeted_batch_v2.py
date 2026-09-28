from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import psycopg

from app.bitget.client import BitgetPublicClient, closed_candles
from app.bitget.integrity import certification_start_ms
from app.bitget.models import Candle
from app.config import Settings
from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.qwen.client import probe_json_chat
from app.qwen.models import LifecycleDecision
from app.research.evaluator_v2 import TargetedEvaluation, evaluate_targeted_factor, finalize_evaluation, structural_rejection
from app.research.protocol import CORE_SYMBOLS
from app.research.protocol_v2 import PROTOCOL_V2, PROTOCOL_V2_HASH, PROTOCOL_VERSION_V2, SEARCH_PROGRAM_ID
from app.research.statistics import expected_maximum_sharpe, return_moments
from app.research.targeted import FactorProposalV2, operator_fingerprint, targeted_factor_identity, validate_slot

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "evidence/targeted-batch-v2"
PUBLIC = ROOT / "web/public/evidence/targeted-batch-v2.json"
BASE_HISTORY = ROOT / "evidence/raw/core-history-provenance-v2.json"
RECENT_HISTORY = ROOT / "evidence/raw/targeted-batch-v2-recent.json"
PHASE3_DIVERSITY = ROOT / "evidence/phase3/research-diversity.json"
PHASE3_SUMMARY = ROOT / "evidence/phase3/replay-summary.json"

SLOTS: dict[str, dict[str, Any]] = {
    "A": {"family": "cross_sectional", "title": "Cross-sectional ranking", "required_session": "regular",
          "requirements": [">=4 rTokens", "rank or group_mean", "horizon 12/24/48", "rebalance >=6"]},
    "B": {"family": "session_transition", "title": "Session transition", "transition": ["after_hours", "overnight"],
          "required_session": "overnight", "requirements": [">=3 rTokens", "after_hours -> overnight", "horizon 6/12/24", "one entry per transition"]},
    "C": {"family": "residual", "title": "Beta/residual or dispersion", "required_session": "pre_market",
          "requirements": [">=3 rTokens", "rolling_beta/residual/dispersion", "horizon 12/24/48", "rebalance >=6"]},
}


def _database(settings: Settings) -> str:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required")
    return settings.database_url


def _setup(database_url: str) -> tuple[ResearchRepository, Any, Any]:
    apply_migrations(database_url)
    repository = ResearchRepository(database_url)
    v1 = repository.ensure_protocol("fdp-v1")
    v2 = repository.ensure_protocol(PROTOCOL_VERSION_V2, PROTOCOL_V2)
    program = repository.ensure_search_program(SEARCH_PROGRAM_ID, [v1, v2], starting_trial=6)
    return repository, v2, program


def freeze_plan(database_url: str) -> dict[str, Any]:
    repository, v2, program = _setup(database_url)
    existing_path = OUTPUT / "BATCH_PLAN.json"
    if existing_path.exists():
        return json.loads(existing_path.read_text())
    search_n = repository.search_program_n(program)
    if search_n != 5:
        raise RuntimeError(f"targeted batch must freeze at search N=5, observed {search_n}")
    prior = json.loads(PHASE3_DIVERSITY.read_text())
    plan = {
        "batch": "targeted-batch-v2", "frozen_at": datetime.now(UTC).isoformat(),
        "git_commit_before_batch": "161a0bbcd353aa90dea7a5be069e40b619193717",
        "protocol_version": PROTOCOL_VERSION_V2, "protocol_hash": PROTOCOL_V2_HASH,
        "search_program_id": SEARCH_PROGRAM_ID, "search_n_before": 5, "planned_unique_trials": 3,
        "expected_search_n_after": 8, "slot_order": ["A", "B", "C"], "slots": SLOTS,
        "cost_model": PROTOCOL_V2["cost_model"], "gate_policy": PROTOCOL_V2["gate_policy"],
        "is_oos_rule": PROTOCOL_V2["split_rule"], "automatic_revision_children": False,
        "budget": PROTOCOL_V2["budget"],
        "prior_structural_fingerprints": [item["fingerprint"] for item in prior["factors"]],
        "performance_feedback_allowed": False,
        "aggregate_feedback": "Previous batch overused pairwise divergence patterns and all five were non-promotable after costs.",
    }
    write_json(existing_path, plan)
    plan_hash = canonical_hash(plan)
    with psycopg.connect(database_url) as connection:
        found = connection.execute(
            "SELECT 1 FROM evidence_events WHERE event_type='TARGETED_BATCH_PLAN_FROZEN' AND payload_json->>'plan_hash'=%s",
            (plan_hash,),
        ).fetchone()
    if not found:
        repository.append_evidence(event_type="TARGETED_BATCH_PLAN_FROZEN", entity_type="research_program",
                                   entity_id=program, payload={"plan_hash": plan_hash, "protocol_id": str(v2),
                                                               "search_program_id": SEARCH_PROGRAM_ID, "search_n": 5})
    return plan


def _load_history() -> dict[str, list[Candle]]:
    raw = json.loads(BASE_HISTORY.read_text())
    return {symbol: [Candle.model_validate(row) for row in raw[symbol]["one_hour"]] for symbol in CORE_SYMBOLS}


def _merge(base: list[Candle], recent: list[Candle]) -> list[Candle]:
    values = {item.timestamp_ms: item for item in base}
    values.update({item.timestamp_ms: item for item in recent})
    return [values[key] for key in sorted(values)]


def _save_run(repository: ResearchRepository, cycle_id: Any, role: str, prompt: str, result: dict[str, Any], model: str) -> Any:
    return repository.save_qwen_run(
        cycle_id=cycle_id, role=role, model=result["observed_model"] or model,
        endpoint_path=result["endpoint_path"], prompt_text=prompt, prompt_version=f"targeted-{role}-v2",
        request_hash=result["request_hash"], response_hash=result["response_hash"], final_text=result["final_text"],
        parsed_json=result["parsed_json"], status="PASS" if result["validation"]["valid"] else (result["error_code"] or "INVALID"),
        token_usage=result["response_metadata"]["usage"], latency_ms=result["latency_ms"],
        attempt_count=1 + result["repair_attempts"],
    )


def _budget(database_url: str, protocol_id: Any) -> dict[str, int]:
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """SELECT count(*), COALESCE(sum(attempt_count),0),
                      COALESCE(sum(CASE WHEN (token_usage->>'measured_all_attempts_total_tokens') ~ '^[0-9]+$'
                          THEN (token_usage->>'measured_all_attempts_total_tokens')::bigint ELSE 0 END),0),
                      COALESCE(sum(CASE WHEN (token_usage->>'conservative_budget_tokens') ~ '^[0-9]+$'
                          THEN (token_usage->>'conservative_budget_tokens')::bigint ELSE 0 END),0)
               FROM qwen_runs q JOIN research_cycles c ON c.id=q.cycle_id WHERE c.protocol_id=%s""",
            (protocol_id,),
        ).fetchone()
    return {"logical_calls": int(row[0]), "http_attempts": int(row[1]), "measured_tokens": int(row[2]),
            "conservative_tokens": int(row[3])}


def _assert_budget(current: dict[str, int], *, reserve_tokens: int) -> None:
    caps = PROTOCOL_V2["budget"]
    if current["logical_calls"] >= caps["max_logical_calls"]:
        raise RuntimeError("TARGETED_LOGICAL_CALL_BUDGET_EXHAUSTED")
    if current["http_attempts"] >= caps["max_live_http_attempts"]:
        raise RuntimeError("TARGETED_HTTP_ATTEMPT_BUDGET_EXHAUSTED")
    if current["conservative_tokens"] + reserve_tokens > caps["max_additional_measured_tokens"]:
        raise RuntimeError("TARGETED_TOKEN_BUDGET_EXHAUSTED")


def _prompt(slot: str, plan: dict[str, Any], forbidden: list[dict[str, int]]) -> str:
    detail = SLOTS[slot]
    transition = f" Transition must be {detail['transition'][0]} -> {detail['transition'][1]}." if "transition" in detail else ""
    return (
        "Return JSON only: one autonomous fdp-v2 rToken FactorProposal matching the supplied schema. "
        f"Schema:{json.dumps(FactorProposalV2.model_json_schema(), separators=(',', ':'))}. "
        f"Slot {slot} ({detail['title']}); required session_filter includes only {detail['required_session']}.{transition} "
        f"Requirements:{json.dumps(detail['requirements'])}. Eligible universe:{json.dumps(list(CORE_SYMBOLS))}. "
        "Use closed OHLC only; volume is forbidden. Use low or medium expected frequency, long/flat, next-bar compatible mechanics, "
        "rebalance >=6, and explain the economic mechanism, structural novelty, and why costs should not dominate. "
        "The first universe symbol is the traded anchor; every referenced symbol must be in universe. "
        f"Forbidden previous/new operator multisets:{json.dumps(forbidden, separators=(',', ':'))}. "
        f"Aggregate structural feedback only:{plan['aggregate_feedback']} Do not claim performance or alpha."
    )


def _plan_semantic(slot: str, proposal: FactorProposalV2, forbidden: list[dict[str, int]]) -> list[str]:
    errors = validate_slot(proposal, slot, forbidden)
    detail = SLOTS[slot]
    if proposal.session_filter != [detail["required_session"]]:
        errors.append("PLAN_SESSION_MISMATCH")
    if "transition" in detail and [proposal.transition_from, proposal.transition_to] != detail["transition"]:
        errors.append("PLAN_TRANSITION_MISMATCH")
    if not set(proposal.universe).issubset(CORE_SYMBOLS):
        errors.append("UNAPPROVED_SYMBOL")
    return errors


async def run_batch(database_url: str) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.qwen_api_key:
        raise RuntimeError("BITGET_QWEN_API_KEY is required")
    repository, protocol_id, program_id = _setup(database_url)
    plan = json.loads((OUTPUT / "BATCH_PLAN.json").read_text())
    plan_hash = canonical_hash(plan)
    with psycopg.connect(database_url) as connection:
        frozen = connection.execute(
            "SELECT 1 FROM evidence_events WHERE event_type='TARGETED_BATCH_PLAN_FROZEN' AND payload_json->>'plan_hash'=%s",
            (plan_hash,),
        ).fetchone()
    if not frozen:
        raise RuntimeError("TARGETED_BATCH_PLAN_FROZEN missing")
    if (OUTPUT / "decision.json").exists():
        return json.loads((OUTPUT / "decision.json").read_text())

    async with BitgetPublicClient() as bitget:
        instruments, *sets = await asyncio.gather(
            bitget.instruments(), *(bitget.recent_candles(symbol, "1H", 1000) for symbol in CORE_SYMBOLS)
        )
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    recent = {symbol: closed_candles(rows, "1H", now_ms) for symbol, rows in zip(CORE_SYMBOLS, sets)}
    write_json(RECENT_HISTORY, {"retrieved_at": datetime.now(UTC).isoformat(),
                                "symbols": {symbol: [row.model_dump(mode="json") for row in rows] for symbol, rows in recent.items()}})
    base = _load_history()
    candles = {symbol: _merge(base[symbol], recent[symbol]) for symbol in CORE_SYMBOLS}
    instrument_map = {item["symbol"]: item for item in instruments["data"]}
    prior = json.loads(PHASE3_DIVERSITY.read_text())
    forbidden = [item["fingerprint"]["operator_multiset"] for item in prior["factors"]]
    trials: list[dict[str, Any]] = []

    with repository.worker_lock() as acquired:
        if not acquired:
            raise RuntimeError("TARGETED_BATCH_LOCKED")
        async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
            for offset, slot in enumerate(SLOTS, start=6):
                key = f"fdp-v2-targeted-slot-{slot}"
                cycle = repository.cycle(key)
                cycle_id = repository.upsert_cycle(protocol_id, offset, key, datetime.now(UTC))
                repository.set_cycle_search_program(cycle_id, program_id, slot)
                existing = repository.hypothesis_for_cycle(cycle_id)
                if existing:
                    try:
                        proposal = FactorProposalV2.model_validate(existing["proposal"])
                    except Exception:
                        proposal = None
                    trial_number = existing["trial_number"]
                    factor_id = existing["factor_version_id"]
                    factor_hash = existing["canonical_hash"]
                else:
                    _assert_budget(_budget(database_url, protocol_id), reserve_tokens=6000)
                    prompt = _prompt(slot, plan, forbidden)
                    repository.append_evidence(event_type="TARGETED_QWEN_REQUEST", entity_type="research_cycle", entity_id=cycle_id,
                                               payload={"slot": slot, "role": "proposer", "prompt_hash": canonical_hash(prompt)})
                    result = await probe_json_chat(
                        client, model=settings.qwen_model, api_key=settings.qwen_api_key, schema=FactorProposalV2,
                        purpose=f"fdp-v2 Slot {slot} FactorProposal", prompt=prompt, max_tokens=3000,
                        max_repair_attempts=1, semantic_validator=lambda item, s=slot, f=list(forbidden): _plan_semantic(s, item, f),
                    )
                    run_id = _save_run(repository, cycle_id, "proposer", prompt, result, settings.qwen_model)
                    repository.append_evidence(event_type="TARGETED_QWEN_RESPONSE", entity_type="research_cycle", entity_id=cycle_id,
                                               payload={"slot": slot, "role": "proposer", "response_hash": result["response_hash"],
                                                        "valid": result["validation"]["valid"], "attempts": 1 + result["repair_attempts"]})
                    trial_number = repository.allocate_search_trial(program_id)
                    if not result["validation"]["valid"]:
                        _, factor_id = repository.commit_invalid_hypothesis(
                            protocol_id=protocol_id, cycle_id=cycle_id, trial_number=trial_number, proposer_run_id=run_id,
                            slot=slot, response_hash=result["response_hash"], validation_error=result["validation"]["error"] or "invalid",
                        )
                        proposal = None
                        factor_hash = result["response_hash"]
                    else:
                        proposal = FactorProposalV2.model_validate(result["parsed_json"])
                        identity = targeted_factor_identity(proposal)
                        _, factor_id, duplicate = repository.commit_hypothesis(
                            protocol_id=protocol_id, cycle_id=cycle_id, trial_number=trial_number,
                            proposer_run_id=run_id, proposal=proposal.model_dump(mode="json"), canonical_hash=identity,
                        )
                        factor_hash = identity
                        if duplicate:
                            proposal = None
                    repository.append_evidence(event_type="TARGETED_HYPOTHESIS_COMMITTED", entity_type="factor_version", entity_id=factor_id,
                                               payload={"slot": slot, "trial_number": trial_number, "canonical_hash": factor_hash,
                                                        "search_n": repository.search_program_n(program_id)})
                errors = _plan_semantic(slot, proposal, forbidden) if proposal else ["REJECTED_STRUCTURAL_MODEL_OUTPUT"]
                fingerprint = operator_fingerprint(proposal) if proposal else {"invalid": 1}
                forbidden.append(fingerprint)
                trials.append({"slot": slot, "cycle_id": cycle_id, "factor_id": factor_id, "trial_number": trial_number,
                               "proposal": proposal, "structural_errors": errors, "fingerprint": fingerprint,
                               "factor_hash": factor_hash})

            evaluations: dict[int, TargetedEvaluation] = {}
            new_sharpes: list[float] = []
            for trial in trials:
                if trial["structural_errors"]:
                    new_sharpes.append(0.0)
                    continue
                proposal = trial["proposal"]
                valid_from = {f"{symbol}.close": certification_start_ms(int(instrument_map[symbol]["launchTime"]))
                              for symbol in proposal.universe}
                evaluation = evaluate_targeted_factor(proposal, candles, trial_number=trial["trial_number"], field_valid_from_ms=valid_from)
                evaluations[trial["trial_number"]] = evaluation
                new_sharpes.append(return_moments([row["net"] for row in evaluation.rows]).sharpe or 0.0)

            old_summary = json.loads(PHASE3_SUMMARY.read_text())
            old_sharpes = [item["dsr"]["observed_sharpe"] or 0.0 for item in old_summary["factors"]]
            hurdle = expected_maximum_sharpe(old_sharpes + new_sharpes, expected_mean=0.0)
            if hurdle["status"] != "OK" or repository.search_program_n(program_id) != 8:
                raise RuntimeError("global search population did not reach the frozen N=8")

            complete: list[dict[str, Any]] = []
            for trial in trials:
                proposal = trial["proposal"]
                proposal_payload = proposal.model_dump(mode="json") if proposal else {"slot": trial["slot"], "invalid": True}
                report = structural_rejection(proposal_payload, trial["trial_number"], trial["structural_errors"], slot=trial["slot"]) if trial["structural_errors"] else finalize_evaluation(
                    evaluations[trial["trial_number"]], benchmark_sharpe=float(hurdle["sr_star"]),
                    search_n=8, sigma_sr=float(hurdle["sigma_sr"]),
                )
                experiment_id = repository.save_experiment(
                    factor_version_id=trial["factor_id"], dataset_hash=report["dataset_hash"],
                    data_contract=report.get("data_contract", {}), metrics=report, report_hash=report["report_hash"],
                    protocol_version=PROTOCOL_VERSION_V2,
                )
                repository.save_gates(experiment_id, report["gates"])
                repository.transition(trial["factor_id"], "COMMITTED", "FORMALIZED", "fdp-v2 structure validated.", experiment_id=experiment_id)
                repository.transition(trial["factor_id"], "FORMALIZED", "BACKTESTED", "Deterministic targeted evaluation completed.", experiment_id=experiment_id)
                for gate in report["gates"]:
                    repository.append_evidence(event_type="TARGETED_GATE_RESULT", entity_type="factor_version", entity_id=trial["factor_id"],
                                               payload={"trial_number": trial["trial_number"], "slot": trial["slot"], **gate})
                existing_lifecycle = repository.qwen_run_for_cycle(trial["cycle_id"], "lifecycle")
                if existing_lifecycle:
                    lifecycle = LifecycleDecision.model_validate(existing_lifecycle["parsed_json"])
                    lifecycle_run_id = existing_lifecycle["id"]
                else:
                    _assert_budget(_budget(database_url, protocol_id), reserve_tokens=1800)
                    detail = {"proposal": proposal_payload, "aggregate": report["aggregate"],
                              "gates": report["gates"], "metrics": report.get("metrics", {}),
                              "instruction": "Explain this trial only. REVISE is recorded but cannot spawn a child. Deterministic gates own promotion."}
                    prompt = ("Return JSON only for LifecycleDecision. Schema:"
                              f"{json.dumps(LifecycleDecision.model_json_schema(), separators=(',', ':'))}. Evidence:"
                              f"{json.dumps(detail, separators=(',', ':'))}")
                    repository.append_evidence(event_type="TARGETED_QWEN_REQUEST", entity_type="research_cycle", entity_id=trial["cycle_id"],
                                               payload={"slot": trial["slot"], "role": "lifecycle", "prompt_hash": canonical_hash(prompt)})
                    result = await probe_json_chat(client, model=settings.qwen_model, api_key=settings.qwen_api_key,
                                                   schema=LifecycleDecision, purpose="LifecycleDecision", prompt=prompt,
                                                   max_tokens=900, max_repair_attempts=1)
                    lifecycle_run_id = _save_run(repository, trial["cycle_id"], "lifecycle", prompt, result, settings.qwen_model)
                    lifecycle = LifecycleDecision.model_validate(result["parsed_json"]) if result["validation"]["valid"] else LifecycleDecision(
                        action="ABANDON", reason="Invalid lifecycle output after one repair; deterministic state retained.", revision_intent=None)
                    repository.append_evidence(event_type="TARGETED_QWEN_RESPONSE", entity_type="research_cycle", entity_id=trial["cycle_id"],
                                               payload={"slot": trial["slot"], "role": "lifecycle", "response_hash": result["response_hash"],
                                                        "valid": result["validation"]["valid"], "attempts": 1 + result["repair_attempts"]})
                repository.transition(trial["factor_id"], "BACKTESTED", report["aggregate"],
                                      f"Deterministic {report['aggregate']}; lifecycle {lifecycle.action}; no revision child.",
                                      qwen_run_id=lifecycle_run_id, experiment_id=experiment_id)
                manifest = {"slot": trial["slot"], "trial_number": trial["trial_number"], "protocol_hash": PROTOCOL_V2_HASH,
                            "factor_hash": trial["factor_hash"], "report_hash": report["report_hash"],
                            "aggregate": report["aggregate"], "search_n": 8, "automatic_revision_child": False}
                manifest_hash = canonical_hash(manifest)
                repository.append_evidence(event_type="TARGETED_CYCLE_COMPLETE", entity_type="research_cycle", entity_id=trial["cycle_id"],
                                           payload={**manifest, "manifest_hash": manifest_hash})
                repository.complete_cycle(trial["cycle_id"], "COMPLETE", manifest_hash)
                complete.append({"slot": trial["slot"], "family": SLOTS[trial["slot"]]["family"],
                                 "trial_number": trial["trial_number"], "factor_version_id": str(trial["factor_id"]),
                                 "proposal": proposal_payload, "operator_fingerprint": trial["fingerprint"],
                                 "report": report, "lifecycle": lifecycle.model_dump(mode="json")})
                write_json(OUTPUT / "trials.json", {"search_program_id": SEARCH_PROGRAM_ID, "trials": complete})

    budget = _budget(database_url, protocol_id)
    if budget["logical_calls"] != 6 or budget["http_attempts"] > 8 or budget["conservative_tokens"] > 25000:
        raise RuntimeError(f"targeted batch budget invariant failed: {budget}")
    gate_counts = Counter(gate["outcome"] for trial in complete for gate in trial["report"]["gates"])
    gate_summary = {"gate_distribution": dict(sorted(gate_counts.items())),
                    "first_hard_fail": {trial["slot"]: trial["report"]["first_hard_fail"] for trial in complete},
                    "outcomes": {trial["slot"]: trial["report"]["aggregate"] for trial in complete}}
    write_json(OUTPUT / "gate-summary.json", gate_summary)
    fingerprints = [trial["operator_fingerprint"] for trial in complete]
    sessions = sorted({session for trial in complete for session in trial["proposal"].get("session_filter", [])})
    diversity = {"accepted": len({trial["family"] for trial in complete}) == 3 and len({json.dumps(value, sort_keys=True) for value in fingerprints}) == 3
                  and not any(value in [item["fingerprint"]["operator_multiset"] for item in prior["factors"]] for value in fingerprints)
                  and len(sessions) >= 2 and any(trial["family"] == "cross_sectional" for trial in complete),
                  "families": sorted({trial["family"] for trial in complete}), "sessions": sessions,
                  "operator_fingerprints": fingerprints, "old_fingerprint_clone": False,
                  "performance_fields_used_for_diversity": False}
    write_json(OUTPUT / "diversity.json", diversity)
    write_json(OUTPUT / "budget.json", {**budget, "caps": PROTOCOL_V2["budget"], "search_n_before": 5,
                                         "search_n_after": repository.search_program_n(program_id), "hurdle": hurdle})
    candidates = sum(trial["report"]["aggregate"] in {"CANDIDATE", "CERTIFIED"} for trial in complete)
    certified = sum(trial["report"]["aggregate"] == "CERTIFIED" for trial in complete)
    recommendation = "PAPER_PROBATION_AVAILABLE" if candidates else "RESEARCH_PROTOCOL_REVIEW"
    decision = {"completed_at": datetime.now(UTC).isoformat(), "protocol": PROTOCOL_VERSION_V2,
                "search_program_id": SEARCH_PROGRAM_ID, "search_n_before": 5, "search_n_after": 8,
                "candidate_count": candidates, "certified_count": certified, "paper_trading_started": False,
                "gate_distribution": dict(sorted(gate_counts.items())), "diversity_accepted": diversity["accepted"],
                "budget": budget, "recommendation": recommendation,
                "trials": [{"slot": trial["slot"], "trial_number": trial["trial_number"],
                            "name": trial["proposal"].get("name", f"Invalid Slot {trial['slot']} proposal"),
                            "thesis": trial["proposal"].get("thesis", "Structurally invalid model output preserved."),
                            "outcome": trial["report"]["aggregate"],
                            "first_hard_fail": trial["report"]["first_hard_fail"]} for trial in complete]}
    write_json(OUTPUT / "decision.json", decision)
    write_json(PUBLIC, {"plan": plan, "trials": complete, "gate_summary": gate_summary,
                        "diversity": diversity, "budget": {**budget, "search_n_before": 5, "search_n_after": 8},
                        "decision": decision})
    repository.append_evidence(event_type="TARGETED_BATCH_COMPLETE", entity_type="research_program", entity_id=program_id,
                               payload={"decision_hash": canonical_hash(decision), "recommendation": recommendation,
                                        "search_n": 8, "paper_trading_started": False})
    return decision


def finalize_budget_abort(database_url: str) -> dict[str, Any]:
    repository, protocol_id, program_id = _setup(database_url)
    plan = json.loads((OUTPUT / "BATCH_PLAN.json").read_text())
    budget = _budget(database_url, protocol_id)
    if budget["measured_tokens"] <= PROTOCOL_V2["budget"]["max_additional_measured_tokens"]:
        raise RuntimeError("budget-abort finalization requires an observed hard-budget breach")
    trials: list[dict[str, Any]] = []
    for slot in ("A", "B"):
        key = f"fdp-v2-targeted-slot-{slot}"
        cycle = repository.cycle(key)
        if not cycle:
            raise RuntimeError(f"missing preserved cycle for Slot {slot}")
        hypothesis = repository.hypothesis_for_cycle(cycle["id"])
        if not hypothesis:
            raise RuntimeError(f"missing preserved hypothesis for Slot {slot}")
        payload = hypothesis["proposal"]
        errors = ["REJECTED_STRUCTURAL_MODEL_OUTPUT", str(payload.get("validation_error", "invalid after repair"))]
        report = structural_rejection(payload, hypothesis["trial_number"], errors, slot=slot)
        experiment_id = repository.save_experiment(
            factor_version_id=hypothesis["factor_version_id"], dataset_hash=report["dataset_hash"],
            data_contract={}, metrics=report, report_hash=report["report_hash"], protocol_version=PROTOCOL_VERSION_V2,
        )
        repository.save_gates(experiment_id, report["gates"])
        repository.transition(hypothesis["factor_version_id"], "COMMITTED", "REJECTED",
                              "Structural model output remained invalid after one repair; lifecycle call blocked by hard token budget.",
                              experiment_id=experiment_id)
        for gate in report["gates"]:
            repository.append_evidence(event_type="TARGETED_GATE_RESULT", entity_type="factor_version",
                                       entity_id=hypothesis["factor_version_id"],
                                       payload={"slot": slot, "trial_number": hypothesis["trial_number"], **gate})
        manifest = {"slot": slot, "trial_number": hypothesis["trial_number"], "protocol_hash": PROTOCOL_V2_HASH,
                    "factor_hash": hypothesis["canonical_hash"], "report_hash": report["report_hash"],
                    "aggregate": "REJECTED", "search_n": repository.search_program_n(program_id),
                    "automatic_revision_child": False, "lifecycle_call": "BLOCKED_BUDGET"}
        manifest_hash = canonical_hash(manifest)
        repository.append_evidence(event_type="TARGETED_CYCLE_COMPLETE", entity_type="research_cycle", entity_id=cycle["id"],
                                   payload={**manifest, "manifest_hash": manifest_hash})
        repository.complete_cycle(cycle["id"], "COMPLETE", manifest_hash)
        trials.append({"slot": slot, "family": SLOTS[slot]["family"], "trial_number": hypothesis["trial_number"],
                       "factor_version_id": str(hypothesis["factor_version_id"]), "proposal": payload,
                       "operator_fingerprint": {"invalid": 1}, "report": report,
                       "lifecycle": {"status": "BLOCKED_BUDGET", "automatic_revision_child": False}})

    slot = "C"
    key = "fdp-v2-targeted-slot-C"
    cycle_id = repository.upsert_cycle(protocol_id, 8, key, datetime.now(UTC))
    repository.set_cycle_search_program(cycle_id, program_id, slot)
    repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_BUDGET_EXHAUSTED")
    repository.append_evidence(event_type="TARGETED_CYCLE_NO_RUN", entity_type="research_cycle", entity_id=cycle_id,
                               payload={"slot": slot, "error_code": "NO_RUN_BUDGET_EXHAUSTED",
                                        "measured_tokens": budget["measured_tokens"], "token_cap": 25000,
                                        "trial_allocated": False, "qwen_called": False})
    trials.append({"slot": "C", "family": SLOTS["C"]["family"], "trial_number": None,
                   "proposal": None, "report": None, "lifecycle": {"status": "NOT_CALLED_BUDGET"},
                   "state": "NO_RUN_BUDGET_EXHAUSTED"})
    write_json(OUTPUT / "trials.json", {"search_program_id": SEARCH_PROGRAM_ID, "trials": trials})

    gate_counts = Counter(gate["outcome"] for trial in trials if trial["report"] for gate in trial["report"]["gates"])
    gate_summary = {"gate_distribution": dict(sorted(gate_counts.items())),
                    "first_hard_fail": {"A": "Syntax", "B": "Syntax", "C": None},
                    "outcomes": {"A": "REJECTED", "B": "REJECTED", "C": "NO_RUN_BUDGET_EXHAUSTED"}}
    write_json(OUTPUT / "gate-summary.json", gate_summary)
    diversity = {"accepted": False, "reason": "Only two invalid structural proposals were committed; Slot C was blocked by budget.",
                 "families_planned": ["cross_sectional", "session_transition", "residual"],
                 "valid_families_observed": [], "valid_sessions_observed": [], "old_fingerprint_clone": None,
                 "performance_fields_used_for_diversity": False}
    write_json(OUTPUT / "diversity.json", diversity)
    write_json(OUTPUT / "budget.json", {**budget, "caps": PROTOCOL_V2["budget"], "hard_cap_breached": True,
                                         "breach_amount_tokens": budget["measured_tokens"] - 25000,
                                         "search_n_before": 5, "search_n_after": repository.search_program_n(program_id)})
    decision = {"completed_at": datetime.now(UTC).isoformat(), "status": "ABORTED_BUDGET",
                "protocol": PROTOCOL_VERSION_V2, "search_program_id": SEARCH_PROGRAM_ID,
                "search_n_before": 5, "search_n_after": repository.search_program_n(program_id),
                "planned_trials": 3, "committed_trials": 2, "no_run_slots": ["C"],
                "candidate_count": 0, "certified_count": 0, "paper_trading_started": False,
                "gate_distribution": dict(sorted(gate_counts.items())), "diversity_accepted": False,
                "budget": budget, "recommendation": "RESEARCH_PROTOCOL_REVIEW",
                "contradiction": "Two repaired proposer calls exceeded the frozen measured-token cap before Slot C."}
    write_json(OUTPUT / "decision.json", decision)
    write_json(PUBLIC, {"plan": plan, "trials": trials, "gate_summary": gate_summary,
                        "diversity": diversity, "budget": {**budget, "search_n_before": 5,
                                                             "search_n_after": repository.search_program_n(program_id)},
                        "decision": decision})
    repository.append_evidence(event_type="TARGETED_BATCH_ABORTED_BUDGET", entity_type="research_program",
                               entity_id=program_id, payload={"decision_hash": canonical_hash(decision),
                                                              "recommendation": "RESEARCH_PROTOCOL_REVIEW",
                                                              "search_n": repository.search_program_n(program_id),
                                                              "paper_trading_started": False})
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze-plan", "run", "finalize-budget-abort"))
    args = parser.parse_args()
    settings = Settings.from_env()
    database_url = _database(settings)
    if args.action == "freeze-plan":
        result = freeze_plan(database_url)
    elif args.action == "run":
        result = asyncio.run(run_batch(database_url))
    else:
        result = finalize_budget_abort(database_url)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
