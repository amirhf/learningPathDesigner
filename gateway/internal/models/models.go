package models

import (
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// Shared Models (Go Structs)
// These define the canonical representation of data throughout the system.
// ============================================================================

type ResourceResult struct {
	ID           uuid.UUID `json:"id"`
	Title        string    `json:"title"`
	URL          string    `json:"url"`
	Provider     *string   `json:"provider,omitempty"`
	License      *string   `json:"license,omitempty"`
	DurationMin  *int      `json:"duration_min,omitempty"`
	Level        *int      `json:"level,omitempty"`
	Skills       []string  `json:"skills"`
	MediaType    *string   `json:"media_type,omitempty"`
	Description  *string   `json:"description,omitempty"`
	Score        *float64  `json:"score,omitempty"`
	SnippetS3Key *string   `json:"snippet_s3_key,omitempty"`
}

type SearchResponse struct {
	Results    []ResourceResult `json:"results"`
	Query      string           `json:"query"`
	TotalFound int              `json:"total_found"`
	Reranked   bool             `json:"reranked"`
}

type ResourceItem struct {
	ResourceID   uuid.UUID `json:"resource_id"`
	Title        string    `json:"title"`
	URL          string    `json:"url"`
	DurationMin  int       `json:"duration_min"`
	Level        *int      `json:"level,omitempty"`
	Skills       []string  `json:"skills"`
	WhyIncluded  string    `json:"why_included"`
	Order        int       `json:"order"`
}

type Milestone struct {
	MilestoneID    uuid.UUID      `json:"milestone_id"`
	Title          string         `json:"title"`
	Description    string         `json:"description"`
	Resources      []ResourceItem `json:"resources"`
	EstimatedHours float64        `json:"estimated_hours"`
	SkillsGained   []string       `json:"skills_gained"`
	Order          int            `json:"order"`
}

type LearningPath struct {
	PlanID          uuid.UUID   `json:"plan_id"`
	Goal            string      `json:"goal"`
	TotalHours      float64     `json:"total_hours"`
	EstimatedWeeks  int         `json:"estimated_weeks"`
	Milestones      []Milestone `json:"milestones"`
	PrerequisitesMet bool        `json:"prerequisites_met"`
	Reasoning       string      `json:"reasoning"`
	CreatedAt       time.Time   `json:"created_at"`
	UpdatedAt       time.Time   `json:"updated_at"`
}

type QuizOption struct {
	OptionID  string `json:"option_id"`
	Text      string `json:"text"`
	IsCorrect bool   `json:"is_correct"` // Hidden from external responses, used internally for grading
}

type QuizQuestion struct {
	QuestionID       string       `json:"question_id"`
	QuestionText     string       `json:"question_text"`
	Options          []QuizOption `json:"options"`
	Explanation      string       `json:"explanation"`
	SourceResourceID string       `json:"source_resource_id"`
	Citation         string       `json:"citation"`
}

type Quiz struct {
	QuizID        string         `json:"quiz_id"`
	Title         *string        `json:"title,omitempty"`
	Questions     []QuizQuestion `json:"questions"`
	TotalQuestions int            `json:"total_questions"`
	CreatedAt     time.Time      `json:"created_at"`
}

type LearningPathWithQuiz struct {
	LearningPath LearningPath `json:"learning_path"`
	Quiz         *Quiz        `json:"quiz,omitempty"`
}

// QuestionResult used in QuizSubmitResponse
type QuestionResult struct {
	QuestionID      string `json:"question_id"`
	Correct         bool   `json:"correct"`
	SelectedOptionID string `json:"selected_option_id"`
	CorrectOptionID string `json:"correct_option_id"`
	Explanation     string `json:"explanation"`
	Citation        string `json:"citation"`
}

// ============================================================================
// Request Models
// ============================================================================

type PlanLearningPathRequest struct {
	Goal            string            `json:"goal"`
	CurrentSkills   []string          `json:"current_skills"`
	TimeBudgetHours int               `json:"time_budget_hours"`
	HoursPerWeek    int               `json:"hours_per_week"`
	Preferences     map[string]string `json:"preferences"` // e.g., media types, providers
	UserID          *string           `json:"user_id,omitempty"`
}

// GenerateQuizRequest represents the request to generate a quiz.
type GenerateQuizRequest struct {
	ResourceIDs  []string `json:"resource_ids"`
	NumQuestions int      `json:"num_questions"`
	Difficulty   string   `json:"difficulty"`
	UserID       *string  `json:"user_id,omitempty"`
}

// IngestRequest represents the request to ingest content URLs.
type IngestRequest struct {
	URLs []string `json:"urls" binding:"required,min=1"`
}

type OrchestrateFullFlowRequest struct {
	PlanLearningPathRequest
	GenerateQuiz  bool `json:"generate_quiz"`
	NumQuestions  int  `json:"num_questions"`
	QuizDifficulty string `json:"quiz_difficulty"`
}

type OrchestrateFullFlowResponse struct {
	LearningPath *LearningPath `json:"learning_path"`
	Quiz         *Quiz         `json:"quiz,omitempty"`
	Error        *string       `json:"error,omitempty"`
}