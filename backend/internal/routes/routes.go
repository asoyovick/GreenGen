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
	DB             handlers.DBPinger
}

func NewRouter(svc Services) http.Handler {
	mux := http.NewServeMux()
	health := handlers.NewHealthHandler(svc.DB)
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

	mux.HandleFunc("GET /api/v1/executions/{id}/summary", func(w http.ResponseWriter, r *http.Request) {
		exec.GetSummary(w, r, strings.TrimSpace(r.PathValue("id")))
	})
	mux.HandleFunc("GET /api/v1/executions/{id}/cells/{cellId}", func(w http.ResponseWriter, r *http.Request) {
		exec.GetCell(w, r, strings.TrimSpace(r.PathValue("id")), strings.TrimSpace(r.PathValue("cellId")))
	})
	mux.HandleFunc("GET /api/v1/executions/{id}/report", func(w http.ResponseWriter, r *http.Request) {
		exec.GetReport(w, r, strings.TrimSpace(r.PathValue("id")))
	})

	return middleware.Chain(mux,
		middleware.Recover,
		middleware.RequestLogger,
		middleware.CORS,
	)
}
