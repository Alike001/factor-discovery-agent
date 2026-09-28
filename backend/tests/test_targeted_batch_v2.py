from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.jobs.targeted_batch_v2 import SLOTS, _assert_budget
from app.research.evaluator_v2 import CANDIDATE_REQUIRED_GATES
from app.research.protocol_v2 import PROTOCOL_V2, SEARCH_PROGRAM_ID
from app.research.targeted import FactorProposalV2, operator_fingerprint, validate_slot


def source(symbol: str) -> dict:
    return {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": symbol, "field": "close"}]}


def proposal(slot: str = "A") -> dict:
    universe = ["RNVDAUSDT", "RAAPLUSDT", "RMSFTUSDT", "RAMDUSDT"]
    signal = {"op": "rank", "args": [source(symbol) for symbol in universe]}
    value = {
        "slot": slot, "name": "Broad relative rank", "thesis": "A broad structural hypothesis with low decision frequency.",
        "universe": universe, "session_filter": ["regular"], "transition_from": None, "transition_to": None,
        "signal": signal, "entry_condition": {"op": "gt", "threshold": 1.0, "args": [{"op": "signal"}]},
        "exit_condition": {"op": "lte", "threshold": 0.0, "args": [{"op": "signal"}]},
        "horizon_bars": 24, "rebalance_bars": 6, "direction": "long_flat", "rationale": "Bounded safe test.",
        "expected_signal_frequency": "low", "economic_mechanism": "Relative leadership persists across one session.",
        "why_not_duplicate": "Uses a four-name rank rather than pair divergence.",
        "why_costs_should_not_dominate": "Six-hour rebalance and twenty-four-hour hold bound turnover.",
    }
    if slot == "B":
        value.update({"session_filter": ["overnight"], "transition_from": "after_hours", "transition_to": "overnight",
                      "horizon_bars": 12, "signal": {"op": "group_mean", "args": [source(symbol) for symbol in universe[:3]]}})
    if slot == "C":
        value.update({"session_filter": ["pre_market"], "horizon_bars": 24,
                      "signal": {"op": "residual", "lookback": 24,
                                 "args": [source("RNVDAUSDT"), source("RMSFTUSDT")]}})
    return value


def test_slot_a_requires_cross_sectional_structure() -> None:
    value = proposal("A")
    value["signal"] = source("RNVDAUSDT")
    with pytest.raises(ValidationError, match="Slot A"):
        FactorProposalV2.model_validate(value)


def test_slot_b_requires_session_transition() -> None:
    value = proposal("B")
    value["transition_from"] = "regular"
    with pytest.raises(ValidationError, match="Slot B"):
        FactorProposalV2.model_validate(value)


def test_slot_c_requires_residual_beta_or_dispersion() -> None:
    value = proposal("C")
    value["signal"] = source("RNVDAUSDT")
    with pytest.raises(ValidationError, match="Slot C"):
        FactorProposalV2.model_validate(value)


def test_old_and_new_fingerprint_clones_are_rejected() -> None:
    item = FactorProposalV2.model_validate(proposal("A"))
    fingerprint = operator_fingerprint(item)
    assert "FORBIDDEN_OPERATOR_FINGERPRINT" in validate_slot(item, "A", [fingerprint])
    assert "FORBIDDEN_OPERATOR_FINGERPRINT" in validate_slot(item, "A", [deepcopy(fingerprint)])


def test_rebalance_horizon_and_frequency_constraints() -> None:
    too_fast = proposal("A")
    too_fast["rebalance_bars"] = 3
    with pytest.raises(ValidationError, match="rebalance"):
        FactorProposalV2.model_validate(too_fast)
    wrong_horizon = proposal("A")
    wrong_horizon["horizon_bars"] = 6
    with pytest.raises(ValidationError, match="horizon"):
        FactorProposalV2.model_validate(wrong_horizon)
    high = proposal("A")
    high["expected_signal_frequency"] = "high"
    with pytest.raises(ValidationError):
        FactorProposalV2.model_validate(high)


def test_batch_is_exactly_three_without_revision_children() -> None:
    assert list(SLOTS) == ["A", "B", "C"]
    assert PROTOCOL_V2["budget"]["trials"] == 3
    assert PROTOCOL_V2["search_program_id"] == SEARCH_PROGRAM_ID
    assert PROTOCOL_V2["search_space_changes"]["automatic_revision_children"] is False


def test_hard_budget_and_candidate_gates_are_unchanged() -> None:
    assert CANDIDATE_REQUIRED_GATES == {"Coverage", "Costs", "OOS", "Permutation", "Baseline"}
    _assert_budget({"logical_calls": 5, "http_attempts": 7, "measured_tokens": 1000, "conservative_tokens": 2000}, reserve_tokens=1000)
    with pytest.raises(RuntimeError, match="LOGICAL"):
        _assert_budget({"logical_calls": 6, "http_attempts": 7, "measured_tokens": 1000, "conservative_tokens": 2000}, reserve_tokens=1000)
