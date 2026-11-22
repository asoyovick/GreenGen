#!/usr/bin/env python3
"""Discover NASA GPM IMERG collections/granules via CMR (Issue #030).

This script uses NASA CMR HTTP APIs (no Earthdata credentials required for
public metadata search). It records query parameters and results for
reproducibility.

Examples:
  python scripts/discover_imerg_cmr.py --short-name GPM_3IMERGM --version 07
  python scripts/discover_imerg_cmr.py --short-name GPM_3IMERGM --version 07 \
      --bbox 33.9 -4.7 41.9 5.5 --start 2001-01-01 --end 2020-12-31 \
      --out docs/nasa-data-guides/imerg_cmr_discovery.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

CMR_BASE = "https://cmr.earthdata.nasa.gov/search"


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=60) as resp:  # nosec - public NASA metadata endpoint
        return json.loads(resp.read().decode("utf-8"))


def discover_collection(short_name: str, version: str | None) -> dict:
    params = {"short_name": short_name, "page_size": 5}
    if version:
        params["version"] = version
    url = f"{CMR_BASE}/collections.json?{urlencode(params)}"
    payload = _get_json(url)
    entries = payload.get("feed", {}).get("entry", [])
    return {"query_url": url, "count": len(entries), "entries": entries}


def discover_granules(short_name: str, version: str | None, bbox=None, start=None, end=None, page_size=10) -> dict:
    params = {"short_name": short_name, "page_size": page_size, "sort_key": "start_date"}
    if version:
        params["version"] = version
    if bbox:
        params["bounding_box"] = ",".join(str(x) for x in bbox)
    if start and end:
        params["temporal"] = f"{start}T00:00:00Z,{end}T23:59:59Z"
    url = f"{CMR_BASE}/granules.json?{urlencode(params)}"
    payload = _get_json(url)
    entries = payload.get("feed", {}).get("entry", [])
    slim = []
    for e in entries:
        data_links = [l.get("href") for l in e.get("links", []) if l.get("rel", "").endswith("/data#")]
        slim.append({
            "title": e.get("title"),
            "id": e.get("id"),
            "time_start": e.get("time_start"),
            "time_end": e.get("time_end"),
            "granule_size": e.get("granule_size"),
            "data_links": data_links,
            "boxes": e.get("boxes"),
        })
    return {"query_url": url, "count_returned": len(entries), "granules": slim}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--short-name", default="GPM_3IMERGM")
    ap.add_argument("--version", default="07")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"))
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--page-size", type=int, default=10)
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tool": "scripts/discover_imerg_cmr.py",
        "cmr_base": CMR_BASE,
        "query": {
            "short_name": args.short_name,
            "version": args.version,
            "bbox": args.bbox,
            "start": args.start,
            "end": args.end,
            "page_size": args.page_size,
        },
        "collection": discover_collection(args.short_name, args.version),
        "granules": discover_granules(args.short_name, args.version, args.bbox, args.start, args.end, args.page_size),
    }
    text = json.dumps(result, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"Wrote {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
