"""FastAPI application for the Global Change Explorer.

All answers come from precomputed layers loaded once at startup. No endpoint
downloads from NASA or runs a trend test on demand.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.layer_store import LayerStore
from src.common.config import REPO_ROOT, AppConfig, load_app_config

VERSION = "0.1.0"


def create_app(
    cfg: AppConfig | None = None,
    *,
    layers_dir: str | Path | None = None,
    overlays_root: str | Path | None = None,
) -> FastAPI:
    cfg = cfg or load_app_config()
    overlays_root_path = Path(overlays_root) if overlays_root else cfg.overlays_dir
    store = LayerStore(
        cfg,
        layers_dir=Path(layers_dir) if layers_dir else None,
        overlays_dir=overlays_root_path / cfg.mode,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load every layer once; requests are pure lookups.
        app.state.store.load()
        yield

    app = FastAPI(
        title="Global Change Explorer API",
        version=VERSION,
        description="Click-to-explore change detection on precomputed NASA/synthetic trend layers.",
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.cfg = cfg

    origins = os.environ.get(
        "GCE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()] or ["*"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def mode_headers(request: Request, call_next):
        response = await call_next(request)
        s: LayerStore = request.app.state.store
        response.headers["X-GCE-Mode"] = s.cfg.mode
        if s.synthetic:
            response.headers["X-GCE-Synthetic"] = "true"
        return response

    def require_layers(request: Request) -> LayerStore:
        s: LayerStore = request.app.state.store
        if not s.available:
            detail = (
                "No trend layers are loaded. Run `make pipeline` first, or set "
                "GCE_LAYERS_DIR to a directory containing <variable>_trend.zarr. "
                + " ".join(s.errors)
            ).strip()
            raise HTTPException(status_code=503, detail=detail)
        return s

    @app.get("/api")
    def api_index():
        return {
            "name": "Global Change Explorer API",
            "version": VERSION,
            "mode": cfg.mode,
            "endpoints": [
                "/api/health", "/api/variables", "/api/report",
                "/api/timeseries", "/api/layers", "/docs",
            ],
            "note": "Observed change only, not a forecast.",
        }

    @app.get("/api/health")
    def health(request: Request):
        s: LayerStore = request.app.state.store
        return {
            "status": "ok" if s.available else "degraded",
            "version": VERSION,
            "mode": s.cfg.mode,
            "synthetic": s.synthetic,
            "synthetic_banner": "SYNTHETIC DEMO DATA, not real observations." if s.synthetic else None,
            "variables_loaded": sorted(s.datasets),
            "overlays_available": s.overlay_metadata is not None,
            "grid": s.grid,
            "period": list(s.cfg.period),
            "errors": s.errors,
            "not_a_forecast": "Observed change only, not a forecast.",
        }

    @app.get("/api/variables")
    def variables(request: Request):
        s = require_layers(request)
        return s.variables_payload()

    @app.get("/api/layers")
    def layers(request: Request):
        s: LayerStore = request.app.state.store
        try:
            return s.layers_payload()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/report")
    def report(
        request: Request,
        lat: float = Query(..., ge=-90, le=90, description="Latitude in degrees"),
        lon: float = Query(..., ge=-180, le=180, description="Longitude in degrees"),
        window: float = Query(5.0, gt=0, le=90, description="Nearby half-width in degrees"),
    ):
        s = require_layers(request)
        try:
            return s.report(lat, lon, window)
        except Exception as exc:  # keep the API alive and return a clear error
            raise HTTPException(
                status_code=500,
                detail=f"Could not build a report at ({lat}, {lon}): {type(exc).__name__}: {exc}",
            ) from exc

    @app.get("/api/timeseries")
    def timeseries(
        request: Request,
        lat: float = Query(..., ge=-90, le=90),
        lon: float = Query(..., ge=-180, le=180),
        variable: str = Query(..., description="Variable key, e.g. precipitation"),
    ):
        s = require_layers(request)
        if variable not in s.datasets:
            known = ", ".join(sorted(s.datasets)) or "none"
            raise HTTPException(
                status_code=404,
                detail=f"Unknown variable {variable!r} for this mode. Available: {known}.",
            )
        try:
            return s.timeseries(variable, lat, lon)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Could not build a time series at ({lat}, {lon}) for {variable}: {exc}",
            ) from exc

    @app.exception_handler(404)
    async def not_found(_request: Request, exc):
        return JSONResponse(status_code=404, content={"detail": getattr(exc, "detail", "Not found")})

    # Overlay images (PNG) are static; metadata comes from /api/layers.
    overlays_root_path.mkdir(parents=True, exist_ok=True)
    app.mount("/overlays", StaticFiles(directory=str(overlays_root_path), check_dir=False), name="overlays")

    # In demo mode the built frontend is served by the same process.
    dist = REPO_ROOT / "frontend" / "dist"
    if dist.exists():

        @app.get("/", include_in_schema=False)
        def frontend_index():
            return FileResponse(dist / "index.html")

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app


app = create_app()
