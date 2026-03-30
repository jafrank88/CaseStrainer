#!/usr/bin/env python3
"""
CaseStrainer regression gate — same entry point for GitHub Actions and local runs.

Default behavior matches CI: run the wolf-aligned test modules, excluding
``local_pdf`` (optional on-disk PDFs), ``local_briefs`` (``downloaded_briefs/`` corpus),
and ``production`` (novel-document suite).

Examples
--------
  python scripts/ci_regression.py
  python scripts/ci_regression.py -v
  python scripts/ci_regression.py --with-local-pdf
  python scripts/ci_regression.py --with-downloaded-briefs
  python scripts/ci_regression.py --wolf
  python scripts/ci_regression.py -- --maxfail=1 -k domain

Environment (optional, same as other test entry points)
-------------------------------------------------------
  PYTHONPATH          Repo root should be on path (script cwd is repo root).
  CASSTRAINER_USE_TEST_REDIS  Set to 1 in CI for Redis-backed tests.
  REDIS_URL / CACHE_REDIS_URL  Local Redis when running async/analyze tests.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INI = "pytest-ci-regression.ini"
WOLF_INI = "pytest-wolf.ini"


def _build_marker_expr(with_local_pdf: bool, with_production: bool) -> str | None:
    # Always exclude local_briefs from the ini-listed gate; run those via --with-downloaded-briefs only.
    parts: list[str] = ["not local_briefs"]
    if not with_local_pdf:
        parts.append("not local_pdf")
    if not with_production:
        parts.append("not production")
    return " and ".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run CaseStrainer regression tests (CI + local).",
    )
    parser.add_argument(
        "--with-local-pdf",
        action="store_true",
        help="Include tests marked local_pdf (they still skip if the PDF path is missing).",
    )
    parser.add_argument(
        "--with-production",
        action="store_true",
        help="Include tests marked production (e.g. tests/test_production_unseen_documents.py).",
    )
    parser.add_argument(
        "--with-downloaded-briefs",
        action="store_true",
        help="Set CASSTRAINER_DOWNLOADED_BRIEF_TESTS=1 and run tests/test_downloaded_briefs_optional.py "
        "after the regression gate (requires PDFs under downloaded_briefs/ or CASSTRAINER_DOWNLOADED_BRIEFS_DIR).",
    )
    parser.add_argument(
        "--ini",
        default=DEFAULT_INI,
        metavar="FILE",
        help=f"Pytest config file under repo root (default: {DEFAULT_INI}).",
    )
    parser.add_argument(
        "--wolf",
        action="store_true",
        help=f"Use {WOLF_INI} instead of {DEFAULT_INI} (same marker filters unless disabled).",
    )
    parser.add_argument(
        "--no-marker-filter",
        action="store_true",
        help="Do not pass -m (run all tests in the selected ini file list).",
    )
    args, pytest_rem = parser.parse_known_args(argv)

    if args.with_downloaded_briefs:
        os.environ["CASSTRAINER_DOWNLOADED_BRIEF_TESTS"] = "1"

    ini_name = WOLF_INI if args.wolf else args.ini
    ini_path = REPO_ROOT / ini_name
    if not ini_path.is_file():
        print(f"ci_regression: missing config {ini_path}", file=sys.stderr)
        return 2

    os.chdir(REPO_ROOT)

    def _run_pytest(extra: list[str] | None = None) -> int:
        cmd_l: list[str] = [sys.executable, "-m", "pytest", "-c", str(ini_path)]
        if not args.no_marker_filter:
            mexpr = _build_marker_expr(
                with_local_pdf=args.with_local_pdf,
                with_production=args.with_production,
            )
            if mexpr:
                cmd_l.extend(["-m", mexpr])
        cmd_l.extend(pytest_rem)
        if extra:
            cmd_l.extend(extra)
        return subprocess.run(cmd_l).returncode

    rc = _run_pytest()
    if rc != 0:
        return rc

    if args.with_downloaded_briefs:
        brief_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_downloaded_briefs_optional.py",
            "-q",
            "--tb=short",
            "--no-cov",
            "-o",
            "addopts=",
        ]
        brief_rc = subprocess.run(brief_cmd).returncode
        if brief_rc != 0:
            return brief_rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
