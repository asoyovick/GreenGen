#!/usr/bin/env python3
"""Check whether NASA Earthdata is reachable and whether credentials work.

This script never prompts for a password. It checks:
  1. CMR (the NASA catalog behind Earthdata Search) over HTTPS.
  2. earthaccess login using only environment variables or ~/.netrc.

It does not download data. Exit code 0 means both checks passed; 2 means CMR is
reachable but no usable credentials were found; 1 means CMR is unreachable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def check_cmr() -> tuple[bool, str]:
    try:
        import httpx
    except ImportError:
        return False, "httpx is not installed"
    url = "https://cmr.earthdata.nasa.gov/search/collections.json"
    try:
        r = httpx.get(url, params={"short_name": "GPM_3IMERGM", "page_size": 1}, timeout=20)
        r.raise_for_status()
        n = len(r.json().get("feed", {}).get("entry", []))
        return n > 0, f"CMR reachable; GPM_3IMERGM entries returned: {n}"
    except Exception as exc:  # network errors are the point of this check
        return False, f"CMR unreachable: {type(exc).__name__}: {exc}"


def check_login() -> tuple[bool, str]:
    try:
        import earthaccess
    except ImportError:
        return False, "earthaccess is not installed"
    have_env = bool(os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD"))
    have_netrc = (Path.home() / ".netrc").exists()
    if not have_env and not have_netrc:
        return False, "no EARTHDATA_USERNAME/PASSWORD and no ~/.netrc; login not attempted"
    try:
        auth = earthaccess.login(strategy="environment" if have_env else "netrc")
        if auth.authenticated:
            return True, "Earthdata Login authenticated"
        return False, "Earthdata Login present but not authenticated"
    except Exception as exc:
        return False, f"Earthdata Login failed: {type(exc).__name__}: {exc}"


def main() -> int:
    cmr_ok, cmr_msg = check_cmr()
    login_ok, login_msg = check_login()
    print(f"CMR:    {'OK' if cmr_ok else 'FAIL'} - {cmr_msg}")
    print(f"LOGIN:  {'OK' if login_ok else 'MISSING'} - {login_msg}")
    if not cmr_ok:
        print("\nNASA is not reachable from this environment. Use synthetic mode.")
        return 1
    if not login_ok:
        print(
            "\nNASA is reachable, but authenticated downloads are not available.\n"
            "Synthetic mode remains fully supported. To run the real pipeline, create\n"
            "a free Earthdata Login account, approve the GES DISC / LP DAAC / PO.DAAC\n"
            "applications, then set EARTHDATA_USERNAME and EARTHDATA_PASSWORD (or ~/.netrc)."
        )
        return 2
    print("\nNASA access is available. Run: make pipeline-real")
    return 0


if __name__ == "__main__":
    sys.exit(main())
