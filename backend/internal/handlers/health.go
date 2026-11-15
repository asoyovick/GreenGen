package handlers

import (
	"context"
	"net/http"
	"time"
)

type DBPinger interface {
	Ping(ctx context.Context) error
}

type HealthHandler struct {
	db DBPinger
}

func NewHealthHandler(db DBPinger) *HealthHandler { return &HealthHandler{db: db} }

func (h *HealthHandler) GetHealth(w http.ResponseWriter, r *http.Request) {
	resp := map[string]any{
		"status":  "ok",
		"service": "greengen-backend",
	}
	if h.db != nil {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		if err := h.db.Ping(ctx); err != nil {
			resp["database"] = map[string]any{"status": "unavailable", "error": err.Error()}
		} else {
			resp["database"] = map[string]any{"status": "ok"}
		}
	} else {
		resp["database"] = map[string]any{"status": "not_configured"}
	}
	writeJSON(w, http.StatusOK, resp)
}
