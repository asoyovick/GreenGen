DROP INDEX IF EXISTS idx_investigation_executions_idempotency_key;
ALTER TABLE investigation_executions DROP COLUMN IF EXISTS idempotency_key;
