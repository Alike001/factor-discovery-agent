from __future__ import annotations

from pathlib import Path

import psycopg


def apply_migrations(database_url: str) -> list[str]:
    directory = Path(__file__).with_name("migrations")
    applied = []
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for path in sorted(directory.glob("*.sql")):
                cursor.execute(path.read_text(encoding="utf-8"))
                applied.append(path.name)
    return applied

