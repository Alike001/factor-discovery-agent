from __future__ import annotations

from app.evidence import canonical_hash
from app.research.protocol_v2 import PROTOCOL_V2, SEARCH_PROGRAM_ID
from app.research.recipes import COMPILER_VERSION, PROMPT_SCHEMA_VERSION, RECIPE_SCHEMA_VERSION, ready_families
from app.research.session_transition import CONTRACT_VERSION, contract_hash

PROTOCOL_VERSION_V3 = "fdp-v3"
FDP_V3 = {
    **PROTOCOL_V2,
    "version": PROTOCOL_VERSION_V3,
    "active": True,
    "search_program_id": SEARCH_PROGRAM_ID,
    "search_n_at_activation": 7,
    "factor_recipe_schema": RECIPE_SCHEMA_VERSION,
    "compiler_version": COMPILER_VERSION,
    "prompt_schema_version": PROMPT_SCHEMA_VERSION,
    "ready_recipe_families": ready_families(),
    "session_transition_contract": {"version": CONTRACT_VERSION, "hash": contract_hash()},
    "token_budget_policy": "postgres-conservative-pre-call-reservation-v1",
    "controlled_batch": {
        "slots": ["A", "B"],
        "families": ["beta_residual", "session_transition"],
        "max_logical_calls": 4,
        "max_http_attempts": 6,
        "hard_reserved_or_charged_tokens": 14_000,
        "max_repairs_per_request": 1,
        "automatic_revision_children": False,
        "hidden_replacements": False,
    },
}
FDP_V3_HASH = canonical_hash(FDP_V3)
