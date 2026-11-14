#!/usr/bin/env python3
"""
Mock/synthetic scientific engine service for GreenGen backend integration testing.

IMPORTANT: This service returns SYNTHETIC, CLEARLY-LABELLED test data only.
It does NOT retrieve NASA data and does NOT produce real scientific results.
Use only for development/integration validation of backend/frontend workflows.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

PORT = int(os.environ.get("MOCK_ENGINE_PORT", "8090"))
_jobs = {}
_lock = threading.Lock()


def _synthetic_result(execution_id: str, payload: dict) -> dict:
    bounds = payload.get("bounds") or {}
    period = payload.get("period") or {}
    inv = payload.get("investigation_id") or "INV-UNKNOWN"
    return {
        "contract": "analysis-response",
        "version": "0.1-draft-synthetic-mock",
        "execution_id": execution_id,
        "status": "completed",
        "synthetic": True,
        "warning": "SYNTHETIC TEST DATA ONLY. Not NASA observations and not real scientific results.",
        "cells": [
            {
                "cell_id": "mock-cell-1",
                "lat": bounds.get("min_lat", 0),
                "lon": bounds.get("min_lon", 0),
                "n_observations": 120,
                "completeness": 1.0,
                "mean": {"value": 50.0, "units": "mm/month (synthetic)"},
                "sens_slope": {"value": -0.1, "units": "mm/month/year (synthetic)", "ci_lower": -0.2, "ci_upper": 0.0},
                "mann_kendall": {"p_value": 0.04},
                "classification": "significant_decrease",
                "flags": ["SYNTHETIC_TEST_DATA"],
            }
        ],
        "run_metadata": {
            "investigation_id": inv,
            "bounds": bounds,
            "period": period,
            "methods": ["synthetic_mock"],
            "engine": "mock_engine.py",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Synthetic fixture for integration testing only.",
        },
    }


def _complete_later(execution_id: str, payload: dict, delay: float = 1.0):
    def run():
        time.sleep(delay)
        with _lock:
            if execution_id in _jobs:
                _jobs[execution_id]["status"] = "completed"
                _jobs[execution_id]["results"] = _synthetic_result(execution_id, payload)
    threading.Thread(target=run, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = "GreenGenMockEngine/0.1"

    def _send(self, code: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/health", "/v1/health"):
            return self._send(200, {"status": "ok", "service": "mock-engine", "synthetic": True})
        if path.startswith("/v1/analyses/"):
            exec_id = path.rsplit("/", 1)[-1]
            with _lock:
                job = _jobs.get(exec_id)
            if not job:
                return self._send(404, {"error": {"code": "NOT_FOUND", "message": "analysis not found"}})
            resp = {"execution_id": exec_id, "status": job["status"], "synthetic": True}
            if job["status"] == "completed":
                resp["results"] = job["results"]
            return self._send(200, resp)
        return self._send(404, {"error": {"code": "NOT_FOUND", "message": "unknown endpoint"}})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self._send(400, {"error": {"code": "VALIDATION_ERROR", "message": "invalid json"}})

        if path in ("/v1/analyses", "/api/v1/analyses"):
            exec_id = payload.get("execution_id") or f"mock-{uuid.uuid4().hex[:8]}"
            job_ref = f"mockjob-{uuid.uuid4().hex[:8]}"
            with _lock:
                _jobs[exec_id] = {"status": "queued", "payload": payload, "engine_job_reference": job_ref}
            _complete_later(exec_id, payload, delay=float(payload.get("mock_delay_seconds", 1.0)))
            return self._send(202, {
                "execution_id": exec_id,
                "engine_job_reference": job_ref,
                "status": "queued",
                "synthetic": True,
                "message": "Synthetic mock analysis accepted (not real NASA/scientific results).",
            })

        return self._send(404, {"error": {"code": "NOT_FOUND", "message": "unknown endpoint"}})

    def log_message(self, fmt, *args):
        print(f"[mock-engine] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Mock engine listening on http://0.0.0.0:{PORT} (SYNTHETIC TEST DATA ONLY)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
