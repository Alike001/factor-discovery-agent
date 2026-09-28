from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from app.bitget.session import AnchorStatus, validate_expected_anchor
from app.jobs.protocol_review_v3 import _candles, golden_recipes
from app.research.evaluator_v2 import evaluate_targeted_factor
from app.research.recipes import (
    REGISTRY,
    FactorRecipe,
    ast_hash,
    compile_recipe,
    generate_proposer_prompt,
    ready_families,
    recipe_hash,
)


def test_prompt_capabilities_equal_ready_registry() -> None:
    prompt = generate_proposer_prompt("beta residual slot", [])
    assert ready_families() == [name for name, value in REGISTRY.items() if value["status"] == "READY"]
    for family in ready_families():
        assert family in prompt
    for forbidden in ("cross_sectional_rank", "session_transition", "rank", "group_mean", "dispersion", '"op"', "source"):
        assert forbidden not in prompt


def test_unknown_recipe_and_raw_ast_are_rejected() -> None:
    value = golden_recipes()[0].model_dump(mode="json")
    value["family"] = "unknown"
    with pytest.raises(ValidationError):
        FactorRecipe.model_validate(value)
    raw = golden_recipes()[0].model_dump(mode="json")
    raw["signal"] = {"op": "source", "symbol": "RNVDAUSDT", "field": "close"}
    with pytest.raises(ValidationError):
        FactorRecipe.model_validate(raw)


def test_recipe_and_ast_hashes_are_stable() -> None:
    recipe = golden_recipes()[0]
    assert recipe_hash(recipe) == recipe_hash(FactorRecipe.model_validate(recipe.model_dump(mode="json")))
    assert ast_hash(compile_recipe(recipe)) == ast_hash(compile_recipe(recipe))


def test_every_ready_recipe_evaluates_on_three_golden_fixtures() -> None:
    assert ready_families() == ["beta_residual"]
    candles = {"RNVDAUSDT": _candles("RNVDAUSDT", phase=.1), "RAMDUSDT": _candles("RAMDUSDT", phase=.7),
               "RMSFTUSDT": _candles("RMSFTUSDT", phase=1.2), "RQQQUSDT": _candles("RQQQUSDT", phase=2.1)}
    for index, recipe in enumerate(golden_recipes()):
        spec = compile_recipe(recipe)
        result = evaluate_targeted_factor(spec, candles, trial_number=20_000 + index,
                                          field_valid_from_ms={f"{symbol}.close": 0 for symbol in spec.universe})
        assert result.report["metrics"]["net"]["observations"] > 0


def test_missing_expected_anchor_fails_closed() -> None:
    from datetime import date
    assert validate_expected_anchor(date(2026, 9, 25), {date(2026, 9, 24)}) == AnchorStatus.MISSING_EXPECTED_ANCHOR
    assert REGISTRY["session_transition"]["status"] == "NOT_READY"


def test_cross_sectional_recipe_not_ready_without_portfolio_evaluator() -> None:
    assert REGISTRY["cross_sectional_rank"]["status"] == "NOT_READY"
    value = golden_recipes()[0].model_dump(mode="json")
    value.update({"family": "cross_sectional_rank", "recipe": {"kind": "cross_sectional_rank", "metric": "return",
                                                               "lookback": 24, "select_side": "leader"}})
    with pytest.raises(ValueError, match="RECIPE_NOT_READY"):
        compile_recipe(FactorRecipe.model_validate(value))


def test_offline_compiler_never_invokes_http(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False
    async def forbidden(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True
        raise AssertionError("HTTP must not be invoked")
    monkeypatch.setattr(httpx.AsyncClient, "post", forbidden)
    compile_recipe(golden_recipes()[0])
    assert called is False
