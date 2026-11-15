package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/service"
)

type InvestigationHandler struct {
	svc *service.InvestigationService
}

func NewInvestigationHandler(svc *service.InvestigationService) *InvestigationHandler {
	return &InvestigationHandler{svc: svc}
}

func (h *InvestigationHandler) ListInvestigations(w http.ResponseWriter, r *http.Request) {
	items, err := h.svc.List(r.Context())
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to list investigations.", map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"investigations": items,
		"count":          len(items),
	})
}

func (h *InvestigationHandler) GetInvestigation(w http.ResponseWriter, r *http.Request, id string) {
	inv, ok, err := h.svc.Get(r.Context(), id)
	if err != nil {
		writeError(w, "INTERNAL_ERROR", "Failed to retrieve investigation.", map[string]any{"id": id, "error": err.Error()})
		return
	}
	if !ok {
		writeError(w, "NOT_FOUND", "Investigation not found.", map[string]any{"id": id})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"investigation": inv})
}

func (h *InvestigationHandler) ValidateExecution(w http.ResponseWriter, r *http.Request) {
	var req service.ExecutionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, "VALIDATION_ERROR", "Invalid JSON request body.", map[string]any{"error": err.Error()})
		return
	}
	req.InvestigationID = strings.TrimSpace(req.InvestigationID)
	issues, inv := h.svc.ValidateExecutionRequest(r.Context(), req)
	if len(issues) > 0 {
		writeJSON(w, http.StatusUnprocessableEntity, map[string]any{
			"valid":  false,
			"issues": issues,
			"error": map[string]any{
				"code":    "VALIDATION_ERROR",
				"message": "Execution request is not valid.",
				"details": issues,
			},
		})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"valid": true,
		"investigation": map[string]any{
			"id":                  inv.ID,
			"availability_status": inv.AvailabilityStatus,
		},
		"note": "Request shape is valid for draft contract checks. Execution may still be unavailable if data/engine integration is not complete.",
	})
}
