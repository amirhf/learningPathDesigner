package clients

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/models"
	"github.com/google/uuid"
)

// PlannerClient defines the interface for interacting with the Planner service.
type PlannerClient interface {
	CreatePlan(ctx context.Context, req models.PlanLearningPathRequest) (*models.LearningPath, error)
	GetPlan(ctx context.Context, planID uuid.UUID) (*models.LearningPath, error)
	GetUserPlans(ctx context.Context, userID string) ([]models.LearningPath, error)
	Replan(ctx context.Context, planID uuid.UUID, req ReplanRequest) (*models.LearningPath, error)
}

type plannerClient struct {
	client  *http.Client
	baseURL string
}

// NewPlannerClient creates a new Planner client.
func NewPlannerClient(baseURL string) PlannerClient {
	return &plannerClient{
		client: &http.Client{
			Timeout: 2 * time.Minute, // Planner operations can be long-running
		},
		baseURL: baseURL,
	}
}

// ReplanRequest mirrors the Python Planner service's ReplanRequest.
type ReplanRequest struct {
	CompletedResources []uuid.UUID `json:"completed_resources"`
	TimeSpentHours     float64     `json:"time_spent_hours"`
	RemainingTimeHours *float64    `json:"remaining_time_hours,omitempty"`
	Feedback           *string     `json:"feedback,omitempty"`
}


// CreatePlan sends a request to the Planner service to create a new learning plan.
func (c *plannerClient) CreatePlan(ctx context.Context, req models.PlanLearningPathRequest) (*models.LearningPath, error) {
	jsonReq, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Planner create plan request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/plan", c.baseURL), bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("failed to create Planner create plan request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Planner create plan request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Planner create plan service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	// DEBUG: Read response body to debug invalid UUID length error
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	fmt.Printf("DEBUG: Planner Response Body: %s\n", string(bodyBytes))
	// Restore body for decoder
	resp.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	var planResp models.LearningPath
	if err := json.NewDecoder(resp.Body).Decode(&planResp); err != nil {
		return nil, fmt.Errorf("failed to decode Planner create plan response: %w", err)
	}

	return &planResp, nil
}

// GetPlan sends a request to the Planner service to retrieve a learning plan by ID.
func (c *plannerClient) GetPlan(ctx context.Context, planID uuid.UUID) (*models.LearningPath, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/plan/%s", c.baseURL, planID.String()), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create Planner get plan request: %w", err)
	}

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Planner get plan request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Planner get plan service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var planResp models.LearningPath
	if err := json.NewDecoder(resp.Body).Decode(&planResp); err != nil {
		return nil, fmt.Errorf("failed to decode Planner get plan response: %w", err)
	}

	return &planResp, nil
}

// GetUserPlans sends a request to the Planner service to retrieve all learning plans for a user.
func (c *plannerClient) GetUserPlans(ctx context.Context, userID string) ([]models.LearningPath, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/plan/user/%s/plans", c.baseURL, userID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create Planner get user plans request: %w", err)
	}

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Planner get user plans request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Planner get user plans service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var plansResp []models.LearningPath
	if err := json.NewDecoder(resp.Body).Decode(&plansResp); err != nil {
		return nil, fmt.Errorf("failed to decode Planner get user plans response: %w", err)
	}

	return plansResp, nil
}

// Replan sends a request to the Planner service to replan an existing learning plan.
func (c *plannerClient) Replan(ctx context.Context, planID uuid.UUID, req ReplanRequest) (*models.LearningPath, error) {
	jsonReq, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Planner replan request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/plan/%s/replan", c.baseURL, planID.String()), bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("failed to create Planner replan request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Planner replan request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Planner replan service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var replanResp models.LearningPath
	if err := json.NewDecoder(resp.Body).Decode(&replanResp); err != nil {
		return nil, fmt.Errorf("failed to decode Planner replan response: %w", err)
	}

	return &replanResp, nil
}