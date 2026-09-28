from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg


class ResearchRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def ensure_protocol(self, version: str, config: dict[str, Any] | None = None) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO research_protocols (version, config_json, frozen_at)
                VALUES (%s, %s::jsonb, CASE WHEN %s::jsonb = '{}'::jsonb THEN NULL ELSE now() END)
                ON CONFLICT (version) DO UPDATE SET version = EXCLUDED.version
                RETURNING id, config_json
                """,
                (version, json.dumps(config or {}), json.dumps(config or {})),
            ).fetchone()
        assert row
        if config is not None and row[1] != config:
            raise ValueError(f"immutable protocol {version} does not match frozen configuration")
        return row[0]

    @contextmanager
    def worker_lock(self, lock_key: int = 0x46525032):
        connection = psycopg.connect(self.database_url, autocommit=True)
        acquired = connection.execute("SELECT pg_try_advisory_lock(%s)", (lock_key,)).fetchone()[0]
        try:
            yield bool(acquired)
        finally:
            if acquired:
                connection.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
            connection.close()

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

    def cycle(self, idempotency_key: str) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                "SELECT id, status, as_of, manifest_hash, error_code FROM research_cycles WHERE idempotency_key = %s",
                (idempotency_key,),
            ).fetchone()
        if not row:
            return None
        return {"id": row[0], "status": row[1], "as_of": row[2], "manifest_hash": row[3], "error_code": row[4]}

    def save_snapshot(self, cycle_id: UUID, as_of: datetime, payload: dict[str, Any], sha256: str) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO data_snapshots (cycle_id, as_of, snapshot_json, sha256)
                VALUES (%s, %s, %s::jsonb, %s)
                ON CONFLICT (cycle_id) DO UPDATE SET cycle_id = EXCLUDED.cycle_id
                RETURNING id
                """,
                (cycle_id, as_of, json.dumps(payload), sha256),
            ).fetchone()
        assert row
        return row[0]

    def qwen_budget(self, protocol_id: UUID) -> dict[str, int]:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                SELECT COALESCE(sum(q.attempt_count), 0),
                       COALESCE(sum(CASE WHEN q.token_usage ? 'budget_tokens'
                           AND (q.token_usage->>'budget_tokens') ~ '^[0-9]+$'
                           THEN (q.token_usage->>'budget_tokens')::bigint
                           WHEN q.token_usage ? 'total_tokens'
                           AND (q.token_usage->>'total_tokens') ~ '^[0-9]+$'
                           THEN (q.token_usage->>'total_tokens')::bigint
                           + GREATEST(q.attempt_count - 1, 0) * CASE WHEN q.role='proposer' THEN 2400 ELSE 900 END
                           ELSE GREATEST(q.attempt_count, 1) * CASE WHEN q.role='proposer' THEN 2400 ELSE 900 END END), 0)
                FROM qwen_runs q JOIN research_cycles c ON c.id = q.cycle_id
                WHERE c.protocol_id = %s
                """,
                (protocol_id,),
            ).fetchone()
        return {"attempts": int(row[0]), "budget_tokens": int(row[1])}

    def qwen_run_for_cycle(self, cycle_id: UUID, role: str) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                SELECT id, parsed_json, status, model, endpoint_path, token_usage, latency_ms, attempt_count
                FROM qwen_runs WHERE cycle_id = %s AND role = %s
                """,
                (cycle_id, role),
            ).fetchone()
        if not row:
            return None
        return {"id": row[0], "parsed_json": row[1], "status": row[2], "model": row[3], "endpoint_path": row[4], "token_usage": row[5], "latency_ms": row[6], "attempt_count": row[7]}

    def save_qwen_run(self, *, cycle_id: UUID, role: str, model: str, endpoint_path: str,
                      prompt_text: str, prompt_version: str, request_hash: str,
                      response_hash: str | None, final_text: str, parsed_json: dict[str, Any] | None,
                      status: str, token_usage: dict[str, Any], latency_ms: int,
                      attempt_count: int) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO qwen_runs
                    (cycle_id, role, model, endpoint_path, prompt_text, prompt_version, request_hash,
                     response_hash, raw_response, parsed_json, status, token_usage, latency_ms, attempt_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s, %s)
                ON CONFLICT (cycle_id, role) DO UPDATE SET role = EXCLUDED.role
                RETURNING id
                """,
                (cycle_id, role, model, endpoint_path, prompt_text, prompt_version, request_hash,
                 response_hash, final_text, json.dumps(parsed_json) if parsed_json else None, status,
                 json.dumps(token_usage), latency_ms, attempt_count),
            ).fetchone()
        assert row
        return row[0]

    def commit_hypothesis(self, *, protocol_id: UUID, cycle_id: UUID, trial_number: int,
                          proposer_run_id: UUID, proposal: dict[str, Any], canonical_hash: str
                          ) -> tuple[UUID, UUID, bool]:
        with psycopg.connect(self.database_url) as connection:
            hypothesis = connection.execute(
                """
                INSERT INTO hypotheses
                    (protocol_id, cycle_id, trial_number, name, thesis, canonical_identity_hash,
                     proposer_run_id, proposal_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (protocol_id, trial_number) DO UPDATE SET name = hypotheses.name
                RETURNING id
                """,
                (protocol_id, cycle_id, trial_number, proposal["name"], proposal["thesis"],
                 canonical_hash, proposer_run_id, json.dumps(proposal)),
            ).fetchone()
            assert hypothesis
            existing = connection.execute(
                "SELECT id FROM factor_versions WHERE protocol_id = %s AND canonical_hash = %s",
                (protocol_id, canonical_hash),
            ).fetchone()
            if existing:
                connection.execute("UPDATE hypotheses SET duplicate_of = %s WHERE id = %s", (existing[0], hypothesis[0]))
                return hypothesis[0], existing[0], True
            factor = connection.execute(
                """
                INSERT INTO factor_versions
                    (protocol_id, hypothesis_id, version, canonical_spec_json, canonical_hash, lifecycle_state)
                VALUES (%s, %s, 1, %s::jsonb, %s, 'COMMITTED') RETURNING id
                """,
                (protocol_id, hypothesis[0], json.dumps(proposal), canonical_hash),
            ).fetchone()
        assert factor
        return hypothesis[0], factor[0], False

    def hypothesis_for_cycle(self, cycle_id: UUID) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                SELECT h.id, h.trial_number, h.proposal_json, h.canonical_identity_hash,
                       h.duplicate_of, f.id
                FROM hypotheses h LEFT JOIN factor_versions f ON f.hypothesis_id = h.id
                WHERE h.cycle_id = %s
                """,
                (cycle_id,),
            ).fetchone()
        if not row:
            return None
        return {"id": row[0], "trial_number": row[1], "proposal": row[2], "canonical_hash": row[3],
                "duplicate_of": row[4], "factor_version_id": row[5] or row[4]}

    def save_experiment(self, *, factor_version_id: UUID, dataset_hash: str,
                        data_contract: dict[str, Any], metrics: dict[str, Any], report_hash: str) -> UUID:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO experiments
                    (factor_version_id, dataset_hash, protocol_version, data_contract_json, metrics_json, report_hash)
                VALUES (%s, %s, 'fdp-v1', %s::jsonb, %s::jsonb, %s)
                ON CONFLICT (factor_version_id, dataset_hash) DO UPDATE SET report_hash = experiments.report_hash
                RETURNING id
                """,
                (factor_version_id, dataset_hash, json.dumps(data_contract), json.dumps(metrics), report_hash),
            ).fetchone()
        assert row
        return row[0]

    def save_gates(self, experiment_id: UUID, gates: list[dict[str, Any]]) -> None:
        with psycopg.connect(self.database_url) as connection:
            for gate in gates:
                connection.execute(
                    """
                    INSERT INTO gate_results (experiment_id, gate_name, outcome, value_json, reason)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (experiment_id, gate_name) DO NOTHING
                    """,
                    (experiment_id, gate["name"], gate["outcome"], json.dumps(gate.get("value", {})), gate["reason"]),
                )

    def transition(self, factor_version_id: UUID, from_state: str | None, to_state: str, reason: str,
                   *, qwen_run_id: UUID | None = None, experiment_id: UUID | None = None) -> None:
        with psycopg.connect(self.database_url) as connection:
            exists = connection.execute(
                """SELECT 1 FROM factor_lifecycle_events
                   WHERE factor_version_id=%s AND to_state=%s AND COALESCE(experiment_id::text,'')=COALESCE(%s::text,'')""",
                (factor_version_id, to_state, experiment_id),
            ).fetchone()
            if exists:
                return
            connection.execute(
                """INSERT INTO factor_lifecycle_events
                   (factor_version_id, from_state, to_state, reason, qwen_run_id, experiment_id)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (factor_version_id, from_state, to_state, reason, qwen_run_id, experiment_id),
            )
            connection.execute("UPDATE factor_versions SET lifecycle_state=%s WHERE id=%s", (to_state, factor_version_id))

    def append_evidence(self, *, event_type: str, entity_type: str, entity_id: UUID | None,
                        payload: dict[str, Any]) -> str:
        from app.evidence import canonical_hash
        with psycopg.connect(self.database_url) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (0x45564944,))
            previous = connection.execute("SELECT event_hash FROM evidence_events ORDER BY seq DESC LIMIT 1").fetchone()
            previous_hash = previous[0] if previous else "0" * 64
            event_hash = canonical_hash({"previous_hash": previous_hash, "payload": payload})
            connection.execute(
                """INSERT INTO evidence_events
                   (event_type, entity_type, entity_id, payload_json, previous_hash, event_hash)
                   VALUES (%s,%s,%s,%s::jsonb,%s,%s) ON CONFLICT (event_hash) DO NOTHING""",
                (event_type, entity_type, entity_id, json.dumps(payload), previous_hash, event_hash),
            )
        return event_hash

    def complete_cycle(self, cycle_id: UUID, status: str, manifest_hash: str | None,
                       error_code: str | None = None) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                """UPDATE research_cycles SET status=%s, manifest_hash=%s, error_code=%s,
                   completed_at=now() WHERE id=%s""",
                (status, manifest_hash, error_code, cycle_id),
            )

    def phase2_summary(self, protocol_id: UUID) -> dict[str, Any]:
        with psycopg.connect(self.database_url) as connection:
            connection.row_factory = psycopg.rows.dict_row
            factors = connection.execute(
                """
                SELECT h.trial_number, h.name, h.thesis, h.canonical_identity_hash, h.duplicate_of,
                       f.id::text factor_version_id, f.lifecycle_state, f.canonical_spec_json,
                       e.metrics_json, e.data_contract_json, e.report_hash, e.created_at,
                       COALESCE(jsonb_agg(jsonb_build_object('name',g.gate_name,'outcome',g.outcome,'reason',g.reason))
                           FILTER (WHERE g.id IS NOT NULL), '[]'::jsonb) gates
                FROM hypotheses h LEFT JOIN factor_versions f ON f.hypothesis_id=h.id
                LEFT JOIN experiments e ON e.factor_version_id=f.id
                LEFT JOIN gate_results g ON g.experiment_id=e.id
                WHERE h.protocol_id=%s
                GROUP BY h.id, f.id, e.id ORDER BY h.trial_number
                """,
                (protocol_id,),
            ).fetchall()
            cycles = connection.execute(
                "SELECT cycle_number,status,as_of,manifest_hash,error_code FROM research_cycles WHERE protocol_id=%s ORDER BY cycle_number",
                (protocol_id,),
            ).fetchall()
            runs = connection.execute(
                """SELECT q.role,q.model,q.endpoint_path,q.token_usage,q.latency_ms,q.attempt_count,q.status
                   FROM qwen_runs q JOIN research_cycles c ON c.id=q.cycle_id
                   WHERE c.protocol_id=%s ORDER BY q.created_at""",
                (protocol_id,),
            ).fetchall()
        return {"protocol": "fdp-v1", "cycles": [dict(row) for row in cycles],
                "factors": [dict(row) for row in factors], "qwen_runs": [dict(row) for row in runs]}
