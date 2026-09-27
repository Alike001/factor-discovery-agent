from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg


class ResearchRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def ensure_protocol(self, version: str) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO research_protocols (version) VALUES (%s)
                ON CONFLICT (version) DO UPDATE SET version = EXCLUDED.version
                RETURNING id
                """,
                (version,),
            ).fetchone()
        assert row
        return row[0]

    def allocate_trial_number(self, protocol_id: UUID) -> int:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                UPDATE research_protocols
                SET next_trial_number = next_trial_number + 1
                WHERE id = %s
                RETURNING next_trial_number - 1
                """,
                (protocol_id,),
            ).fetchone()
        if row is None:
            raise KeyError("unknown protocol")
        return row[0]

    def upsert_cycle(self, protocol_id: UUID, cycle_number: int, idempotency_key: str, as_of: datetime) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO research_cycles (protocol_id, cycle_number, idempotency_key, status, as_of)
                VALUES (%s, %s, %s, 'STARTED', %s)
                ON CONFLICT (idempotency_key) DO UPDATE
                SET idempotency_key = EXCLUDED.idempotency_key
                RETURNING id
                """,
                (protocol_id, cycle_number, idempotency_key, as_of),
            ).fetchone()
        assert row
        return row[0]

    def create_factor_experiment_once(
        self,
        *,
        protocol_id: UUID,
        cycle_id: UUID,
        trial_number: int,
        canonical_hash: str,
        dataset_hash: str,
    ) -> tuple[UUID, UUID]:
        spec = {"canonical_hash": canonical_hash}
        with psycopg.connect(self.database_url) as connection:
            hypothesis = connection.execute(
                """
                INSERT INTO hypotheses
                    (protocol_id, cycle_id, trial_number, name, thesis, canonical_identity_hash)
                VALUES (%s, %s, %s, 'integrity-test', 'integrity-test hypothesis', %s)
                ON CONFLICT (protocol_id, trial_number) DO UPDATE
                SET canonical_identity_hash = hypotheses.canonical_identity_hash
                RETURNING id
                """,
                (protocol_id, cycle_id, trial_number, canonical_hash),
            ).fetchone()
            assert hypothesis
            factor = connection.execute(
                """
                INSERT INTO factor_versions
                    (protocol_id, hypothesis_id, version, canonical_spec_json, canonical_hash, lifecycle_state)
                VALUES (%s, %s, 1, %s::jsonb, %s, 'COMMITTED')
                ON CONFLICT (protocol_id, canonical_hash) DO UPDATE
                SET canonical_hash = factor_versions.canonical_hash
                RETURNING id
                """,
                (protocol_id, hypothesis[0], json.dumps(spec), canonical_hash),
            ).fetchone()
            assert factor
            experiment = connection.execute(
                """
                INSERT INTO experiments (factor_version_id, dataset_hash, protocol_version)
                VALUES (%s, %s, 'phase1.5')
                ON CONFLICT (factor_version_id, dataset_hash) DO UPDATE
                SET dataset_hash = experiments.dataset_hash
                RETURNING id
                """,
                (factor[0], dataset_hash),
            ).fetchone()
        assert experiment
        return factor[0], experiment[0]

