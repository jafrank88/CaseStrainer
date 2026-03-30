"""
End-to-end extraction smoke for 1031351.pdf (Erickson v. Pharmacia).

Not part of the default wolf gate (slow). Run when you have the PDF locally:

  set CASSTRAINER_TEST_PDF=file:///D:/dev/casestrainer/1031351.pdf
  python -m pytest tests/test_1031351_pdf_smoke.py -q --no-cov -o addopts=

Or rely on 1031351.pdf in the repo root if present and omit the env var.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote

import pytest

from src.models import ProcessingConfig
from src.unified_citation_processor_v2 import extract_citations_unified
from src.unified_text_extractor import extract_text_from_file_unified


def _file_uri_or_path_to_path(raw: str) -> Path:
    s = raw.strip()
    if s.lower().startswith("file:"):
        parsed = urlparse(s)
        path = unquote(parsed.path or "")
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
        return Path(path)
    return Path(s)


def _resolve_pdf_path() -> Optional[Path]:
    env = (os.environ.get("CASSTRAINER_TEST_PDF") or "").strip()
    if env:
        p = _file_uri_or_path_to_path(env)
        return p if p.is_file() else None
    root = Path(__file__).resolve().parent.parent
    cand = root / "1031351.pdf"
    return cand if cand.is_file() else None


@pytest.mark.integration
@pytest.mark.timeout(600)
def test_extract_citations_from_1031351_pdf():
    pdf = _resolve_pdf_path()
    if pdf is None:
        pytest.skip(
            "Set CASSTRAINER_TEST_PDF to a PDF path or file:// URL, or place 1031351.pdf at repo root."
        )

    text, _method = extract_text_from_file_unified(str(pdf), verbose=False)
    assert len(text) > 10_000, "Expected a full opinion-length extract"

    cfg = ProcessingConfig(enable_verification=False)
    result = extract_citations_unified(text, cfg)
    citations = result.get("citations", result) if isinstance(result, dict) else result
    if not isinstance(citations, list):
        citations = list(citations) if citations else []
    assert len(citations) >= 35, f"Expected many citations from 1031351; got {len(citations)}"

    joined = " ".join(
        f"{getattr(c, 'citation', '')} {getattr(c, 'extracted_case_name', '')}" for c in citations
    )
    text_l = text.lower()
    assert "erickson" in text_l and "pharmacia" in text_l
    assert "erickson" in joined.lower() or "pharmacia" in joined.lower() or "wn." in joined.lower()
