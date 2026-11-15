-- Draft: idempotency support for execution submissions (subject to contract/team agreement)
ALTER TABLE investigation_executions
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_investigation_executions_idempotency_key
    ON investigation_executions (idempotency_key)
    WHERE idempotency_key IS NOT NULL;
