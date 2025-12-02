package handlers

import (
	"net/http"

	"github.com/amirhf/learnpath-gateway/internal/common"
	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/amirhf/learnpath-gateway/internal/models"
	"github.com/amirhf/learnpath-gateway/internal/orchestrator"
	"github.com/gin-gonic/gin"
)

// IngestContentRequest represents the request body for content ingestion
type IngestContentRequest struct {
	URLs []string `json:"urls" binding:"required,min=1"`
}

// IngestContent handler
func IngestContent(cfg *config.Config, orch orchestrator.Orchestrator) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req IngestContentRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Propagate context
		ctx := c.Request.Context()
		if requestID := c.GetString("request_id"); requestID != "" {
			ctx = common.WithRequestID(ctx, requestID)
		}
		if tenantID := c.GetString("tenant_id"); tenantID != "" {
			ctx = common.WithTenantID(ctx, tenantID)
		} else {
			// Should default to global if not set, but for BYO Content,
			// if no tenant is set (anonymous), maybe we should forbid it?
			// Or allow it and it goes to "global"?
			// Let's allow it for now, but typically BYO is for a specific tenant.
			ctx = common.WithTenantID(ctx, "global")
		}

		orchReq := models.IngestRequest{
			URLs: req.URLs,
		}

		if err := orch.IngestContent(ctx, orchReq); err != nil {
			c.JSON(http.StatusInternalServerError, ErrorResponse{
				Error:   "ingestion_failed",
				Message: err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "Content ingestion started successfully",
			"count":   len(req.URLs),
		})
	}
}
