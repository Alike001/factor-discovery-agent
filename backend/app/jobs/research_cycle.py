from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.research.tracer import run_tracer


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    evidence = asyncio.run(run_tracer(root))
    print(json.dumps({"status": "COMPLETE", "factor_hash": evidence["factor_hash"]}))


if __name__ == "__main__":
    main()

