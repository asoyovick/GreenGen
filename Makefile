SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install synthetic pipeline pipeline-real overlays api frontend test verify-earthdata demo clean-generated

help:
	@echo "Global Change Explorer"
	@echo "  make install          create .venv and install Python dependencies"
	@echo "  make synthetic        generate clearly fake 0.5-degree cubes (fast, no NASA access)"
	@echo "  make pipeline         run prep + trends + overlays on synthetic data"
	@echo "  make pipeline-real    run the real NASA pipeline (needs Earthdata credentials)"
	@echo "  make api              start FastAPI on http://127.0.0.1:8000"
	@echo "  make frontend         start Vite dev server on http://127.0.0.1:5173"
	@echo "  make test             run the pytest suite (synthetic fixtures, no network)"
	@echo "  make verify-earthdata check CMR and Earthdata Login availability"
	@echo "  make demo             build frontend and serve everything from FastAPI on :8000"

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	cd frontend && npm install

synthetic:
	$(PY) scripts/make_synthetic_data.py --config config/app.yaml

pipeline:
	$(PY) scripts/run_pipeline.py --synthetic

pipeline-real:
	$(PY) scripts/run_pipeline.py --real

overlays:
	$(PY) scripts/export_overlays.py --mode synthetic

api:
	$(PY) -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	$(PY) -m pytest -q

verify-earthdata:
	$(PY) scripts/verify_earthdata.py

demo: pipeline
	cd frontend && npm run build
	$(PY) -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

clean-generated:
	rm -rf layers/overlays data/synthetic
