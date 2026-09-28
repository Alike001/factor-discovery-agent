from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.research.dsl.models import FactorSpec


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FactorProposal(FactorSpec):
    """The proposer contract is exactly the executable safe FactorSpec contract."""


class LifecycleDecision(StrictModel):
    action: Literal["ABANDON", "REVISE", "PROMOTE_RECOMMENDATION"]
    reason: str
    revision_intent: str | None = None

    @model_validator(mode="after")
    def revision_requires_intent(self) -> "LifecycleDecision":
        if self.action == "REVISE" and not self.revision_intent:
            raise ValueError("REVISE requires revision_intent")
        return self


class PortfolioDecision(StrictModel):
    action: Literal["HOLD", "OPEN", "REDUCE", "CLOSE"]
    symbol: str | None
    factor_version_id: str | None
    target_weight: Literal[0.0, 0.025, 0.05]
    reason: str
    invalidation: str
