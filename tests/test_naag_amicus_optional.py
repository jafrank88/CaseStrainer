"""
Smoke extraction on ``downloaded_briefs/naag_amicus/*.pdf`` (NAAG multistate amicus corpus).

The folder is gitignored. This module is omitted from collection unless
``CASSTRAINER_NAAG_AMICUS_TESTS=1`` (see ``tests/conftest.py``).

Populate PDFs::

    python scripts/download_naag_amicus_briefs.py

Run::

    set CASSTRAINER_NAAG_AMICUS_TESTS=1
    python -m pytest tests/test_naag_amicus_optional.py -q --no-cov -o addopts=
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.models import ProcessingConfig
from src.unified_citation_processor_v2 import extract_citations_unified
from src.unified_text_extractor import extract_text_from_file_unified


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _naag_dir() -> Path | None:
    env = (os.environ.get("CASSTRAINER_NAAG_AMICUS_DIR") or "").strip()
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    cand = _repo_root() / "downloaded_briefs" / "naag_amicus"
    return cand if cand.is_dir() else None


def _iter_pdfs(*, limit: int) -> list[Path]:
    root = _naag_dir()
    if not root:
        return []
    return sorted(root.glob("*.pdf"))[:limit]


# Below this, do not require citations (short filings or odd text layers).
MIN_TEXT_CHARS_FOR_CITATION_ASSERT = 20_000

# Known NAAG PDFs where PyMuPDF yields no usable text (image-only or protected layer).
SKIP_MIN_TEXT = frozenset({"24_DDAVP-2d-Cir_2007.pdf"})


@pytest.mark.local_briefs
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.timeout(900)
def test_naag_amicus_extraction_smoke():
    paths = _iter_pdfs(limit=30)
    if not paths:
        pytest.skip(
            "No NAAG PDFs: run scripts/download_naag_amicus_briefs.py, or set "
            "CASSTRAINER_NAAG_AMICUS_DIR to a folder of .pdf files."
        )
    errors: list[str] = []
    for pdf_path in paths:
        try:
            text, _m = extract_text_from_file_unified(str(pdf_path), verbose=False)
            if pdf_path.name in SKIP_MIN_TEXT:
                continue
            assert len(text) >= 200, f"{pdf_path.name}: expected >= 200 chars, got {len(text)}"
            cfg = ProcessingConfig(enable_verification=False)
            result = extract_citations_unified(text, cfg)
            citations = result.get("citations", result) if isinstance(result, dict) else result
            if not isinstance(citations, list):
                citations = list(citations) if citations else []
            n = len(citations)
            if len(text) >= MIN_TEXT_CHARS_FOR_CITATION_ASSERT and n < 1:
                errors.append(f"{pdf_path.name}: text={len(text)} but citation_count={n}")
        except Exception as e:  # noqa: BLE001 — aggregate failures for summary
            errors.append(f"{pdf_path.name}: {e}")
    assert not errors, ";\n".join(errors)
