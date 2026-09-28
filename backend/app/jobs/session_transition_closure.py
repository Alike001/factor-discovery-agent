from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg

from app.bitget.client import BitgetPublicClient, closed_candles
from app.bitget.models import Candle
from app.bitget.session import NEW_YORK, parse_calendar_closures
from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.evidence.verify import verify_chain
from app.qwen.budget import conservative_reservation, estimated_input_tokens
from app.research.capabilities import capability_matrix
from app.research.protocol_v3_draft import PROTOCOL_V3_DRAFT, PROTOCOL_V3_DRAFT_HASH
from app.research.recipes import (
    COMPILER_VERSION,
    PROMPT_SCHEMA_VERSION,
    RECIPE_SCHEMA_VERSION,
    FactorRecipe,
    ast_hash,
    compile_recipe,
    generate_proposer_prompt,
    ready_families,
    recipe_hash,
)
from app.research.session_transition import (
    ANCHOR_INTERVAL_MS,
    CONTRACT_VERSION,
    SESSION_TRANSITION_CONTRACT,
    SUPPORTED_TRANSITIONS,
    CalendarWindow,
    TransitionStatus,
    contract_hash,
    evaluate_transition_recipe,
    event_availability,
    expected_event,
    resolve_transition,
)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "evidence/capability-closure-v4"
PUBLIC = ROOT / "web/public/evidence/session-transition-closure.json"
DATABASE_URL_DEFAULT = "postgresql://postgres@127.0.0.1:55432/bitget_research"


def _state(database_url: str) -> dict[str, int]:
    with psycopg.connect(database_url) as connection:
        attempts = connection.execute("SELECT COALESCE(sum(attempt_count),0) FROM qwen_runs").fetchone()[0]
        program = connection.execute("SELECT id FROM research_programs WHERE program_key='rtoken-session-alpha-v1'").fetchone()
    if not program:
        raise RuntimeError("search program missing")
    return {"qwen_http_attempts": int(attempts),
            "search_n": ResearchRepository(database_url).search_program_n(program[0]),
            "program_id": program[0]}


def freeze(database_url: str) -> dict[str, Any]:
    apply_migrations(database_url)
    state = _state(database_url)
    if state["search_n"] != 7:
        raise RuntimeError(f"closure requires global search N=7, observed {state['search_n']}")
    artifact = {"contract": SESSION_TRANSITION_CONTRACT, "contract_hash": contract_hash(),
                "frozen_before_golden_or_real_replay": True}
    path = OUTPUT / "SESSION_TRANSITION_CONTRACT.json"
    if path.exists():
        existing = json.loads(path.read_text())
        if existing != artifact:
            raise RuntimeError("frozen transition contract differs from implementation")
        return artifact
    write_json(path, artifact)
    event_hash = ResearchRepository(database_url).append_evidence(
        event_type="SESSION_TRANSITION_CONTRACT_FROZEN", entity_type="research_program",
        entity_id=state["program_id"], payload={"contract_version": CONTRACT_VERSION,
                                                "contract_hash": contract_hash(), "search_n": 7})
    write_json(OUTPUT / "contract-freeze-event.json", {"event_type": "SESSION_TRANSITION_CONTRACT_FROZEN",
                                                        "event_hash": event_hash})
    return artifact


def _recipe(transition: str, *, normalization: str = "none", name: str = "Golden transition") -> FactorRecipe:
    from_session, to_session = transition.split("_to_")
    nested: dict[str, Any] = {"kind": "session_transition", "transition": transition,
                              "feature": "transition_return_zscore" if normalization == "zscore" else "transition_return",
                              "normalization": normalization, "threshold": 1.0 if normalization == "zscore" else 0.0,
                              "direction": "continuation"}
    if normalization == "zscore":
        nested["feature_lookback"] = 6
    return FactorRecipe.model_validate({
        "schema_version": RECIPE_SCHEMA_VERSION, "name": name,
        "thesis": "An exact session boundary return can be evaluated only after both anchors close.",
        "family": "session_transition", "universe": ["RNVDAUSDT"],
        "session_contract": {"kind": "transition", "from_session": from_session, "to_session": to_session},
        "recipe": nested, "horizon_bars": 6, "rebalance_bars": 6, "direction": "long_flat",
        "expected_signal_frequency": "low", "economic_mechanism": "Session boundary repricing may persist.",
        "why_not_duplicate": "Uses exact boundary anchors and is distinct from beta residuals.",
        "why_costs_should_not_dominate": "At most one transition decision occurs per eligible day.",
    })


def _candle(timestamp_ms: int, price: float) -> Candle:
    value = Decimal(str(price))
    return Candle(timestamp_ms=timestamp_ms, open=value, high=value, low=value, close=value)


def _fixture_bars(day: date, transition: str) -> tuple[list[Candle], int]:
    event = expected_event(day, transition)
    bars = [_candle(event.from_anchor_ms + index * ANCHOR_INTERVAL_MS, 100 + index * .1) for index in range(27)]
    return bars, bars[-1].timestamp_ms + ANCHOR_INTERVAL_MS


def _golden_calendar() -> CalendarWindow:
    return CalendarWindow(closures=(), available_from=date(2026, 1, 1), available_through=date(2026, 12, 31),
                          as_of=datetime(2026, 12, 31, tzinfo=UTC))


def golden_results() -> dict[str, Any]:
    valid = []
    for transition in SUPPORTED_TRANSITIONS:
        for regime, day in (("EST", date(2026, 1, 12)), ("EDT", date(2026, 7, 13))):
            factor = _recipe(transition)
            compiled = compile_recipe(factor)
            bars, as_of_ms = _fixture_bars(day, transition)
            report = evaluate_transition_recipe(factor, compiled, bars, calendar=_golden_calendar(), as_of_ms=as_of_ms)
            passed = report["valid_anchors"] == 1 and report["no_lookahead_violations"] == 0
            valid.append({"transition": transition, "dst_regime": regime, "status": "PASS" if passed else "FAIL",
                          "recipe_hash": recipe_hash(factor), "ast_hash": ast_hash(compiled),
                          "report_hash": report["report_hash"]})
    event = expected_event(date(2026, 7, 13), "pre_market_to_regular")
    exact = {event.from_anchor_ms: _candle(event.from_anchor_ms, 100),
             event.to_anchor_ms: _candle(event.to_anchor_ms, 101),
             event.next_fill_ms: _candle(event.next_fill_ms, 102)}
    holiday = CalendarWindow(
        closures=((datetime(2026, 7, 12, 20, tzinfo=NEW_YORK), datetime(2026, 7, 13, 20, tzinfo=NEW_YORK)),),
        available_from=date(2026, 1, 1), available_through=date(2026, 12, 31),
        as_of=datetime(2026, 12, 31, tzinfo=UTC))
    missing_from = dict(exact); missing_from.pop(event.from_anchor_ms)
    missing_to = dict(exact); missing_to.pop(event.to_anchor_ms)
    no_next = dict(exact); no_next.pop(event.next_fill_ms)
    failures = [
        ("missing_from_anchor", resolve_transition(event, missing_from, as_of_ms=event.observable_ms, calendar=_golden_calendar())["status"], "MISSING_EXPECTED_ANCHOR"),
        ("missing_to_anchor", resolve_transition(event, missing_to, as_of_ms=event.observable_ms, calendar=_golden_calendar())["status"], "MISSING_EXPECTED_ANCHOR"),
        ("holiday_closure", event_availability(event, holiday).value, "TRANSITION_UNAVAILABLE"),
        ("weekend_unavailable", event_availability(expected_event(date(2026, 7, 11), "pre_market_to_regular"), _golden_calendar()).value, "TRANSITION_UNAVAILABLE"),
        ("dst_transition_week", event_availability(expected_event(date(2026, 3, 9), "pre_market_to_regular"), _golden_calendar()).value, "READY"),
        ("forming_to_anchor", resolve_transition(event, exact, as_of_ms=event.observable_ms - 1, calendar=_golden_calendar())["status"], "FORMING_TO_ANCHOR"),
        ("stale_calendar", event_availability(expected_event(date(2027, 1, 4), "pre_market_to_regular"), _golden_calendar()).value, "SESSION_CALENDAR_UNAVAILABLE"),
        ("exact_boundary_absent", resolve_transition(event, missing_to, as_of_ms=event.observable_ms, calendar=_golden_calendar())["status"], "MISSING_EXPECTED_ANCHOR"),
        ("no_next_executable_bar", resolve_transition(event, no_next, as_of_ms=event.observable_ms, calendar=_golden_calendar())["status"], "NO_NEXT_EXECUTABLE_BAR"),
    ]
    invalid = [{"fixture": name, "observed": observed, "expected": expected,
                "status": "PASS" if observed == expected else "FAIL"} for name, observed, expected in failures]
    return {"valid": valid, "invalid": invalid, "valid_passed": sum(x["status"] == "PASS" for x in valid),
            "invalid_passed": sum(x["status"] == "PASS" for x in invalid), "search_trials_created": 0}


async def _real_inputs() -> tuple[list[Candle], CalendarWindow, int, dict[str, Any]]:
    async with BitgetPublicClient() as client:
        candles, calendar_payload = await asyncio.gather(
            client.recent_candles("RNVDAUSDT", "15m", 1000), client.market_calendar())
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    closed = closed_candles(candles, "15m", now_ms)
    if not closed:
        raise RuntimeError("real tracer returned no closed candles")
    calendar_data = calendar_payload["data"]
    request_time_ms = int(calendar_payload["requestTime"])
    calendar_as_of = datetime.fromtimestamp(request_time_ms / 1000, tz=UTC)
    window = CalendarWindow(closures=tuple(parse_calendar_closures(calendar_data.get("specificConfig", []))),
                            available_from=date(2026, 6, 2),
                            available_through=calendar_as_of.astimezone(NEW_YORK).date(), as_of=calendar_as_of)
    as_of_ms = closed[-1].timestamp_ms + ANCHOR_INTERVAL_MS
    provenance = {"symbol": "RNVDAUSDT", "endpoint": "/api/v3/market/candles",
                  "calendar_endpoint": "/api/v3/reality/market/calendar", "interval": "15m",
                  "rows": len(closed), "first_timestamp": closed[0].timestamp.isoformat(),
                  "last_timestamp": closed[-1].timestamp.isoformat(), "calendar_request_time": calendar_as_of.isoformat(),
                  "response_hash": canonical_hash(calendar_payload)}
    return closed, window, as_of_ms, provenance


def run(database_url: str) -> dict[str, Any]:
    frozen = freeze(database_url)
    before = _state(database_url)
    golden = golden_results()
    if golden["valid_passed"] != 8 or golden["invalid_passed"] != 9:
        raise RuntimeError("golden transition fixtures failed")
    write_json(OUTPUT / "golden-fixtures.json", golden)
    candles, calendar, as_of_ms, provenance = asyncio.run(_real_inputs())
    factor = _recipe("pre_market_to_regular", normalization="zscore", name="SESSION_TRANSITION_ARCHITECTURE_TRACER")
    compiled = compile_recipe(factor)
    tracer = evaluate_transition_recipe(factor, compiled, candles, calendar=calendar, as_of_ms=as_of_ms,
                                        architecture_tracer=True)
    tracer["provenance"] = provenance
    tracer["architecture_only"] = True
    tracer["search_n_effect"] = 0
    write_json(OUTPUT / "real-history-tracer.json", tracer)
    matrix = capability_matrix()
    write_json(OUTPUT / "capability-matrix.json", {"rows": matrix, "ready_families": ready_families()})
    prompt = generate_proposer_prompt("choose one READY executable family", ["prior-structure-hashes-only"])
    estimate = estimated_input_tokens(prompt)
    _, reserved = conservative_reservation(prompt, 1200)
    write_json(OUTPUT / "prompt.json", {"prompt_schema_version": PROMPT_SCHEMA_VERSION, "prompt": prompt,
                                         "estimated_input_tokens": estimate, "conservative_reserved_tokens": reserved,
                                         "live_qwen_calls": 0, "families": ready_families()})
    write_json(OUTPUT / "DRAFT_PROTOCOL.json", {"draft": PROTOCOL_V3_DRAFT,
                                                 "draft_hash": PROTOCOL_V3_DRAFT_HASH, "activated": False})
    after = _state(database_url)
    if before["qwen_http_attempts"] != after["qwen_http_attempts"] or before["search_n"] != after["search_n"]:
        raise RuntimeError(f"offline closure changed research state: before={before}, after={after}")
    chain_before_completion = verify_chain(database_url)
    closure = {
        "status": "COMPLETE", "completed_at": datetime.now(UTC).isoformat(),
        "qwen_http_attempts_phase": 0, "qwen_http_attempts_total_before": before["qwen_http_attempts"],
        "qwen_http_attempts_total_after": after["qwen_http_attempts"],
        "search_n_before": before["search_n"], "search_n_after": after["search_n"],
        "contract_version": CONTRACT_VERSION, "contract_hash": frozen["contract_hash"],
        "anchor_resolution": "15m", "supported_transitions": list(SUPPORTED_TRANSITIONS),
        "ready_families": ready_families(),
        "not_ready_families": ["cross_sectional_rank", "dispersion", "spread_bps", "generic_baskets"],
        "golden_valid_passed": golden["valid_passed"], "golden_invalid_passed": golden["invalid_passed"],
        "tracer_metrics": {key: tracer[key] for key in ("expected_transition_events", "valid_anchors", "missing_anchors", "signals", "fills", "costs", "no_lookahead_violations")},
        "recipe_schema_version": RECIPE_SCHEMA_VERSION, "compiler_version": COMPILER_VERSION,
        "prompt_schema_version": PROMPT_SCHEMA_VERSION, "prompt_estimated_input_tokens": estimate,
        "token_reservation_policy": "postgres-conservative-pre-call-reservation-v1",
        "fdp_v3_draft_active": False, "paper_trading_started": False,
        "chain_before_completion": chain_before_completion,
        "recommendation": "READY_FOR_FDP_V3_BATCH",
    }
    write_json(OUTPUT / "closure.json", closure)
    event_hash = ResearchRepository(database_url).append_evidence(
        event_type="SESSION_TRANSITION_CAPABILITY_CLOSED", entity_type="research_program",
        entity_id=after["program_id"], payload={"closure_hash": canonical_hash(closure), "contract_hash": contract_hash(),
                                                 "qwen_http_attempts": 0, "search_n": 7, "draft_active": False,
                                                 "paper_trading_started": False})
    chain = verify_chain(database_url)
    closure["completion_event_hash"] = event_hash
    closure["evidence_chain"] = chain
    write_json(OUTPUT / "closure.json", closure)
    write_json(PUBLIC, {"closure": closure, "capability_matrix": matrix,
                        "golden": {"valid_passed": golden["valid_passed"], "invalid_passed": golden["invalid_passed"]},
                        "tracer": {"label": tracer["label"], "metrics": closure["tracer_metrics"]}})
    return closure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "run"))
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL", DATABASE_URL_DEFAULT)
    result = freeze(database_url) if args.action == "freeze" else run(database_url)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
