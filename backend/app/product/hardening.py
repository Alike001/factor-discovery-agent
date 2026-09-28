from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

FORBIDDEN_PUBLIC_KEYS = {
    "authorization",
    "api_key",
    "api_secret",
    "passphrase",
    "password",
    "raw_prompt",
    "prompt_text",
    "raw_response",
    "reasoning_content",
    "database_url",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def executable_hypothesis(recipe: Mapping[str, Any]) -> str:
    """Describe executable semantics using structured fields only."""
    if recipe.get("invalid") is True or not isinstance(recipe.get("recipe"), Mapping):
        return "Executable hypothesis unavailable because no valid structured recipe compiled."
    family = recipe.get("family")
    details = recipe.get("recipe") or {}
    session = (recipe.get("session_contract") or {}).get("session", "all supported sessions")
    horizon = recipe.get("horizon_bars")
    if family == "beta_residual":
        side = details.get("entry_side")
        side_text = {
            "positive_continuation": "Positive",
            "negative_continuation": "Negative",
            "positive_reversion": "Positive",
            "negative_reversion": "Negative",
        }.get(side, str(side))
        behavior = "continuation" if "continuation" in str(side) else "reversion"
        return (
            f"{side_text} {details.get('target')} residual versus {details.get('reference')}, "
            f"estimated over a {details.get('beta_lookback')}-bar beta window and measured over a "
            f"{details.get('signal_lookback')}-bar {details.get('residual_transform')} window, is tested "
            f"as a {behavior} signal above {details.get('threshold')} during the {session} session "
            f"with a {horizon}-bar holding horizon."
        )
    if family == "session_transition":
        transition = details.get("transition", "unknown transition").replace("_", " ")
        return (
            f"The {details.get('target')} {details.get('feature', 'transition_return')} across "
            f"{transition} is tested as a {details.get('direction')} signal with a "
            f"{horizon}-bar holding horizon."
        )
    return "Executable hypothesis unavailable because no valid structured recipe compiled."


def semantic_lint(recipe: Mapping[str, Any]) -> list[str]:
    """Flag explicit structured/text contradictions without interpreting execution from prose."""
    text = " ".join(
        str(recipe.get(key, "")) for key in ("name", "thesis", "economic_mechanism")
    ).lower()
    details = recipe.get("recipe") or {}
    entry_side = str(details.get("entry_side", ""))
    issues: list[str] = []
    if "continuation" in entry_side and any(word in text for word in ("mean reversion", "reverts", "decay", "compresses back")):
        issues.append("RATIONALE_RECIPE_DIRECTION_MISMATCH")
    if "reversion" in entry_side and any(word in text for word in ("continuation", "persists", "momentum")):
        issues.append("RATIONALE_RECIPE_DIRECTION_MISMATCH")
    return issues


def sanitize_public(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_PUBLIC_KEYS or lowered.endswith("_secret"):
                continue
            clean[str(key)] = sanitize_public(item)
        return clean
    if isinstance(value, list):
        return [sanitize_public(item) for item in value]
    return value


def public_package_errors(files: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    serialized = canonical_json(files).lower()
    for key in FORBIDDEN_PUBLIC_KEYS:
        if f'"{key}"' in serialized:
            errors.append(f"forbidden key: {key}")
    summary = files.get("RESEARCH_SUMMARY.json", {})
    if summary.get("global_search_n") != 9:
        errors.append("global search N must remain 9")
    if summary.get("paper", {}).get("fills") != 0:
        errors.append("paper fills must remain zero")
    if summary.get("discovery_status") != "CLOSED":
        errors.append("discovery must be closed")
    return errors
