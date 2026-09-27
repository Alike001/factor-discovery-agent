from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AllowedOperator = Literal[
    "source",
    "signal",
    "ret",
    "vol",
    "sma",
    "zscore",
    "add",
    "sub",
    "mul",
    "div",
    "abs",
    "sign",
    "clip",
    "gt",
    "gte",
    "lt",
    "lte",
    "and",
    "or",
    "not",
    "session_in",
    "data_available",
]
AllowedField = Literal["open", "high", "low", "close", "volume"]
AllowedLookback = Literal[1, 3, 6, 12, 24, 48, 120, 168]
AllowedThreshold = Literal[-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Expression(StrictModel):
    op: AllowedOperator
    args: list["Expression"] = Field(default_factory=list)
    symbol: str | None = None
    field: AllowedField | None = None
    lookback: AllowedLookback | None = None
    threshold: AllowedThreshold | None = None
    sessions: list[Literal["pre_market", "regular", "after_hours", "overnight", "weekend"]] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "Expression":
        unary = {"ret", "vol", "sma", "zscore", "abs", "sign", "not", "data_available"}
        binary = {"add", "sub", "mul", "div", "and", "or"}
        comparisons = {"gt", "gte", "lt", "lte"}
        if self.op == "source":
            if self.args or not self.symbol or not self.field:
                raise ValueError("source requires symbol and field, with no args")
        elif self.op == "signal":
            if self.args or self.symbol or self.field:
                raise ValueError("signal reference accepts no fields or arguments")
        elif self.op in unary and len(self.args) != 1:
            raise ValueError(f"{self.op} requires one argument")
        elif self.op in binary and len(self.args) != 2:
            raise ValueError(f"{self.op} requires two arguments")
        elif self.op in comparisons and (len(self.args) != 1 or self.threshold is None):
            raise ValueError(f"{self.op} requires one argument and an approved threshold")
        elif self.op == "clip" and len(self.args) != 1:
            raise ValueError("clip requires one argument")
        elif self.op == "session_in" and (self.args or not self.sessions):
            raise ValueError("session_in requires sessions and no args")
        if self.op in {"ret", "vol", "sma", "zscore"} and self.lookback is None:
            raise ValueError(f"{self.op} requires an approved lookback")
        return self

    def walk(self) -> list["Expression"]:
        return [self, *(descendant for child in self.args for descendant in child.walk())]

    def depth(self) -> int:
        return 1 + max((child.depth() for child in self.args), default=0)


class FactorSpec(StrictModel):
    name: str = Field(min_length=3, max_length=120)
    thesis: str = Field(min_length=10, max_length=600)
    universe: list[str] = Field(min_length=1, max_length=12)
    session_filter: list[Literal["pre_market", "regular", "after_hours", "overnight", "weekend"]]
    signal: Expression
    entry_condition: Expression
    exit_condition: Expression
    horizon_bars: AllowedLookback
    rebalance_bars: AllowedLookback
    direction: Literal["long_flat"]
    rationale: str

    @model_validator(mode="after")
    def enforce_limits(self) -> "FactorSpec":
        expressions = [self.signal, self.entry_condition, self.exit_condition]
        all_nodes = [node for expression in expressions for node in expression.walk()]
        if len(all_nodes) > 40:
            raise ValueError("AST exceeds 40 nodes")
        if max(expression.depth() for expression in expressions) > 6:
            raise ValueError("AST exceeds depth 6")
        lookbacks = {node.lookback for node in all_nodes if node.lookback is not None}
        if len(lookbacks) > 3:
            raise ValueError("AST uses more than three distinct lookbacks")
        referenced = {node.symbol for node in all_nodes if node.symbol}
        if not referenced.issubset(set(self.universe)):
            raise ValueError("expression references symbol outside approved universe")
        if any(node.op == "vol" or node.field == "volume" for node in all_nodes):
            raise ValueError("volume operators are disabled until rToken volume provenance is established")
        return self
