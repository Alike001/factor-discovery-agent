from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from app.evidence import canonical_hash
from app.research.targeted import ExpressionV2, StrictModel

RECIPE_SCHEMA_VERSION = "factor-recipe-v1"
COMPILER_VERSION = "factor-recipe-compiler-v1"
PROMPT_SCHEMA_VERSION = "factor-recipe-prompt-v1"
Session = Literal["pre_market", "regular", "after_hours", "overnight", "weekend"]
Family = Literal["cross_sectional_rank", "session_transition", "beta_residual"]


class SessionContract(StrictModel):
    kind: Literal["single_session", "transition"]
    session: Session | None = None
    from_session: Session | None = None
    to_session: Session | None = None

    @model_validator(mode="after")
    def valid_contract(self) -> "SessionContract":
        if self.kind == "single_session" and (self.session is None or self.from_session or self.to_session):
            raise ValueError("single_session requires only session")
        if self.kind == "transition" and (not self.from_session or not self.to_session or self.session):
            raise ValueError("transition requires from_session and to_session")
        return self


class CrossSectionalRankRecipe(StrictModel):
    kind: Literal["cross_sectional_rank"]
    metric: Literal["return", "residual"]
    lookback: Literal[12, 24, 48]
    select_side: Literal["leader", "laggard"]


class SessionTransitionRecipe(StrictModel):
    kind: Literal["session_transition"]
    lookback: Literal[6, 12, 24]
    normalization: Literal["raw", "zscore"]


class BetaResidualRecipe(StrictModel):
    kind: Literal["beta_residual"]
    target: str
    reference: str
    beta_lookback: Literal[24, 48, 120]
    residual_transform: Literal["zscore"]
    signal_lookback: Literal[24, 48, 120]
    entry_side: Literal["negative_reversion", "positive_continuation"]


class FactorRecipe(StrictModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["factor-recipe-v1"]
    name: str = Field(min_length=3, max_length=120)
    thesis: str = Field(min_length=10, max_length=600)
    family: Family
    universe: list[str] = Field(min_length=2, max_length=8)
    session_contract: SessionContract
    recipe: CrossSectionalRankRecipe | SessionTransitionRecipe | BetaResidualRecipe
    horizon_bars: Literal[6, 12, 24, 48]
    rebalance_bars: Literal[6, 12, 24, 48]
    direction: Literal["long_flat"]
    expected_signal_frequency: Literal["low", "medium"]
    economic_mechanism: str = Field(min_length=10, max_length=600)
    why_not_duplicate: str = Field(min_length=10, max_length=600)
    why_costs_should_not_dominate: str = Field(min_length=10, max_length=600)

    @model_validator(mode="after")
    def aligned_family(self) -> "FactorRecipe":
        if self.family != self.recipe.kind:
            raise ValueError("family must equal recipe.kind")
        if self.rebalance_bars < 6:
            raise ValueError("rebalance must be at least 6 bars")
        return self


class CompiledFactorSpec(StrictModel):
    compiler_version: Literal["factor-recipe-compiler-v1"]
    slot: Literal["C"] = "C"
    name: str
    thesis: str
    universe: list[str]
    session_filter: list[Session]
    transition_from: None = None
    transition_to: None = None
    signal: ExpressionV2
    entry_condition: ExpressionV2
    exit_condition: ExpressionV2
    horizon_bars: Literal[12, 24, 48]
    rebalance_bars: Literal[6, 12, 24, 48]
    direction: Literal["long_flat"]
    rationale: str
    expected_signal_frequency: Literal["low", "medium"]
    economic_mechanism: str
    why_not_duplicate: str
    why_costs_should_not_dominate: str


REGISTRY: dict[str, dict[str, Any]] = {
    "cross_sectional_rank": {
        "status": "NOT_READY",
        "reason": "Evaluator has no cross-sectional portfolio selection, per-symbol attribution, or leave-one-symbol-out path.",
    },
    "session_transition": {
        "status": "NOT_READY",
        "reason": "Exact phase anchors and MISSING_EXPECTED_ANCHOR fail-closed semantics are not implemented.",
    },
    "beta_residual": {
        "status": "READY",
        "compiler": COMPILER_VERSION,
        "parameters": {
            "beta_lookback": [24, 48, 120], "signal_lookback": [24, 48, 120],
            "residual_transform": ["zscore"], "entry_side": ["negative_reversion", "positive_continuation"],
            "sessions": ["pre_market", "regular", "after_hours", "overnight", "weekend"],
            "horizon_bars": [12, 24, 48], "rebalance_bars": [6, 12, 24, 48],
        },
        "example": {
            "schema_version": RECIPE_SCHEMA_VERSION, "name": "Residual reversion probe",
            "thesis": "A target residual may normalize after beta-adjusted dislocation.",
            "family": "beta_residual", "universe": ["RNVDAUSDT", "RQQQUSDT"],
            "session_contract": {"kind": "single_session", "session": "pre_market"},
            "recipe": {"kind": "beta_residual", "target": "RNVDAUSDT", "reference": "RQQQUSDT",
                       "beta_lookback": 48, "residual_transform": "zscore", "signal_lookback": 48,
                       "entry_side": "negative_reversion"},
            "horizon_bars": 24, "rebalance_bars": 6, "direction": "long_flat",
            "expected_signal_frequency": "low", "economic_mechanism": "Beta-adjusted dislocations may normalize.",
            "why_not_duplicate": "Uses rolling residual rather than a raw pair-return difference.",
            "why_costs_should_not_dominate": "Six-hour rebalance and a twenty-four-hour horizon bound turnover.",
        },
    },
}


def ready_families() -> list[str]:
    return sorted(name for name, item in REGISTRY.items() if item["status"] == "READY")


def recipe_hash(recipe: FactorRecipe) -> str:
    return canonical_hash(recipe.model_dump(mode="json"))


def compile_recipe(recipe: FactorRecipe) -> CompiledFactorSpec:
    registry = REGISTRY.get(recipe.family)
    if not registry or registry["status"] != "READY":
        raise ValueError(f"RECIPE_NOT_READY:{recipe.family}")
    if not isinstance(recipe.recipe, BetaResidualRecipe):
        raise ValueError("compiler only accepts registered beta_residual recipe")
    if recipe.session_contract.kind != "single_session" or not recipe.session_contract.session:
        raise ValueError("beta_residual requires a single session")
    if recipe.recipe.target == recipe.recipe.reference:
        raise ValueError("target and reference must differ")
    if set(recipe.universe) != {recipe.recipe.target, recipe.recipe.reference}:
        raise ValueError("universe must contain exactly target and reference")
    if recipe.horizon_bars not in {12, 24, 48}:
        raise ValueError("unsupported beta_residual horizon")
    target_return = ExpressionV2(op="ret", lookback=1, args=[ExpressionV2(op="source", symbol=recipe.recipe.target, field="close")])
    reference_return = ExpressionV2(op="ret", lookback=1, args=[ExpressionV2(op="source", symbol=recipe.recipe.reference, field="close")])
    residual = ExpressionV2(op="residual", lookback=recipe.recipe.beta_lookback, args=[target_return, reference_return])
    signal = ExpressionV2(op="zscore", lookback=recipe.recipe.signal_lookback, args=[residual])
    if recipe.recipe.entry_side == "negative_reversion":
        entry = ExpressionV2(op="lt", threshold=-1.0, args=[ExpressionV2(op="signal")])
        exit_condition = ExpressionV2(op="gte", threshold=0.0, args=[ExpressionV2(op="signal")])
    else:
        entry = ExpressionV2(op="gt", threshold=1.0, args=[ExpressionV2(op="signal")])
        exit_condition = ExpressionV2(op="lte", threshold=0.0, args=[ExpressionV2(op="signal")])
    return CompiledFactorSpec(
        compiler_version=COMPILER_VERSION, name=recipe.name, thesis=recipe.thesis,
        universe=[recipe.recipe.target, recipe.recipe.reference], session_filter=[recipe.session_contract.session],
        signal=signal, entry_condition=entry, exit_condition=exit_condition,
        horizon_bars=recipe.horizon_bars, rebalance_bars=recipe.rebalance_bars, direction=recipe.direction,
        rationale=f"Compiled deterministically from {RECIPE_SCHEMA_VERSION}; recipe={recipe_hash(recipe)}",
        expected_signal_frequency=recipe.expected_signal_frequency, economic_mechanism=recipe.economic_mechanism,
        why_not_duplicate=recipe.why_not_duplicate, why_costs_should_not_dominate=recipe.why_costs_should_not_dominate,
    )


def ast_hash(spec: CompiledFactorSpec) -> str:
    return canonical_hash(spec.model_dump(mode="json"))


def estimate_input_tokens(text: str, safety_factor: float = 1.25) -> int:
    return math.ceil(len(text) / 4 * safety_factor)


def generate_proposer_prompt(slot_requirement: str, fingerprints: list[str]) -> str:
    capabilities = {name: {"parameters": REGISTRY[name]["parameters"], "example": REGISTRY[name]["example"]}
                    for name in ready_families()}
    return (
        f"Return one JSON FactorRecipe {RECIPE_SCHEMA_VERSION}; never return AST nodes. "
        f"READY registry:{capabilities}. Slot:{slot_requirement}. Avoid fingerprints:{fingerprints}. "
        "Use only a READY family and its legal enums. Return one JSON object; do not claim performance."
    )
