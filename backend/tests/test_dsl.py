import pytest
from pydantic import ValidationError

from app.research.dsl import Expression, FactorSpec
from app.research.tracer import TRACER_SPEC


def test_factor_spec_rejects_unknown_operator() -> None:
    with pytest.raises(ValidationError):
        Expression.model_validate({"op": "exec", "args": []})


def test_future_field_is_impossible() -> None:
    with pytest.raises(ValidationError):
        Expression.model_validate({"op": "source", "symbol": "RNVDAUSDT", "field": "future_close"})


def test_tracer_spec_is_valid_and_canonicalizable() -> None:
    spec = FactorSpec.model_validate(TRACER_SPEC)
    assert spec.signal.op == "zscore"


def test_volume_operator_disabled_by_default() -> None:
    proposal = dict(TRACER_SPEC)
    proposal["signal"] = {
        "op": "vol",
        "lookback": 12,
        "args": [{"op": "source", "symbol": "RNVDAUSDT", "field": "volume"}],
    }
    with pytest.raises(ValidationError, match="volume operators are disabled"):
        FactorSpec.model_validate(proposal)
