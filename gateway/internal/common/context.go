package common

import "context"

type contextKey string

const (
	RequestIDKey contextKey = "request_id"
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
