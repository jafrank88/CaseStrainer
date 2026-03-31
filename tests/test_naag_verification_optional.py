"""
CourtListener verification + canonical ``citation_field_rules`` on NAAG amicus PDFs.

Requires:
  - ``CASSTRAINER_NAAG_VERIFY_TESTS=1`` (see ``tests/conftest.py``)
  - ``COURTLISTENER_API_KEY`` and network access
  - ``downloaded_briefs/naag_amicus/*.pdf`` from ``scripts/download_naag_amicus_briefs.py``

Manifest: ``tests/fixtures/naag_verify_manifest.json`` (four briefs, ~10+ minutes total).

Run::

    set CASSTRAINER_NAAG_VERIFY_TESTS=1
    python -m pytest tests/test_naag_verification_optional.py -q --no-cov -o addopts= --tb=short

Or CLI (same checks)::

    python scripts/verify_naag_subset.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "tests" / "fixtures" / "naag_verify_manifest.json"
SAMPLE_PDF = REPO / "downloaded_briefs" / "naag_amicus" / "18_AmEx-v-Italian-Colors_2012.pdf"


@pytest.mark.local_briefs
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.timeout(1200)
def test_naag_verification_and_canonical_goldens():
    if not SAMPLE_PDF.is_file():
        pytest.skip(
            "NAAG PDFs missing: run python scripts/download_naag_amicus_briefs.py "
            f"(expected {SAMPLE_PDF})"
        )
    if not MANIFEST.is_file():
        pytest.fail(f"Missing manifest {MANIFEST}")

    try:
        from src.config import COURTLISTENER_API_KEY
    except ImportError:
        pytest.fail("Could not import src.config")

    if not (COURTLISTENER_API_KEY or "").strip():
        pytest.skip("COURTLISTENER_API_KEY not set; cannot run live verification.")

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "brief_goldens.py"),
        "verify",
        "--manifest",
        str(MANIFEST),
        "--briefs-dir",
        str(REPO),
    ]
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    proc = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1100)
    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        pytest.fail(f"brief_goldens verify failed ({proc.returncode}):\n{out[-8000:]}")
