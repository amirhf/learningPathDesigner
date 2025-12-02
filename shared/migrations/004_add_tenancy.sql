-- Add tenant_id to resource table
ALTER TABLE resource ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'global';
CREATE INDEX IF NOT EXISTS idx_resource_tenant_id ON resource(tenant_id);

-- Add tenant_id to learning_plans table
ALTER TABLE learning_plans ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'global';
CREATE INDEX IF NOT EXISTS idx_learning_plans_tenant_id ON learning_plans(tenant_id);

-- Add tenant_id to quizzes table
ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'global';
CREATE INDEX IF NOT EXISTS idx_quizzes_tenant_id ON quizzes(tenant_id);

-- Add tenant_id to quiz_attempts table
ALTER TABLE quiz_attempts ADD COLUMN IF NOT EXISTS tenant_id TEXT DEFAULT 'global';
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_tenant_id ON quiz_attempts(tenant_id);