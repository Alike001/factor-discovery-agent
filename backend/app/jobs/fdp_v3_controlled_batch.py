from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

import httpx
import psycopg
from pydantic import BaseModel

from app.bitget.client import BitgetPublicClient, closed_candles
from app.bitget.integrity import certification_start_ms
from app.bitget.models import Candle
from app.bitget.session import NEW_YORK, parse_calendar_closures
from app.config import Settings
from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.evidence.verify import verify_chain
from app.qwen.budget import PostgresTokenBudget, ProjectedBudgetExhausted
from app.qwen.client import json_chat_attempt
from app.qwen.models import LifecycleDecision
from app.research.evaluator_v2 import TargetedEvaluation, evaluate_targeted_factor, finalize_evaluation, structural_rejection
from app.research.protocol import CORE_SYMBOLS
from app.research.protocol_v2 import PROTOCOL_V2, PROTOCOL_VERSION_V2, SEARCH_PROGRAM_ID
from app.research.protocol_v3 import FDP_V3, FDP_V3_HASH, PROTOCOL_VERSION_V3
from app.research.recipes import REGISTRY, FactorRecipe, ast_hash, compile_recipe, recipe_hash
from app.research.session_transition import (
    ANCHOR_INTERVAL_MS,
    CONTRACT_VERSION,
    CalendarWindow,
    evaluate_transition_recipe,
    finalize_transition_evaluation,
)
from app.research.statistics import expected_maximum_sharpe, return_moments

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "evidence/fdp-v3-batch"
PUBLIC = ROOT / "web/public/evidence/fdp-v3-batch.json"
BASE_HISTORY = ROOT / "evidence/raw/core-history-provenance-v2.json"
PHASE3_SUMMARY = ROOT / "evidence/phase3/replay-summary.json"
BUDGET_SCOPE = "fdp-v3-controlled-batch"
HARD_TOKEN_LIMIT = 14_000

SLOTS: dict[str, dict[str, Any]] = {
    "A": {"family": "beta_residual", "title": "Beta residual"},
    "B": {"family": "session_transition", "title": "Session transition"},
}


def _database(settings: Settings) -> str:
    return settings.database_url or "postgresql://postgres@127.0.0.1:55432/bitget_research"


def _setup(database_url: str) -> tuple[ResearchRepository, Any, Any]:
    apply_migrations(database_url)
    repository = ResearchRepository(database_url)
    v1 = repository.ensure_protocol("fdp-v1")
    v2 = repository.ensure_protocol(PROTOCOL_VERSION_V2, PROTOCOL_V2)
    v3 = repository.ensure_protocol(PROTOCOL_VERSION_V3, FDP_V3)
    program = repository.ensure_search_program(SEARCH_PROGRAM_ID, [v1, v2, v3], starting_trial=6)
    return repository, v3, program


def _prior_fingerprint_hashes() -> list[str]:
    values: list[Any] = []
    diversity = ROOT / "evidence/phase3/research-diversity.json"
    if diversity.exists():
        values.extend(item["fingerprint"] for item in json.loads(diversity.read_text())["factors"])
    targeted = ROOT / "evidence/targeted-batch-v2/trials.json"
    if targeted.exists():
        values.extend(item.get("operator_fingerprint", {"invalid": True})
                      for item in json.loads(targeted.read_text())["trials"] if item.get("trial_number"))
    return sorted({canonical_hash(value) for value in values})


def activate_and_freeze(database_url: str) -> dict[str, Any]:
    repository, protocol_id, program_id = _setup(database_url)
    search_n = repository.search_program_n(program_id)
    if search_n != 7:
        raise RuntimeError(f"fdp-v3 activation requires search N=7, observed {search_n}")
    protocol_artifact = {"protocol": FDP_V3, "protocol_hash": FDP_V3_HASH, "activated": True,
                         "activated_before_first_qwen_call": True}
    protocol_path = OUTPUT / "PROTOCOL.json"
    if protocol_path.exists() and json.loads(protocol_path.read_text()) != protocol_artifact:
        raise RuntimeError("immutable fdp-v3 protocol artifact mismatch")
    if not protocol_path.exists():
        write_json(protocol_path, protocol_artifact)
        repository.append_evidence(
            event_type="FDP_V3_PROTOCOL_ACTIVATED", entity_type="research_protocol", entity_id=protocol_id,
            payload={"protocol_hash": FDP_V3_HASH, "search_program_id": SEARCH_PROGRAM_ID, "search_n": 7},
        )
    plan = {
        "batch": "fdp-v3-controlled-two-slot", "protocol_version": PROTOCOL_VERSION_V3,
        "protocol_hash": FDP_V3_HASH, "search_program_id": SEARCH_PROGRAM_ID,
        "search_n_before": 7, "maximum_slots": 2, "slot_order": ["A", "B"],
        "slots": SLOTS, "ready_families": ["beta_residual", "session_transition"],
        "cost_model": FDP_V3["cost_model"], "gate_policy": FDP_V3["gate_policy"],
        "split_rule": FDP_V3["split_rule"], "session_transition_contract": CONTRACT_VERSION,
        "automatic_revision_children": False, "hidden_replacements": False,
        "performance_feedback_allowed": False,
        "model_context_fact": "Earlier raw-AST proposals caused structural failures, so this protocol uses deterministic FactorRecipe compilation. Prior economic performance is intentionally hidden.",
        "prior_structural_fingerprint_hashes": _prior_fingerprint_hashes(),
        "budget": {"max_logical_calls": 4, "max_http_attempts": 6,
                   "hard_reserved_or_charged_tokens": HARD_TOKEN_LIMIT, "max_repairs_per_request": 1},
    }
    plan_path = OUTPUT / "BATCH_PLAN.json"
    if plan_path.exists() and json.loads(plan_path.read_text()) != plan:
        raise RuntimeError("immutable fdp-v3 batch plan mismatch")
    if not plan_path.exists():
        write_json(plan_path, plan)
        repository.append_evidence(
            event_type="FDP_V3_BATCH_PLAN_FROZEN", entity_type="research_program", entity_id=program_id,
            payload={"plan_hash": canonical_hash(plan), "protocol_hash": FDP_V3_HASH,
                     "slot_order": ["A", "B"], "search_n": 7},
        )
    return {"protocol_hash": FDP_V3_HASH, "plan_hash": canonical_hash(plan), "search_n": search_n}


def _slot_prompt(slot: str, plan: dict[str, Any]) -> str:
    family = SLOTS[slot]["family"]
    item = REGISTRY[family]
    return (
        f"Return exactly one JSON object validating as factor-recipe-v1 for controlled FDP-v3 Slot {slot}. "
        f"Required family:{family}. Legal parameters:{json.dumps(item['parameters'], separators=(',', ':'))}. "
        f"Valid shape example:{json.dumps(item['example'], separators=(',', ':'))}. "
        f"Eligible symbols:{json.dumps(list(CORE_SYMBOLS))}. Use only the assigned family and eligible symbols. "
        "No raw AST, signal, entry_condition, exit_condition, performance claim, prior PnL, Sharpe, DSR, ranking, or revision. "
        "Choose a falsifiable economic mechanism, legal parameters, low/medium frequency, and explain novelty and cost tolerance. "
        f"Avoid prior structural fingerprint hashes:{json.dumps(plan['prior_structural_fingerprint_hashes'])}. "
        f"Current global search N is 7. {plan['model_context_fact']}"
    )


def _recipe_errors(slot: str, recipe: FactorRecipe) -> list[str]:
    expected = SLOTS[slot]["family"]
    errors = []
    if recipe.family != expected:
        errors.append("SLOT_FAMILY_MISMATCH")
    if not set(recipe.universe).issubset(CORE_SYMBOLS):
        errors.append("UNAPPROVED_SYMBOL")
    try:
        compile_recipe(recipe)
    except (TypeError, ValueError) as exc:
        errors.append(f"COMPILER_REJECTED:{exc}")
    return errors


def _usage_total(result: dict[str, Any]) -> int | None:
    total = result["response_metadata"]["usage"].get("total_tokens")
    return int(total) if isinstance(total, int) else None


async def _logical_call(
    *, client: httpx.AsyncClient, settings: Settings, database_url: str, repository: ResearchRepository,
    cycle_id: Any, slot: str, role: str, schema: type[BaseModel], prompt: str, max_tokens: int,
    semantic_validator: Callable[[Any], list[str]] | None = None,
) -> tuple[dict[str, Any], Any]:
    budget = PostgresTokenBudget(database_url, BUDGET_SCOPE, HARD_TOKEN_LIMIT)
    attempts: list[dict[str, Any]] = []
    current_prompt = prompt
    budget_blocked = False
    for attempt_number in (1, 2):
        call_key = f"slot-{slot}-{role}-attempt-{attempt_number}"
        with psycopg.connect(database_url) as connection:
            prior_attempts = connection.execute(
                "SELECT count(*) FROM qwen_token_reservations WHERE scope=%s", (BUDGET_SCOPE,)
            ).fetchone()[0]
        if prior_attempts >= 6:
            budget_blocked = True
            repository.append_evidence(
                event_type="FDP_V3_QWEN_ATTEMPT_REFUSED", entity_type="research_cycle", entity_id=cycle_id,
                payload={"slot": slot, "role": role, "attempt": attempt_number,
                         "reason": "HTTP_ATTEMPT_CAP", "prompt_hash": canonical_hash(current_prompt)},
            )
            break
        try:
            reservation = budget.reserve(call_key, current_prompt, max_tokens)
        except ProjectedBudgetExhausted:
            budget_blocked = True
            repository.append_evidence(
                event_type="FDP_V3_QWEN_ATTEMPT_REFUSED", entity_type="research_cycle", entity_id=cycle_id,
                payload={"slot": slot, "role": role, "attempt": attempt_number,
                         "reason": "NO_RUN_PROJECTED_BUDGET_EXHAUSTED",
                         "prompt_hash": canonical_hash(current_prompt)},
            )
            break
        repository.append_evidence(
            event_type="FDP_V3_QWEN_REQUEST_RESERVED", entity_type="research_cycle", entity_id=cycle_id,
            payload={"slot": slot, "role": role, "attempt": attempt_number,
                     "reservation_id": str(reservation.id), "reserved_tokens": reservation.reserved_tokens,
                     "prompt_hash": canonical_hash(current_prompt)},
        )
        result = await json_chat_attempt(
            client, model=settings.qwen_model, api_key=settings.qwen_api_key or "", schema=schema,
            purpose=f"fdp-v3 Slot {slot} {role}", prompt=current_prompt, max_tokens=max_tokens,
            semantic_validator=semantic_validator,
        )
        charged = budget.settle(reservation, _usage_total(result))
        metadata = {
            "attempt": attempt_number, "request_hash": result["request_hash"],
            "response_hash": result["response_hash"], "endpoint_path": result["endpoint_path"],
            "model": result["observed_model"] or settings.qwen_model, "latency_ms": result["latency_ms"],
            "usage": result["response_metadata"]["usage"], "reservation": reservation.reserved_tokens,
            "actual_charged": charged, "valid": result["validation"]["valid"],
        }
        attempts.append(metadata)
        repository.append_evidence(
            event_type="FDP_V3_QWEN_RESPONSE", entity_type="research_cycle", entity_id=cycle_id,
            payload={"slot": slot, "role": role, **metadata},
        )
        if result["validation"]["valid"]:
            break
        if attempt_number == 1:
            current_prompt = (
                f"Repair the prior invalid {role} JSON and return only one JSON object. "
                f"Validation error:{result['validation']['error']}. Invalid response:{result['final_text']}. "
                f"Original requirements:{prompt}"
            )
    if not attempts:
        return {"validation": {"valid": False, "error": "NO_RUN_PROJECTED_BUDGET_EXHAUSTED"},
                "parsed_json": None, "attempts": [], "budget_blocked": True}, None
    final = result
    if budget_blocked and not final["validation"]["valid"]:
        final["validation"]["error"] = "NO_RUN_PROJECTED_BUDGET_EXHAUSTED_AFTER_INVALID_OUTPUT"
    usage = {
        "attempts": attempts,
        "measured_tokens": sum(int(item["usage"]["total_tokens"]) for item in attempts
                               if isinstance(item["usage"].get("total_tokens"), int)),
        "reserved_tokens": sum(item["reservation"] for item in attempts),
        "charged_tokens": sum(item["actual_charged"] for item in attempts),
        "repair_count": len(attempts) - 1,
    }
    run_id = repository.save_qwen_run(
        cycle_id=cycle_id, role=role, model=attempts[-1]["model"], endpoint_path=attempts[-1]["endpoint_path"],
        prompt_text="", prompt_version=f"fdp-v3-{role}-v1", request_hash=canonical_hash([x["request_hash"] for x in attempts]),
        response_hash=canonical_hash([x["response_hash"] for x in attempts]), final_text="", parsed_json=None,
        status="PASS" if final["validation"]["valid"] else "INVALID", token_usage=usage,
        latency_ms=sum(item["latency_ms"] for item in attempts), attempt_count=len(attempts),
    )
    return {**final, "attempts": attempts, "budget_blocked": budget_blocked}, run_id


def _load_hourly(symbols: list[str]) -> dict[str, list[Candle]]:
    raw = json.loads(BASE_HISTORY.read_text())
    return {symbol: [Candle.model_validate(row) for row in raw[symbol]["one_hour"]] for symbol in symbols}


def _merge(base: list[Candle], recent: list[Candle]) -> list[Candle]:
    values = {item.timestamp_ms: item for item in base}
    values.update({item.timestamp_ms: item for item in recent})
    return [values[key] for key in sorted(values)]


def _existing_sharpes() -> list[float]:
    summary = json.loads(PHASE3_SUMMARY.read_text())
    values = [item["dsr"]["observed_sharpe"] or 0.0 for item in summary["factors"]]
    return values + [0.0, 0.0]


def _structural_report(recipe_payload: dict[str, Any], trial_number: int, errors: list[str]) -> dict[str, Any]:
    report = structural_rejection(recipe_payload, trial_number, errors, slot="A" if recipe_payload.get("family") == "beta_residual" else "B")
    report["protocol"] = PROTOCOL_VERSION_V3
    report["protocol_hash"] = FDP_V3_HASH
    report["search_program_id"] = SEARCH_PROGRAM_ID
    report["report_hash"] = canonical_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def _budget_evidence(database_url: str) -> dict[str, Any]:
    budget = PostgresTokenBudget(database_url, BUDGET_SCOPE, HARD_TOKEN_LIMIT).usage()
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """SELECT call_key,estimated_input_tokens,max_completion_tokens,reserved_tokens,
                      actual_tokens,charged_tokens,status,created_at,settled_at
               FROM qwen_token_reservations WHERE scope=%s ORDER BY created_at""", (BUDGET_SCOPE,)
        ).fetchall()
    reservations = [
        {"call_key": row[0], "estimated_input_tokens": row[1], "max_completion_tokens": row[2],
         "reserved_tokens": row[3], "actual_tokens": row[4], "charged_tokens": row[5],
         "status": row[6], "created_at": row[7].isoformat(), "settled_at": row[8].isoformat() if row[8] else None}
        for row in rows
    ]
    return {**budget, "reservations": reservations,
            "reserved_tokens_total": sum(item["reserved_tokens"] for item in reservations),
            "measured_tokens_total": sum(item["actual_tokens"] or 0 for item in reservations),
            "http_attempts": len(reservations)}


async def run_batch(database_url: str) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.qwen_api_key:
        raise RuntimeError("BITGET_QWEN_API_KEY is required")
    repository, protocol_id, program_id = _setup(database_url)
    plan = json.loads((OUTPUT / "BATCH_PLAN.json").read_text())
    with psycopg.connect(database_url) as connection:
        activated = connection.execute(
            "SELECT 1 FROM evidence_events WHERE event_type='FDP_V3_PROTOCOL_ACTIVATED' AND payload_json->>'protocol_hash'=%s",
            (FDP_V3_HASH,),
        ).fetchone()
        frozen = connection.execute(
            "SELECT 1 FROM evidence_events WHERE event_type='FDP_V3_BATCH_PLAN_FROZEN' AND payload_json->>'plan_hash'=%s",
            (canonical_hash(plan),),
        ).fetchone()
    if not activated or not frozen:
        raise RuntimeError("fdp-v3 protocol and batch plan must be frozen before live calls")
    if (OUTPUT / "decision.json").exists():
        return json.loads((OUTPUT / "decision.json").read_text())
    if repository.search_program_n(program_id) != 7:
        raise RuntimeError("fdp-v3 batch must begin at search N=7")

    trials: list[dict[str, Any]] = []
    preliminary: dict[int, TargetedEvaluation | dict[str, Any]] = {}
    new_sharpes: list[float] = []
    instrument_map: dict[str, Any] = {}
    async with BitgetPublicClient() as bitget:
        instruments = await bitget.instruments()
    instrument_map = {item["symbol"]: item for item in instruments["data"]}

    with repository.worker_lock() as acquired:
        if not acquired:
            raise RuntimeError("FDP_V3_BATCH_LOCKED")
        async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
            for cycle_number, slot in enumerate(("A", "B"), start=9):
                cycle_id = repository.upsert_cycle(protocol_id, cycle_number, f"fdp-v3-controlled-slot-{slot}", datetime.now(UTC))
                repository.set_cycle_search_program(cycle_id, program_id, slot)
                existing = repository.hypothesis_for_cycle(cycle_id)
                if existing:
                    trial_number = existing["trial_number"]
                    factor_id = existing["factor_version_id"]
                    try:
                        recipe = FactorRecipe.model_validate(existing["proposal"])
                        compiled = compile_recipe(recipe)
                        errors: list[str] = []
                    except Exception:
                        recipe, compiled, errors = None, None, ["REJECTED_STRUCTURAL_MODEL_OUTPUT"]
                    duplicate = existing["duplicate_of"] is not None
                else:
                    prompt = _slot_prompt(slot, plan)
                    if len(prompt) / 4 * 1.25 > 1500:
                        raise RuntimeError("proposer prompt exceeds frozen 1,500-token estimate")
                    result, run_id = await _logical_call(
                        client=client, settings=settings, database_url=database_url, repository=repository,
                        cycle_id=cycle_id, slot=slot, role="proposer", schema=FactorRecipe,
                        prompt=prompt, max_tokens=1200,
                        semantic_validator=lambda item, current_slot=slot: _recipe_errors(current_slot, item),
                    )
                    if run_id is None:
                        repository.complete_cycle(cycle_id, "NO_RUN", None, "NO_RUN_PROJECTED_BUDGET_EXHAUSTED")
                        trials.append({"slot": slot, "trial_number": None, "factor_id": None, "recipe": None,
                                       "compiled": None, "errors": ["NO_RUN_PROJECTED_BUDGET_EXHAUSTED"],
                                       "duplicate": False, "cycle_id": cycle_id})
                        continue
                    trial_number = repository.allocate_search_trial(program_id)
                    if not result["validation"]["valid"]:
                        _, factor_id = repository.commit_invalid_hypothesis(
                            protocol_id=protocol_id, cycle_id=cycle_id, trial_number=trial_number,
                            proposer_run_id=run_id, slot=slot, response_hash=result["response_hash"],
                            validation_error=result["validation"]["error"] or "invalid",
                        )
                        recipe, compiled, errors, duplicate = None, None, [result["validation"]["error"] or "INVALID_RECIPE"], False
                    else:
                        recipe = FactorRecipe.model_validate(result["parsed_json"])
                        compiled = compile_recipe(recipe)
                        identity = recipe_hash(recipe)
                        _, factor_id, duplicate = repository.commit_recipe_hypothesis(
                            protocol_id=protocol_id, program_id=program_id, cycle_id=cycle_id,
                            trial_number=trial_number, proposer_run_id=run_id,
                            recipe=recipe.model_dump(mode="json"), compiled_spec=compiled.model_dump(mode="json"),
                            canonical_identity_hash=identity, compiled_hash=ast_hash(compiled),
                        )
                        errors = ["DUPLICATE_SUPPRESSED"] if duplicate else []
                    repository.append_evidence(
                        event_type="FDP_V3_HYPOTHESIS_COMMITTED", entity_type="factor_version", entity_id=factor_id,
                        payload={"slot": slot, "trial_number": trial_number, "family": SLOTS[slot]["family"],
                                 "duplicate": duplicate, "search_n": repository.search_program_n(program_id)},
                    )
                trials.append({"slot": slot, "trial_number": trial_number, "factor_id": factor_id,
                               "recipe": recipe, "compiled": compiled, "errors": errors,
                               "duplicate": duplicate, "cycle_id": cycle_id})

            for trial in trials:
                recipe = trial["recipe"]
                if trial["errors"] or recipe is None:
                    if trial["trial_number"] is not None and not trial["duplicate"]:
                        new_sharpes.append(0.0)
                    continue
                compiled = trial["compiled"]
                if recipe.family == "beta_residual":
                    symbols = list(compiled.universe)
                    async with BitgetPublicClient() as bitget:
                        recent_sets = await asyncio.gather(*(bitget.recent_candles(symbol, "1H", 1000) for symbol in symbols))
                    now_ms = int(datetime.now(UTC).timestamp() * 1000)
                    base = _load_hourly(symbols)
                    candle_map = {symbol: _merge(base[symbol], closed_candles(rows, "1H", now_ms))
                                  for symbol, rows in zip(symbols, recent_sets)}
                    valid_from = {f"{symbol}.close": certification_start_ms(int(instrument_map[symbol]["launchTime"]))
                                  for symbol in symbols}
                    evaluation = evaluate_targeted_factor(compiled, candle_map, trial_number=trial["trial_number"],
                                                          field_valid_from_ms=valid_from)
                    trial["data"] = {"candles": candle_map, "valid_from": valid_from}
                    preliminary[trial["trial_number"]] = evaluation
                    new_sharpes.append(return_moments([row["net"] for row in evaluation.rows]).sharpe or 0.0)
                else:
                    symbol = recipe.universe[0]
                    floor = certification_start_ms(int(instrument_map[symbol]["launchTime"]))
                    async with BitgetPublicClient() as bitget:
                        candles, calendar_payload = await asyncio.gather(
                            bitget.complete_candle_history(symbol, "15m", lower_bound_ms=floor, max_pages=200),
                            bitget.market_calendar(),
                        )
                    now_ms = int(datetime.now(UTC).timestamp() * 1000)
                    closed = closed_candles(candles, "15m", now_ms)
                    calendar_as_of = datetime.fromtimestamp(int(calendar_payload["requestTime"]) / 1000, tz=UTC)
                    calendar = CalendarWindow(
                        closures=tuple(parse_calendar_closures(calendar_payload["data"].get("specificConfig", []))),
                        available_from=datetime.fromtimestamp(floor / 1000, tz=UTC).astimezone(NEW_YORK).date(),
                        available_through=calendar_as_of.astimezone(NEW_YORK).date(), as_of=calendar_as_of,
                    )
                    as_of_ms = closed[-1].timestamp_ms + ANCHOR_INTERVAL_MS
                    report = evaluate_transition_recipe(recipe, compiled, closed, calendar=calendar,
                                                        as_of_ms=as_of_ms, trial_number=trial["trial_number"])
                    trial["data"] = {"calendar_hash": canonical_hash(calendar_payload), "rows": len(closed)}
                    preliminary[trial["trial_number"]] = report
                    new_sharpes.append(return_moments([row["net"] for row in report["records"]]).sharpe or 0.0)

            search_n = repository.search_program_n(program_id)
            hurdle = expected_maximum_sharpe(_existing_sharpes() + new_sharpes, expected_mean=0.0)
            if hurdle["status"] != "OK" or int(hurdle["search_n"]) != search_n:
                raise RuntimeError(f"DSR search population mismatch: hurdle={hurdle}, database_n={search_n}")

            complete: list[dict[str, Any]] = []
            for trial in trials:
                if trial["trial_number"] is None:
                    complete.append({"slot": trial["slot"], "family": SLOTS[trial["slot"]]["family"],
                                     "trial_number": None, "state": "NO_RUN_PROJECTED_BUDGET_EXHAUSTED",
                                     "recipe": None, "compiled": None, "report": None, "lifecycle": None})
                    continue
                recipe_payload = trial["recipe"].model_dump(mode="json") if trial["recipe"] else {
                    "family": SLOTS[trial["slot"]]["family"], "invalid": True}
                if trial["errors"]:
                    report = _structural_report(recipe_payload, trial["trial_number"], trial["errors"])
                elif trial["recipe"].family == "beta_residual":
                    report = finalize_evaluation(preliminary[trial["trial_number"]],
                                                 benchmark_sharpe=float(hurdle["sr_star"]), search_n=search_n,
                                                 sigma_sr=float(hurdle["sigma_sr"]))
                    report["protocol"] = PROTOCOL_VERSION_V3
                    report["protocol_hash"] = FDP_V3_HASH
                    report["recipe"] = recipe_payload
                    report["compiler_version"] = trial["compiled"].compiler_version
                else:
                    report = finalize_transition_evaluation(preliminary[trial["trial_number"]],
                                                            benchmark_sharpe=float(hurdle["sr_star"]),
                                                            search_n=search_n, sigma_sr=float(hurdle["sigma_sr"]))
                    report["protocol_version"] = PROTOCOL_VERSION_V3
                    report["protocol_hash"] = FDP_V3_HASH
                if trial["duplicate"]:
                    manifest = {"slot": trial["slot"], "trial_number": trial["trial_number"],
                                "protocol_hash": FDP_V3_HASH, "aggregate": "REJECTED",
                                "reason": "DUPLICATE_SUPPRESSED", "search_n": search_n,
                                "automatic_revision_child": False}
                    manifest_hash = canonical_hash(manifest)
                    repository.append_evidence(event_type="FDP_V3_CYCLE_COMPLETE", entity_type="research_cycle",
                                               entity_id=trial["cycle_id"], payload={**manifest, "manifest_hash": manifest_hash})
                    repository.complete_cycle(trial["cycle_id"], "COMPLETE", manifest_hash)
                    complete.append({"slot": trial["slot"], "family": SLOTS[trial["slot"]]["family"],
                                     "trial_number": trial["trial_number"], "factor_version_id": str(trial["factor_id"]),
                                     "recipe": recipe_payload, "compiled": trial["compiled"].model_dump(mode="json"),
                                     "recipe_hash": recipe_hash(trial["recipe"]), "ast_hash": ast_hash(trial["compiled"]),
                                     "duplicate": True, "report": report, "lifecycle": None})
                    continue
                experiment_id = repository.save_experiment(
                    factor_version_id=trial["factor_id"], dataset_hash=report["dataset_hash"],
                    data_contract=report.get("data_contract", {"contract_version": CONTRACT_VERSION,
                                                                 "anchor_statistics": {key: report.get(key) for key in
                                                                                       ("expected_transition_events", "valid_anchors", "missing_anchors")}}),
                    metrics=report, report_hash=report["report_hash"], protocol_version=PROTOCOL_VERSION_V3,
                )
                repository.save_gates(experiment_id, report["gates"])
                repository.transition(trial["factor_id"], "COMMITTED", "FORMALIZED",
                                      "fdp-v3 FactorRecipe compiled deterministically.", experiment_id=experiment_id)
                repository.transition(trial["factor_id"], "FORMALIZED", "BACKTESTED",
                                      "Controlled deterministic evaluation completed.", experiment_id=experiment_id)
                for gate in report["gates"]:
                    repository.append_evidence(event_type="FDP_V3_GATE_RESULT", entity_type="factor_version",
                                               entity_id=trial["factor_id"],
                                               payload={"slot": trial["slot"], "trial_number": trial["trial_number"], **gate})
                lifecycle = None
                lifecycle_run_id = None
                if not trial["errors"]:
                    lifecycle_prompt = (
                        "Return JSON only for LifecycleDecision with action ABANDON, REVISE, or PROMOTE_RECOMMENDATION; "
                        "REVISE must include revision_intent. Deterministic gates cannot be overridden and no revision child is allowed. "
                        f"Factor family:{trial['recipe'].family}. Aggregate:{report['aggregate']}. "
                        f"FIRST_HARD_FAIL:{report['first_hard_fail']}. Gates:"
                        f"{json.dumps({gate['name']: gate['outcome'] for gate in report['gates']}, separators=(',', ':'))}."
                    )
                    lifecycle_result, lifecycle_run_id = await _logical_call(
                        client=client, settings=settings, database_url=database_url, repository=repository,
                        cycle_id=trial["cycle_id"], slot=trial["slot"], role="lifecycle",
                        schema=LifecycleDecision, prompt=lifecycle_prompt, max_tokens=500,
                    )
                    if lifecycle_run_id and lifecycle_result["validation"]["valid"]:
                        lifecycle = LifecycleDecision.model_validate(lifecycle_result["parsed_json"])
                    elif lifecycle_run_id:
                        lifecycle = LifecycleDecision(action="ABANDON", reason="Invalid lifecycle output; deterministic state retained.")
                repository.transition(
                    trial["factor_id"], "BACKTESTED", report["aggregate"],
                    f"Deterministic {report['aggregate']}; lifecycle {lifecycle.action if lifecycle else 'BLOCKED'}; no revision child.",
                    qwen_run_id=lifecycle_run_id, experiment_id=experiment_id,
                )
                manifest = {"slot": trial["slot"], "trial_number": trial["trial_number"],
                            "protocol_hash": FDP_V3_HASH, "recipe_hash": recipe_hash(trial["recipe"]) if trial["recipe"] else None,
                            "ast_hash": ast_hash(trial["compiled"]) if trial["compiled"] else None,
                            "report_hash": report["report_hash"], "aggregate": report["aggregate"],
                            "search_n": search_n, "automatic_revision_child": False}
                manifest_hash = canonical_hash(manifest)
                repository.append_evidence(event_type="FDP_V3_CYCLE_COMPLETE", entity_type="research_cycle",
                                           entity_id=trial["cycle_id"], payload={**manifest, "manifest_hash": manifest_hash})
                repository.complete_cycle(trial["cycle_id"], "COMPLETE", manifest_hash)
                complete.append({"slot": trial["slot"], "family": SLOTS[trial["slot"]]["family"],
                                 "trial_number": trial["trial_number"], "factor_version_id": str(trial["factor_id"]),
                                 "recipe": recipe_payload,
                                 "compiled": trial["compiled"].model_dump(mode="json") if trial["compiled"] else None,
                                 "recipe_hash": recipe_hash(trial["recipe"]) if trial["recipe"] else None,
                                 "ast_hash": ast_hash(trial["compiled"]) if trial["compiled"] else None,
                                 "duplicate": trial["duplicate"], "report": report,
                                 "lifecycle": lifecycle.model_dump(mode="json") if lifecycle else None})
                write_json(OUTPUT / "trials.json", {"search_program_id": SEARCH_PROGRAM_ID, "trials": complete})

    if len(trials) != 2 or [trial["slot"] for trial in trials] != ["A", "B"]:
        raise RuntimeError("controlled batch did not close exactly the two frozen slots")
    budget = _budget_evidence(database_url)
    if budget["charged_tokens"] > HARD_TOKEN_LIMIT or budget["outstanding_reservations"]:
        raise RuntimeError(f"hard token budget invariant failed: {budget}")
    with psycopg.connect(database_url) as connection:
        logical_calls, http_attempts = connection.execute(
            """SELECT count(*),COALESCE(sum(attempt_count),0) FROM qwen_runs q
               JOIN research_cycles c ON c.id=q.cycle_id WHERE c.protocol_id=%s""", (protocol_id,)
        ).fetchone()
    if logical_calls > 4 or http_attempts > 6:
        raise RuntimeError("fdp-v3 call-count cap exceeded")
    write_json(OUTPUT / "budget.json", {**budget, "logical_calls": logical_calls})
    gate_summary = {
        "gate_distribution": dict(sorted(Counter(gate["outcome"] for trial in complete if trial["report"]
                                                 for gate in trial["report"]["gates"]).items())),
        "first_hard_fail": {trial["slot"]: trial["report"]["first_hard_fail"] if trial["report"] else None
                            for trial in complete},
        "outcomes": {trial["slot"]: trial["report"]["aggregate"] if trial["report"] else trial["state"]
                     for trial in complete},
    }
    write_json(OUTPUT / "gate-summary.json", gate_summary)
    candidates = sum(trial["report"] and trial["report"]["aggregate"] == "CANDIDATE" for trial in complete)
    certified = sum(trial["report"] and trial["report"]["aggregate"] == "CERTIFIED" for trial in complete)
    final_n = repository.search_program_n(program_id)
    decision = {
        "status": "COMPLETE", "completed_at": datetime.now(UTC).isoformat(),
        "protocol_version": PROTOCOL_VERSION_V3, "protocol_hash": FDP_V3_HASH,
        "search_n_before": 7, "search_n_after": final_n, "slots_closed": ["A", "B"],
        "logical_calls": logical_calls, "http_attempts": http_attempts,
        "reserved_tokens": budget["reserved_tokens_total"], "measured_tokens": budget["measured_tokens_total"],
        "charged_tokens": budget["charged_tokens"], "candidates": candidates, "certified": certified,
        "paper_trading_started": False, "another_batch_started": False,
        "recommendation": "PAPER_PROBATION_AVAILABLE" if candidates else "PRODUCT_HARDENING_NO_CANDIDATE",
    }
    write_json(OUTPUT / "decision.json", decision)
    repository.append_evidence(
        event_type="FDP_V3_CONTROLLED_BATCH_COMPLETE", entity_type="research_program", entity_id=program_id,
        payload={"decision_hash": canonical_hash(decision), "protocol_hash": FDP_V3_HASH,
                 "search_n": final_n, "slots_closed": ["A", "B"], "paper_trading_started": False},
    )
    decision["evidence_chain"] = verify_chain(database_url)
    write_json(OUTPUT / "decision.json", decision)
    write_json(PUBLIC, {"decision": decision, "budget": budget, "gate_summary": gate_summary,
                        "trials": complete})
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("activate-freeze", "run"))
    args = parser.parse_args()
    database_url = _database(Settings.from_env())
    result = activate_and_freeze(database_url) if args.action == "activate-freeze" else asyncio.run(run_batch(database_url))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
