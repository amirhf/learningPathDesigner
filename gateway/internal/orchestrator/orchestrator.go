package orchestrator

import (
	"context"
	"fmt"

	"github.com/amirhf/learnpath-gateway/internal/clients"
	"github.com/amirhf/learnpath-gateway/internal/models"
)

// ============================================================================
// Orchestrator Service Interface
// ============================================================================

type Orchestrator interface {
	PlanLearningPath(ctx context.Context, req models.PlanLearningPathRequest) (*models.LearningPath, error)
	GenerateQuiz(ctx context.Context, req models.GenerateQuizRequest) (*models.Quiz, error)
	OrchestrateFullFlow(ctx context.Context, req models.OrchestrateFullFlowRequest) (*models.LearningPathWithQuiz, error)
	IngestContent(ctx context.Context, req models.IngestRequest) error
}

// NewOrchestrator creates a new Orchestrator instance.
func NewOrchestrator(ragBaseURL, plannerBaseURL, quizBaseURL string) Orchestrator {
	return &orchestratorService{
		ragClient:    clients.NewRAGClient(ragBaseURL),
		plannerClient: clients.NewPlannerClient(plannerBaseURL),
		quizClient:   clients.NewQuizClient(quizBaseURL),
	}
}

// orchestratorService implements the Orchestrator interface.
type orchestratorService struct {
	ragClient    clients.RAGClient
	plannerClient clients.PlannerClient
	quizClient   clients.QuizClient
}

// PlanLearningPath orchestrates the creation of a learning path.
func (s *orchestratorService) PlanLearningPath(ctx context.Context, req models.PlanLearningPathRequest) (*models.LearningPath, error) {
	learningPath, err := s.plannerClient.CreatePlan(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to create learning plan: %w", err)
	}
	return learningPath, nil
}

// GenerateQuiz orchestrates the generation of a quiz for a given learning path.
func (s *orchestratorService) GenerateQuiz(ctx context.Context, req models.GenerateQuizRequest) (*models.Quiz, error) {
	generatedQuiz, err := s.quizClient.GenerateQuiz(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to generate quiz: %w", err)
	}
	return generatedQuiz, nil
}

// OrchestrateFullFlow orchestrates the entire process of generating a learning path and an associated quiz.
func (s *orchestratorService) OrchestrateFullFlow(ctx context.Context, req models.OrchestrateFullFlowRequest) (*models.LearningPathWithQuiz, error) {
	// 1. Call RAG service to get relevant resources
	ragSearchReq := clients.SearchRequest{
		Query: req.Goal,
		TopK:  10, // Default for now, can be made configurable
		Rerank: true,
		RerankTopN: 5, // Default for now
		Filters: &clients.SearchFilters{
			Skills: req.CurrentSkills,
			// TODO: Add other filters from req.Preferences if applicable
		},
	}

	_, err := s.ragClient.Search(ctx, ragSearchReq)
	if err != nil {
		return nil, fmt.Errorf("failed to search RAG resources: %w", err)
	}

	// 2. Prepare Planner request with RAG results (if any)
	// Currently, Planner service doesn't take RAG results directly,
	// it relies on its own RAG call based on skills and goal.
	// This might be a point for future refactoring if the planner needs explicit context.
	plannerReq := models.PlanLearningPathRequest{
		Goal:            req.Goal,
		CurrentSkills:   req.CurrentSkills,
		TimeBudgetHours: req.TimeBudgetHours,
		HoursPerWeek:    req.HoursPerWeek,
		Preferences:     req.Preferences,
		UserID:          req.UserID,
	}

	// 3. Call Planner service to create the learning path
	learningPath, err := s.plannerClient.CreatePlan(ctx, plannerReq)
	if err != nil {
		return nil, fmt.Errorf("failed to create learning plan: %w", err)
	}

	// 4. Optionally call Quiz service to generate a quiz
	var quiz *models.Quiz
	if req.GenerateQuiz {
		// Extract resource IDs from the generated learning path for quiz generation
		var resourceIDs []string
		for _, milestone := range learningPath.Milestones {
			for _, resource := range milestone.Resources {
				resourceIDs = append(resourceIDs, resource.ResourceID.String())
			}
		}

		if len(resourceIDs) == 0 {
			// Even if GenerateQuiz is true, if no resources, then no quiz.
			// This is a business logic decision.
			// Could also return an error or a quiz with a warning.
			// For now, let's just not generate a quiz.
			quiz = nil
		} else {
			quizReq := models.GenerateQuizRequest{
				ResourceIDs:  resourceIDs,
				NumQuestions: req.NumQuestions,
				Difficulty:   req.QuizDifficulty,
				UserID:       req.UserID,
			}

			generatedQuiz, err := s.quizClient.GenerateQuiz(ctx, quizReq)
			if err != nil {
				return nil, fmt.Errorf("failed to generate quiz: %w", err)
			}
			quiz = generatedQuiz
		}
	}

	return &models.LearningPathWithQuiz{
		LearningPath: *learningPath,
		Quiz:         quiz,
	}, nil
}

// IngestContent orchestrates the ingestion of content URLs.
func (s *orchestratorService) IngestContent(ctx context.Context, req models.IngestRequest) error {
	// Directly forward to RAG client's ingestion
	// In future, this could involve validation, quota checking, etc.
	return s.ragClient.IngestResources(ctx, req.URLs)
}

// ============================================================================
// Explicit Agent Patterns (Placeholder)
// This will be expanded in future steps for PlannerExecutorAgent abstraction.
// ============================================================================

// PlannerExecutorAgent defines an interface for an agent that plans and executes steps.
type PlannerExecutorAgent interface {
	Plan(ctx context.Context, goal string, constraints map[string]string) (interface{}, error)
	Execute(ctx context.Context, plan interface{}) (interface{}, error)
	Refine(ctx context.Context, plan interface{}, feedback interface{}) (interface{}, error)
}

// VerifierAgent defines an interface for an agent that verifies outputs.
type VerifierAgent interface {
	VerifyLearningPath(ctx context.Context, lp models.LearningPath) (bool, []string, error) // Returns true if valid, list of issues
	VerifyQuiz(ctx context.Context, quiz models.Quiz) (bool, []string, error)
}