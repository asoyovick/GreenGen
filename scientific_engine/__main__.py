"""Run the scientific engine HTTP service.

Usage:
  python -m scientific_engine.service  (uvicorn target: scientific_engine.service:app)
  python -m uvicorn scientific_engine.service:app --host 0.0.0.0 --port 8090
"""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("scientific_engine.service:app", host="0.0.0.0", port=8090, reload=False)
