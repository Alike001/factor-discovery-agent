from __future__ import annotations

from app.evidence import canonical_hash

PROTOCOL_VERSION = "fdp-v1"
CORE_SYMBOLS = (
    "RNVDAUSDT",
    "RAAPLUSDT",
    "RTSLAUSDT",
    "RMSFTUSDT",
    "RAMZNUSDT",
    "RMETAUSDT",
    "RAMDUSDT",
    "RQQQUSDT",
)

PROTOCOL = {
    "version": PROTOCOL_VERSION,
    "enabled_symbols": list(CORE_SYMBOLS),
    "enabled_fields": ["open", "high", "low", "close", "session"],
    "volume_enabled": False,
    "allowed_lookbacks": [1, 3, 6, 12, 24, 48, 120, 168],
    "approved_thresholds": [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0],
    "cost_model": {
        "version": "rtoken-cost-v1",
        "fee_per_fill": 0.0005,
        "fee_basis": "ASSUMED_PUBLISHED_BASELINE",
        "slippage_per_fill": 0.00025,
    },
    "split_rule": "latest closed aligned bar minus 30 calendar days",
    "session_classifier": "america-new-york-v1",
    "certification_floor": "2026-06-02T00:00:00Z",
    "gate_policy": {
        "history_days": 60,
        "oos_days": 30,
        "oos_trade_events": 20,
        "permutations": 2000,
        "candidate_permutation_p": 0.10,
        "certification_permutation_p": 0.05,
        "dsr_probability": 0.90,
    },
    "budget": {
        "max_live_http_attempts": 20,
        "max_measured_total_tokens": 50000,
        "max_repairs_per_request": 1,
        "max_calls_per_cycle": {"proposer": 1, "lifecycle": 1},
    },
    "trial_semantics": "every committed proposal allocates one monotonic trial; duplicates remain logged but are not evaluated twice",
}
PROTOCOL_HASH = canonical_hash(PROTOCOL)
