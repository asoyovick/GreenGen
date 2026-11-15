#!/usr/bin/env python3
"""Build the offline place gazetteer from Natural Earth (1:50m) GeoJSON.

Downloads are not performed here; provide local Natural Earth GeoJSON files
(default: data/places/raw/*.geojson). Sources should be the official Natural
Earth data or the nvkelso/natural-earth-vector repository. Record source,
version, and access date in docs/DATA_SOURCES.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.places.gazetteer import (  # noqa: E402
    Gazetteer,
    build_city_records,
    build_country_records,
    build_region_records,
    build_sea_records,
    finalize_record,
    save_gazetteer,
)

RAW_FILES = {
    "countries": "ne_50m_admin_0_countries.geojson",
    "regions": "ne_50m_admin_1_states_provinces.geojson",
    "cities": "ne_50m_populated_places.geojson",
    "seas": "ne_50m_geography_marine_polys.geojson",
}

# simplification tolerances in degrees (display, mask). 0 = keep original.
# 1:50m is already generalized; keep mask geometry close to original.
SIMPLIFY = {
    "country": (0.03, 0.01),
    "region": (0.02, 0.005),
    "city": (0.0, 0.0),
    "sea": (0.05, 0.01),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", default=str(REPO_ROOT / "data/places/raw"))
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "data/places/gazetteer"))
    ap.add_argument("--source-note", default="Natural Earth 1:50m via nvkelso/natural-earth-vector (raw.githubusercontent.com)")
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    out = Path(args.out_dir)
    missing = [name for name, fn in RAW_FILES.items() if not (raw / fn).exists()]
    if missing:
        print("Missing raw files in", raw, file=sys.stderr)
        for name in missing:
            print(" -", RAW_FILES[name], file=sys.stderr)
        return 2

    print("Building countries...")
    countries = build_country_records(raw / RAW_FILES["countries"])
    print(f"  {len(countries)} countries")
    print("Building regions...")
    regions = build_region_records(raw / RAW_FILES["regions"], countries)
    print(f"  {len(regions)} regions")
    print("Building cities...")
    cities = build_city_records(raw / RAW_FILES["cities"], countries, regions)
    print(f"  {len(cities)} cities")
    print("Building seas/marine areas...")
    seas = build_sea_records(raw / RAW_FILES["seas"])
    print(f"  {len(seas)} seas")

    all_places: list[dict] = []
    for level, items in [("country", countries), ("region", regions), ("city", cities), ("sea", seas)]:
        sd, sm = SIMPLIFY[level]
        for rec, geom in items:
            final, _, _ = finalize_record(rec, geom, simplify_display=sd, simplify_mask=sm)
            all_places.append(final)

    # de-duplicate ids if any collisions
    seen: dict[str, int] = {}
    for p in all_places:
        pid = p["id"]
        if pid in seen:
            seen[pid] += 1
            p["id"] = f"{pid}-{seen[pid]}"
        else:
            seen[pid] = 0

    gaz = Gazetteer(all_places)
    meta = {
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": args.source_note,
        "raw_dir": str(raw),
        "counts": {lvl: len(gaz.by_level.get(lvl, [])) for lvl in ["country", "region", "city", "sea"]},
        "simplify_deg": SIMPLIFY,
        "note": "Boundaries and names as provided by Natural Earth; for reference only.",
    }
    save_gazetteer(out, all_places, gaz.search_index, meta)
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Wrote gazetteer to", out)
    print(json.dumps(meta["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
