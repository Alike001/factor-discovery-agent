from __future__ import annotations

import json
from pathlib import Path

from app.evidence import canonical_hash


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    path = root / "evidence" / "tracer" / "tracer-experiment.json"
    payload = json.loads(path.read_text())
    print(json.dumps({"status": "COMPLETE", "path": str(path), "sha256": canonical_hash(payload)}))

