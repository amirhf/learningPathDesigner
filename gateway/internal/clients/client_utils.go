package clients

import (
	"fmt"
	"math"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/common"
)

const (
	defaultRetryAttempts = 3
	defaultRetryWait     = 500 * time.Millisecond
)

// doRequestWithRetries executes an HTTP request with retries and correlation ID injection.
func doRequestWithRetries(client *http.Client, req *http.Request) (*http.Response, error) {
	// 1. Inject Correlation ID
	requestID := common.GetRequestID(req.Context())
	if requestID != "" {
		req.Header.Set("X-Request-ID", requestID)
	}

	var resp *http.Response
	var err error

	// 2. Retry Loop
	for i := 0; i < defaultRetryAttempts; i++ {
		if i > 0 {
			// Exponential backoff
			backoff := time.Duration(float64(defaultRetryWait) * math.Pow(2, float64(i-1)))
			select {
			case <-req.Context().Done():
				return nil, req.Context().Err()
			case <-time.After(backoff):
			}
		}

		// Clone request body if needed (for retries) - usually handled by GetBody,
		// but standard http.Request.GetBody is set for bytes.Buffer/strings.Reader.
		if i > 0 && req.GetBody != nil {
			newBody, err := req.GetBody()
			if err != nil {
				return nil, fmt.Errorf("failed to reset request body: %w", err)
			}
			req.Body = newBody
		}
		
		resp, err = client.Do(req)
		
		// Check for network errors or 5xx status codes
		if err != nil {
			continue // Network error, retry
		}

		if resp.StatusCode >= 500 {
			resp.Body.Close() // Close body before retrying
			err = fmt.Errorf("server error: %d", resp.StatusCode)
			continue
		}

		// If 4xx or 2xx, return immediately (don't retry client errors)
		return resp, nil
	}

	// Return last error if all retries failed
	if err != nil {
		return nil, fmt.Errorf("request failed after %d attempts: %w", defaultRetryAttempts, err)
	}
	return resp, nil
}
