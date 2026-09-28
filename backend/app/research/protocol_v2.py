from __future__ import annotations

from app.evidence import canonical_hash
from app.research.protocol import CORE_SYMBOLS, PROTOCOL

PROTOCOL_VERSION_V2 = "fdp-v2"
SEARCH_PROGRAM_ID = "rtoken-session-alpha-v1"

PROTOCOL_V2 = {
    **PROTOCOL,
    "version": PROTOCOL_VERSION_V2,
    "search_program_id": SEARCH_PROGRAM_ID,
    "search_space_changes": {
        "minimum_rebalance_bars": 6,
        "allowed_horizons": [6, 12, 24, 48],
        "expected_signal_frequency": ["low", "medium"],
        "slots": ["A", "B", "C"],
        "automatic_revision_children": False,
    },
    "enabled_symbols": list(CORE_SYMBOLS),
    "budget": {
        "max_logical_calls": 6,
        "max_live_http_attempts": 8,
        "max_additional_measured_tokens": 25000,
        "max_repairs_per_request": 1,
        "trials": 3,
    },
    "trial_semantics": "global monotonic trial in rtoken-session-alpha-v1; every committed proposal counts; no hidden replacement",
}
PROTOCOL_V2_HASH = canonical_hash(PROTOCOL_V2)
