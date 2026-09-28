ALTER TABLE research_protocols
    ADD COLUMN IF NOT EXISTS config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS frozen_at timestamptz;

ALTER TABLE research_cycles
    ADD COLUMN IF NOT EXISTS error_code text;

ALTER TABLE qwen_runs
    ADD COLUMN IF NOT EXISTS endpoint_path text,
    ADD COLUMN IF NOT EXISTS prompt_text text,
    ADD COLUMN IF NOT EXISTS prompt_version text,
    ADD COLUMN IF NOT EXISTS token_usage jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 1;

ALTER TABLE hypotheses
    ADD COLUMN IF NOT EXISTS proposer_run_id uuid REFERENCES qwen_runs(id),
    ADD COLUMN IF NOT EXISTS proposal_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS duplicate_of uuid REFERENCES factor_versions(id);

ALTER TABLE experiments
    ADD COLUMN IF NOT EXISTS data_contract_json jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE factor_lifecycle_events
    ADD COLUMN IF NOT EXISTS qwen_run_id uuid REFERENCES qwen_runs(id),
    ADD COLUMN IF NOT EXISTS experiment_id uuid REFERENCES experiments(id);

CREATE UNIQUE INDEX IF NOT EXISTS one_role_per_cycle
ON qwen_runs (cycle_id, role);

CREATE UNIQUE INDEX IF NOT EXISTS one_snapshot_per_cycle
ON data_snapshots (cycle_id);
