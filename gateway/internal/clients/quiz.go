package clients

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/models"
)

// QuizClient defines the interface for interacting with the Quiz service.
type QuizClient interface {
	GenerateQuiz(ctx context.Context, req models.GenerateQuizRequest) (*models.Quiz, error)
	SubmitQuiz(ctx context.Context, req QuizSubmitRequest) (*QuizSubmitResponse, error)
}

type quizClient struct {
	client  *http.Client
	baseURL string
}

// NewQuizClient creates a new Quiz client.
func NewQuizClient(baseURL string) QuizClient {
	return &quizClient{
		client: &http.Client{
			Timeout: 1 * time.Minute, // Default timeout for quiz operations
		},
		baseURL: baseURL,
	}
}

// QuizSubmitRequest mirrors the Python Quiz service's QuizSubmitRequest.
type QuizSubmitRequest struct {
	QuizID  string       `json:"quiz_id"`
	Answers []QuizAnswer `json:"answers"`
}

// QuizAnswer mirrors the Python Quiz service's QuizAnswer.
type QuizAnswer struct {
	QuestionID      string `json:"question_id"`
	SelectedOptionID string `json:"selected_option_id"`
}

// QuizSubmitResponse mirrors the Python Quiz service's QuizSubmitResponse.
type QuizSubmitResponse struct {
	QuizID         string                      `json:"quiz_id"`
	Score          float64                     `json:"score"`
	TotalQuestions int                         `json:"total_questions"`
	CorrectAnswers int                         `json:"correct_answers"`
	Results        []models.QuestionResult     `json:"results"`
}

// GenerateQuiz sends a request to the Quiz service to generate a new quiz.
func (c *quizClient) GenerateQuiz(ctx context.Context, req models.GenerateQuizRequest) (*models.Quiz, error) {
	jsonReq, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Quiz generate request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/generate", c.baseURL), bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("failed to create Quiz generate request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Quiz generate request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Quiz generate service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var quizResp models.Quiz
	if err := json.NewDecoder(resp.Body).Decode(&quizResp); err != nil {
		return nil, fmt.Errorf("failed to decode Quiz generate response: %w", err)
	}

	return &quizResp, nil
}

// SubmitQuiz sends a request to the Quiz service to submit answers and get results.
func (c *quizClient) SubmitQuiz(ctx context.Context, req QuizSubmitRequest) (*QuizSubmitResponse, error) {
	jsonReq, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Quiz submit request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/submit", c.baseURL), bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("failed to create Quiz submit request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send Quiz submit request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("Quiz submit service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var submitResp QuizSubmitResponse
	if err := json.NewDecoder(resp.Body).Decode(&submitResp); err != nil {
		return nil, fmt.Errorf("failed to decode Quiz submit response: %w", err)
	}

	return &submitResp, nil
}