# EARTH SYSTEM TREND DETECTIVE
## Team Development, Scientific Requirements and Contribution Handbook

**Project:** NASA Space Apps Challenge 2026  
**Challenge:** Be an Earth System Trend Detective!  
**Team size:** 6 contributors  
**Working arrangement:** Remote collaboration  
**Initial geographical focus:** Kenya  
**Initial environmental variable:** Precipitation  
**Initial data source:** NASA GPM IMERG  
**Document purpose:** Define the product, distribute responsibilities, establish development procedures and create an actionable GitHub issue backlog.

---

# PART 1: PROJECT OVERVIEW

## 1.1 What are we building?

Earth System Trend Detective is a scientific investigation platform that uses NASA Earth observation data to identify, measure and explain changes in Earth's environmental systems across geographical locations and historical periods.

The platform will allow users to investigate predefined environmental questions without having to independently discover datasets, build data-processing pipelines or implement statistical tests.

The application will retrieve real NASA observations, analyse them geographically at grid-cell level, determine whether observed trends are statistically significant and present the findings through interactive maps, visualizations and scientific reports.

## 1.2 The problem we are addressing

NASA provides extensive Earth observation datasets covering precipitation, temperature, vegetation, soil moisture and other environmental variables.

However, obtaining meaningful scientific conclusions from these datasets can require users to:

- Discover appropriate datasets.
- Understand dataset variables and metadata.
- Retrieve observations for particular geographical areas.
- Process large scientific datasets.
- Handle missing observations and data quality.
- Perform statistical trend analysis.
- Interpret geographical differences.
- Communicate findings accurately.

These steps can be difficult for users without experience in scientific programming and geospatial analysis.

Our application aims to simplify this process.

### Our central problem statement

How can we make the identification, measurement and interpretation of significant Earth system changes geographically accessible, scientifically reliable and understandable to different categories of users?

## 1.3 Our proposed solution

We will develop a guided scientific investigation platform.

A user selects a predefined investigation, chooses a geographical area and historical period, and runs an analysis.

The application:

1. Retrieves relevant NASA observations.
2. Validates the observations.
3. Processes the data into an appropriate temporal format.
4. Performs grid-level geographical analysis.
5. Tests for statistically significant trends.
6. Calculates the magnitude of observed changes.
7. Evaluates uncertainty and data limitations.
8. Generates interactive visualizations and scientific reports.

## 1.4 Our target users

The platform will serve five primary audiences.

| Audience | Primary needs |
|---|---|
| Scientists | Statistical evidence, methodology, uncertainty and detailed results. |
| Researchers | Historical observations, geographical comparisons and reproducible analysis. |
| Students | Guided investigations and understandable scientific explanations. |
| Journalists | Credible findings, geographical context and accessible summaries. |
| Educators | Demonstrations, teaching resources and scientific investigation exercises. |

We will maintain one scientific analysis engine.

Different presentation levels will make its results accessible to different audiences without producing different scientific conclusions.

---

# PART 2: PRODUCT SCOPE

## 2.1 Core product capabilities

The initial platform will contain the following capabilities.

| Capability | Description | Priority |
|---|---|---|
| Investigation catalogue | Displays predefined scientific investigations. | Critical |
| Investigation configuration | Allows users to select geography and historical period. | Critical |
| NASA data integration | Retrieves actual observations from NASA datasets. | Critical |
| Data validation | Checks missing observations, quality and completeness. | Critical |
| Grid-level analysis | Analyses individual geographical grid cells. | Critical |
| Trend detection | Identifies increasing and decreasing trends. | Critical |
| Statistical significance | Evaluates the evidence supporting detected trends. | Critical |
| Trend magnitude | Calculates the estimated rate of change. | Critical |
| Interactive maps | Displays geographical trend classifications. | High |
| Time-series visualization | Displays historical observations. | High |
| Scientific reports | Presents methodology and investigation findings. | High |
| AI explanations | Explains verified findings in understandable language. | Later |

## 2.2 Predefined scientific investigations

We will eventually support multiple environmental investigations.

However, only the first investigation will be implemented completely during the initial development phase.

### Investigation 001: Precipitation trends

Scientific question:

How has precipitation changed across different geographical locations over a selected historical period?

Dataset: NASA GPM IMERG.

Variables:
- Monthly precipitation.
- Annual precipitation.
- Seasonal precipitation.

Potential findings:
- Significant increasing trends.
- Significant decreasing trends.
- No statistically significant trend detected.
- Insufficient data.

### Investigation 002: Temperature trends

Scientific question:

How have temperature conditions changed geographically over time?

Potential variables:
- Land surface temperature.
- Atmospheric temperature.
- Temperature anomalies.

Status: Future investigation.

### Investigation 003: Soil moisture trends

Scientific question:

How has soil moisture changed across geographical locations?

Potential findings:
- Increasing soil moisture.
- Decreasing soil moisture.
- Areas with no statistically significant trend.

Status: Future investigation.

### Investigation 004: Vegetation trends

Scientific question:

How has vegetation greenness changed geographically?

Potential variables:
- Normalized Difference Vegetation Index (NDVI).
- Enhanced Vegetation Index (EVI).

Status: Future investigation.

**Development rule:** An investigation must not appear as fully functional until its dataset integration, processing configuration and scientific methodology have been implemented and validated.

---

# PART 3: GRID-LEVEL ANALYSIS

## 3.1 What does grid-level analysis mean?

Instead of treating Kenya as one geographical observation, we divide the geographical area into individual grid cells.

Each cell contains environmental observations for a particular geographical location.

For example, a precipitation investigation might contain thousands of grid cells.

Each cell is independently analysed.

The system should be able to identify:

- Where precipitation is increasing.
- Where precipitation is decreasing.
- Where no statistically significant trend is detected.
- Where the observations are insufficient.

## 3.2 Initial geographical resolution

GPM IMERG provides precipitation estimates at approximately 0.1-degree spatial resolution.

Our initial implementation should preserve the dataset's native grid wherever practical.

We must not arbitrarily change spatial resolution to make the map look more detailed.

Each grid cell must retain its geographical coordinates and relationship to the source dataset.

## 3.3 Required calculations for each grid cell

| Measurement | Purpose |
|---|---|
| Observation count | Determines the number of usable observations. |
| Data completeness | Determines the proportion of available observations. |
| Mean precipitation | Describes average precipitation over the selected period. |
| Trend direction | Identifies increasing or decreasing behaviour. |
| Sen's slope | Estimates the rate of change. |
| Mann-Kendall statistic | Evaluates evidence of a monotonic trend. |
| P-value | Measures statistical evidence against the no-trend hypothesis. |
| Confidence interval | Quantifies uncertainty in the estimated trend. |
| Quality assessment | Identifies limitations affecting the observations. |

## 3.4 Grid classification

Each grid cell should receive one of these classifications:

| Classification | Meaning |
|---|---|
| Significant increase | Statistically significant increasing trend detected. |
| Significant decrease | Statistically significant decreasing trend detected. |
| No significant trend detected | Available evidence does not establish a significant trend. |
| Insufficient data | Observations are inadequate for reliable analysis. |
| Inconclusive | Results require further investigation or are sensitive to methodological assumptions. |

The map legend must explain these classifications.

A grid cell without a statistically significant trend must not automatically be described as environmentally stable.

## 3.5 Scientific safeguards

Grid-level analysis introduces several challenges.

The analysis engine must account for:

1. Missing observations.
2. Seasonal precipitation patterns.
3. Temporal autocorrelation.
4. Multiple statistical comparisons.
5. Dataset quality flags.
6. Changes in measurement and processing systems.
7. Spatial resolution differences.

For example, testing 10,000 grid cells independently can produce false-positive findings.

We should investigate false discovery rate correction, such as the Benjamini-Hochberg procedure.

The statistical methodology must be documented and reviewed before we publish results.

---

# PART 4: SYSTEM ARCHITECTURE

## 4.1 Proposed architecture

We will separate the application into four main components.

```text
                  HTML / CSS FRONTEND
                         |
                         |
                         v
                    GO BACKEND
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          DATABASE    NASA DATA    JOB QUEUE
             |           |           |
             |           v           |
             |      DATA RETRIEVAL   |
             |           |           |
             |           v           |
             |     SCIENTIFIC ENGINE |
             |           ^           |
             |           |           |
             |      PYTHON SERVICE   |
             |                       |
             +-----------+-----------+
                         |
                         v
                  ANALYSIS RESULTS
                         |
                         v
                  GO BACKEND API
                         |
                         v
                  HTML / CSS FRONTEND
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          TREND MAP   TIME SERIES   REPORT
```

## 4.2 Technology stack

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | HTML/CSS | User interface and investigation workflows. |
| Backend | Go | Application logic, APIs and orchestration. |
| Scientific engine | Python | Scientific data processing and statistical analysis. |
| Database | PostgreSQL | Application and investigation records. |
| Geospatial extension | PostGIS | Geographical queries and spatial operations. |
| Scientific processing | Xarray | Multidimensional scientific datasets. |
| Numerical computation | NumPy | Numerical operations. |
| Statistical analysis | SciPy and appropriate statistical libraries | Statistical calculations. |
| Geospatial processing | GeoPandas | Geographical data operations. |
| Interactive mapping | MapLibre GL JS | Geographical visualization. |
| Data discovery | NASA CMR | Dataset and metadata discovery. |
| Data access | NASA Harmony and appropriate NASA services | Data retrieval and subsetting. |

## 4.3 Responsibilities of each component

### Frontend

The frontend should:

- Display available investigations.
- Allow geographical selection.
- Allow historical-period selection.
- Submit investigation requests.
- Display analysis progress.
- Display geographical maps.
- Display historical time series.
- Present scientific results.
- Allow report exports.

### Go backend

The backend should:

- Manage API requests.
- Validate user inputs.
- Manage investigation configurations.
- Communicate with NASA data services.
- Schedule scientific analysis jobs.
- Communicate with the Python service.
- Store investigation metadata and results.
- Return results to the frontend.

### Python scientific engine

The scientific engine should:

- Process NASA observations.
- Validate scientific data.
- Perform temporal aggregation.
- Handle seasonal analysis.
- Perform grid-level calculations.
- Calculate trend statistics.
- Assess uncertainty.
- Apply appropriate statistical corrections.
- Return structured analysis results.

### Database

The database should store:

- Investigation definitions.
- Investigation executions.
- Geographical selections.
- Data source references.
- Processing configurations.
- Grid-level results.
- Statistical outputs.
- Report metadata.

We should avoid storing entire NASA datasets in PostgreSQL. Large scientific data should be accessed and processed using suitable scientific data services and storage formats.

---

# PART 5: SIX-PERSON TEAM STRUCTURE

We will divide responsibilities into six workstreams.

Each contributor should own a clearly defined area while collaborating with the rest of the team.

## MEMBER 1: PRODUCT, SCIENTIFIC COORDINATION AND INTEGRATION LEAD

### Main responsibility

Ensure that the product addresses the NASA challenge and that all components work together toward the same scientific objective.

### Tasks

1. Maintain the product requirements document.
2. Define predefined scientific investigations.
3. Document scientific questions and expected outputs.
4. Coordinate dataset and methodology decisions.
5. Review scientific requirements.
6. Coordinate cross-team dependencies.
7. Review pull requests involving system integration.
8. Monitor project progress.
9. Ensure that the final application satisfies the challenge requirements.

### Deliverables

- Product requirements document.
- Investigation catalogue.
- Scientific methodology documentation.
- Integration plan.
- Final demonstration and presentation material.

### Definition of done

The product requirements are documented, the team understands the expected behaviour, and completed components integrate into one working application.

**Important:** This person coordinates scientific decisions but should not approve statistical methods without technical review from the scientific analysis contributor.

---

## MEMBER 2: NASA DATA INTEGRATION ENGINEER

### Main responsibility

Discover, retrieve and prepare actual NASA Earth observation data.

### Tasks

1. Study NASA GPM IMERG.
2. Understand available products and versions.
3. Identify the appropriate monthly precipitation product.
4. Understand the data format.
5. Identify geographical and temporal metadata.
6. Investigate NASA CMR and relevant data-access services.
7. Retrieve data for the selected geographical area.
8. Implement geographical and temporal subsetting.
9. Handle missing observations and quality information.
10. Provide processed observations to the scientific engine.

### Deliverables

- NASA dataset documentation.
- Data retrieval implementation.
- Data validation implementation.
- Sample real-data extraction.
- Documented data format and metadata.
- Data integration tests.

### Definition of done

The application can retrieve actual NASA precipitation observations for a selected geographical area and historical period, with their metadata and quality information preserved.

### Important restriction

Do not replace NASA observations with manually created or randomly generated data.

Synthetic data may be used for isolated tests, but it must never be presented as real investigation results.

---

## MEMBER 3: SCIENTIFIC ANALYSIS ENGINEER

### Main responsibility

Build and validate the scientific calculations.

This is one of the most scientifically demanding roles.

### Tasks

1. Study time-series trend analysis.
2. Implement temporal aggregation.
3. Investigate seasonal behaviour.
4. Implement Mann-Kendall testing where appropriate.
5. Implement Sen's slope estimation.
6. Calculate confidence intervals.
7. Assess temporal autocorrelation.
8. Implement appropriate significance adjustments.
9. Implement grid-level analysis.
10. Validate calculations against independently calculated reference results.
11. Document assumptions and methodological limitations.

### Deliverables

- Python scientific engine.
- Grid-level analysis implementation.
- Statistical testing implementation.
- Uncertainty calculations.
- Scientific methodology documentation.
- Unit and validation tests.

### Definition of done

Given a validated dataset, the engine produces reproducible grid-level statistical results that have been checked against independent reference calculations.

### Important restriction

Do not treat a p-value alone as proof of meaningful environmental change.

The engine must distinguish statistical significance, magnitude of change and uncertainty.

---

## MEMBER 4: GO BACKEND ENGINEER

### Main responsibility

Build the central application backend and connect the frontend, NASA services and scientific engine.

### Tasks

1. Establish the Go backend structure.
2. Define API contracts.
3. Implement investigation endpoints.
4. Validate investigation requests.
5. Implement data retrieval orchestration.
6. Integrate the Python analysis service.
7. Implement asynchronous analysis execution.
8. Store investigation metadata and results.
9. Implement status tracking.
10. Handle errors and failed jobs.
11. Write backend tests.

### Deliverables

- Go backend.
- API documentation.
- Investigation endpoints.
- Scientific engine integration.
- Database integration.
- Job-status management.
- Backend tests.

### Definition of done

The backend can accept an investigation request, validate it, coordinate data retrieval and analysis, persist results and provide those results through documented APIs.

---

## MEMBER 5: FRONTEND AND GEOSPATIAL VISUALIZATION ENGINEER

### Main responsibility

Build the user experience and present scientific findings geographically.

### Tasks

1. Design the investigation catalogue.
2. Build investigation detail pages.
3. Implement geographical selection.
4. Implement historical-period selection.
5. Build analysis execution interface.
6. Implement interactive maps.
7. Display grid-level classifications.
8. Implement grid-cell inspection.
9. Display historical time series.
10. Display statistical results.
11. Implement report presentation.
12. Ensure that different audiences can understand the results.

### Deliverables

- Investigation interface.
- Geographical selection interface.
- Interactive grid-level map.
- Time-series visualizations.
- Statistical results interface.
- Responsive layouts.

### Definition of done

A user can select an investigation, configure its geographical area and historical period, execute it and explore the returned scientific results.

### Important restriction

Do not invent frontend data to make the application look complete. Use clearly labelled loading, empty and error states until real results are available.

---

## MEMBER 6: QUALITY ASSURANCE, SCIENTIFIC VALIDATION AND DOCUMENTATION ENGINEER

### Main responsibility

Ensure that the application behaves correctly and that the scientific results can be trusted.

### Tasks

1. Define testing strategy.
2. Create test datasets.
3. Verify API contracts.
4. Test NASA data retrieval.
5. Validate statistical outputs.
6. Test geographical grid alignment.
7. Check missing-data behaviour.
8. Test different historical periods.
9. Verify statistical classifications.
10. Test frontend and backend integration.
11. Document reproducibility procedures.
12. Maintain user and technical documentation.

### Deliverables

- Test strategy.
- Test cases.
- Scientific validation report.
- Integration test suite.
- Bug reports.
- User documentation.
- Final quality assessment.

### Definition of done

The application passes agreed functional and scientific validation tests, and known limitations are documented.

---

# PART 6: GITHUB ISSUE BACKLOG

The following issues are the team's initial development backlog.

Create these as GitHub Issues in your project repository.

Use the suggested titles and descriptions. Each issue should be independently understandable.

## MILESTONE 1: PROJECT FOUNDATION

### ISSUE 001: Establish project repository and development conventions

**Assignee:** Member 1  
**Priority:** Critical  
**Labels:** `setup`, `documentation`, `team`

**Description**

Establish the repository structure and shared development conventions for all six contributors.

**Tasks**

- Establish the main repository.
- Define the branch strategy.
- Create the project README.
- Document the technology stack.
- Establish coding conventions.
- Define pull-request requirements.
- Define commit-message conventions.
- Add contribution instructions.
- Establish environment configuration requirements.

**Acceptance criteria**

- All six contributors can access the repository.
- Development instructions are documented.
- The branch strategy is agreed upon.
- Contributors can run the project locally.
- Pull requests require review before merging.

---

### ISSUE 002: Define the scientific investigation catalogue

**Assignee:** Member 1  
**Priority:** Critical  
**Labels:** `product`, `science`, `documentation`

**Description**

Define the predefined investigations supported by the platform.

**Tasks**

- Document the precipitation investigation.
- Define its scientific question.
- Identify its dataset and variables.
- Define its expected outputs.
- Document future temperature, soil moisture and vegetation investigations.
- Define which investigations are available in the MVP.
- Document investigation-specific scientific requirements.

**Acceptance criteria**

- The precipitation investigation has a complete definition.
- Future investigations are documented but not falsely represented as implemented.
- Every investigation has a scientific question and expected output.

---

### ISSUE 003: Define the initial database schema

**Assignee:** Member 4  
**Priority:** High  
**Labels:** `backend`, `database`

**Description**

Design the database structures required to manage investigations and their results.

**Suggested entities**

- Investigations.
- Investigation executions.
- Data sources.
- Geographical selections.
- Processing configurations.
- Grid analysis results.
- Reports.

**Tasks**

- Design entity relationships.
- Define primary and foreign keys.
- Define investigation execution states.
- Define geographical metadata storage.
- Document database migrations.
- Review schema with the team.

**Acceptance criteria**

- Database schema is documented.
- Migrations can create the required structures.
- Investigation executions can be associated with their results.
- The schema supports multiple investigations and repeated executions.

---

## MILESTONE 2: NASA DATA INTEGRATION

### ISSUE 004: Research and document NASA GPM IMERG

**Assignee:** Member 2  
**Priority:** Critical  
**Labels:** `data`, `NASA`, `research`

**Description**

Investigate NASA GPM IMERG and determine the most appropriate precipitation product for the MVP.

**Tasks**

- Study IMERG product versions.
- Identify the monthly precipitation product.
- Document spatial resolution.
- Document temporal coverage.
- Identify units and measurement conventions.
- Understand quality information.
- Identify download and API options.
- Document known limitations.

**Acceptance criteria**

- The selected product is documented.
- Its variables and units are understood.
- Its temporal and geographical coverage are established.
- Data-access instructions are reproducible.
- The team approves the selection.

---

### ISSUE 005: Implement NASA precipitation data retrieval

**Assignee:** Member 2  
**Priority:** Critical  
**Labels:** `data`, `NASA`, `backend`

**Description**

Implement the retrieval of actual GPM IMERG observations for a specified geographical area and historical period.

**Tasks**

- Implement dataset access.
- Accept geographical boundaries.
- Accept start and end dates.
- Retrieve the appropriate observations.
- Preserve source metadata.
- Handle failed requests.
- Document returned data formats.

**Acceptance criteria**

- Real NASA observations can be retrieved.
- Geographical and temporal selections work.
- Source metadata is preserved.
- Retrieval failures are handled.
- Results can be passed to the scientific engine.

---

### ISSUE 006: Implement geographical and temporal data subsetting

**Assignee:** Member 2  
**Priority:** High  
**Labels:** `data`, `geospatial`

**Description**

Ensure that the system retrieves only the geographical and temporal observations required for an investigation.

**Tasks**

- Accept geographical boundaries.
- Identify intersecting grid cells.
- Select the requested historical period.
- Preserve grid coordinates.
- Handle cells at geographical boundaries.
- Verify that subsetting does not distort the source data.

**Acceptance criteria**

- Only relevant observations are selected.
- Grid coordinates remain correct.
- Temporal filtering works.
- The output can be independently checked against the source dataset.

---

### ISSUE 007: Implement NASA observation quality validation

**Assignee:** Member 2  
**Priority:** High  
**Labels:** `data`, `quality`

**Description**

Implement checks to identify missing or questionable observations before scientific analysis.

**Tasks**

- Identify missing values.
- Inspect available quality information.
- Calculate observation completeness.
- Identify invalid observations.
- Record data quality warnings.
- Define which observations are excluded and why.

**Acceptance criteria**

- Invalid observations are identified.
- Missing observations are documented.
- Completeness is calculated.
- Quality information is available to the scientific engine.

---

## MILESTONE 3: SCIENTIFIC ANALYSIS

### ISSUE 008: Define and document the precipitation analysis methodology

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `research`, `documentation`

**Description**

Define the statistical methodology for detecting precipitation trends.

**Tasks**

- Define the temporal aggregation strategy.
- Document seasonal considerations.
- Select appropriate trend tests.
- Define the treatment of autocorrelation.
- Define trend magnitude calculations.
- Define confidence interval calculations.
- Define significance thresholds.
- Define multiple-testing correction.
- Document assumptions and limitations.

**Acceptance criteria**

- The methodology is documented.
- Each statistical method has a clear purpose.
- Seasonal and autocorrelation issues are addressed.
- The methodology is reviewed by the team before implementation.

---

### ISSUE 009: Implement temporal aggregation

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `processing`

**Description**

Convert retrieved observations into appropriate monthly and annual precipitation time series.

**Tasks**

- Inspect source temporal resolution.
- Implement monthly aggregation where necessary.
- Implement annual aggregation.
- Define handling of incomplete months.
- Define handling of incomplete years.
- Preserve units.
- Test aggregation against independent calculations.

**Acceptance criteria**

- Monthly and annual values are calculated correctly.
- Incomplete periods are handled transparently.
- Units remain consistent.
- Results are reproducible.

---

### ISSUE 010: Implement Mann-Kendall trend detection

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `statistics`

**Description**

Implement a suitable Mann-Kendall trend test for environmental time-series observations.

**Tasks**

- Implement the selected Mann-Kendall method.
- Determine trend direction.
- Calculate the test statistic.
- Calculate the p-value.
- Handle ties appropriately.
- Investigate seasonal variants where necessary.
- Account for autocorrelation where appropriate.
- Create statistical test cases.

**Acceptance criteria**

- The method produces reproducible results.
- Increasing and decreasing trends are correctly identified.
- No-trend cases are handled correctly.
- Assumptions and limitations are documented.
- Results are checked against an independent implementation.

---

### ISSUE 011: Implement Sen's slope estimation

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `statistics`

**Description**

Calculate the magnitude of observed environmental trends.

**Tasks**

- Implement Sen's slope.
- Define the units of the estimated slope.
- Handle tied observations.
- Handle missing observations appropriately.
- Calculate confidence intervals.
- Validate results against reference datasets.

**Acceptance criteria**

- Trend magnitude is returned for eligible time series.
- Units are documented.
- Confidence intervals are available.
- Calculations are reproducible.

---

### ISSUE 012: Implement statistical reliability and multiple-testing assessment

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `statistics`, `quality`

**Description**

Ensure that statistical classifications remain scientifically defensible, particularly when thousands of grid cells are tested.

**Tasks**

- Assess temporal autocorrelation.
- Implement appropriate significance testing adjustments.
- Investigate false discovery rate correction.
- Define confidence interval reporting.
- Define insufficient-data conditions.
- Document statistical limitations.
- Validate adjusted and unadjusted results.

**Acceptance criteria**

- Statistical assumptions are documented.
- Multiple comparisons are addressed.
- Insufficient data do not produce misleading classifications.
- Statistical reliability information is returned with results.

---

### ISSUE 013: Implement grid-level analysis

**Assignee:** Member 3  
**Priority:** Critical  
**Labels:** `science`, `geospatial`

**Description**

Run the selected scientific analysis independently for each eligible geographical grid cell.

**Tasks**

- Identify individual grid cells.
- Extract each cell's time series.
- Validate observations.
- Perform trend detection.
- Calculate Sen's slope.
- Calculate significance information.
- Apply appropriate multiple-testing correction.
- Generate structured grid-level results.

**Acceptance criteria**

- Each eligible grid cell receives an analysis result.
- Results retain the correct geographical coordinates.
- Insufficient-data cells are identified.
- Statistical results can be passed to the backend.
- Grid results can be independently validated.

---

## MILESTONE 4: BACKEND DEVELOPMENT

### ISSUE 014: Implement investigation management APIs

**Assignee:** Member 4  
**Priority:** Critical  
**Labels:** `backend`, `api`

**Description**

Implement the backend endpoints required to retrieve and manage predefined investigations.

**Tasks**

- Implement investigation listing.
- Implement investigation details.
- Implement investigation configuration validation.
- Define request and response structures.
- Document API behaviour.
- Write API tests.

**Acceptance criteria**

- The frontend can retrieve available investigations.
- Investigation details include supported variables and configuration requirements.
- Invalid requests return appropriate errors.
- API documentation is available.

---

### ISSUE 015: Implement investigation execution and job management

**Assignee:** Member 4  
**Priority:** Critical  
**Labels:** `backend`, `integration`

**Description**

Implement the workflow for executing scientific investigations.

**Tasks**

- Accept investigation requests.
- Validate geographical and temporal parameters.
- Create execution records.
- Trigger data retrieval.
- Trigger scientific processing.
- Track execution status.
- Handle failed executions.
- Return execution identifiers.

**Acceptance criteria**

- A valid investigation can be submitted.
- Its status can be retrieved.
- Failed jobs are recorded.
- Results are associated with the correct execution.

---

### ISSUE 016: Integrate the Go backend with the Python scientific engine

**Assignee:** Member 4  
**Priority:** Critical  
**Labels:** `backend`, `science`, `integration`

**Description**

Connect the Go application backend to the Python analysis service.

**Tasks**

- Agree on the communication protocol.
- Define input and output schemas.
- Implement service communication.
- Pass validated observations.
- Receive grid-level analysis results.
- Handle timeouts and failures.
- Implement integration tests.

**Acceptance criteria**

- Go can submit an analysis request to Python.
- Python returns structured results.
- Errors are handled.
- Results can be persisted.
- The integration works with real retrieved observations.

---

## MILESTONE 5: FRONTEND AND VISUALIZATION

### ISSUE 017: Implement the predefined investigation catalogue interface

**Assignee:** Member 5  
**Priority:** High  
**Labels:** `frontend`, `ui`

**Description**

Build the interface through which users discover and select scientific investigations.

**Tasks**

- Display available investigations.
- Display scientific questions.
- Display environmental variables.
- Display dataset information.
- Display investigation availability.
- Provide an investigation detail page.

**Acceptance criteria**

- Users can browse available investigations.
- Users can distinguish implemented investigations from planned ones.
- Investigation information comes from the backend.

---

### ISSUE 018: Implement geographical and historical-period selection

**Assignee:** Member 5  
**Priority:** High  
**Labels:** `frontend`, `geospatial`

**Description**

Allow users to configure the geographical area and historical period for an investigation.

**Tasks**

- Implement geographical map selection.
- Support predefined geographical boundaries.
- Allow geographical area selection.
- Implement start and end dates.
- Validate supported periods.
- Submit valid investigation configurations.

**Acceptance criteria**

- Users can select a geographical area.
- Users can select a historical period.
- Invalid selections are rejected.
- Selected parameters reach the backend correctly.

---

### ISSUE 019: Implement the grid-level trend map

**Assignee:** Member 5  
**Priority:** Critical  
**Labels:** `frontend`, `geospatial`, `visualization`

**Description**

Build the interactive map displaying scientific analysis results at grid-cell level.

**Tasks**

- Integrate MapLibre.
- Display the geographical study area.
- Display grid-level results.
- Implement trend classification legends.
- Allow users to select individual grid cells.
- Display selected-cell statistics.
- Handle missing and inconclusive results.

**Acceptance criteria**

- Grid cells align with their geographical coordinates.
- Trend classifications are displayed correctly.
- Users can inspect individual cells.
- Map legends explain the classifications.
- The visualization uses actual backend results.

---

### ISSUE 020: Implement time-series and scientific results visualization

**Assignee:** Member 5  
**Priority:** High  
**Labels:** `frontend`, `visualization`

**Description**

Present historical observations and statistical findings in an understandable interface.

**Tasks**

- Display historical precipitation time series.
- Display trend estimates.
- Display significance information.
- Display confidence intervals.
- Display data completeness.
- Explain statistical classifications.
- Provide detailed and simplified presentation levels.

**Acceptance criteria**

- Historical observations are displayed correctly.
- Statistical results match backend responses.
- Users can distinguish observations from fitted trends.
- Uncertainty and data limitations are visible.

---

## MILESTONE 6: TESTING, DOCUMENTATION AND DELIVERY

### ISSUE 021: Establish scientific reference datasets and validation tests

**Assignee:** Member 6  
**Priority:** Critical  
**Labels:** `testing`, `science`, `quality`

**Description**

Create independent tests for validating scientific calculations.

**Tasks**

- Prepare controlled test datasets.
- Include known increasing trends.
- Include known decreasing trends.
- Include datasets without clear trends.
- Include missing observations.
- Include seasonal patterns.
- Include autocorrelated observations.
- Compare results with independent statistical implementations.

**Acceptance criteria**

- Each major analytical scenario has a test.
- Expected results are documented.
- Incorrect statistical classifications are detected.
- Scientific calculations have reproducible validation evidence.

---

### ISSUE 022: Implement backend and frontend integration tests

**Assignee:** Member 6  
**Priority:** High  
**Labels:** `testing`, `integration`

**Description**

Test the complete user workflow from investigation selection to results presentation.

**Tasks**

- Test investigation retrieval.
- Test configuration submission.
- Test execution status.
- Test analysis integration.
- Test result retrieval.
- Test geographical visualization.
- Test error handling.

**Acceptance criteria**

- The complete investigation workflow can be tested.
- Integration failures are identified.
- Results displayed in the frontend match backend outputs.

---

### ISSUE 023: Document user workflows and scientific methodology

**Assignee:** Member 6  
**Priority:** High  
**Labels:** `documentation`

**Description**

Create documentation explaining how to use the platform and interpret its scientific results.

**Tasks**

- Document investigation selection.
- Document geographical selection.
- Explain grid-level analysis.
- Explain statistical significance.
- Explain Sen's slope.
- Explain confidence intervals.
- Document dataset limitations.
- Document report interpretation.

**Acceptance criteria**

- New users can understand the investigation workflow.
- Scientific terms are explained.
- Dataset sources are identified.
- Limitations are clearly disclosed.

---

### ISSUE 024: Prepare final deployment and demonstration

**Assignee:** Members 1, 4, 5 and 6  
**Priority:** Critical  
**Labels:** `deployment`, `documentation`, `demo`

**Description**

Prepare the working application for the NASA Space Apps demonstration.

**Tasks**

- Configure deployment environments.
- Deploy the frontend.
- Deploy the backend.
- Deploy the scientific engine.
- Configure required environment variables.
- Verify NASA data access.
- Run an end-to-end investigation.
- Prepare a demonstration scenario.
- Prepare presentation slides.
- Document known limitations.

**Acceptance criteria**

- The deployed application is accessible.
- The complete investigation workflow works.
- Real NASA data are used.
- Results can be explained and reproduced.
- The demonstration clearly addresses the challenge.

---

# PART 7: HOW WE WILL WORK REMOTELY

Six contributors working independently without a shared process can easily create six disconnected implementations.

We need a consistent workflow.

## 7.1 Communication

Use one primary communication channel for project coordination.

Recommended structure:

**General**
- Announcements.
- Questions.
- Decisions.

**Development**
- Frontend.
- Backend.
- Scientific analysis.
- NASA data integration.
- Testing.

**Coordination**
- Daily updates.
- Blockers.
- Code reviews.
- Demonstrations.

Important technical decisions should be recorded in the repository rather than disappearing into chat conversations.

## 7.2 Weekly or daily check-ins

For a short hackathon, I recommend a brief daily check-in.

Each member reports:

1. What did I complete?
2. What am I currently working on?
3. What is blocking me?
4. What do I need from another member?

Keep meetings short and use written updates where possible.

## 7.3 GitHub branch strategy

Use the following branches:

```text
main
  |
  +---- develop
           |
           +---- feat/investigation-catalogue
           |
           +---- feat/nasa-data-retrieval
           |
           +---- feat/trend-analysis
           |
           +---- feat/grid-analysis
           |
           +---- feat/backend-api
           |
           +---- feat/trend-map
           |
           +---- test/scientific-validation
```

### Branch rules

- `main`: Stable, tested application.
- `develop`: Integration branch.
- `feat/*`: New functionality.
- `fix/*`: Bug fixes.
- `test/*`: Testing work.
- `docs/*`: Documentation changes.

No contributor should push directly to `main`.

All changes should enter through pull requests.

## 7.4 Commit conventions

Use clear, descriptive commit messages.

Examples:

```text
feat: add precipitation investigation definition

feat: implement IMERG data retrieval

feat: add Mann-Kendall trend detection

feat: calculate Sen's slope

feat: implement grid-level analysis

fix: handle missing precipitation observations

test: validate trend calculations

docs: document scientific methodology
```

Keep commits focused.

Do not combine unrelated changes into one enormous commit.

## 7.5 Pull request requirements

Every pull request must include:

- What was implemented?
- Why was it implemented?
- Which issue does it address?
- How can the changes be tested?
- Are there any limitations?
- Are there screenshots or sample outputs where relevant?

Pull requests should be reviewed by at least one other contributor.

Scientific changes should receive review from the scientific analysis owner.

---

# PART 8: DEFINITION OF DONE

A GitHub issue is not complete simply because code has been written.

An issue is complete when:

1. Its stated requirements have been implemented.
2. Its acceptance criteria have been satisfied.
3. Relevant tests pass.
4. Documentation has been updated.
5. Changes have been reviewed.
6. The pull request has been merged into the agreed integration branch.

For scientific functionality, add two additional requirements:

7. Results have been checked against independent calculations or reference data.
8. Assumptions and limitations have been documented.

This prevents the team from declaring scientific features complete when they only produce plausible-looking numbers.

---

# PART 9: CROSS-TEAM DEPENDENCIES

The six members must not work as isolated departments.

These are the most important dependencies.

| Work | Depends on | Required collaboration |
|---|---|---|
| NASA data retrieval | Dataset research | Members 1 and 2 |
| Scientific methodology | Dataset characteristics | Members 2 and 3 |
| Statistical engine | Validated observations | Members 2 and 3 |
| Backend integration | Python input/output contract | Members 3 and 4 |
| Frontend integration | Backend API contract | Members 4 and 5 |
| Grid map | Grid-level output schema | Members 3, 4 and 5 |
| Scientific validation | Analysis engine | Members 3 and 6 |
| Final demonstration | Working end-to-end system | All members |

## Critical collaboration rule

Do not wait until everyone finishes their work before attempting integration.

Agree on data structures and API contracts early.

For example, Member 3 and Member 4 should agree on the Python analysis request and response format before the analysis engine is fully implemented.

Similarly, Members 4 and 5 should agree on the API response format before the frontend is completed.

This avoids the classic problem where everything works independently but nothing works together.

---

# PART 10: INITIAL DEVELOPMENT TIMELINE

The schedule below is a suggested seven-day intensive development plan. Adjust it to the actual hackathon deadline.

| Day | Main objective | Expected output |
|---|---|---|
| Day 1 | Foundation and technical agreements | Repository, issues, architecture and methodology |
| Day 2 | NASA data integration | Real precipitation observations retrieved |
| Day 3 | Scientific analysis | Temporal aggregation and trend calculations |
| Day 4 | Grid-level analysis and backend | Structured geographical results |
| Day 5 | Frontend integration | Investigation interface and trend map |
| Day 6 | Validation and bug fixing | Tested end-to-end investigation |
| Day 7 | Deployment and presentation | Working demonstration and documentation |

### Critical milestone

By the end of Day 3, we should be able to demonstrate that real NASA observations can pass through our scientific analysis pipeline.

If we cannot achieve that, reduce the scope rather than spending the remaining time polishing an incomplete dashboard.

---

# PART 11: REPOSITORY STRUCTURE

Suggested project structure:

```text
earth-system-trend-detective/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   └── public/
│
├── backend/
│   ├── cmd/
│   ├── internal/
│   │   ├── investigations/
│   │   ├── datasets/
│   │   ├── execution/
│   │   ├── results/
│   │   └── storage/
│   ├── migrations/
│   └── tests/
│
├── scientific-engine/
│   ├── src/
│   │   ├── data/
│   │   ├── quality/
│   │   ├── processing/
│   │   ├── statistics/
│   │   ├── spatial/
│   │   └── reports/
│   ├── tests/
│   └── requirements.txt
│
├── docs/
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── SCIENTIFIC_METHODOLOGY.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── CONTRIBUTING.md
│   ├── API_CONTRACTS.md
│   └── USER_GUIDE.md
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── README.md
└── LICENSE
```

This is a proposed structure, not a requirement to create every directory immediately.

Create folders when their corresponding components are being developed.

---

# PART 12: PROJECT-WIDE ACCEPTANCE CRITERIA

The initial MVP will be considered successful when the following conditions are met.

### Data

- The system retrieves actual NASA GPM IMERG observations.
- The user can select a supported geographical area.
- The user can select a supported historical period.
- Dataset metadata and quality information are preserved.

### Scientific analysis

- Observations are processed correctly.
- Grid cells are analysed independently.
- Trend direction is calculated.
- Trend magnitude is calculated.
- Statistical significance is evaluated appropriately.
- Uncertainty is reported.
- Missing or insufficient observations are handled.
- Multiple testing is addressed.

### User experience

- Users can browse predefined investigations.
- Users can configure their geographical area and period.
- Users can execute an investigation.
- Users can explore grid-level results.
- Users can inspect historical observations.
- Users can understand the scientific findings.

### Reproducibility

Every investigation result should record:

- Dataset name and version.
- Data retrieval date.
- Historical period.
- Geographical boundaries.
- Processing configuration.
- Statistical methods.
- Software or methodology version.
- Data quality information.

A researcher should be able to understand how a finding was produced.

---

# PART 13: IMPORTANT PROJECT RULES

All contributors must follow these principles.

**Rule 1: No fabricated scientific results.**

Use actual NASA observations for real investigations. Test fixtures must be clearly identified as synthetic.

**Rule 2: No unsupported environmental claims.**

A detected precipitation trend does not automatically establish its cause.

**Rule 3: No premature feature expansion.**

Complete precipitation analysis before attempting to implement all four investigations.

**Rule 4: No unreviewed scientific calculations.**

Statistical methods must be independently validated.

**Rule 5: No disconnected development.**

Agree on API contracts and data formats before implementing dependent features.

**Rule 6: No direct commits to main.**

Use feature branches and pull requests.

**Rule 7: No hidden uncertainty.**

Show users when observations are incomplete, results are inconclusive or statistical assumptions limit interpretation.

**Rule 8: No AI-generated scientific facts.**

AI may explain verified results, but the analysis engine must calculate them.

---

# PART 14: FIRST ACTIONS FOR ALL SIX MEMBERS

Before development begins, the following actions should be completed.

| Member | First action |
|---|---|
| Member 1 | Create the repository, publish this handbook and organize the issue backlog. |
| Member 2 | Research GPM IMERG and retrieve a small sample of real precipitation data. |
| Member 3 | Finalize the statistical methodology and prepare reference calculations. |
| Member 4 | Establish the Go backend and agree on API contracts. |
| Member 5 | Create the investigation interface and agree on the grid visualization format. |
| Member 6 | Define the testing strategy and prepare scientific validation cases. |

All six members should participate in the initial architecture discussion.

Do not allow everyone to start coding before the interfaces between components are agreed upon.

---

# FINAL PROJECT DIRECTION

Our first objective is not to build a platform containing every possible environmental variable.

It is to demonstrate one complete, scientifically reliable investigation.

**The first question our application must answer is:**

"How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant?"

The application must retrieve real NASA observations, process them, analyse each eligible grid cell, quantify the trends and present the results with sufficient scientific evidence for another person to inspect and reproduce the investigation.

If we achieve that, we will have established the foundation for a much larger Earth system investigation platform.

**Our development philosophy: One complete scientific investigation is more valuable than ten unfinished features.**
