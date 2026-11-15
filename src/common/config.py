"""Configuration loading and path helpers.

All paths in config are relative to the repository root. The mode is never
inferred from files on disk: it comes from config/app.yaml or the GCE_MODE
environment variable, so real and synthetic layers cannot be mixed silently.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    """Return the repository root."""
    return REPO_ROOT


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


@dataclass(frozen=True)
class AppConfig:
    """Validated application configuration."""

    raw: dict[str, Any]
    mode: str

    @property
    def resolution(self) -> float:
        return float(self.raw["grid"]["resolution_deg"])

    @property
    def period(self) -> tuple[str, str]:
        return str(self.raw["period"]["start"]), str(self.raw["period"]["end"])

    @property
    def analysis(self) -> dict[str, Any]:
        return dict(self.raw["analysis"])

    @property
    def variables(self) -> dict[str, Any]:
        return dict(self.raw["variables"])

    def mode_variables(self, mode: str | None = None) -> list[str]:
        mode = mode or self.mode
        return list(self.raw[mode]["variables"])

    @property
    def layers_dir(self) -> Path:
        override = os.environ.get("GCE_LAYERS_DIR")
        if override:
            return Path(override).expanduser().resolve()
        key = "layers_synthetic" if self.mode == "synthetic" else "layers_real"
        return REPO_ROOT / self.raw["paths"][key]

    @property
    def overlays_dir(self) -> Path:
        override = os.environ.get("GCE_OVERLAYS_DIR")
        if override:
            return Path(override).expanduser().resolve()
        return REPO_ROOT / self.raw["paths"]["overlays"]

    def data_dir(self, key: str) -> Path:
        return REPO_ROOT / self.raw["paths"][key]

    def require_mode(self) -> None:
        if self.mode not in {"synthetic", "real"}:
            raise ValueError(f"mode must be 'synthetic' or 'real', got {self.mode!r}")


def load_app_config(path: str | Path | None = None) -> AppConfig:
    """Load config/app.yaml and apply the optional GCE_MODE override."""
    config_path = Path(path) if path else REPO_ROOT / "config" / "app.yaml"
    raw = _read_yaml(config_path)
    mode = os.environ.get("GCE_MODE", raw.get("mode", "synthetic"))
    mode = str(mode).lower()
    if mode not in {"synthetic", "real"}:
        raise ValueError(f"mode must be 'synthetic' or 'real', got {mode!r}")
    cfg = AppConfig(raw=raw, mode=mode)
    cfg.require_mode()
    return cfg


def load_datasets_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load config/datasets.yaml."""
    config_path = Path(path) if path else REPO_ROOT / "config" / "datasets.yaml"
    return _read_yaml(config_path)


def variable_meta(cfg: AppConfig, key: str) -> dict[str, Any]:
    """Return display metadata for a variable key."""
    try:
        meta = dict(cfg.variables[key])
    except KeyError as exc:
        raise KeyError(f"Unknown variable {key!r}") from exc
    meta["key"] = key
    return meta
