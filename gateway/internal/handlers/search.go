package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/gin-gonic/gin"
)

// SearchRequest represents the search request payload
type SearchRequest struct {
	Query       string        `json:"query" binding:"required,min=1"`
	TopK        int           `json:"top_k,omitempty"`
	Rerank      bool          `json:"rerank,omitempty"`
	RerankTopN  int           `json:"rerank_top_n,omitempty"`
	Filters     *SearchFilter `json:"filters,omitempty"`
}

// SearchFilter represents search filters
type SearchFilter struct {
	Level          *int    `json:"level,omitempty"`
	MaxDurationMin *int    `json:"max_duration_min,omitempty"`
	Skills         []string `json:"skills,omitempty"`
	MediaType      *string  `json:"media_type,omitempty"`
	Provider       *string  `json:"provider,omitempty"`
}

// ResourceResult represents a search result
type ResourceResult struct {
	ResourceID   string   `json:"resource_id"`
	Title        string   `json:"title"`
	URL          string   `json:"url"`
	Provider     *string  `json:"provider,omitempty"`
	License      *string  `json:"license,omitempty"`
	DurationMin  *int     `json:"duration_min,omitempty"`
	Level        *int     `json:"level,omitempty"`
	Skills       []string `json:"skills"`
	MediaType    *string  `json:"media_type,omitempty"`
	Score        float64  `json:"score"`
	WhyRelevant  *string  `json:"why_relevant,omitempty"`
}

// SearchResponse represents the search response
type SearchResponse struct {
	Results    []ResourceResult `json:"results"`
	Query      string           `json:"query"`
	TotalFound int              `json:"total_found"`
	Reranked   bool             `json:"reranked"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}

// Search returns a search handler
func Search(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req SearchRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Set defaults
		if req.TopK == 0 {
			req.TopK = 20
		}
		if req.RerankTopN == 0 {
			req.RerankTopN = 5
		}
		// Default rerank to false to avoid timeout issues with model loading
		// Frontend can explicitly set to true if needed
		// Note: Rerank is currently disabled due to model loading time

		// Forward request to RAG service
		ragURL := fmt.Sprintf("%s/search", cfg.RAGServiceURL)
		
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
			ragURL,
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
		// Increased timeout to 60s to allow for model loading on cold start
		client := &http.Client{
			Timeout: 60 * time.Second,
		}
		resp, err := client.Do(httpReq)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, ErrorResponse{
				Error:   "service_unavailable",
				Message: "RAG service is unavailable",
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
					Error:   "rag_service_error",
					Message: string(body),
				})
			}
			return
		}

		// Parse response
		var searchResp SearchResponse
		if err := json.Unmarshal(body, &searchResp); err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "internal_error",
				Message: "Failed to parse response",
			})
			return
		}

		// Return response
		c.JSON(http.StatusOK, searchResp)
	}
}
