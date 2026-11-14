package handlers

import (
	"net/http"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
)

type InvestigationHandler struct{}

func NewInvestigationHandler() *InvestigationHandler { return &InvestigationHandler{} }

func (h *InvestigationHandler) ListInvestigations(w http.ResponseWriter, r *http.Request) {
	items := domain.SeedInvestigations()
	// Provide both "data" and "investigations" for contract flexibility during draft phase.
	writeJSON(w, http.StatusOK, map[string]any{
		"investigations": items,
		"count":          len(items),
	})
}

func (h *InvestigationHandler) GetInvestigation(w http.ResponseWriter, r *http.Request, id string) {
	inv, ok := domain.FindInvestigationByID(id)
	if !ok {
		writeError(w, "NOT_FOUND", "Investigation not found.", map[string]any{"id": id})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"investigation": inv})
}
