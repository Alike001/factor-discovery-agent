#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.research.tracer import run_tracer_v2  # noqa: E402


if __name__ == "__main__":
    result = asyncio.run(run_tracer_v2(ROOT))
    print(json.dumps({"schema_version": result["schema_version"], "metrics": result["metrics"]}, indent=2))
