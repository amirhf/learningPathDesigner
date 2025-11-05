-- Learning Path Designer - Service Tables
-- Version: 002
-- Description: Additional tables for planner and quiz services

-- Skills table (simplified naming from skill to skills for consistency)
CREATE TABLE IF NOT EXISTS skills (
    skill_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    level_hint INT DEFAULT 0 CHECK (level_hint IN (0, 1, 2)),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_skills_slug ON skills(slug);
CREATE INDEX IF NOT EXISTS idx_skills_level ON skills(level_hint);

-- Resources table (simplified naming)
CREATE TABLE IF NOT EXISTS resources (
    resource_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    provider TEXT,
    license TEXT,
    duration_min INT CHECK (duration_min > 0),
    level INT CHECK (level IN (0, 1, 2)),
    skills UUID[] NOT NULL,
    media_type TEXT CHECK (media_type IN ('video', 'reading', 'interactive', 'audio', 'course')),
    snippet_s3_key TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resources_skills ON resources USING GIN(skills);
CREATE INDEX IF NOT EXISTS idx_resources_level ON resources(level);
CREATE INDEX IF NOT EXISTS idx_resources_media_type ON resources(media_type);

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

-- Quizzes (for quiz service)
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

-- Update triggers for new tables
CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_plans_updated_at BEFORE UPDATE ON learning_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE skills IS 'Skills and topics in the learning domain';
COMMENT ON TABLE resources IS 'Learning resources with metadata';
COMMENT ON TABLE learning_plans IS 'AI-generated learning plans';
COMMENT ON TABLE quizzes IS 'Generated quizzes from resources';
COMMENT ON TABLE quiz_attempts IS 'User quiz attempts and results';
