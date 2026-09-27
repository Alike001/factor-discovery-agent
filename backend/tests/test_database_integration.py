from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import psycopg
from psycopg.errors import RaiseException
import pytest

from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository


DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not configured")


@pytest.fixture(scope="module")
def repository() -> ResearchRepository:
    assert DATABASE_URL
    apply_migrations(DATABASE_URL)
    return ResearchRepository(DATABASE_URL)


def test_concurrent_trial_allocations_are_unique(repository: ResearchRepository) -> None:
    protocol = repository.ensure_protocol("phase1.5-pytest")
    with ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(lambda _: repository.allocate_trial_number(protocol), range(24)))
    assert len(values) == len(set(values))
    assert max(values) - min(values) == len(values) - 1


def test_cycle_rerun_is_idempotent(repository: ResearchRepository) -> None:
    protocol = repository.ensure_protocol("phase1.5-pytest")
    first = repository.upsert_cycle(protocol, 9_150_001, "pytest-cycle-idempotency", datetime.now(UTC))
    second = repository.upsert_cycle(protocol, 9_150_001, "pytest-cycle-idempotency", datetime.now(UTC))
    assert first == second


def test_duplicate_factor_does_not_create_second_experiment(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    protocol = repository.ensure_protocol("phase1.5-pytest")
    cycle = repository.upsert_cycle(protocol, 9_150_002, "pytest-duplicate-factor", datetime.now(UTC))
    trial = repository.allocate_trial_number(protocol)
    first = repository.create_factor_experiment_once(
        protocol_id=protocol,
        cycle_id=cycle,
        trial_number=trial,
        canonical_hash="pytest-canonical-factor",
        dataset_hash="pytest-dataset",
    )
    second = repository.create_factor_experiment_once(
        protocol_id=protocol,
        cycle_id=cycle,
        trial_number=trial,
        canonical_hash="pytest-canonical-factor",
        dataset_hash="pytest-dataset",
    )
    assert first == second
    with psycopg.connect(DATABASE_URL) as connection:
        count = connection.execute(
            "SELECT count(*) FROM experiments WHERE factor_version_id = %s AND dataset_hash = %s",
            (first[0], "pytest-dataset"),
        ).fetchone()
    assert count == (1,)


def test_lifecycle_events_are_append_only(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    protocol = repository.ensure_protocol("phase1.5-pytest")
    cycle = repository.upsert_cycle(protocol, 9_150_003, "pytest-append-only", datetime.now(UTC))
    trial = repository.allocate_trial_number(protocol)
    factor, _ = repository.create_factor_experiment_once(
        protocol_id=protocol,
        cycle_id=cycle,
        trial_number=trial,
        canonical_hash="pytest-append-only-factor",
        dataset_hash="pytest-append-only-dataset",
    )
    with pytest.raises(RaiseException):
        with psycopg.connect(DATABASE_URL) as connection:
            event = connection.execute(
                """
                INSERT INTO factor_lifecycle_events (factor_version_id, from_state, to_state, reason)
                VALUES (%s, 'COMMITTED', 'FORMALIZED', 'test') RETURNING id
                """,
                (factor,),
            ).fetchone()
            connection.execute("UPDATE factor_lifecycle_events SET reason = 'mutated' WHERE id = %s", (event[0],))
