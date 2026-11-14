package engine

import (
	"context"

	"github.com/asoyovick/GreenGen/backend/internal/service"
)

// ServiceAdapter adapts engine.Client to service.Engine interface.
type ServiceAdapter struct {
	Client Client
}

func (a ServiceAdapter) Submit(ctx context.Context, executionID, investigationID string, req service.ExecutionRequest, dataset map[string]any) (string, string, error) {
	var b *Bounds
	var p *Period
	if req.Bounds != nil {
		b = &Bounds{MinLon: req.Bounds.MinLon, MinLat: req.Bounds.MinLat, MaxLon: req.Bounds.MaxLon, MaxLat: req.Bounds.MaxLat}
	}
	if req.Period != nil {
		p = &Period{Start: req.Period.Start, End: req.Period.End}
	}
	acc, err := a.Client.SubmitAnalysis(ctx, AnalysisRequest{
		ExecutionID:     executionID,
		InvestigationID: investigationID,
		Dataset:         dataset,
		Bounds:          b,
		Period:          p,
		Config:          req.Options,
		SchemaVersion:   "0.1-draft",
	})
	if err != nil {
		return "", "", err
	}
	status := acc.Status
	if status == "" {
		status = "queued"
	}
	return acc.EngineJobReference, status, nil
}

func (a ServiceAdapter) GetStatus(ctx context.Context, executionID string) (string, string, string, error) {
	st, err := a.Client.GetStatus(ctx, executionID)
	if err != nil {
		return "", "ENGINE_STATUS_UNAVAILABLE", err.Error(), err
	}
	errCode, _ := st.Raw["error_code"].(string)
	errMsg := st.Error
	if errMsg == "" {
		errMsg, _ = st.Raw["error_message"].(string)
	}
	return st.Status, errCode, errMsg, nil
}
