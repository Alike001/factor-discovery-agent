CREATE TABLE IF NOT EXISTS research_programs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    program_key text NOT NULL UNIQUE,
    next_trial_number bigint NOT NULL DEFAULT 1 CHECK (next_trial_number > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS research_program_protocols (
    program_id uuid NOT NULL REFERENCES research_programs(id),
    protocol_id uuid NOT NULL REFERENCES research_protocols(id),
    PRIMARY KEY (program_id, protocol_id),
    UNIQUE (protocol_id)
);

ALTER TABLE research_cycles
    ADD COLUMN IF NOT EXISTS search_program_id uuid REFERENCES research_programs(id),
    ADD COLUMN IF NOT EXISTS research_slot text;
