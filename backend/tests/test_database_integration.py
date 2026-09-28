from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
from psycopg.errors import RaiseException
import pytest

from app.db.migrate import apply_migrations
from app.db.repository import ResearchRepository
from app.qwen.budget import PostgresTokenBudget, ProjectedBudgetExhausted


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


def test_search_program_counter_spans_protocol_versions(repository: ResearchRepository) -> None:
    suffix = uuid4().hex
    first = repository.ensure_protocol(f"pytest-fdp-v1-{suffix}")
    second = repository.ensure_protocol(f"pytest-fdp-v2-{suffix}")
    key = f"pytest-search-program-{suffix}"
    program = repository.ensure_search_program(key, [first, second], starting_trial=101)
    assert repository.allocate_search_trial(program) == 101
    assert repository.allocate_search_trial(program) == 102
    same = repository.ensure_search_program(key, [first, second], starting_trial=101)
    assert same == program
    assert repository.allocate_search_trial(program) == 103


def test_token_reservation_normal_max_unmeasured_and_repair(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    scope = f"pytest-budget-{uuid4().hex}"
    budget = PostgresTokenBudget(DATABASE_URL, scope, 5000)
    normal = budget.reserve("normal", "short prompt", 500)
    assert budget.settle(normal, 200) == 200
    unmeasured = budget.reserve("unmeasured", "another prompt", 500)
    assert budget.settle(unmeasured, None) == unmeasured.reserved_tokens
    repair = budget.reserve("repair-1", "invalid response repair", 500)
    budget.settle(repair, 300)
    maximum = budget.reserve("max", "x" * 100, 500)
    assert budget.settle(maximum, maximum.reserved_tokens) == maximum.reserved_tokens
    usage = budget.usage()
    assert usage["charged_tokens"] <= usage["hard_limit"]
    with pytest.raises(ProjectedBudgetExhausted):
        budget.reserve("too-large-repair", "x" * 5000, 1000)


def test_concurrent_token_reservations_cannot_exceed_hard_limit(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    budget = PostgresTokenBudget(DATABASE_URL, f"pytest-concurrent-budget-{uuid4().hex}", 2200)
    def attempt(index: int) -> int:
        try:
            return budget.reserve(f"call-{index}", "x" * 500, 500).reserved_tokens
        except ProjectedBudgetExhausted:
            return 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations = list(pool.map(attempt, range(8)))
    usage = budget.usage()
    assert sum(reservations) == usage["outstanding_reservations"]
    assert usage["charged_tokens"] + usage["outstanding_reservations"] <= usage["hard_limit"]


def test_controlled_fdp_v3_batch_advances_global_search_n_to_nine(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL) as connection:
        program = connection.execute(
            "SELECT id FROM research_programs WHERE program_key='rtoken-session-alpha-v1'"
        ).fetchone()
    assert program and repository.search_program_n(program[0]) == 9


def test_fdp_v3_freeze_reservation_and_two_slot_controls(repository: ResearchRepository) -> None:
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL) as connection:
        protocol = connection.execute("SELECT id FROM research_protocols WHERE version='fdp-v3'").fetchone()
        assert protocol
        events = connection.execute(
            """SELECT seq,event_type FROM evidence_events
               WHERE event_type IN ('FDP_V3_PROTOCOL_ACTIVATED','FDP_V3_BATCH_PLAN_FROZEN',
                                    'FDP_V3_QWEN_REQUEST_RESERVED') ORDER BY seq"""
        ).fetchall()
        cycles = connection.execute(
            """SELECT research_slot,status FROM research_cycles WHERE protocol_id=%s ORDER BY cycle_number""",
            (protocol[0],),
        ).fetchall()
        roles = connection.execute(
            """SELECT c.research_slot,array_agg(q.role ORDER BY q.created_at)
               FROM research_cycles c JOIN qwen_runs q ON q.cycle_id=c.id
               WHERE c.protocol_id=%s GROUP BY c.research_slot ORDER BY c.research_slot""",
            (protocol[0],),
        ).fetchall()
        account = connection.execute(
            "SELECT charged_tokens,hard_limit_tokens FROM qwen_budget_accounts WHERE scope='fdp-v3-controlled-batch'"
        ).fetchone()
        active = connection.execute(
            """SELECT COALESCE(sum(reserved_tokens),0) FROM qwen_token_reservations
               WHERE scope='fdp-v3-controlled-batch' AND status='RESERVED'"""
        ).fetchone()[0]
    assert events[0][1] == "FDP_V3_PROTOCOL_ACTIVATED"
    assert events[1][1] == "FDP_V3_BATCH_PLAN_FROZEN"
    assert all(seq > events[1][0] for seq, kind in events if kind == "FDP_V3_QWEN_REQUEST_RESERVED")
    assert cycles == [("A", "COMPLETE"), ("B", "COMPLETE")]
    assert roles == [("A", ["proposer", "lifecycle"]), ("B", ["proposer"])]
    assert account and account[0] + active <= account[1] == 14_000
