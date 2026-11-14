package handlers

import (
	"encoding/json"
	"log"
	"net/http"

	apierrors "github.com/asoyovick/GreenGen/backend/internal/errors"
)

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if v == nil {
		return
	}
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("write json response: %v", err)
	}
}

func writeError(w http.ResponseWriter, code, message string, details any) {
	status := apierrors.StatusForCode(code)
	writeJSON(w, status, apierrors.New(code, message, details))
}
