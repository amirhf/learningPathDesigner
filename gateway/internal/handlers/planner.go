package handlers

import (
	"fmt"
	"net/http"
	"io"
	"bytes"
	"encoding/json"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/common"
	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/amirhf/learnpath-gateway/internal/models"
	"github.com/amirhf/learnpath-gateway/internal/orchestrator"
	"github.com/gin-gonic/gin"
)

// PlanRequest represents the plan generation request
type PlanRequest struct {
	Goal            string   `json:"goal" binding:"required,min=1"`
	CurrentSkills   []string `json:"current_skills,omitempty"`
	TimeBudgetHours int      `json:"time_budget_hours" binding:"required,gt=0"`
	HoursPerWeek    int      `json:"hours_per_week" binding:"required,gt=0"`
	Preferences     map[string]interface{} `json:"preferences,omitempty"`
	UserID          string   `json:"user_id,omitempty"`
	// Optional fields for quiz generation
	GenerateQuiz   bool   `json:"generate_quiz,omitempty"`
	NumQuestions   int    `json:"num_questions,omitempty"`
	QuizDifficulty string `json:"quiz_difficulty,omitempty"`
}

// ReplanRequest represents the replan request
type ReplanRequest struct {
	PlanID           string   `json:"plan_id" binding:"required"`
	CompletedLessons []string `json:"completed_lessons"`
	Feedback         string   `json:"feedback,omitempty"`
}

// CreatePlan returns a handler for creating learning plans
func CreatePlan(cfg *config.Config, orch orchestrator.Orchestrator) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req PlanRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Convert preferences map[string]interface{} to map[string]string
		prefs := make(map[string]string)
		for k, v := range req.Preferences {
			prefs[k] = fmt.Sprintf("%v", v)
		}

		// Prepare orchestrator request
		// Default to generating quiz if not specified, or allow frontend to control
		generateQuiz := req.GenerateQuiz
		
		numQuestions := req.NumQuestions
		if numQuestions == 0 {
			numQuestions = 3 // Default
		}
		
		difficulty := req.QuizDifficulty
		if difficulty == "" {
			difficulty = "medium"
		}

		orchReq := models.OrchestrateFullFlowRequest{
			PlanLearningPathRequest: models.PlanLearningPathRequest{
				Goal:            req.Goal,
				CurrentSkills:   req.CurrentSkills,
				TimeBudgetHours: req.TimeBudgetHours,
				HoursPerWeek:    req.HoursPerWeek,
				Preferences:     prefs,
				UserID:          &req.UserID,
			},
			GenerateQuiz:   generateQuiz,
			NumQuestions:   numQuestions,
			QuizDifficulty: difficulty,
		}

		// Propagate Request ID to context
		ctx := c.Request.Context()
		if requestID := c.GetString("request_id"); requestID != "" {
			ctx = common.WithRequestID(ctx, requestID)
		}

		// Call Orchestrator
		result, err := orch.OrchestrateFullFlow(ctx, orchReq)
		if err != nil {
			// TODO: Differentiate between 400 (validation) and 500 (service) errors
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "orchestration_error",
				Message: err.Error(),
			})
			return
		}

		// Return response
		c.JSON(http.StatusOK, result)
	}
}

// GetPlan returns a handler for retrieving a plan
func GetPlan(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		planID := c.Param("id")
		if planID == "" {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: "Plan ID is required",
			})
			return
		}

		// Forward request to Planner service
		plannerURL := fmt.Sprintf("%s/plan/%s", cfg.PlannerServiceURL, planID)
		
		// Create HTTP request
		httpReq, err := http.NewRequestWithContext(
			c.Request.Context(),
			"GET",
			plannerURL,
			nil,
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to create request",
			})
			return
		}

		// Set headers
		if requestID := c.GetString("request_id"); requestID != "" {
			httpReq.Header.Set("X-Request-ID", requestID)
		}

		// Send request
		client := &http.Client{
			Timeout: 10 * time.Second,
		}
		resp, err := client.Do(httpReq)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, ErrorResponse{
				Error:   "service_unavailable",
				Message: "Planner service is unavailable",
			})
			return
		}
		defer resp.Body.Close()

		// Read response
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to read response",
			})
			return
		}

		// Check status code
		if resp.StatusCode != http.StatusOK {
			var errResp ErrorResponse
			if err := json.Unmarshal(body, &errResp); err == nil {
				c.JSON(resp.StatusCode, errResp)
			} else {
				c.JSON(resp.StatusCode, ErrorResponse{
					Error:   "planner_service_error",
					Message: string(body),
				})
			}
			return
		}

		// Parse and return response
		var planResp map[string]interface{}
		if err := json.Unmarshal(body, &planResp); err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to parse response",
			})
			return
		}

		// Return response
		c.JSON(http.StatusOK, planResp)
	}
}

// Replan returns a handler for replanning
func Replan(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req ReplanRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Forward request to Planner service
		plannerURL := fmt.Sprintf("%s/replan", cfg.PlannerServiceURL)
		
		// Marshal request
		reqBody, err := json.Marshal(req)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to marshal request",
			})
			return
		}

		// Create HTTP request
		httpReq, err := http.NewRequestWithContext(
			c.Request.Context(),
			"POST",
			plannerURL,
			bytes.NewBuffer(reqBody),
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to create request",
			})
			return
		}

		// Set headers
		httpReq.Header.Set("Content-Type", "application/json")
		if requestID := c.GetString("request_id"); requestID != "" {
			httpReq.Header.Set("X-Request-ID", requestID)
		}

		// Send request
		client := &http.Client{
			Timeout: 60 * time.Second,
		}
		resp, err := client.Do(httpReq)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, ErrorResponse{
				Error:   "service_unavailable",
				Message: "Planner service is unavailable",
			})
			return
		}
		defer resp.Body.Close()

		// Read response
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to read response",
			})
			return
		}

		// Check status code
		if resp.StatusCode != http.StatusOK {
			var errResp ErrorResponse
			if err := json.Unmarshal(body, &errResp); err == nil {
				c.JSON(resp.StatusCode, errResp)
			} else {
				c.JSON(resp.StatusCode, ErrorResponse{
					Error:   "planner_service_error",
					Message: string(body),
				})
			}
			return
		}

		// Parse and return response
		var replanResp map[string]interface{}
		if err := json.Unmarshal(body, &replanResp); err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to parse response",
			})
			return
		}

		// Return response
		c.JSON(http.StatusOK, replanResp)
	}
}

// GetUserPlans handles GET /api/plan/user/:user_id/plans
func GetUserPlans(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID := c.Param("user_id")
		
		if userID == "" {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: "user_id is required",
			})
			return
		}

		// Forward request to Planner service
		plannerURL := fmt.Sprintf("%s/user/%s/plans", cfg.PlannerServiceURL, userID)
		
		// Create HTTP request
		httpReq, err := http.NewRequestWithContext(
			c.Request.Context(),
			http.MethodGet,
			plannerURL,
			nil,
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to create request",
			})
			return
		}

		// Forward request
		client := &http.Client{Timeout: 30 * time.Second}
		resp, err := client.Do(httpReq)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, ErrorResponse{
				Error:   "service_unavailable",
				Message: "Planner service is unavailable",
			})
			return
		}
		defer resp.Body.Close()

		// Read response
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to read response",
			})
			return
		}

		// Check status code
		if resp.StatusCode != http.StatusOK {
			var errResp ErrorResponse
			if err := json.Unmarshal(body, &errResp); err == nil {
				c.JSON(resp.StatusCode, errResp)
			} else {
				c.JSON(resp.StatusCode, ErrorResponse{
					Error:   "planner_service_error",
					Message: string(body),
				})
			}
			return
		}

		// Parse and return response
		var plansResp map[string]interface{}
		if err := json.Unmarshal(body, &plansResp); err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to parse response",
			})
			return
		}

		c.JSON(http.StatusOK, plansResp)
	}
}
