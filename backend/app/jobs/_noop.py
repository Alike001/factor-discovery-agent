from __future__ import annotations

import json
from datetime import UTC, datetime


def no_op(job: str) -> None:
    print(
        json.dumps(
            {
                "job": job,
                "status": "NO_RUN",
                "reason": "Phase 1 has no promoted factor or paper position.",
                "execution_mode": "local_paper",
                "observed_at": datetime.now(UTC).isoformat(),
                "financial_state_mutated": False,
            }
        )
    )

