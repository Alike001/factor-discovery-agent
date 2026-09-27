import json
from datetime import datetime
from pathlib import Path

from app.bitget.session import NEW_YORK, classify_session


FIXTURE = Path(__file__).parent / "fixtures" / "session_cases.json"
JULY_3_CLOSURE = [
    (
        datetime(2026, 7, 2, 20, 0, tzinfo=NEW_YORK),
        datetime(2026, 7, 3, 20, 0, tzinfo=NEW_YORK),
    )
]


def test_fifty_fixed_historical_session_cases() -> None:
    cases = json.loads(FIXTURE.read_text())
    assert len(cases) == 50
    for timestamp, expected in cases:
        observed = classify_session(datetime.fromisoformat(timestamp.replace("Z", "+00:00")), JULY_3_CLOSURE)
        assert observed.value == expected, timestamp
