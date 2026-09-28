from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from app.evidence import canonical_hash
from app.research.canonical import canonical_expression
from app.research.dsl.models import AllowedField, AllowedLookback, AllowedThreshold, StrictModel

Session = Literal["pre_market", "regular", "after_hours", "overnight", "weekend"]
Slot = Literal["A", "B", "C"]
V2Operator = Literal[
    "source", "signal", "ret", "vol", "sma", "zscore", "add", "sub", "mul", "div",
    "abs", "sign", "clip", "gt", "gte", "lt", "lte", "and", "or", "not", "session_in",
    "data_available", "rank", "group_mean", "rolling_beta", "residual", "dispersion",
]


class ExpressionV2(StrictModel):
    op: V2Operator
    args: list["ExpressionV2"] = Field(default_factory=list)
    symbol: str | None = None
    field: AllowedField | None = None
    lookback: AllowedLookback | None = None
    threshold: AllowedThreshold | None = None
    sessions: list[Session] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "ExpressionV2":
        unary = {"ret", "vol", "sma", "zscore", "abs", "sign", "not", "data_available"}
        binary = {"add", "sub", "mul", "div", "and", "or", "rolling_beta", "residual"}
        comparisons = {"gt", "gte", "lt", "lte"}
        if self.op == "source":
            if self.args or not self.symbol or not self.field:
                raise ValueError("source requires symbol and field, with no args")
        elif self.op == "signal":
            if self.args or self.symbol or self.field:
                raise ValueError("signal accepts no fields or arguments")
        elif self.op in unary and len(self.args) != 1:
            raise ValueError(f"{self.op} requires one argument")
        elif self.op in binary and len(self.args) != 2:
            raise ValueError(f"{self.op} requires two arguments")
        elif self.op in comparisons and (len(self.args) != 1 or self.threshold is None):
            raise ValueError(f"{self.op} requires one argument and a threshold")
        elif self.op == "clip" and len(self.args) != 1:
            raise ValueError("clip requires one argument")
        elif self.op == "session_in" and (self.args or not self.sessions):
            raise ValueError("session_in requires sessions")
        elif self.op in {"rank", "group_mean", "dispersion"} and len(self.args) < 3:
            raise ValueError(f"{self.op} requires at least three cross-sectional arguments")
        if self.op in {"ret", "vol", "sma", "zscore", "rolling_beta", "residual"} and self.lookback is None:
            raise ValueError(f"{self.op} requires an approved lookback")
        return self

    def walk(self) -> list["ExpressionV2"]:
        return [self, *(node for child in self.args for node in child.walk())]

    def depth(self) -> int:
        return 1 + max((child.depth() for child in self.args), default=0)


class FactorProposalV2(StrictModel):
    model_config = ConfigDict(extra="forbid")
    slot: Slot
    name: str = Field(min_length=3, max_length=120)
    thesis: str = Field(min_length=10, max_length=600)
    universe: list[str] = Field(min_length=3, max_length=12)
    session_filter: list[Session]
    transition_from: Session | None = None
    transition_to: Session | None = None
    signal: ExpressionV2
    entry_condition: ExpressionV2
    exit_condition: ExpressionV2
    horizon_bars: AllowedLookback
    rebalance_bars: AllowedLookback
    direction: Literal["long_flat"]
    rationale: str
    expected_signal_frequency: Literal["low", "medium"]
    economic_mechanism: str = Field(min_length=10)
    why_not_duplicate: str = Field(min_length=10)
    why_costs_should_not_dominate: str = Field(min_length=10)

    @model_validator(mode="after")
    def safe_limits(self) -> "FactorProposalV2":
        nodes = [node for expression in (self.signal, self.entry_condition, self.exit_condition) for node in expression.walk()]
        if len(nodes) > 60 or max(expression.depth() for expression in (self.signal, self.entry_condition, self.exit_condition)) > 7:
            raise ValueError("AST exceeds fdp-v2 safety limits")
        if len({node.lookback for node in nodes if node.lookback is not None}) > 3:
            raise ValueError("AST uses more than three lookbacks")
        if not {node.symbol for node in nodes if node.symbol}.issubset(set(self.universe)):
            raise ValueError("expression references symbol outside universe")
        if any(node.op == "vol" or node.field == "volume" for node in nodes):
            raise ValueError("volume remains disabled")
        operators = {node.op for node in nodes}
        if self.rebalance_bars < 6:
            raise ValueError("fdp-v2 rebalance must be at least 6 bars")
        if self.slot == "A":
            if len(self.universe) < 4 or not ({"rank", "group_mean"} & operators):
                raise ValueError("Slot A requires >=4 symbols and rank/group_mean")
            if len(self.session_filter) != 1 or self.horizon_bars not in {12, 24, 48}:
                raise ValueError("Slot A session/horizon contract failed")
        elif self.slot == "B":
            if (self.transition_from, self.transition_to) not in ADJACENT_TRANSITIONS or len(self.universe) < 3:
                raise ValueError("Slot B requires an adjacent transition and >=3 symbols")
            if self.transition_to not in self.session_filter or self.horizon_bars not in {6, 12, 24}:
                raise ValueError("Slot B session/horizon contract failed")
        elif not ({"rolling_beta", "residual", "dispersion"} & operators) or self.horizon_bars not in {12, 24, 48}:
            raise ValueError("Slot C requires beta/residual/dispersion and an allowed horizon")
        return self


ADJACENT_TRANSITIONS = {
    ("after_hours", "overnight"),
    ("overnight", "pre_market"),
    ("pre_market", "regular"),
    ("regular", "after_hours"),
}


def operator_fingerprint(proposal: FactorProposalV2) -> dict[str, int]:
    nodes = [node for expression in (proposal.signal, proposal.entry_condition, proposal.exit_condition) for node in expression.walk()]
    return dict(sorted(Counter(node.op for node in nodes).items()))


def validate_slot(proposal: FactorProposalV2, slot: Slot, forbidden_fingerprints: list[dict[str, int]]) -> list[str]:
    errors: list[str] = []
    nodes = [node for expression in (proposal.signal, proposal.entry_condition, proposal.exit_condition) for node in expression.walk()]
    operators = {node.op for node in nodes}
    if proposal.slot != slot:
        errors.append("SLOT_MISMATCH")
    if proposal.rebalance_bars < 6:
        errors.append("REBALANCE_TOO_FAST")
    if proposal.expected_signal_frequency == "high":
        errors.append("HIGH_SIGNAL_FREQUENCY")
    if slot == "A":
        if len(proposal.universe) < 4 or not ({"rank", "group_mean"} & operators):
            errors.append("SLOT_A_REQUIRES_CROSS_SECTION")
        if len(proposal.session_filter) != 1 or proposal.horizon_bars not in {12, 24, 48}:
            errors.append("SLOT_A_CONTRACT")
    elif slot == "B":
        transition = (proposal.transition_from, proposal.transition_to)
        if transition not in ADJACENT_TRANSITIONS or len(proposal.universe) < 3:
            errors.append("SLOT_B_REQUIRES_TRANSITION")
        if proposal.horizon_bars not in {6, 12, 24}:
            errors.append("SLOT_B_HORIZON")
    else:
        if not ({"rolling_beta", "residual", "dispersion"} & operators) or len(proposal.universe) < 3:
            errors.append("SLOT_C_REQUIRES_RESIDUAL_BETA_DISPERSION")
        if proposal.horizon_bars not in {12, 24, 48}:
            errors.append("SLOT_C_HORIZON")
    fingerprint = operator_fingerprint(proposal)
    if fingerprint in forbidden_fingerprints:
        errors.append("FORBIDDEN_OPERATOR_FINGERPRINT")
    return errors


def canonical_targeted_factor(proposal: FactorProposalV2) -> dict[str, Any]:
    value = proposal.model_dump(mode="json", exclude_none=True)
    for field in ("name", "thesis", "rationale", "economic_mechanism", "why_not_duplicate", "why_costs_should_not_dominate", "expected_signal_frequency", "slot"):
        value.pop(field, None)
    value["universe"] = sorted(value["universe"])
    value["session_filter"] = sorted(value["session_filter"])
    for field in ("signal", "entry_condition", "exit_condition"):
        value[field] = canonical_expression(value[field])
    return value


def targeted_factor_identity(proposal: FactorProposalV2) -> str:
    return canonical_hash(canonical_targeted_factor(proposal))
