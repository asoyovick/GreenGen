-- Initial schema for GreenGen / Global Change Explorer backend
-- PostgreSQL + PostGIS. Do NOT store bulk NASA datasets in relational tables.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Execution/job lifecycle states are enforced in application logic and/or via checks.
-- Suggested states: pending, queued, running, completed, failed (and optionally cancelled).

CREATE TABLE IF NOT EXISTS investigations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE, -- stable identifier, e.g. INV-001
    name            TEXT NOT NULL,
    description     TEXT,
    scientific_question TEXT,
    scientific_variable TEXT NOT NULL, -- e.g. precipitation
    dataset_name    TEXT,              -- e.g. GPM IMERG
    dataset_reference JSONB NOT NULL DEFAULT '{}'::jsonb, -- product/version/DOI/metadata refs
    supported_geographical_coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
    supported_temporal_coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
    supported_variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    methodology_summary TEXT,
    availability_status TEXT NOT NULL DEFAULT 'planned', -- planned|available|disabled
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE SET NULL,
    source_type     TEXT NOT NULL, -- nasa_dataset|cmr|harmony|local_reference
    name            TEXT NOT NULL,
    short_name      TEXT,
    version         TEXT,
    doi             TEXT,
    uri             TEXT,
    temporal_coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
    spatial_coverage  JSONB NOT NULL DEFAULT '{}'::jsonb,
    variable_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_metadata  JSONB NOT NULL DEFAULT '{}'::jsonb,
    retrieved_at    TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS geographical_selections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    selection_type  TEXT NOT NULL, -- bbox|polygon|point|region_preset
    geometry        GEOMETRY(GEOMETRY, 4326),
    bbox_min_lon    DOUBLE PRECISION,
    bbox_min_lat    DOUBLE PRECISION,
    bbox_max_lon    DOUBLE PRECISION,
    bbox_max_lat    DOUBLE PRECISION,
    region_code     TEXT,
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT geographical_selections_geometry_or_bbox_chk CHECK (
        geometry IS NOT NULL OR (
            bbox_min_lon IS NOT NULL AND bbox_min_lat IS NOT NULL AND
            bbox_max_lon IS NOT NULL AND bbox_max_lat IS NOT NULL
        ) OR region_code IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_geographical_selections_geometry ON geographical_selections USING GIST (geometry);

CREATE TABLE IF NOT EXISTS processing_configurations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregation         TEXT, -- monthly|annual|seasonal
    trend_test          TEXT, -- e.g. mann_kendall
    significance_level  DOUBLE PRECISION,
    multiple_testing_correction TEXT, -- e.g. benjamini_hochberg
    autocorrelation_handling TEXT,
    min_completeness    DOUBLE PRECISION,
    parameters          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS investigation_executions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id    UUID NOT NULL REFERENCES investigations(id) ON DELETE RESTRICT,
    geographical_selection_id UUID REFERENCES geographical_selections(id) ON DELETE SET NULL,
    processing_configuration_id UUID REFERENCES processing_configurations(id) ON DELETE SET NULL,
    data_source_id      UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    status              TEXT NOT NULL DEFAULT 'pending', -- pending|queued|running|completed|failed
    scientific_variable TEXT,
    period_start        DATE,
    period_end          DATE,
    request_payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_code          TEXT,
    error_message       TEXT,
    error_details       JSONB,
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT investigation_executions_status_chk CHECK (status IN ('pending','queued','running','completed','failed')),
    CONSTRAINT investigation_executions_period_chk CHECK (period_start IS NULL OR period_end IS NULL OR period_start <= period_end)
);

CREATE INDEX IF NOT EXISTS idx_investigation_executions_investigation_id ON investigation_executions(investigation_id);
CREATE INDEX IF NOT EXISTS idx_investigation_executions_status ON investigation_executions(status);
CREATE INDEX IF NOT EXISTS idx_investigation_executions_requested_at ON investigation_executions(requested_at DESC);

CREATE TABLE IF NOT EXISTS jobs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_execution_id UUID NOT NULL REFERENCES investigation_executions(id) ON DELETE CASCADE,
    job_type            TEXT NOT NULL DEFAULT 'analysis', -- retrieval|analysis|report
    status              TEXT NOT NULL DEFAULT 'pending', -- pending|queued|running|completed|failed
    engine_job_reference TEXT, -- external/engine-side identifier
    attempt             INTEGER NOT NULL DEFAULT 0,
    max_attempts        INTEGER NOT NULL DEFAULT 1,
    payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_code          TEXT,
    error_message       TEXT,
    error_details       JSONB,
    queued_at           TIMESTAMPTZ,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jobs_status_chk CHECK (status IN ('pending','queued','running','completed','failed'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_execution_id ON jobs(investigation_execution_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Stores references/metadata for analysis outputs. Grid-level values may be stored
-- as structured JSON/JSONB for MVP or referenced via external artifacts (files/objects),
-- but bulk NASA source datasets must not be stored here.
CREATE TABLE IF NOT EXISTS analysis_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_execution_id UUID NOT NULL UNIQUE REFERENCES investigation_executions(id) ON DELETE CASCADE,
    result_type         TEXT NOT NULL DEFAULT 'grid_analysis',
    status              TEXT NOT NULL DEFAULT 'available', -- available|unavailable|partial
    storage_uri         TEXT, -- optional pointer to external artifact (NetCDF/Zarr/GeoJSON/object store)
    summary             JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance          JSONB NOT NULL DEFAULT '{}'::jsonb, -- dataset/version, retrieval, period, bounds, methods, software
    quality             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grid_cell_results (
    id                  BIGSERIAL PRIMARY KEY,
    analysis_result_id  UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    cell_id             TEXT, -- engine/grid identifier
    geom                GEOMETRY(GEOMETRY, 4326),
    centroid_lat        DOUBLE PRECISION,
    centroid_lon        DOUBLE PRECISION,
    n_observations      INTEGER,
    completeness        DOUBLE PRECISION,
    mean_value          DOUBLE PRECISION,
    mean_units          TEXT,
    trend_direction     TEXT,
    sens_slope          DOUBLE PRECISION,
    sens_slope_units    TEXT,
    sens_slope_ci_lower DOUBLE PRECISION,
    sens_slope_ci_upper DOUBLE PRECISION,
    mk_statistic        DOUBLE PRECISION,
    p_value             DOUBLE PRECISION,
    p_value_adjusted    DOUBLE PRECISION,
    classification      TEXT, -- significant_increase|significant_decrease|no_significant_trend|insufficient_data|inconclusive
    quality_flags       JSONB NOT NULL DEFAULT '[]'::jsonb,
    metrics             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grid_cell_results_analysis_id ON grid_cell_results(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_grid_cell_results_geom ON grid_cell_results USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_grid_cell_results_classification ON grid_cell_results(classification);

CREATE TABLE IF NOT EXISTS time_series_results (
    id                  BIGSERIAL PRIMARY KEY,
    analysis_result_id  UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    cell_id             TEXT,
    scope               TEXT NOT NULL DEFAULT 'cell', -- cell|region|aggregate
    variable            TEXT,
    units               TEXT,
    series              JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{time,value,trend?,quality?}, ...]
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_time_series_results_analysis_id ON time_series_results(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_time_series_results_cell_id ON time_series_results(cell_id);

CREATE TABLE IF NOT EXISTS reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_execution_id UUID NOT NULL REFERENCES investigation_executions(id) ON DELETE CASCADE,
    status              TEXT NOT NULL DEFAULT 'unavailable', -- unavailable|pending|available|failed
    format              TEXT, -- json|pdf|html|markdown
    storage_uri         TEXT,
    content             JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_execution_id ON reports(investigation_execution_id);

-- Seed MVP investigation (INV-001). Mark as planned until fully implemented/validated.
INSERT INTO investigations (code, name, description, scientific_question, scientific_variable, dataset_name, dataset_reference, supported_geographical_coverage, supported_temporal_coverage, supported_variables, methodology_summary, availability_status, metadata)
VALUES (
    'INV-001',
    'Precipitation Trends in Kenya',
    'Analyze historical precipitation trends across Kenya using NASA Earth observation data.',
    'How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant?',
    'precipitation',
    'NASA GPM IMERG',
    '{"dataset":"GPM IMERG","status":"to_be_finalized","notes":"Confirm monthly product/version per data integration"}'::jsonb,
    '{"type":"country","name":"Kenya","crs":"EPSG:4326","notes":"Initial MVP focus; exact bounds/presets to be finalized with Members 1/2.","suggested_bounds":{"min_lon":33.9,"min_lat":-4.7,"max_lon":41.9,"max_lat":5.5,"draft":true}}'::jsonb,
    '{"status":"to_be_finalized","notes":"Constrained by selected IMERG product coverage and validated configuration.","suggested_period":{"start":"2000-06-01","end":"2026-12-31","draft":true,"notes":"Draft placeholder; finalize against selected IMERG product/version."}}'::jsonb,
    '["monthly_precipitation","annual_precipitation","seasonal_precipitation"]'::jsonb,
    'Grid-level temporal aggregation and trend analysis (e.g. Mann-Kendall/Sen''s slope) with uncertainty, quality checks, and multiple-testing considerations as defined by the scientific methodology.',
    'planned',
    '{"mvp":true}'::jsonb
)
ON CONFLICT (code) DO NOTHING;
