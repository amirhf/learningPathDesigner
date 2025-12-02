package clients

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/common"
	"github.com/amirhf/learnpath-gateway/internal/models"
)

// RAGClient defines the interface for interacting with the RAG service.
type RAGClient interface {
	Search(ctx context.Context, req SearchRequest) (*models.SearchResponse, error)
	IngestResources(ctx context.Context, urls []string) error
	// TODO: Add other RAG service methods if needed, like Embed, Rerank
}

type ragClient struct {
	client  *http.Client
	baseURL string
}

// NewRAGClient creates a new RAG client.
func NewRAGClient(baseURL string) RAGClient {
	return &ragClient{
		client: &http.Client{
			Timeout: 10 * time.Second, // Default timeout for RAG operations
		},
		baseURL: baseURL,
	}
}

// SearchRequest mirrors the Python RAG service's SearchRequest.
type SearchRequest struct {
	Query string `json:"query"`
	TopK  int    `json:"top_k,omitempty"`
	Rerank bool  `json:"rerank,omitempty"`
	RerankTopN int `json:"rerank_top_n,omitempty"`
	Filters *SearchFilters `json:"filters,omitempty"`
	TenantID string `json:"tenant_id,omitempty"`
}

// SearchFilters mirrors the Python RAG service's SearchFilters.
type SearchFilters struct {
	Skills       []string `json:"skills,omitempty"`
	MediaTypes   []string `json:"media_types,omitempty"`
	Levels       []int    `json:"levels,omitempty"`
	Providers    []string `json:"providers,omitempty"`
	MinDuration  *int     `json:"min_duration,omitempty"`
	MaxDuration  *int     `json:"max_duration,omitempty"`
	ExcludeURLs  []string `json:"exclude_urls,omitempty"`
}

// IngestResource mirrors the Python RAG service's Resource model for ingestion.
type IngestResource struct {
	Title       string   `json:"title"`
	URL         string   `json:"url"`
	Provider    string   `json:"provider,omitempty"`
	TenantID    string   `json:"tenant_id,omitempty"`
	// Other fields optional/default
}

// IngestRequest mirrors the Python RAG service's IngestResourcesRequest.
type IngestRequestPayload struct {
	Resources          []IngestResource `json:"resources"`
	GenerateEmbeddings bool             `json:"generate_embeddings"`
	ExtractContent     bool             `json:"extract_content"`
}


// Search sends a search request to the RAG service.
func (c *ragClient) Search(ctx context.Context, req SearchRequest) (*models.SearchResponse, error) {
	// Inject Tenant ID from context if not set
	if req.TenantID == "" {
		req.TenantID = common.GetTenantID(ctx)
	}

	jsonReq, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal RAG search request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/search", c.baseURL), bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("failed to create RAG search request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := doRequestWithRetries(c.client, httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send RAG search request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return nil, fmt.Errorf("RAG search service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	var searchResp models.SearchResponse
	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		return nil, fmt.Errorf("failed to decode RAG search response: %w", err)
	}

	return &searchResp, nil
}

// IngestResources sends resources to be ingested.
func (c *ragClient) IngestResources(ctx context.Context, urls []string) error {
	tenantID := common.GetTenantID(ctx)
	if tenantID == "" {
		tenantID = "global" // Fallback if not set (though handler should ensure it)
	}

	resources := make([]IngestResource, len(urls))
	for i, url := range urls {
		resources[i] = IngestResource{
			Title:    url, // Temporary title, assume backend extracts or user updates later
			URL:      url,
			TenantID: tenantID,
		}
	}

	payload := IngestRequestPayload{
		Resources:          resources,
		GenerateEmbeddings: true,
		ExtractContent:     true,
	}

	jsonReq, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal ingest request: %w", err)
	}

	// Increase timeout for ingestion as it involves scraping/embedding
	client := &http.Client{Timeout: 60 * time.Second} 
	
	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/ingest/resources", c.baseURL), bytes.NewBuffer(jsonReq))
	if err != nil {
		return fmt.Errorf("failed to create ingest request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send ingest request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errRes map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errRes)
		return fmt.Errorf("ingest service returned non-OK status: %d, error: %v", resp.StatusCode, errRes)
	}

	return nil
}