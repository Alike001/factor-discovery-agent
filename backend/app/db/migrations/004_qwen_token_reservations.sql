CREATE TABLE IF NOT EXISTS qwen_budget_accounts (
    scope text PRIMARY KEY,
    hard_limit_tokens bigint NOT NULL CHECK (hard_limit_tokens > 0),
    charged_tokens bigint NOT NULL DEFAULT 0 CHECK (charged_tokens >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS qwen_token_reservations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope text NOT NULL REFERENCES qwen_budget_accounts(scope),
    call_key text NOT NULL,
    estimated_input_tokens bigint NOT NULL,
    max_completion_tokens bigint NOT NULL,
    reserved_tokens bigint NOT NULL CHECK (reserved_tokens > 0),
    actual_tokens bigint,
    charged_tokens bigint,
    status text NOT NULL CHECK (status IN ('RESERVED','SETTLED')),
    settled_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(scope,call_key)
);
