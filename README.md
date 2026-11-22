# GreenGen | Global Change Explorer

> **Click anywhere on Earth. Discover what is changing, where it is changing, how much it is changing, and whether the change is statistically significant.**

GreenGen is an interactive Earth observation analysis platform designed to make environmental change detection more accessible. It uses NASA Earth science datasets and statistical methods to identify, quantify, and visualize environmental trends across geographical locations.

Built for the **NASA Space Apps Challenge 2026**.

---

## Table of Contents

- [The Challenge](#1-the-challenge)
- [The Problem](#2-the-problem)
- [Our Solution](#3-our-solution)
- [Who We Are Building For](#4-who-we-are-building-for)
- [Core Features](#5-core-features)
- [How It Works](#6-how-it-works)
- [Scientific Methodology](#7-scientific-methodology)
- [Data Sources](#8-data-sources)
- [Technology Stack](#9-technology-stack)
- [System Architecture](#10-system-architecture)
- [Project Structure](#11-project-structure)
- [Getting Started](#12-getting-started)
- [Development Roadmap](#13-development-roadmap)
- [Scientific Limitations](#14-scientific-limitations)
- [Contributors](#15-contributors)
- [Contributing](#16-contributing)
- [References](#17-references)
- [License](#18-license)

---

## 1. The Challenge

Earth is a complex and interconnected system. Its environmental conditions continuously change across time and geographical locations.

Scientists collect enormous amounts of Earth observation data through satellites, scientific missions, and Earth system models. However, identifying meaningful environmental trends across these datasets is not always straightforward.

The NASA challenge asks us to develop a solution that helps people:

- Identify Earth science variables that indicate environmental change.
- Visualize how these variables change over time.
- Determine where changes are occurring.
- Quantify the magnitude and direction of those changes.
- Establish whether observed trends are statistically significant.
- Understand why the same environmental variable may behave differently across different geographical regions.

GreenGen aims to make this process easier to explore, understand, and communicate.

## 2. The Problem

Earth science data is widely available, but extracting meaningful information from it requires knowledge of datasets, data processing, geographical analysis, and statistical methods.

A person interested in understanding environmental changes in a particular location may need to:

1. Identify relevant environmental variables.
2. Find suitable satellite or model datasets.
3. Access and process the observations.
4. Analyze historical measurements.
5. Calculate the direction and magnitude of change.
6. Determine the statistical reliability of the results.
7. Compare findings across geographical locations.

This creates a barrier for people who need environmental information but do not necessarily have advanced remote sensing or statistical expertise.

There is also an important scientific challenge: **the same environmental variable can increase in one region and decrease in another.**

A global average may hide these regional differences.

GreenGen addresses this problem through location-based exploration and grid-level analysis.

## 3. Our Solution

GreenGen is a global environmental change exploration platform.

Instead of requiring users to understand datasets and select variables before beginning an investigation, GreenGen allows them to start with a geographical location or a predefined scientific question.

The platform analyzes available environmental observations and presents the detected changes in an understandable format.

### The central experience

**Select a location → Discover available variables → Explore environmental trends → Understand the results.**

### Two ways to investigate

#### A. Explore a location

Users interact with a global map to:

1. Select a geographical location.
2. Discover environmental variables available for that area.
3. View the direction and magnitude of detected trends.
4. Examine statistical significance and data quality.
5. Explore historical time series.
6. Compare the selected grid cell with surrounding areas.

#### B. Guided investigations

Users select a predefined environmental investigation.

For example:

- How has precipitation changed over time?
- Where are vegetation greenness trends increasing or decreasing?
- How have land surface temperatures changed?
- Which neighbouring regions show contrasting environmental trends?

Users can specify a geographical area and historical period where supported.

Both experiences use the same underlying scientific analysis engine.

## 4. Who We Are Building For

GreenGen is designed for people who need to understand and communicate environmental change.

| Audience | What GreenGen helps them do |
|---|---|
| Scientists | Explore environmental trends and inspect statistical results. |
| Students | Understand Earth system changes through interactive visualizations. |
| Researchers | Investigate geographical patterns and export analytical results. |
| Journalists | Find and communicate evidence of environmental change. |
| Educators | Demonstrate environmental processes using real Earth observation data. |

The scientific calculations remain consistent across audiences. The presentation can be adapted to provide simpler explanations or more detailed scientific information.

## 5. Core Features

### 5.1 Interactive Global Map

Explore geographical locations using an interactive map.

Users can inspect environmental trend layers and select locations for detailed analysis.

### 5.2 Automatic Variable Discovery

Identify which environmental variables are available and relevant to a selected geographical location.

Variables that do not apply to a particular surface type should not be presented as applicable measurements.

### 5.3 Predefined Investigations

Provide guided environmental investigations that help users explore specific scientific questions without requiring them to understand the underlying datasets first.

### 5.4 Grid-Level Trend Analysis

Analyze environmental changes at individual geographical grid cells rather than relying exclusively on global or regional averages.

This helps reveal local patterns and opposing trends across neighbouring locations.

### 5.5 Statistical Significance

Distinguish statistically significant trends from trends that do not meet the selected statistical criteria.

Present the statistical results alongside their limitations and uncertainty.

### 5.6 Historical Time Series

Visualize historical measurements and calculated trends for selected environmental variables.

### 5.7 Regional Comparison

Compare neighbouring geographical cells to identify areas experiencing similar or contrasting changes.

### 5.8 Understandable Scientific Reports

Translate verified analytical results into clear explanations while preserving the original measurements, units, statistical information, and data limitations.

---

## 6. How It Works

GreenGen follows a scientific processing workflow.

```text
                  USER
                    |
                    v
          Select location or
        predefined investigation
                    |
                    v
           Identify available
          environmental variables
                    |
                    v
            NASA DATA SOURCES
                    |
                    v
            Data acquisition
                    |
                    v
          Data quality checks
                    |
                    v
          Temporal processing
                    |
                    v
          Grid-level analysis
                    |
                    v
          Statistical assessment
                    |
                    v
          Store processed results
                    |
                    v
           API / DATA ACCESS
                    |
                    v
          Interactive visualization
                    |
                    v
             USER REPORT
```

### Processing stages

| Stage | Description |
|---|---|
| Data discovery | Identify relevant NASA datasets and available observations. |
| Data acquisition | Retrieve the required geographical and historical data. |
| Quality assessment | Check missing observations, quality flags, and record completeness. |
| Preprocessing | Prepare observations for consistent temporal analysis. |
| Trend analysis | Calculate the direction and magnitude of change. |
| Significance testing | Evaluate whether the observed trend meets statistical significance criteria. |
| Spatial analysis | Analyze and compare results across geographical grid cells. |
| Visualization | Present maps, time series, and analytical summaries. |

---

## 7. Scientific Methodology

Scientific reliability is central to GreenGen.

The platform must distinguish between an observed change, a statistically significant trend, and an environmentally meaningful change.

### 7.1 Temporal Analysis

Environmental observations are organized into historical time series.

Depending on the dataset, measurements may be aggregated into monthly or annual observations.

Seasonality must be considered so that recurring seasonal patterns are not incorrectly interpreted as long-term trends.

### 7.2 Trend Magnitude

GreenGen uses the Theil-Sen estimator to calculate robust trend slopes.

The result communicates how quickly a variable is changing.

Examples of possible units include:

- Millimetres per year for precipitation.
- Degrees Celsius per decade for temperature.
- Appropriate dataset-specific units for other environmental variables.

### 7.3 Statistical Significance

The Mann-Kendall test can be used to evaluate whether a monotonic trend is statistically significant.

Where necessary, the analysis must account for temporal autocorrelation.

A statistical significance threshold should be explicitly documented.

### 7.4 Multiple Comparisons

Analyzing thousands of grid cells introduces the risk of false positive results.

GreenGen will use an appropriate multiple-testing correction, such as the Benjamini-Hochberg False Discovery Rate procedure, where applicable.

### 7.5 Grid-Level Analysis

Each valid grid cell is analyzed independently.

For every cell, the platform aims to retain:

- Trend direction.
- Trend magnitude.
- Statistical significance.
- Number of valid observations.
- Analysis period.
- Data quality information.
- Relevant uncertainty information.

### 7.6 Regional Comparison

Neighbouring grid cells can be compared to identify spatial differences.

For example, precipitation may increase in one region while decreasing in a neighbouring region.

The platform should communicate these differences rather than hiding them behind a single regional average.

### 7.7 Scientific Reproducibility

Every result should be traceable to:

- Its original dataset.
- Dataset version.
- Variable and units.
- Geographical coverage.
- Historical period.
- Processing configuration.
- Statistical methodology.

All statistical calculations must be performed by the scientific processing engine, not generated by an AI language model.

AI may assist with explaining verified results, but it must never invent measurements or statistical conclusions.

---

## 8. Data Sources

GreenGen uses NASA Earth science observations and model-produced datasets.

The following are candidate data sources. Their suitability, temporal coverage, access methods, and versions must be verified before implementation.

| Environmental variable | Dataset | Potential application |
|---|---|---|
| Precipitation | GPM IMERG | Historical precipitation trends. |
| Vegetation greenness | MODIS MOD13 | Vegetation condition and greenness changes. |
| Land surface temperature | MODIS MOD11 | Historical land surface temperature changes. |
| Air temperature | MERRA-2 | Atmospheric temperature trends. |
| Terrestrial water storage | GRACE / GRACE-FO | Changes in terrestrial water storage. |
| Soil moisture | SMAP / GLDAS | Changes in soil moisture conditions. |
| Sea ice concentration | NSIDC datasets | Historical sea ice changes. |

### NASA data resources

| Resource | Purpose |
|---|---|
| [NASA Earthdata](https://www.earthdata.nasa.gov/) | Access NASA Earth science data. |
| [Earthdata Search](https://search.earthdata.nasa.gov/) | Discover datasets and inspect their metadata. |
| [earthaccess](https://earthaccess.readthedocs.io/) | Access NASA Earthdata programmatically using Python. |
| [NASA Giovanni](https://giovanni.gsfc.nasa.gov/) | Explore and independently inspect environmental datasets. |
| [NASA Worldview](https://worldview.earthdata.nasa.gov/) | Explore satellite imagery. |
| [Common Metadata Repository](https://cmr.earthdata.nasa.gov/) | Search NASA Earth science dataset metadata. |

### Initial implementation priority

The first complete data pipeline should focus on one dataset, such as GPM IMERG precipitation.

The team should demonstrate that it can:

1. Retrieve real NASA observations.
2. Validate the data.
3. Process the historical time series.
4. Calculate grid-level trends.
5. Evaluate statistical significance.
6. Visualize the results.

Additional variables should be integrated after the first pipeline has been validated.

### Important data principle

GreenGen should preserve the native spatial resolution and characteristics of each dataset during initial processing.

If datasets need to be placed on a common grid for comparison, the team must document the harmonization method and its effect on the results.

---

## 9. Technology Stack

The following is the proposed technology stack based on the current project direction.

| Component | Technology | Responsibility |
|---|---|---|
| Programming language | Python | Scientific processing and data integration. |
| Data processing | Xarray, NumPy, Pandas | Multidimensional Earth science data processing. |
| Statistical analysis | SciPy, statsmodels, pymannkendall | Statistical calculations and trend analysis. |
| NASA data access | earthaccess | NASA Earthdata access. |
| Backend API | FastAPI | Application endpoints and processing orchestration. |
| Frontend | React | User interface. |
| Geospatial visualization | MapLibre GL JS | Interactive geographical maps. |
| Time-series visualization | Plotly | Historical data visualization. |
| Scientific storage | NetCDF / Zarr | Processed scientific datasets and arrays. |
| Version control | Git and GitHub | Collaboration and source code management. |

Technology choices may be refined as implementation progresses. Any major architectural change should be discussed and documented by the team.

---

## 10. System Architecture

GreenGen separates scientific processing from the user-facing application.

### Data layer

Responsible for discovering, retrieving, validating, and preparing NASA datasets.

### Scientific engine

Responsible for temporal processing, trend calculations, statistical testing, and grid-level analysis.

### Results storage

Stores processed analytical outputs and the metadata needed to reproduce and interpret them.

Large scientific datasets should not be unnecessarily stored as ordinary relational database records.

### Backend API

Provides access to investigation definitions, available variables, analytical results, and processing status.

### Frontend

Provides the interactive map, investigation catalogue, historical charts, and scientific result reports.

### Architecture principle

The frontend should not perform scientific calculations.

The backend should not invent scientific results.

The scientific engine should be responsible for producing reproducible analytical outputs.

---

## 11. Project Structure

The repository will evolve as the application is implemented.

A proposed structure is:

```text
GreenGen/
│
├── README.md
│
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── SCIENTIFIC_METHODOLOGY.md
│   ├── DATA_SOURCES.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TEAM_ROLES.md
│   ├── DEVELOPMENT_ROADMAP.md
│   └── CONTRIBUTING.md
│
├── frontend/
│
├── backend/
│
├── scientific-engine/
│
├── tests/
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
└── .gitignore
```

This is the intended organization, not a claim that every directory has already been implemented.

---

## 12. Getting Started

### Prerequisites

- Git.
- Python 3.10 or later.
- Node.js and npm.
- A NASA Earthdata account for accessing applicable datasets.

### Clone the repository

```bash
git clone https://github.com/asoyovick/GreenGen.git

cd GreenGen
```

### Scientific environment

```bash
python -m venv .venv

source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### Install initial scientific dependencies

```bash
pip install earthaccess xarray netCDF4 zarr dask numpy scipy pandas statsmodels pymannkendall fastapi uvicorn
```

### NASA Earthdata authentication

Create an Earthdata account and configure authentication using the official earthaccess documentation.

### Running the application

The exact commands for running the backend and frontend will be added when their application entry points and dependency files have been established.

Do not assume the example setup commands represent an already completed implementation.

---

## 13. Development Roadmap

Development will be organized into milestones.

| Milestone | Objective | Expected outcome |
|---|---|---|
| 1. Foundation | Finalize requirements, architecture, repository conventions, and team responsibilities. | Agreed technical and scientific direction. |
| 2. Data acquisition | Integrate the first NASA dataset. | Real observations available for processing. |
| 3. Scientific engine | Implement temporal processing and grid-level trend analysis. | Validated scientific outputs. |
| 4. Backend | Expose investigations and analytical results through APIs. | Working application data layer. |
| 5. Frontend | Build the global map and investigation experience. | Users can explore results. |
| 6. Validation | Test scientific correctness and application reliability. | Reproducible and trustworthy results. |
| 7. Delivery | Deploy and prepare the final demonstration. | Functional hackathon submission. |

### MVP priorities

The first working version should demonstrate:

- At least one real NASA dataset.
- A working geographical exploration experience.
- Historical time-series visualization.
- Grid-level trend analysis.
- Statistical significance assessment.
- Clear explanations of results and limitations.

### Stretch goals

- Additional environmental variables.
- More advanced regional comparison.
- Combined environmental change indicators.
- Natural-language exploration.
- Downloadable investigation reports.
- Cross-variable analysis.

The team should prioritize a complete, scientifically defensible workflow over a large collection of partially implemented features.

---

## 14. Scientific Limitations

GreenGen must communicate scientific limitations honestly.

| Limitation | Required treatment |
|---|---|
| Missing observations | Identify and report missing data. |
| Seasonal variation | Account for seasonality in the analysis. |
| Temporal autocorrelation | Use an appropriate statistical correction. |
| Multiple testing | Apply suitable false discovery rate control. |
| Different dataset resolutions | Preserve and report native resolution. |
| Short historical records | Flag results with limited temporal coverage. |
| Dataset changes | Document product versions and known discontinuities. |
| Regional differences | Avoid relying exclusively on global averages. |
| Statistical significance | Do not confuse statistical significance with practical importance. |
| Correlation | Do not present correlation as proof of causation. |

A statistically significant trend does not automatically mean that the change is environmentally important.

Likewise, a trend that is not statistically significant does not prove that no environmental change has occurred.

GreenGen is an environmental change detection platform, not a climate attribution or future forecasting system.

---

## 15. Contributors

GreenGen is built by a team of six contributors collaborating remotely as part of the NASA Space Apps Challenge 2026.

Each contributor is responsible for their assigned workstream and contributes to the project's development, testing, and improvement.

### Development Team

| Name | GitHub Username | Responsibility |
|---|---|---|
| Victor Oumad | asoyovick | Product coordination and integration |
| Hellen Onyango |hellonyango | NASA data acquisition and processing |
| miriam chemeres | mchemere| NASA data acquisition and processing |
| To be added | To be added | Scientific analysis and grid-level statistics |
| To be added | To be added | Backend development and API integration |
| To be added | To be added | Frontend development and geospatial visualization |
| To be added | To be added | Testing, scientific validation and documentation |

### How to Add Yourself

Each team member should:

1. Fork or clone the repository.
2. Add their name and GitHub username to the contributors table.
3. Keep the assigned responsibility unchanged unless the team agrees otherwise.
4. Submit a pull request for review.

**We believe in collaborative development, shared ownership, and building solutions through teamwork.**
---

## 16. Contributing

We welcome contributions from all members of the GreenGen development team.

### Development workflow

1. Check the GitHub Issues board.
2. Select or get assigned an issue.
3. Create a dedicated branch.
4. Implement the assigned functionality.
5. Test your changes.
6. Submit a pull request.
7. Request a review.
8. Merge after approval.

### Branch naming

Use descriptive branch names:

```text
feature/nasa-data-ingestion
feature/grid-trend-analysis
feature/global-map
fix/data-validation
docs/scientific-methodology
```

### Commit messages

Use clear, focused commit messages:

```text
feat: add NASA precipitation data ingestion

feat: implement grid-level trend analysis

fix: handle missing observation values

docs: update scientific methodology
```

### Collaboration principles

- Do not commit directly to the main branch.
- Keep pull requests focused on a specific issue.
- Test scientific calculations before submitting them.
- Document assumptions and data transformations.
- Do not commit NASA data files or large generated datasets.
- Never present synthetic test data as real NASA observations.
- Discuss major architectural changes before implementation.

---

## 17. References

### Project documentation

- [Product Requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Investigation Catalogue](docs/INVESTIGATION_CATALOGUE.md)
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Data Sources and Observation Handoff](docs/DATA_SOURCES.md)
- [Scientific Methodology](docs/SCIENTIFIC_METHODOLOGY.md)
- [Testing Strategy](docs/TESTING_STRATEGY.md)
- [Reproducibility Procedures](docs/REPRODUCIBILITY.md)
- [Scientific Validation Report](docs/SCIENTIFIC_VALIDATION_REPORT.md)
- [Quality Assessment and Known Limitations](docs/QUALITY_ASSESSMENT.md)
- [Demo Narrative and Challenge Alignment](docs/DEMO_NARRATIVE.md)
- [Bug Triage](docs/BUG_TRIAGE.md)
- [Contribution Handbook](docs/CONTRIBUTION.md)

### NASA resources

- [NASA Earthdata](https://www.earthdata.nasa.gov/)
- [NASA Earthdata Search](https://search.earthdata.nasa.gov/)
- [NASA Giovanni](https://giovanni.gsfc.nasa.gov/)
- [NASA Worldview](https://worldview.earthdata.nasa.gov/)
- [NASA Common Metadata Repository](https://cmr.earthdata.nasa.gov/)
- [earthaccess documentation](https://earthaccess.readthedocs.io/)

### Statistical references

- Mann, H. B. (1945). Nonparametric tests against trend.
- Kendall, M. G. (1975). Rank Correlation Methods.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau.
- Hamed, K. H., and Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data.
- Benjamini, Y., and Hochberg, Y. (1995). Controlling the false discovery rate.

---

## 18. License

A license has not yet been selected.

The team should agree on an appropriate open-source license before publishing the final project release.

NASA datasets should be credited appropriately, and the terms applicable to each individual dataset should be respected.

---

**GreenGen: Making Earth's environmental changes easier to discover, analyze, and understand.**
