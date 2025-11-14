-- Learning Path Designer - Schema Unification
-- Version: 003
-- Description: Unify duplicate tables and standardize naming
-- This migration fixes the duplicate resource/resources and skill/skills tables

-- Step 1: Drop duplicate tables created in migration 002
DROP TABLE IF EXISTS quiz_attempts CASCADE;
DROP TABLE IF EXISTS quizzes CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS skills CASCADE;

-- Step 2: Add missing columns to original tables from migration 001
-- Add snippet_s3_key as alias for s3_cache_key in resource table
ALTER TABLE resource ADD COLUMN IF NOT EXISTS snippet_s3_key TEXT;

-- Sync snippet_s3_key with s3_cache_key
UPDATE resource SET snippet_s3_key = s3_cache_key WHERE s3_cache_key IS NOT NULL;
UPDATE resource SET s3_cache_key = snippet_s3_key WHERE snippet_s3_key IS NOT NULL;

-- Add description column to resource table
ALTER TABLE resource ADD COLUMN IF NOT EXISTS description TEXT;

-- Step 3: Recreate service tables with correct references
-- Learning plans (for planner service)
CREATE TABLE IF NOT EXISTS learning_plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    plan_data JSONB NOT NULL,
    total_hours NUMERIC(10,2) NOT NULL,
    estimated_weeks INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_plans_user ON learning_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_plans_created ON learning_plans(created_at DESC);

-- Quizzes (for quiz service) - references resource table
CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_ids UUID[] NOT NULL,
    questions JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quizzes_created ON quizzes(created_at DESC);

-- Quiz attempts (for quiz service)
CREATE TABLE IF NOT EXISTS quiz_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    score NUMERIC(5,2) CHECK (score >= 0 AND score <= 100),
    answers JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON quiz_attempts(user_id);

-- Step 4: Update triggers
CREATE TRIGGER update_learning_plans_updated_at BEFORE UPDATE ON learning_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Add index for snippet_s3_key
CREATE INDEX IF NOT EXISTS idx_resource_snippet_s3_key ON resource(snippet_s3_key);

-- Comments
COMMENT ON TABLE resource IS 'Learning resources with metadata (unified table)';
COMMENT ON TABLE learning_plans IS 'AI-generated learning plans';
COMMENT ON TABLE quizzes IS 'Generated quizzes from resources';
COMMENT ON TABLE quiz_attempts IS 'User quiz attempts and results';
COMMENT ON COLUMN resource.s3_cache_key IS 'S3 key for cached content (legacy)';
COMMENT ON COLUMN resource.snippet_s3_key IS 'S3 key for content snippets (preferred)';
