from copy import deepcopy
from decimal import Decimal

from app.bitget.models import Candle
from app.research.dsl import FactorSpec
from app.research.engine import EngineConfig, evaluate_factor
from app.research.tracer import TRACER_SPEC


def series(count: int = 320) -> tuple[list[Candle], list[Candle]]:
    asset = []
    benchmark = []
    for index in range(count):
        base = Decimal("100") + Decimal(index) / Decimal("20")
        wave = Decimal((index % 17) - 8) / Decimal("10")
        asset_price = base + wave
        benchmark_price = Decimal("100") + Decimal(index) / Decimal("25")
        timestamp = index * 3_600_000
        asset.append(Candle(timestamp_ms=timestamp, open=asset_price, high=asset_price, low=asset_price, close=asset_price))
        benchmark.append(Candle(timestamp_ms=timestamp, open=benchmark_price, high=benchmark_price, low=benchmark_price, close=benchmark_price))
    return asset, benchmark


def test_signal_cannot_fill_on_decision_candle() -> None:
    asset, benchmark = series()
    result = evaluate_factor(
        FactorSpec.model_validate(TRACER_SPEC),
        asset,
        benchmark,
        EngineConfig("RNVDAUSDT", "RQQQUSDT", entry_threshold=2.0, exit_threshold=-2.0),
    )
    assert result.evidence["execution_audit"]["fill_count"] > 0
    assert result.evidence["execution_audit"]["same_decision_candle_violations"] == 0


def test_fee_changes_net_performance() -> None:
    asset, benchmark = series()
    spec = FactorSpec.model_validate(TRACER_SPEC)
    free = evaluate_factor(spec, asset, benchmark, EngineConfig("RNVDAUSDT", "RQQQUSDT", fee_per_fill=0, slippage_per_fill=0))
    costly = evaluate_factor(spec, asset, benchmark, EngineConfig("RNVDAUSDT", "RQQQUSDT", fee_per_fill=0.01, slippage_per_fill=0))
    assert costly.evidence["metrics"]["net"]["total_return"] <= free.evidence["metrics"]["net"]["total_return"]


def test_oos_boundary_is_fixed_by_input() -> None:
    asset, benchmark = series()
    split = 250 * 3_600_000
    result = evaluate_factor(
        FactorSpec.model_validate(TRACER_SPEC), asset, benchmark, EngineConfig("RNVDAUSDT", "RQQQUSDT"), split_timestamp_ms=split
    )
    assert result.evidence["protocol"]["split_timestamp"] == "1970-01-11T10:00:00+00:00"


def test_same_input_produces_same_financial_output() -> None:
    asset, benchmark = series()
    spec = FactorSpec.model_validate(deepcopy(TRACER_SPEC))
    first = evaluate_factor(spec, asset, benchmark, EngineConfig("RNVDAUSDT", "RQQQUSDT"))
    second = evaluate_factor(spec, asset, benchmark, EngineConfig("RNVDAUSDT", "RQQQUSDT"))
    assert first.evidence["metrics"] == second.evidence["metrics"]
    assert first.evidence["integrity"] == second.evidence["integrity"]


def test_per_field_valid_from_excludes_older_rows() -> None:
    asset, benchmark = series()
    valid_from = 150 * 3_600_000
    result = evaluate_factor(
        FactorSpec.model_validate(TRACER_SPEC),
        asset,
        benchmark,
        EngineConfig(
            "RNVDAUSDT",
            "RQQQUSDT",
            field_valid_from_ms={"RNVDAUSDT.close": valid_from, "RQQQUSDT.close": valid_from},
        ),
    )
    assert result.evidence["source"]["first_timestamp"] == "1970-01-07T06:00:00+00:00"
    assert result.evidence["protocol"]["field_valid_from"]["RNVDAUSDT.close"] == "1970-01-07T06:00:00+00:00"
