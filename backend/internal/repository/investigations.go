package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
)

type InvestigationRepository struct {
	db *sql.DB
}

func NewInvestigationRepository(db *sql.DB) *InvestigationRepository {
	return &InvestigationRepository{db: db}
}

func (r *InvestigationRepository) Available() bool { return r != nil && r.db != nil }

func (r *InvestigationRepository) EnsureSeeded(ctx context.Context) error {
	if !r.Available() {
		return nil
	}
	for _, inv := range domain.SeedInvestigations() {
		if err := r.upsert(ctx, inv); err != nil {
			return fmt.Errorf("seed investigation %s: %w", inv.ID, err)
		}
	}
	return nil
}

func (r *InvestigationRepository) upsert(ctx context.Context, inv domain.Investigation) error {
	dataset, _ := json.Marshal(inv.Dataset)
	geo, _ := json.Marshal(inv.SupportedGeographical)
	temp, _ := json.Marshal(inv.SupportedTemporal)
	vars, _ := json.Marshal(inv.SupportedVariables)
	meta, _ := json.Marshal(inv.Metadata)
	code := inv.Code
	if code == "" {
		code = inv.ID
	}
	_, err := r.db.ExecContext(ctx, `
INSERT INTO investigations (
	code, name, description, scientific_question, scientific_variable, dataset_name,
	dataset_reference, supported_geographical_coverage, supported_temporal_coverage,
	supported_variables, methodology_summary, availability_status, metadata, updated_at
) VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10::jsonb,$11,$12,$13::jsonb,NOW())
ON CONFLICT (code) DO UPDATE SET
	name = EXCLUDED.name,
	description = EXCLUDED.description,
	scientific_question = EXCLUDED.scientific_question,
	scientific_variable = EXCLUDED.scientific_variable,
	dataset_name = EXCLUDED.dataset_name,
	dataset_reference = EXCLUDED.dataset_reference,
	supported_geographical_coverage = EXCLUDED.supported_geographical_coverage,
	supported_temporal_coverage = EXCLUDED.supported_temporal_coverage,
	supported_variables = EXCLUDED.supported_variables,
	methodology_summary = EXCLUDED.methodology_summary,
	availability_status = EXCLUDED.availability_status,
	metadata = EXCLUDED.metadata,
	updated_at = NOW()
`, code, inv.Name, inv.Description, inv.ScientificQuestion, inv.ScientificVariable, stringFromAny(inv.Dataset["name"]),
		string(dataset), string(geo), string(temp), string(vars), inv.MethodologySummary, inv.AvailabilityStatus, string(meta))
	return err
}

func (r *InvestigationRepository) List(ctx context.Context) ([]domain.Investigation, error) {
	if !r.Available() {
		return domain.SeedInvestigations(), nil
	}
	rows, err := r.db.QueryContext(ctx, `
SELECT id, code, name, description, scientific_question, scientific_variable, dataset_name,
       dataset_reference, supported_geographical_coverage, supported_temporal_coverage,
       supported_variables, methodology_summary, availability_status, metadata, created_at, updated_at
FROM investigations
ORDER BY code ASC`)
	if err != nil {
		// Fallback to seeds if DB schema/data unavailable (e.g. migrations not applied yet).
		return domain.SeedInvestigations(), nil
	}
	defer rows.Close()
	var out []domain.Investigation
	for rows.Next() {
		inv, err := scanInvestigation(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, inv)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	if len(out) == 0 {
		// DB reachable but empty - seed and return
		if err := r.EnsureSeeded(ctx); err != nil {
			return domain.SeedInvestigations(), nil
		}
		return r.List(ctx)
	}
	return out, nil
}

func (r *InvestigationRepository) GetByID(ctx context.Context, id string) (domain.Investigation, bool, error) {
	if !r.Available() {
		inv, ok := domain.FindInvestigationByID(id)
		return inv, ok, nil
	}
	row := r.db.QueryRowContext(ctx, `
SELECT id, code, name, description, scientific_question, scientific_variable, dataset_name,
       dataset_reference, supported_geographical_coverage, supported_temporal_coverage,
       supported_variables, methodology_summary, availability_status, metadata, created_at, updated_at
FROM investigations
WHERE code = $1 OR id::text = $1
LIMIT 1`, id)
	inv, err := scanInvestigationRow(row)
	if errors.Is(err, sql.ErrNoRows) {
		// fallback to seed definitions if not found in DB
		if s, ok := domain.FindInvestigationByID(id); ok {
			return s, true, nil
		}
		return domain.Investigation{}, false, nil
	}
	if err != nil {
		// fallback on query/schema errors
		if s, ok := domain.FindInvestigationByID(id); ok {
			return s, true, nil
		}
		return domain.Investigation{}, false, nil
	}
	return inv, true, nil
}

type scanner interface{ Scan(dest ...any) error }

func scanInvestigation(s scanner) (domain.Investigation, error) {
	var (
		id, code, name, desc, question, variable, datasetName, methodology, status sql.NullString
		datasetRef, geo, tempCov, vars, meta                                       []byte
		createdAt, updatedAt                                                       sql.NullTime
	)
	if err := s.Scan(&id, &code, &name, &desc, &question, &variable, &datasetName,
		&datasetRef, &geo, &tempCov, &vars, &methodology, &status, &meta, &createdAt, &updatedAt); err != nil {
		return domain.Investigation{}, err
	}
	inv := domain.Investigation{
		ID:                    code.String,
		Code:                  code.String,
		Name:                  name.String,
		Title:                 name.String,
		Description:           desc.String,
		ScientificQuestion:    question.String,
		ScientificVariable:    variable.String,
		Dataset:               map[string]any{},
		SupportedGeographical: map[string]any{},
		SupportedTemporal:     map[string]any{},
		AvailabilityStatus:    status.String,
		MethodologySummary:    methodology.String,
		Metadata:              map[string]any{},
	}
	if id.String != "" {
		inv.Metadata["db_id"] = id.String
	}
	if datasetName.String != "" {
		inv.Dataset["name"] = datasetName.String
	}
	_ = json.Unmarshal(datasetRef, &inv.Dataset)
	if inv.Dataset == nil {
		inv.Dataset = map[string]any{}
	}
	_ = json.Unmarshal(geo, &inv.SupportedGeographical)
	_ = json.Unmarshal(tempCov, &inv.SupportedTemporal)
	_ = json.Unmarshal(meta, &inv.Metadata)
	var supportedVars []any
	if err := json.Unmarshal(vars, &supportedVars); err == nil {
		inv.SupportedVariables = supportedVars
		inv.Variables = extractStringVars(supportedVars)
	}
	if createdAt.Valid {
		inv.CreatedAt = createdAt.Time
	} else {
		inv.CreatedAt = time.Now().UTC()
	}
	if updatedAt.Valid {
		inv.UpdatedAt = updatedAt.Time
	} else {
		inv.UpdatedAt = inv.CreatedAt
	}
	return inv, nil
}

func scanInvestigationRow(row *sql.Row) (domain.Investigation, error) {
	return scanInvestigation(row)
}

func extractStringVars(v []any) []string {
	out := make([]string, 0, len(v))
	for _, x := range v {
		if s, ok := x.(string); ok {
			out = append(out, s)
		}
	}
	return out
}

func stringFromAny(v any) string {
	s, _ := v.(string)
	return s
}
