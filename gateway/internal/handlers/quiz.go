package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/common"
	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/amirhf/learnpath-gateway/internal/models"
	"github.com/amirhf/learnpath-gateway/internal/orchestrator"
	"github.com/gin-gonic/gin"
)

// QuizGenerateRequest represents quiz generation request
type QuizGenerateRequest struct {
	ResourceIDs  []string `json:"resource_ids" binding:"required,min=1"`
	NumQuestions int      `json:"num_questions,omitempty"`
	Difficulty   string   `json:"difficulty,omitempty"`
}

// QuizSubmitRequest represents quiz submission
type QuizSubmitRequest struct {
	QuizID  string       `json:"quiz_id" binding:"required"`
	Answers []QuizAnswer `json:"answers" binding:"required"`
}

// QuizAnswer represents a single answer
type QuizAnswer struct {
	QuestionID       string `json:"question_id"`
	SelectedOptionID string `json:"selected_option_id"`
}

// GenerateQuiz uses the orchestrator to generate a quiz
func GenerateQuiz(cfg *config.Config, orch orchestrator.Orchestrator) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req QuizGenerateRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Set defaults
		if req.NumQuestions == 0 {
			req.NumQuestions = 5
		}
		if req.Difficulty == "" {
			req.Difficulty = "medium"
		}

		// Propagate Request ID to context
		ctx := c.Request.Context()
		if requestID := c.GetString("request_id"); requestID != "" {
			ctx = common.WithRequestID(ctx, requestID)
		}

		// Use Orchestrator
		orchReq := models.GenerateQuizRequest{
			ResourceIDs:  req.ResourceIDs,
			NumQuestions: req.NumQuestions,
			Difficulty:   req.Difficulty,
			// UserID from auth middleware if available, otherwise empty/nil
		}

		quiz, err := orch.GenerateQuiz(ctx, orchReq)
		if err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "quiz_generation_error",
				Message: err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, quiz)
	}
}

// SubmitQuiz proxies quiz submission to quiz service
func SubmitQuiz(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req QuizSubmitRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Forward to quiz service
		quizURL := fmt.Sprintf("%s/submit", cfg.QuizServiceURL)
		proxyRequest(c, quizURL, req, 30*time.Second)
	}
}

// proxyRequest is a helper to forward requests to backend services
func proxyRequest(c *gin.Context, serviceURL string, payload interface{}, timeout time.Duration) {
	// Marshal request
	reqBody, err := json.Marshal(payload)
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
		serviceURL,
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
		Timeout: timeout,
	}
	resp, err := client.Do(httpReq)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, ErrorResponse{
			Error:   "service_unavailable",
			Message: "Quiz service is unavailable",
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
				Error:   "quiz_service_error",
				Message: string(body),
			})
		}
		return
	}

	// Forward response with correct content type
	c.Data(resp.StatusCode, "application/json", body)
}
