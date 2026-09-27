#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.research.tracer import run_tracer  # noqa: E402


if __name__ == "__main__":
    evidence = asyncio.run(run_tracer(ROOT))
    print(json.dumps({"factor_hash": evidence["factor_hash"], "metrics": evidence["metrics"], "gates": evidence["gates"]}, indent=2))

