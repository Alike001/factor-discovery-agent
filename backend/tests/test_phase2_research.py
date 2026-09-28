from __future__ import annotations

from copy import deepcopy

from app.research.canonical import factor_identity
from app.research.dsl import FactorSpec
from app.research.tracer import TRACER_SPEC


def test_commutative_canonical_equivalence() -> None:
    left = deepcopy(TRACER_SPEC)
    left["signal"] = {
        "op": "add",
        "args": [
            {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RNVDAUSDT", "field": "close"}]},
            {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RQQQUSDT", "field": "close"}]},
        ],
    }
    right = deepcopy(left)
    right["signal"]["args"].reverse()
    right["name"] = "Different display name"
    right["thesis"] = "Different words do not change the executable identity."
    assert factor_identity(FactorSpec.model_validate(left)) == factor_identity(FactorSpec.model_validate(right))


def test_noncommutative_expression_changes_identity() -> None:
    left = FactorSpec.model_validate(TRACER_SPEC)
    value = deepcopy(TRACER_SPEC)
    value["signal"]["args"][0]["args"].reverse()
    right = FactorSpec.model_validate(value)
    assert factor_identity(left) != factor_identity(right)
