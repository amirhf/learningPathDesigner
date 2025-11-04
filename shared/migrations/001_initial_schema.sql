-- Learning Path Designer - Initial Schema
-- Version: 001
-- Description: Core tables for skills, resources, users, goals, plans, lessons, and progress

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Skills and prerequisites
CREATE TABLE skill (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    level_hint INT DEFAULT 0 CHECK (level_hint IN (0, 1, 2)),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_slug ON skill(slug);
CREATE INDEX idx_skill_level ON skill(level_hint);

-- Skill prerequisites (directed graph)
CREATE TABLE skill_edge (
    from_skill UUID REFERENCES skill(id) ON DELETE CASCADE,
    to_skill UUID REFERENCES skill(id) ON DELETE CASCADE,
    PRIMARY KEY (from_skill, to_skill),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_edge_from ON skill_edge(from_skill);
CREATE INDEX idx_skill_edge_to ON skill_edge(to_skill);

-- Resource catalog (metadata; vectors live in Qdrant)
CREATE TABLE resource (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    provider TEXT,
    license TEXT,
    duration_min INT CHECK (duration_min > 0),
    level INT CHECK (level IN (0, 1, 2)),
    skills UUID[] NOT NULL,
    recency_date DATE,
    s3_cache_key TEXT,
    media_type TEXT CHECK (media_type IN ('video', 'reading', 'interactive', 'audio', 'course')),
    popularity NUMERIC(5,2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_resource_skills ON resource USING GIN(skills);
CREATE INDEX idx_resource_level ON resource(level);
CREATE INDEX idx_resource_media_type ON resource(media_type);
CREATE INDEX idx_resource_provider ON resource(provider);

-- Users
CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    cognito_sub TEXT UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_app_user_email ON app_user(email);
CREATE INDEX idx_app_user_cognito_sub ON app_user(cognito_sub);

-- Learning goals
CREATE TABLE goal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    target_date DATE,
    hours_per_week INT CHECK (hours_per_week > 0),
    level INT CHECK (level IN (0, 1, 2)),
    prefs JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_goal_user ON goal(user_id);
CREATE INDEX idx_goal_target_date ON goal(target_date);

-- Learning plans
CREATE TABLE plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID REFERENCES goal(id) ON DELETE CASCADE,
    total_weeks INT NOT NULL CHECK (total_weeks > 0),
    share_token TEXT UNIQUE,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_plan_goal ON plan(goal_id);
CREATE INDEX idx_plan_share_token ON plan(share_token) WHERE share_token IS NOT NULL;

-- Lessons within plans
CREATE TABLE lesson (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES plan(id) ON DELETE CASCADE,
    week INT NOT NULL CHECK (week > 0),
    seq INT NOT NULL CHECK (seq >= 0),
    title TEXT NOT NULL,
    resource_ids UUID[] NOT NULL,
    est_minutes INT CHECK (est_minutes > 0),
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(plan_id, week, seq)
);

CREATE INDEX idx_lesson_plan ON lesson(plan_id);
CREATE INDEX idx_lesson_week ON lesson(plan_id, week, seq);

-- Progress tracking
CREATE TABLE progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID REFERENCES lesson(id) ON DELETE CASCADE,
    user_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'done', 'skipped')),
    actual_minutes INT CHECK (actual_minutes >= 0),
    quiz_score NUMERIC(5,2) CHECK (quiz_score >= 0 AND quiz_score <= 100),
    notes TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(lesson_id, user_id)
);

CREATE INDEX idx_progress_lesson ON progress(lesson_id);
CREATE INDEX idx_progress_user ON progress(user_id);
CREATE INDEX idx_progress_status ON progress(status);

-- Quizzes
CREATE TABLE quiz (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID REFERENCES lesson(id) ON DELETE CASCADE,
    items JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_quiz_lesson ON quiz(lesson_id);

-- Quiz attempts
CREATE TABLE quiz_attempt (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quiz(id) ON DELETE CASCADE,
    user_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    score NUMERIC(5,2) CHECK (score >= 0 AND score <= 100),
    feedback JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_quiz_attempt_quiz ON quiz_attempt(quiz_id);
CREATE INDEX idx_quiz_attempt_user ON quiz_attempt(user_id);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_skill_updated_at BEFORE UPDATE ON skill
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resource_updated_at BEFORE UPDATE ON resource
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goal_updated_at BEFORE UPDATE ON goal
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plan_updated_at BEFORE UPDATE ON plan
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_progress_updated_at BEFORE UPDATE ON progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE skill IS 'Skills and topics in the learning domain';
COMMENT ON TABLE skill_edge IS 'Prerequisite relationships between skills';
COMMENT ON TABLE resource IS 'Learning resources (articles, videos, courses)';
COMMENT ON TABLE app_user IS 'Application users';
COMMENT ON TABLE goal IS 'User learning goals';
COMMENT ON TABLE plan IS 'Generated learning plans';
COMMENT ON TABLE lesson IS 'Individual lessons within a plan';
COMMENT ON TABLE progress IS 'User progress on lessons';
COMMENT ON TABLE quiz IS 'Generated quizzes for lessons';
COMMENT ON TABLE quiz_attempt IS 'User quiz attempts and scores';
