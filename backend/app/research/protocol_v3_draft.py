from __future__ import annotations

from app.evidence import canonical_hash
from app.research.protocol_v2 import PROTOCOL_V2, SEARCH_PROGRAM_ID
from app.research.recipes import COMPILER_VERSION, PROMPT_SCHEMA_VERSION, RECIPE_SCHEMA_VERSION, ready_families

PROTOCOL_V3_DRAFT = {
    **PROTOCOL_V2,
    "version": "fdp-v3-draft",
    "active": False,
    "search_program_id": SEARCH_PROGRAM_ID,
    "current_global_search_n": 7,
    "factor_recipe_schema": RECIPE_SCHEMA_VERSION,
    "compiler_version": COMPILER_VERSION,
    "prompt_schema_version": PROMPT_SCHEMA_VERSION,
    "ready_recipe_families": ready_families(),
    "token_budget_policy": "postgres-conservative-pre-call-reservation-v1",
}
PROTOCOL_V3_DRAFT_HASH = canonical_hash(PROTOCOL_V3_DRAFT)
