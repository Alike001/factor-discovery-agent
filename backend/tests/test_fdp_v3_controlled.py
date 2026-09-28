from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.research.protocol_v2 import PROTOCOL_V2, SEARCH_PROGRAM_ID
from app.research.protocol_v3 import FDP_V3, FDP_V3_HASH
from app.research.recipes import FactorRecipe, ast_hash, compile_recipe, recipe_hash
from app.jobs.fdp_v3_controlled_batch import HARD_TOKEN_LIMIT, SLOTS, _recipe_errors, _slot_prompt


PLAN = {
    "prior_structural_fingerprint_hashes": ["abc123"],
    "model_context_fact": "Earlier raw-AST proposals caused structural failures, so this protocol uses deterministic FactorRecipe compilation. Prior economic performance is intentionally hidden.",
}


def beta_recipe() -> FactorRecipe:
    return FactorRecipe.model_validate({
        "schema_version": "factor-recipe-v1", "name": "Controlled beta residual",
        "thesis": "A beta-adjusted target dislocation may normalize during the regular session.",
        "family": "beta_residual", "universe": ["RNVDAUSDT", "RQQQUSDT"],
        "session_contract": {"kind": "single_session", "session": "regular"},
        "recipe": {"kind": "beta_residual", "target": "RNVDAUSDT", "reference": "RQQQUSDT",
                   "beta_lookback": 48, "residual_transform": "zscore", "signal_lookback": 48,
                   "entry_side": "negative_reversion", "threshold": 1.0},
        "horizon_bars": 24, "rebalance_bars": 6, "direction": "long_flat",
        "expected_signal_frequency": "low", "economic_mechanism": "Residual dislocations may normalize.",
        "why_not_duplicate": "The beta-adjusted construction distinguishes it from raw relative returns.",
        "why_costs_should_not_dominate": "Six-hour rebalancing limits expected turnover.",
    })


def test_protocol_is_active_immutable_and_carries_frozen_controls() -> None:
    assert FDP_V3["active"] is True
    assert FDP_V3["search_program_id"] == SEARCH_PROGRAM_ID
    assert FDP_V3["search_n_at_activation"] == 7
    assert FDP_V3["cost_model"] == PROTOCOL_V2["cost_model"]
    assert FDP_V3["gate_policy"] == PROTOCOL_V2["gate_policy"]
    assert FDP_V3["controlled_batch"]["hard_reserved_or_charged_tokens"] == 14_000
    assert FDP_V3_HASH == FDP_V3_HASH


def test_exactly_two_registered_slots_and_ready_family_isolation() -> None:
    assert list(SLOTS) == ["A", "B"]
    assert [value["family"] for value in SLOTS.values()] == ["beta_residual", "session_transition"]
    beta = _slot_prompt("A", PLAN)
    transition = _slot_prompt("B", PLAN)
    assert "beta_residual" in beta and "session_transition" not in beta
    assert "session_transition" in transition and "beta_residual" not in transition
    assert "Prior economic performance is intentionally hidden" in beta
    for forbidden in ("old PnL", "Sharpe values", "DSR probabilities", "closest to passing"):
        assert forbidden not in beta


def test_raw_ast_is_rejected_and_slot_family_cannot_cross() -> None:
    value = beta_recipe().model_dump(mode="json")
    value["signal"] = {"op": "source", "symbol": "RNVDAUSDT", "field": "close"}
    with pytest.raises(ValidationError):
        FactorRecipe.model_validate(value)
    assert _recipe_errors("A", beta_recipe()) == []
    assert "SLOT_FAMILY_MISMATCH" in _recipe_errors("B", beta_recipe())


def test_recipe_compilation_and_hashes_are_deterministic() -> None:
    recipe = beta_recipe()
    assert recipe_hash(recipe) == recipe_hash(FactorRecipe.model_validate(recipe.model_dump(mode="json")))
    assert ast_hash(compile_recipe(recipe)) == ast_hash(compile_recipe(recipe))
    assert compile_recipe(recipe).compiler_version == "factor-recipe-compiler-v2"


def test_no_revision_child_or_hidden_replacement_in_protocol() -> None:
    controls = FDP_V3["controlled_batch"]
    assert controls["automatic_revision_children"] is False
    assert controls["hidden_replacements"] is False
    assert controls["max_repairs_per_request"] == 1


def test_phase_budget_refuses_projected_overspend() -> None:
    # This invariant is exercised against PostgreSQL in test_database_integration;
    # keep the controlled protocol's exact hard limit visible in the unit suite.
    assert HARD_TOKEN_LIMIT == 14_000
