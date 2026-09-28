from __future__ import annotations

import json
import os

import psycopg

from app.evidence import canonical_hash


def verify_chain(database_url: str) -> dict[str, object]:
    previous = "0" * 64
    count = 0
    with psycopg.connect(database_url) as connection:
        rows = connection.execute("SELECT seq,payload_json,previous_hash,event_hash FROM evidence_events ORDER BY seq").fetchall()
    for seq, payload, stored_previous, event_hash in rows:
        expected = canonical_hash({"previous_hash": previous, "payload": payload})
        if stored_previous != previous or event_hash != expected:
            return {"status": "FAIL", "event_count": count, "failed_seq": seq}
        previous = event_hash
        count += 1
    return {"status": "PASS", "event_count": count, "head_hash": previous}


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    result = verify_chain(database_url)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
