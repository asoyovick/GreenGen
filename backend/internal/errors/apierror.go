package apierrors

import "net/http"

type APIError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details any    `json:"details,omitempty"`
}

type ErrorResponse struct {
	Error APIError `json:"error"`
}

func New(code, message string, details any) ErrorResponse {
	return ErrorResponse{Error: APIError{Code: code, Message: message, Details: details}}
}

func StatusForCode(code string) int {
	switch code {
	case "VALIDATION_ERROR", "INVALID_REQUEST":
		return http.StatusBadRequest
	case "NOT_FOUND":
		return http.StatusNotFound
	case "CONFLICT":
		return http.StatusConflict
	case "UNPROCESSABLE_ENTITY":
		return http.StatusUnprocessableEntity
	case "SERVICE_UNAVAILABLE", "ENGINE_UNAVAILABLE", "DATABASE_UNAVAILABLE":
		return http.StatusServiceUnavailable
	case "NOT_IMPLEMENTED":
		return http.StatusNotImplemented
	default:
		return http.StatusInternalServerError
	}
}
