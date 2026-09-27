from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FactorProposal(StrictModel):
    name: str = Field(min_length=3, max_length=120)
    thesis: str = Field(min_length=10, max_length=600)
    universe: list[str] = Field(min_length=1, max_length=12)
    session_filter: list[Literal["pre_market", "regular", "after_hours", "overnight", "weekend"]]
    signal: dict
    horizon_bars: int
    direction: Literal["long_flat"]
    rationale: str


class LifecycleDecision(StrictModel):
    action: Literal["ABANDON", "EXPLAIN", "REVISE", "PROMOTE_RECOMMENDATION"]
    reason: str
    revision: dict | None = None


class PortfolioDecision(StrictModel):
    action: Literal["HOLD", "OPEN", "REDUCE", "CLOSE"]
    symbol: str | None
    factor_version_id: str | None
    target_weight: Literal[0.0, 0.025, 0.05]
    reason: str
    invalidation: str

