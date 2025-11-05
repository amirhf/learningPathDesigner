package handlers

import (
	"net/http"

	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/gin-gonic/gin"
)

// HealthResponse represents the health check response
type HealthResponse struct {
	Status  string            `json:"status"`
	Service string            `json:"service"`
	Version string            `json:"version"`
	Services map[string]string `json:"services"`
}

// HealthCheck returns a health check handler
func HealthCheck(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, HealthResponse{
			Status:  "healthy",
			Service: "gateway",
			Version: "1.0.0",
			Services: map[string]string{
				"rag":     cfg.RAGServiceURL,
				"planner": cfg.PlannerServiceURL,
				"quiz":    cfg.QuizServiceURL,
			},
		})
	}
}
