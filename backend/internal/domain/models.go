package domain

import "time"

type Investigation struct {
	ID                    string         `json:"id"`
	Code                  string         `json:"code,omitempty"`
	Name                  string         `json:"name"`
	Title                 string         `json:"title,omitempty"`
	Description           string         `json:"description,omitempty"`
	ScientificQuestion    string         `json:"scientific_question,omitempty"`
	ScientificVariable    string         `json:"scientific_variable,omitempty"`
	Variables             []string       `json:"variables,omitempty"`
	Dataset               map[string]any `json:"dataset,omitempty"`
	SupportedGeographical map[string]any `json:"supported_geographical_coverage,omitempty"`
	SupportedTemporal     map[string]any `json:"supported_temporal_coverage,omitempty"`
	SupportedVariables    []any          `json:"supported_variables_detail,omitempty"`
	MethodologySummary    string         `json:"methodology_summary,omitempty"`
	AvailabilityStatus    string         `json:"availability_status"`
	Metadata              map[string]any `json:"metadata,omitempty"`
	CreatedAt             time.Time      `json:"created_at,omitempty"`
	UpdatedAt             time.Time      `json:"updated_at,omitempty"`
}

type ExecutionStatus string

const (
	ExecutionPending   ExecutionStatus = "pending"
	ExecutionQueued    ExecutionStatus = "queued"
	ExecutionRunning   ExecutionStatus = "running"
	ExecutionCompleted ExecutionStatus = "completed"
	ExecutionFailed    ExecutionStatus = "failed"
)

type InvestigationExecution struct {
	ID              string          `json:"id"`
	InvestigationID string          `json:"investigation_id"`
	Status          ExecutionStatus `json:"status"`
	PeriodStart     *string         `json:"period_start,omitempty"`
	PeriodEnd       *string         `json:"period_end,omitempty"`
	ErrorCode       string          `json:"error_code,omitempty"`
	ErrorMessage    string          `json:"error_message,omitempty"`
	RequestedAt     time.Time       `json:"requested_at"`
	StartedAt       *time.Time      `json:"started_at,omitempty"`
	CompletedAt     *time.Time      `json:"completed_at,omitempty"`
	UpdatedAt       time.Time       `json:"updated_at,omitempty"`
}

type Job struct {
	ID                     string          `json:"id"`
	InvestigationExecution string          `json:"investigation_execution_id"`
	JobType                string          `json:"job_type"`
	Status                 ExecutionStatus `json:"status"`
	EngineJobReference     string          `json:"engine_job_reference,omitempty"`
	ErrorCode              string          `json:"error_code,omitempty"`
	ErrorMessage           string          `json:"error_message,omitempty"`
	CreatedAt              time.Time       `json:"created_at"`
	UpdatedAt              time.Time       `json:"updated_at"`
}
