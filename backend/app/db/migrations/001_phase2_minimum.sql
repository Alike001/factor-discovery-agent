CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS research_protocols (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version text NOT NULL UNIQUE,
    next_trial_number bigint NOT NULL DEFAULT 1 CHECK (next_trial_number > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS research_cycles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id uuid NOT NULL REFERENCES research_protocols(id),
    cycle_number bigint NOT NULL UNIQUE,
    idempotency_key text NOT NULL UNIQUE,
    status text NOT NULL,
    as_of timestamptz NOT NULL,
    completed_at timestamptz,
    manifest_hash text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id uuid NOT NULL REFERENCES research_cycles(id),
    as_of timestamptz NOT NULL,
    snapshot_json jsonb NOT NULL,
    sha256 text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS qwen_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id uuid NOT NULL REFERENCES research_cycles(id),
    role text NOT NULL,
    model text NOT NULL,
    request_hash text NOT NULL,
    response_hash text,
    raw_response text,
    parsed_json jsonb,
    status text NOT NULL,
    latency_ms integer,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id uuid NOT NULL REFERENCES research_protocols(id),
    cycle_id uuid NOT NULL REFERENCES research_cycles(id),
    trial_number bigint NOT NULL,
    name text NOT NULL,
    thesis text NOT NULL,
    canonical_identity_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (protocol_id, trial_number)
);

CREATE TABLE IF NOT EXISTS factor_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id uuid NOT NULL REFERENCES research_protocols(id),
    hypothesis_id uuid NOT NULL REFERENCES hypotheses(id),
    version integer NOT NULL,
    canonical_spec_json jsonb NOT NULL,
    canonical_hash text NOT NULL,
    lifecycle_state text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (protocol_id, canonical_hash)
);

CREATE TABLE IF NOT EXISTS experiments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_version_id uuid NOT NULL REFERENCES factor_versions(id),
    dataset_hash text NOT NULL,
    protocol_version text NOT NULL,
    metrics_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    report_hash text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (factor_version_id, dataset_hash)
);

CREATE TABLE IF NOT EXISTS gate_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id uuid NOT NULL REFERENCES experiments(id),
    gate_name text NOT NULL,
    outcome text NOT NULL,
    value_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (experiment_id, gate_name)
);

CREATE TABLE IF NOT EXISTS factor_lifecycle_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_version_id uuid NOT NULL REFERENCES factor_versions(id),
    from_state text,
    to_state text NOT NULL,
    reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seq bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    event_type text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid,
    payload_json jsonb NOT NULL,
    previous_hash text,
    event_hash text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION reject_append_only_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS factor_lifecycle_events_append_only ON factor_lifecycle_events;
CREATE TRIGGER factor_lifecycle_events_append_only
BEFORE UPDATE OR DELETE ON factor_lifecycle_events
FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();

DROP TRIGGER IF EXISTS evidence_events_append_only ON evidence_events;
CREATE TRIGGER evidence_events_append_only
BEFORE UPDATE OR DELETE ON evidence_events
FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();

