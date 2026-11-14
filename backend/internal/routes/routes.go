package routes

import (
	"net/http"
	"strings"

	"github.com/asoyovick/GreenGen/backend/internal/handlers"
	"github.com/asoyovick/GreenGen/backend/internal/middleware"
	"github.com/asoyovick/GreenGen/backend/internal/service"
)

type Services struct {
	Investigations *service.InvestigationService
	Executions     *service.ExecutionService
}

func NewRouter(svc Services) http.Handler {
	mux := http.NewServeMux()
	health := handlers.NewHealthHandler()
	inv := handlers.NewInvestigationHandler(svc.Investigations)
	exec := handlers.NewExecutionHandler(svc.Executions)

	mux.HandleFunc("GET /api/health", health.GetHealth)
	mux.HandleFunc("GET /api/v1/health", health.GetHealth)

	mux.HandleFunc("GET /api/v1/investigations", inv.ListInvestigations)
	mux.HandleFunc("GET /api/v1/investigations/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := strings.TrimSpace(r.PathValue("id"))
		inv.GetInvestigation(w, r, id)
	})
	mux.HandleFunc("POST /api/v1/executions/validate", inv.ValidateExecution)

	mux.HandleFunc("POST /api/v1/executions", exec.SubmitExecution)
	mux.HandleFunc("GET /api/v1/executions/{id}", func(w http.ResponseWriter, r *http.Request) {
		exec.GetExecution(w, r, strings.TrimSpace(r.PathValue("id")))
	})
	mux.HandleFunc("GET /api/v1/executions/{id}/results", func(w http.ResponseWriter, r *http.Request) {
		exec.GetResults(w, r, strings.TrimSpace(r.PathValue("id")))
	})
	mux.HandleFunc("POST /api/v1/executions/{id}/refresh", func(w http.ResponseWriter, r *http.Request) {
		exec.RefreshExecution(w, r, strings.TrimSpace(r.PathValue("id")))
	})

	// Draft endpoints (not yet fully implemented) - explicit responses, no fabricated results.
	notImplemented := func(msg string) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusNotImplemented)
			_, _ = w.Write([]byte(`{"error":{"code":"NOT_IMPLEMENTED","message":"` + msg + `"}}`))
		}
	}
	mux.HandleFunc("GET /api/v1/executions/{id}/summary", notImplemented("Execution summary is not implemented yet (depends on analysis results)."))
	mux.HandleFunc("GET /api/v1/executions/{id}/cells/{cellId}", notImplemented("Cell-level results retrieval is not implemented yet."))
	mux.HandleFunc("GET /api/v1/executions/{id}/report", notImplemented("Execution report retrieval is not implemented yet."))

	return middleware.Chain(mux,
		middleware.Recover,
		middleware.RequestLogger,
		middleware.CORS,
	)
}
