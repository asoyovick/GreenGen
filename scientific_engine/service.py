"""HTTP service adapter for Go backend ↔ Python scientific engine.

Draft endpoints (aligned with backend/internal/engine/client.go):
- POST /v1/analyses  -> accept analysis request, start processing
- GET  /v1/analyses/{id} -> status/results

Jobs run in background threads and store state in memory.
"""

from __future__ import annotations

import threading
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from .grid_analysis import analyze_grid
from .io import load_observation


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


app = FastAPI(title="GreenGen Scientific Engine", version="0.1.0-draft")

_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _set_job(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _jobs.setdefault(job_id, {"id": job_id})
        job.update(fields)
        job["updated_at"] = _utc_now()


def _run_job(job_id: str, req: dict[str, Any]) -> None:
    _set_job(job_id, status="running", started_at=_utc_now())
    try:
        investigation_id = req.get("investigation_id")
        bounds = req.get("bounds")
        period = req.get("period")
        config = req.get("config") or {}
        dataset = req.get("dataset") or {}
        observation_ref = req.get("observation_ref") or config.get("observation_ref") or dataset.get("observation_ref")
        variable = config.get("variable") or dataset.get("variable") or req.get("variable")

        da, input_meta = load_observation(str(observation_ref) if observation_ref else "", variable=variable)
        dataset_meta = {**dataset, **input_meta}
        results = analyze_grid(
            da,
            investigation_id=investigation_id,
            bounds=bounds,
            period=period,
            config=config,
            dataset_meta=dataset_meta,
            variable_name=variable,
        )
        # Ensure no synthetic marker in emitted results
        results["synthetic"] = False
        results.setdefault("run_metadata", {})["observation_ref"] = observation_ref
        _set_job(job_id, status="completed", results=results, completed_at=_utc_now(), error=None, error_message=None)
    except Exception as e:
        _set_job(
            job_id,
            status="failed",
            completed_at=_utc_now(),
            error=type(e).__name__,
            error_message=str(e),
            error_code="ANALYSIS_FAILED",
            # include traceback only for debugging contexts? keep minimal
            details={"traceback": traceback.format_exc(limit=5)},
        )


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "greengen-scientific-engine", "version": "0.1.0-draft"}


@app.post("/v1/analyses")
def submit_analysis(req: dict[str, Any]) -> dict[str, Any]:
    execution_id = req.get("execution_id") or f"exec_{uuid.uuid4().hex[:12]}"
    job_id = execution_id
    with _lock:
        if job_id in _jobs and _jobs[job_id].get("status") in {"queued", "running", "completed"}:
            # idempotent-ish replay
            job = _jobs[job_id]
            return {
                "execution_id": job_id,
                "engine_job_reference": job_id,
                "status": job.get("status", "queued"),
            }
        _jobs[job_id] = {
            "id": job_id,
            "execution_id": job_id,
            "status": "queued",
            "request": req,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
    t = threading.Thread(target=_run_job, args=(job_id, req), daemon=True)
    t.start()
    return {"execution_id": job_id, "engine_job_reference": job_id, "status": "queued"}


@app.get("/v1/analyses/{job_id}")
def get_analysis(job_id: str) -> dict[str, Any]:
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Analysis job not found", "details": {"id": job_id}})
    resp: dict[str, Any] = {
        "execution_id": job.get("execution_id", job_id),
        "status": job.get("status", "unknown"),
    }
    if job.get("error_message"):
        resp["error"] = job.get("error_message")
        resp["error_code"] = job.get("error_code")
        resp["error_message"] = job.get("error_message")
    if job.get("status") == "completed" and job.get("results") is not None:
        resp["results"] = job.get("results")
    # include selected metadata for debugging/traceability (non-fabricated)
    for k in ("created_at", "started_at", "completed_at", "updated_at"):
        if job.get(k):
            resp[k] = job[k]
    return resp
