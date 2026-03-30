"""
Smoke extraction over PDFs in ``downloaded_briefs/`` (or ``CASSTRAINER_DOWNLOADED_BRIEFS_DIR``).

That folder is gitignored. This module is **not collected** unless
``CASSTRAINER_DOWNLOADED_BRIEF_TESTS=1`` is set (see ``tests/conftest.py``), so GitHub
CI and normal ``pytest`` runs stay quiet.

Run locally (Windows PowerShell)::

  $env:CASSTRAINER_DOWNLOADED_BRIEF_TESTS='1'
  python -m pytest tests/test_downloaded_briefs_optional.py -q --no-cov -o addopts=

Or point at another directory::

  $env:CASSTRAINER_DOWNLOADED_BRIEF_TESTS='1'
  $env:CASSTRAINER_DOWNLOADED_BRIEFS_DIR='D:\\dev\\casestrainer\\downloaded_briefs'
  python -m pytest tests/test_downloaded_briefs_optional.py -q --no-cov -o addopts=

Or: ``python scripts/ci_regression.py --with-downloaded-briefs``
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


def _resolve_briefs_dir() -> Path | None:
    env = (os.environ.get("CASSTRAINER_DOWNLOADED_BRIEFS_DIR") or "").strip()
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    cand = _repo_root() / "downloaded_briefs"
    return cand if cand.is_dir() else None


def _iter_brief_pdfs(*, limit: int = 30) -> list[Path]:
    root = _resolve_briefs_dir()
    if not root:
        return []
    return sorted(root.rglob("*.pdf"))[:limit]


# Below this length, extraction is often a cover page or partial OCR; do not require cites.
# Some real filings (e.g. short SG memoranda) also have no reporter citations in the text layer;
# zero cites is valid then—only assert when the extract is long enough to expect them.
MIN_TEXT_CHARS_FOR_CITATION_ASSERT = 4000


@pytest.mark.local_briefs
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.timeout(600)
def test_downloaded_briefs_extraction_smoke():
    paths = _iter_brief_pdfs(limit=30)
    if not paths:
        pytest.skip(
            "No PDFs found: add files under repo downloaded_briefs/ or set "
            "CASSTRAINER_DOWNLOADED_BRIEFS_DIR to a directory containing .pdf files."
        )
    errors: list[str] = []
    for pdf_path in paths:
        try:
            text, _method = extract_text_from_file_unified(str(pdf_path), verbose=False)
            assert len(text) >= 200, f"expected >= 200 chars of text, got {len(text)}"
            cfg = ProcessingConfig(enable_verification=False)
            result = extract_citations_unified(text, cfg)
            citations = result.get("citations", result) if isinstance(result, dict) else result
            if not isinstance(citations, list):
                citations = list(citations) if citations else []
            if len(text) >= MIN_TEXT_CHARS_FOR_CITATION_ASSERT:
                assert len(citations) >= 1, (
                    "expected at least one citation mention when extract is substantial "
                    f"({len(text)} chars)"
                )
        except Exception as exc:
            errors.append(f"{pdf_path}: {exc}")
    assert not errors, "Failures:\n" + "\n".join(errors)
