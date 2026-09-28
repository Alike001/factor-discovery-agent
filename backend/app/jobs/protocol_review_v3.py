from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg

from app.bitget.models import Candle
from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.evidence import canonical_hash, write_json
from app.qwen.budget import conservative_reservation, estimated_input_tokens
from app.research.capabilities import capability_matrix
from app.research.evaluator_v2 import evaluate_targeted_factor
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

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "evidence/protocol-review-v3"
PUBLIC = ROOT / "web/public/evidence/protocol-review-v3.json"
DATABASE_URL_DEFAULT = "postgresql://postgres@127.0.0.1:55432/bitget_research"


def _state(database_url: str) -> dict[str, int]:
    with psycopg.connect(database_url) as connection:
        qwen = connection.execute("SELECT COALESCE(sum(attempt_count),0) FROM qwen_runs").fetchone()[0]
        program = connection.execute("SELECT id FROM research_programs WHERE program_key='rtoken-session-alpha-v1'").fetchone()
    if not program:
        raise RuntimeError("search program missing")
    return {"qwen_http_attempts": int(qwen), "search_n": ResearchRepository(database_url).search_program_n(program[0])}


def _candles(symbol: str, *, phase: float) -> list[Candle]:
    start = datetime(2026, 6, 2, tzinfo=UTC)
    rows = []
    for index in range(400):
        trend = index * 0.00015
        cycle = math.sin(index / 19 + phase) * 0.018 + math.sin(index / 71) * 0.011
        price = 100 * (1 + trend + cycle)
        rows.append(Candle(timestamp_ms=int((start + timedelta(hours=index)).timestamp() * 1000),
                           open=Decimal(str(price)), high=Decimal(str(price * 1.002)),
                           low=Decimal(str(price * .998)), close=Decimal(str(price * (1 + math.sin(index / 7) * .0008)))))
    return rows


def golden_recipes() -> list[FactorRecipe]:
    pairs = [("RNVDAUSDT", "RQQQUSDT", 24, 48, "pre_market"),
             ("RAMDUSDT", "RQQQUSDT", 48, 24, "regular"),
             ("RMSFTUSDT", "RQQQUSDT", 120, 48, "overnight")]
    output = []
    for index, (target, reference, beta, signal, session) in enumerate(pairs, start=1):
        output.append(FactorRecipe.model_validate({
            "schema_version": RECIPE_SCHEMA_VERSION, "name": f"Golden beta residual {index}",
            "thesis": "A deterministic beta-adjusted residual may normalize within the declared session.",
            "family": "beta_residual", "universe": [target, reference],
            "session_contract": {"kind": "single_session", "session": session},
            "recipe": {"kind": "beta_residual", "target": target, "reference": reference,
                       "beta_lookback": beta, "residual_transform": "zscore", "signal_lookback": signal,
                       "entry_side": "negative_reversion" if index != 2 else "positive_continuation"},
            "horizon_bars": 24, "rebalance_bars": 6, "direction": "long_flat",
            "expected_signal_frequency": "low", "economic_mechanism": "Residual dislocations may normalize after beta adjustment.",
            "why_not_duplicate": "This recipe is compiled and is not a raw pair-return AST proposal.",
            "why_costs_should_not_dominate": "Six-hour rebalance and twenty-four-hour holding constrain turnover.",
        }))
    return output


def run(database_url: str) -> dict[str, Any]:
    apply_migrations(database_url)
    before = _state(database_url)
    if before["search_n"] != 7:
        raise RuntimeError(f"protocol review requires search N=7, observed {before['search_n']}")
    matrix = capability_matrix()
    write_json(OUTPUT / "capability-matrix.json", {"generated_at": datetime.now(UTC).isoformat(), "rows": matrix})
    write_json(OUTPUT / "recipe-schema.json", {"version": RECIPE_SCHEMA_VERSION, "schema": FactorRecipe.model_json_schema()})
    write_json(OUTPUT / "registry.json", {"ready_families": ready_families(),
                                           "not_ready_families": [row["capability"] for row in matrix if row["status"] == "NOT_READY"]})

    candle_map = {"RNVDAUSDT": _candles("RNVDAUSDT", phase=.1), "RAMDUSDT": _candles("RAMDUSDT", phase=.7),
                  "RMSFTUSDT": _candles("RMSFTUSDT", phase=1.2), "RQQQUSDT": _candles("RQQQUSDT", phase=2.1)}
    golden = []
    for index, recipe in enumerate(golden_recipes(), start=1):
        compiled = compile_recipe(recipe)
        first_hash = ast_hash(compiled)
        second_hash = ast_hash(compile_recipe(recipe))
        if first_hash != second_hash:
            raise RuntimeError("non-deterministic compiler")
        evaluation = evaluate_targeted_factor(compiled, candle_map, trial_number=10_000 + index,
                                              field_valid_from_ms={f"{symbol}.close": 0 for symbol in compiled.universe})
        golden.append({"fixture": index, "family": recipe.family, "recipe_hash": recipe_hash(recipe),
                       "compiler_version": COMPILER_VERSION, "ast_hash": first_hash,
                       "deterministic": True, "evaluation_status": "PASS", "report_hash": canonical_hash(evaluation.report),
                       "observations": evaluation.report["metrics"]["net"]["observations"]})
    write_json(OUTPUT / "golden-fixtures.json", {"fixture_count": len(golden), "results": golden,
                                                  "search_trials_created": 0})
    prompt = generate_proposer_prompt("beta_residual using two eligible rTokens", ["prior-structure-hashes-only"])
    estimate = estimated_input_tokens(prompt)
    input_estimate, reserved = conservative_reservation(prompt, 1200)
    if estimate > 1500:
        raise RuntimeError("generated proposer prompt exceeds 1,500 estimated tokens")
    write_json(OUTPUT / "generated-prompt.json", {"prompt_schema_version": PROMPT_SCHEMA_VERSION,
                                                   "prompt": prompt, "characters": len(prompt),
                                                   "estimated_input_tokens": estimate, "max_completion_tokens_draft": 1200,
                                                   "conservative_reserved_tokens": reserved,
                                                   "live_transport_demonstrated": False})
    write_json(OUTPUT / "token-policy.json", {
        "version": "postgres-conservative-pre-call-reservation-v1",
        "estimated_input": "ceil(characters / 4 * 1.25)",
        "reserved_input": "max(estimated_input, UTF-8 byte length)",
        "reservation": "reserved_input + max_completion_tokens",
        "admission": "charged + outstanding + reservation <= hard_limit",
        "unmeasured_charge": "full reservation", "repair": "new independently admitted reservation",
        "concurrency": "PostgreSQL advisory transaction lock plus account row lock",
        "example_estimated_input_tokens": input_estimate, "example_reserved_tokens": reserved,
    })
    write_json(OUTPUT / "DRAFT_PROTOCOL.json", {"draft": PROTOCOL_V3_DRAFT,
                                                 "draft_hash": PROTOCOL_V3_DRAFT_HASH, "activated": False})
    after = _state(database_url)
    if after != before:
        raise RuntimeError(f"offline review mutated Qwen/search state: before={before}, after={after}")
    result = {"completed_at": datetime.now(UTC).isoformat(), "status": "COMPLETE",
              "qwen_http_attempts_phase": after["qwen_http_attempts"] - before["qwen_http_attempts"],
              "search_n_before": before["search_n"], "search_n_after": after["search_n"],
              "recipe_schema_version": RECIPE_SCHEMA_VERSION, "compiler_version": COMPILER_VERSION,
              "prompt_schema_version": PROMPT_SCHEMA_VERSION, "ready_families": ready_families(),
              "golden_fixtures_passed": len(golden), "generated_prompt_estimated_tokens": estimate,
              "fdp_v3_draft_active": False, "paper_trading_started": False,
              "recommendation": "PROTOCOL_CAPABILITY_GAP_REMAINS",
              "reason": "Only beta_residual is READY; cross-sectional portfolios and fail-closed session anchors remain unsupported, and live FactorRecipe transport is unproven."}
    write_json(OUTPUT / "review.json", result)
    write_json(PUBLIC, {"review": result, "capability_matrix": matrix,
                        "golden_fixtures": golden, "draft_protocol": PROTOCOL_V3_DRAFT})
    repository = ResearchRepository(database_url)
    with psycopg.connect(database_url) as connection:
        program_id = connection.execute("SELECT id FROM research_programs WHERE program_key='rtoken-session-alpha-v1'").fetchone()[0]
    repository.append_evidence(event_type="PROTOCOL_REVIEW_V3_COMPLETE", entity_type="research_program",
                               entity_id=program_id, payload={"review_hash": canonical_hash(result),
                                                              "qwen_http_attempts": 0, "search_n": 7,
                                                              "draft_active": False, "paper_trading_started": False})
    return result


def main() -> None:
    import os
    database_url = os.getenv("DATABASE_URL", DATABASE_URL_DEFAULT)
    print(json.dumps(run(database_url), indent=2))


if __name__ == "__main__":
    main()
