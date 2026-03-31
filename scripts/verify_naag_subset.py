#!/usr/bin/env python3
"""
Run CourtListener verification + canonical spot checks on a subset of NAAG amicus PDFs.

Requires:
  - ``COURTLISTENER_API_KEY`` (and network)
  - ``python scripts/download_naag_amicus_briefs.py`` (PDFs under ``downloaded_briefs/naag_amicus/``)

Uses ``tests/fixtures/naag_verify_manifest.json`` (``citation_field_rules`` for verified URLs/names).

Examples::

    python scripts/verify_naag_subset.py
    python scripts/verify_naag_subset.py --manifest path/to/other_manifest.json
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "tests" / "fixtures" / "naag_verify_manifest.json"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify NAAG PDF subset with CourtListener + canonical rules.")
    p.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Golden manifest (default: {DEFAULT_MANIFEST})",
    )
    args = p.parse_args(argv)

    sys.path.insert(0, str(REPO_ROOT))
    from src.config import COURTLISTENER_API_KEY

    if not (COURTLISTENER_API_KEY or "").strip():
        print("verify_naag_subset: set COURTLISTENER_API_KEY in the environment.", file=sys.stderr)
        return 2

    m = args.manifest.resolve()
    if not m.is_file():
        print(f"verify_naag_subset: missing manifest {m}", file=sys.stderr)
        return 2

    sample = REPO_ROOT / "downloaded_briefs" / "naag_amicus" / "18_AmEx-v-Italian-Colors_2012.pdf"
    if not sample.is_file():
        print(
            "verify_naag_subset: NAAG PDFs not found. Run: python scripts/download_naag_amicus_briefs.py",
            file=sys.stderr,
        )
        return 2

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "brief_goldens.py"),
        "verify",
        "--manifest",
        str(m),
        "--briefs-dir",
        str(REPO_ROOT),
    ]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(cmd, cwd=str(REPO_ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
