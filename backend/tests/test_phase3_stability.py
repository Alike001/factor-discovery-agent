from __future__ import annotations

from app.research.phase3 import factor_scope, temporal_stability
from app.research.tracer import TRACER_SPEC
from app.research.dsl import FactorSpec


def test_pair_factor_scope_is_structural() -> None:
    assert factor_scope(FactorSpec.model_validate(TRACER_SPEC)) == "PAIR_RELATIVE_SESSION"


def test_stability_requires_three_evaluable_blocks() -> None:
    hour = 3_600_000
    rows = [{"timestamp_ms": index * hour, "net": 0.01 if index == 2 else 0.0,
             "turnover": 1.0 if index == 2 else 0.0} for index in range(40)]
    result = temporal_stability(rows, 0, 39 * hour, session_purity=True)
    assert result["status"] == "INCONCLUSIVE"
    assert result["reason_code"] == "INCONCLUSIVE_STABILITY_SAMPLE"


def test_session_impurity_is_hard_failure() -> None:
    result = temporal_stability([], 0, 100, session_purity=False)
    assert result["status"] == "FAIL"
    assert result["reason_code"] == "SESSION_PURITY_FAIL"


def test_four_consistent_distributed_blocks_pass() -> None:
    hour = 3_600_000
    rows = []
    for index in range(40):
        rows.append({"timestamp_ms": index * hour, "net": 0.002 if index in {2, 12, 22, 32} else 0.0,
                     "turnover": 1.0 if index in {2, 12, 22, 32} else 0.0})
    result = temporal_stability(rows, 0, 39 * hour, session_purity=True)
    assert result["status"] == "PASS"
