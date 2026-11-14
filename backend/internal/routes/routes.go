package routes

import (
	"net/http"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/handlers"
	"github.com/asoyovick/GreenGen/backend/internal/middleware"
)

func NewRouter() http.Handler {
	mux := http.NewServeMux()
	health := handlers.NewHealthHandler()
	inv := handlers.NewInvestigationHandler()

	mux.HandleFunc("GET /api/health", health.GetHealth)
	mux.HandleFunc("GET /api/v1/health", health.GetHealth)

	mux.HandleFunc("GET /api/v1/investigations", inv.ListInvestigations)
	mux.HandleFunc("GET /api/v1/investigations/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		id = strings.TrimSpace(id)
		inv.GetInvestigation(w, r, id)
	})

	// Draft endpoints (not yet fully implemented) - explicit responses, no fabricated results.
	notImplemented := func(msg string) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			handlers := struct {
				write func(http.ResponseWriter, string, string, any)
			}{}
			_ = handlers
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusNotImplemented)
			_, _ = w.Write([]byte(`{"error":{"code":"NOT_IMPLEMENTED","message":"` + msg + `"}}`))
		}
	}
	mux.HandleFunc("POST /api/v1/executions", notImplemented("Investigation execution is not implemented yet. Contract and job orchestration are pending."))
	mux.HandleFunc("GET /api/v1/executions/{id}", notImplemented("Execution status retrieval is not implemented yet."))
	mux.HandleFunc("GET /api/v1/executions/{id}/results", notImplemented("Execution results retrieval is not implemented yet."))
	mux.HandleFunc("GET /api/v1/executions/{id}/summary", notImplemented("Execution summary retrieval is not implemented yet."))
	mux.HandleFunc("GET /api/v1/executions/{id}/cells/{cellId}", notImplemented("Cell-level results retrieval is not implemented yet."))
	mux.HandleFunc("GET /api/v1/executions/{id}/report", notImplemented("Execution report retrieval is not implemented yet."))

	return middleware.Chain(mux,
		middleware.Recover,
		middleware.RequestLogger,
		middleware.CORS,
	)
}
