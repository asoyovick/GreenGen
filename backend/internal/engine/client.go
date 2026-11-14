package engine

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

// Client integrates with the Python scientific engine/service (Member 3).
// Go must not perform scientific calculations or fabricate results.
type Client interface {
	SubmitAnalysis(ctx context.Context, req AnalysisRequest) (*AnalysisAccepted, error)
	GetStatus(ctx context.Context, executionID string) (*AnalysisStatus, error)
}

type Bounds struct {
	MinLon float64 `json:"min_lon"`
	MinLat float64 `json:"min_lat"`
	MaxLon float64 `json:"max_lon"`
	MaxLat float64 `json:"max_lat"`
}

type Period struct {
	Start string `json:"start"`
	End   string `json:"end"`
}

// AnalysisRequest is a draft contract payload (see docs/API_CONTRACTS.md, subject to agreement).
type AnalysisRequest struct {
	ExecutionID     string         `json:"execution_id,omitempty"`
	InvestigationID string         `json:"investigation_id"`
	Dataset         map[string]any `json:"dataset,omitempty"`
	ObservationRef  string         `json:"observation_ref,omitempty"`
	Bounds          *Bounds        `json:"bounds,omitempty"`
	Period          *Period        `json:"period,omitempty"`
	Config          map[string]any `json:"config,omitempty"`
	SchemaVersion   string         `json:"schema_version,omitempty"`
}

type AnalysisAccepted struct {
	ExecutionID        string         `json:"execution_id,omitempty"`
	EngineJobReference string         `json:"engine_job_reference,omitempty"`
	Status             string         `json:"status,omitempty"`
	Raw                map[string]any `json:"raw,omitempty"`
}

type AnalysisStatus struct {
	Status  string         `json:"status"`
	Error   string         `json:"error,omitempty"`
	Raw     map[string]any `json:"raw,omitempty"`
	Results map[string]any `json:"results,omitempty"`
}

type UnavailableClient struct{ Reason string }

func (c UnavailableClient) SubmitAnalysis(context.Context, AnalysisRequest) (*AnalysisAccepted, error) {
	msg := strings.TrimSpace(c.Reason)
	if msg == "" {
		msg = "scientific engine integration is not configured (#016)"
	}
	return nil, fmt.Errorf("%s", msg)
}

func (c UnavailableClient) GetStatus(context.Context, string) (*AnalysisStatus, error) {
	return &AnalysisStatus{Status: "unavailable"}, nil
}

type HTTPClient struct {
	BaseURL    string
	HTTP       *http.Client
	SubmitPath string
	StatusPath string // template containing {id}
}

func NewHTTPClient(baseURL string, timeout time.Duration) *HTTPClient {
	return &HTTPClient{
		BaseURL:    strings.TrimRight(baseURL, "/"),
		HTTP:       &http.Client{Timeout: timeout},
		SubmitPath: "/v1/analyses",
		StatusPath: "/v1/analyses/{id}",
	}
}

func (c *HTTPClient) SubmitAnalysis(ctx context.Context, req AnalysisRequest) (*AnalysisAccepted, error) {
	if c == nil || c.BaseURL == "" {
		return nil, fmt.Errorf("engine base URL not configured")
	}
	b, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	url := c.BaseURL + c.SubmitPath
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(b))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")
	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("engine request failed: %w", err)
	}
	defer resp.Body.Close()
	var raw map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&raw)
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("engine returned status %d", resp.StatusCode)
	}
	acc := &AnalysisAccepted{Raw: raw}
	if v, ok := raw["engine_job_reference"].(string); ok {
		acc.EngineJobReference = v
	}
	if v, ok := raw["execution_id"].(string); ok {
		acc.ExecutionID = v
	}
	if v, ok := raw["status"].(string); ok {
		acc.Status = v
	}
	return acc, nil
}

func (c *HTTPClient) GetStatus(ctx context.Context, executionID string) (*AnalysisStatus, error) {
	if c == nil || c.BaseURL == "" {
		return &AnalysisStatus{Status: "unavailable"}, fmt.Errorf("engine base URL not configured")
	}
	path := strings.ReplaceAll(c.StatusPath, "{id}", executionID)
	url := c.BaseURL + path
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Accept", "application/json")
	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("engine status request failed: %w", err)
	}
	defer resp.Body.Close()
	var raw map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&raw)
	st := &AnalysisStatus{Raw: raw}
	if v, ok := raw["status"].(string); ok {
		st.Status = v
	}
	if v, ok := raw["error"].(string); ok {
		st.Error = v
	}
	if v, ok := raw["results"].(map[string]any); ok {
		st.Results = v
	}
	return st, nil
}
