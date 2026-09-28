from __future__ import annotations

from typing import Any

from app.evidence import canonical_hash
from app.research.dsl import FactorSpec

COMMUTATIVE = {"add", "mul", "and", "or"}


def canonical_expression(value: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: item for key, item in value.items() if item is not None}
    args = [canonical_expression(item) for item in normalized.get("args", [])]
    if normalized.get("op") in COMMUTATIVE:
        args.sort(key=canonical_hash)
    normalized["args"] = args
    if "sessions" in normalized:
        normalized["sessions"] = sorted(normalized["sessions"])
    return normalized


def canonical_factor(spec: FactorSpec) -> dict[str, Any]:
    value = spec.model_dump(mode="json", exclude_none=True)
    value["universe"] = sorted(value["universe"])
    value["session_filter"] = sorted(value["session_filter"])
    for field in ("signal", "entry_condition", "exit_condition"):
        value[field] = canonical_expression(value[field])
    value.pop("name", None)
    value.pop("thesis", None)
    value.pop("rationale", None)
    return value


def factor_identity(spec: FactorSpec) -> str:
    return canonical_hash(canonical_factor(spec))
