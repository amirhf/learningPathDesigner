package middleware

import (
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/amirhf/learnpath-gateway/internal/common"
	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/gin-gonic/gin"
)

type jwtPayload struct {
	Sub         string                 `json:"sub"`
	AppMetadata map[string]interface{} `json:"app_metadata"`
	UserMetadata map[string]interface{} `json:"user_metadata"`
}

// Auth middleware extracts user and tenant info from JWT
func Auth(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			// Allow anonymous access for now, or block?
			// For reference architecture, let's allow but set anonymous context
			// c.Set("user_id", "anonymous")
			// c.Set("tenant_id", "global")
			// c.Next()
			// return
			
			// Actually, let's assume we want to enforce it, but handle missing header gracefully
			c.Next() 
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid_auth_header"})
			c.Abort()
			return
		}

		tokenString := parts[1]
		payload, err := parseJWTPayload(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid_token"})
			c.Abort()
			return
		}

		// Extract User ID
		userID := payload.Sub
		
		// Extract Tenant ID (convention: app_metadata.tenant_id, fallback to global)
		tenantID := "global"
		if tid, ok := payload.AppMetadata["tenant_id"].(string); ok && tid != "" {
			tenantID = tid
		}

		// Set in context (Gin context + request context)
		c.Set("user_id", userID)
		c.Set("tenant_id", tenantID)
		
		// Propagate to Request Context for clients/orchestrator
		ctx := common.WithUserID(c.Request.Context(), userID)
		ctx = common.WithTenantID(ctx, tenantID)
		c.Request = c.Request.WithContext(ctx)

		c.Next()
	}
}

func parseJWTPayload(tokenString string) (*jwtPayload, error) {
	parts := strings.Split(tokenString, ".")
	if len(parts) != 3 {
		return nil, http.ErrNoCookie // Just a generic error
	}

	// Decode payload (2nd part)
	payloadSegment := parts[1]
	
	// Base64 padding if needed
	if l := len(payloadSegment) % 4; l > 0 {
		payloadSegment += strings.Repeat("=", 4-l)
	}

	payloadBytes, err := base64.URLEncoding.DecodeString(payloadSegment)
	if err != nil {
		// Try std encoding if URL encoding fails
		payloadBytes, err = base64.StdEncoding.DecodeString(payloadSegment)
		if err != nil {
			return nil, err
		}
	}

	var payload jwtPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return nil, err
	}

	return &payload, nil
}
