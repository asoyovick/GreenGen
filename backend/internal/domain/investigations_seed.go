package domain

import "time"

// SeedInvestigations returns predefined investigation definitions for MVP.
// These are definitions/catalogue entries, not fabricated scientific results.
func SeedInvestigations() []Investigation {
	now := time.Now().UTC()
	return []Investigation{
		{
			ID:                 "INV-001",
			Code:               "INV-001",
			Name:               "Precipitation Trends in Kenya",
			Title:              "Precipitation Trends in Kenya",
			Description:        "Analyze historical precipitation trends across Kenya using NASA Earth observation data.",
			ScientificQuestion: "How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant?",
			ScientificVariable: "precipitation",
			Variables:          []string{"monthly_precipitation", "annual_precipitation", "seasonal_precipitation"},
			Dataset: map[string]any{
				"name":      "NASA GPM IMERG",
				"status":    "to_be_finalized",
				"notes":     "Confirm monthly product/version, units, quality fields, and access method with data integration team.",
				"reference": "https://gpm.nasa.gov/data/imerg",
			},
			SupportedGeographical: map[string]any{
				"type":  "country",
				"name":  "Kenya",
				"crs":   "EPSG:4326",
				"notes": "Initial MVP focus; exact bounds/presets to be finalized with Members 1/2.",
				"suggested_bounds": map[string]any{
					"min_lon": 33.9, "min_lat": -4.7, "max_lon": 41.9, "max_lat": 5.5,
					"draft": true,
				},
			},
			SupportedTemporal: map[string]any{
				"status": "to_be_finalized",
				"notes":  "Constrained by selected GPM IMERG product coverage and validated configuration.",
				"suggested_period": map[string]any{
					"start": "2000-06-01",
					"end":   "2026-12-31",
					"draft": true,
					"notes": "Draft placeholder; finalize against selected IMERG product/version.",
				},
			},
			MethodologySummary: "Grid-level temporal aggregation and trend analysis (e.g. Mann–Kendall, Sen’s slope) with uncertainty, data quality/completeness handling, and multiple-testing considerations as defined by the agreed scientific methodology.",
			AvailabilityStatus: "planned",
			Metadata:           map[string]any{"mvp": true},
			CreatedAt:          now,
			UpdatedAt:          now,
		},
		{
			ID:                    "INV-002",
			Code:                  "INV-002",
			Name:                  "Temperature Trends",
			Title:                 "Temperature Trends",
			Description:           "Planned investigation of temperature changes over time.",
			ScientificQuestion:    "How have temperature conditions changed geographically over time?",
			ScientificVariable:    "temperature",
			Variables:             []string{"land_surface_temperature", "air_temperature", "temperature_anomaly"},
			Dataset:               map[string]any{"status": "to_be_determined"},
			SupportedGeographical: map[string]any{"status": "to_be_determined"},
			SupportedTemporal:     map[string]any{"status": "to_be_determined"},
			AvailabilityStatus:    "planned",
			CreatedAt:             now,
			UpdatedAt:             now,
		},
		{
			ID:                    "INV-003",
			Code:                  "INV-003",
			Name:                  "Soil Moisture Trends",
			Title:                 "Soil Moisture Trends",
			Description:           "Planned investigation of soil moisture changes.",
			ScientificQuestion:    "How has soil moisture changed across geographical locations?",
			ScientificVariable:    "soil_moisture",
			Variables:             []string{"soil_moisture"},
			Dataset:               map[string]any{"status": "to_be_determined"},
			SupportedGeographical: map[string]any{"status": "to_be_determined"},
			SupportedTemporal:     map[string]any{"status": "to_be_determined"},
			AvailabilityStatus:    "planned",
			CreatedAt:             now,
			UpdatedAt:             now,
		},
		{
			ID:                    "INV-004",
			Code:                  "INV-004",
			Name:                  "Vegetation Trends",
			Title:                 "Vegetation Trends",
			Description:           "Planned investigation of vegetation greenness changes.",
			ScientificQuestion:    "How has vegetation greenness changed geographically?",
			ScientificVariable:    "vegetation",
			Variables:             []string{"ndvi", "evi"},
			Dataset:               map[string]any{"status": "to_be_determined"},
			SupportedGeographical: map[string]any{"status": "to_be_determined"},
			SupportedTemporal:     map[string]any{"status": "to_be_determined"},
			AvailabilityStatus:    "planned",
			CreatedAt:             now,
			UpdatedAt:             now,
		},
	}
}

func FindInvestigationByID(id string) (Investigation, bool) {
	for _, inv := range SeedInvestigations() {
		if inv.ID == id || inv.Code == id {
			return inv, true
		}
	}
	return Investigation{}, false
}
