#!/usr/bin/env python3
"""Search and download NASA Earthdata granules and write a provenance manifest.

Examples:
  python download_granules.py --short-name GPM_3IMERGM --version 07 \
      --start 2002-01-01 --end 2024-12-31 --dry-run
  python download_granules.py --short-name GPM_3IMERGM --version 07 \
      --start 2002-01-01 --end 2024-12-31 --out data/raw/imerg

Requires: pip install earthaccess. Verify the short name and version in
Earthdata Search first; they change over time.
"""
import argparse
import datetime
import json
import os
import sys


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--short-name", required=True, help="Dataset short name, e.g. GPM_3IMERGM")
    ap.add_argument("--version", default=None, help="Dataset version, e.g. 07")
    ap.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"),
                    help="Optional bounding box; omit for global")
    ap.add_argument("--out", default="data/raw", help="Output directory")
    ap.add_argument("--dry-run", action="store_true", help="Only report how many granules match")
    ap.add_argument("--limit", type=int, default=None, help="Cap the number of granules (useful for a first test)")
    return ap.parse_args()


def main():
    args = parse_args()
    try:
        import earthaccess
    except ImportError:
        sys.exit("earthaccess is not installed. Run: pip install earthaccess")

    earthaccess.login()  # env vars, ~/.netrc, then interactive prompt

    query = {"short_name": args.short_name, "temporal": (args.start, args.end)}
    if args.version:
        query["version"] = args.version
    if args.bbox:
        query["bounding_box"] = tuple(args.bbox)
    if args.limit:
        query["count"] = args.limit

    results = earthaccess.search_data(**query)
    print(f"Found {len(results)} granules for {args.short_name} {args.version or '(any version)'}")
    if not results:
        print("No granules. Check short name, version, and dates in Earthdata Search; remove filters one at a time.")
        return 1
    if args.dry_run:
        return 0

    os.makedirs(args.out, exist_ok=True)
    files = earthaccess.download(results, args.out)
    manifest = {
        "short_name": args.short_name,
        "version": args.version,
        "temporal": [args.start, args.end],
        "bounding_box": args.bbox,
        "n_granules_found": len(results),
        "files": [str(f) for f in files],
        "download_date": datetime.date.today().isoformat(),
        "doi": None,  # fill in from the dataset page for citation
    }
    with open(os.path.join(args.out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Downloaded {len(files)} files to {args.out}; wrote manifest.json (fill in the DOI)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
