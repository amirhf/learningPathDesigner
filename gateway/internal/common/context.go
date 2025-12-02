package common

import "context"

type contextKey string

const (
	RequestIDKey contextKey = "request_id"
	UserIDKey    contextKey = "user_id"
	TenantIDKey  contextKey = "tenant_id"
)

// WithRequestID returns a new context with the given RequestID.
func WithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, RequestIDKey, requestID)
}

// GetRequestID retrieves the RequestID from the context.
func GetRequestID(ctx context.Context) string {
	if val, ok := ctx.Value(RequestIDKey).(string); ok {
		return val
	}
	return ""
}

// WithUserID returns a new context with the given UserID.
func WithUserID(ctx context.Context, userID string) context.Context {
	return context.WithValue(ctx, UserIDKey, userID)
}

// GetUserID retrieves the UserID from the context.
func GetUserID(ctx context.Context) string {
	if val, ok := ctx.Value(UserIDKey).(string); ok {
		return val
	}
	return ""
}

// WithTenantID returns a new context with the given TenantID.
func WithTenantID(ctx context.Context, tenantID string) context.Context {
	return context.WithValue(ctx, TenantIDKey, tenantID)
}

// GetTenantID retrieves the TenantID from the context.
func GetTenantID(ctx context.Context) string {
	if val, ok := ctx.Value(TenantIDKey).(string); ok {
		return val
	}
	return ""
}
