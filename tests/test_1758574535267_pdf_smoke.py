"""
Optional local-PDF smoke test for 1758574535267.pdf (copyright / citation survey style).

The PDF stays gitignored (*.pdf at repo root). CI skips this test when the file is absent.

Run locally (Windows example):

  set CASSTRAINER_TEST_PDF_1758574535267=D:\\dev\\casestrainer\\1758574535267.pdf
  python -m pytest tests/test_1758574535267_pdf_smoke.py -v --no-cov -o addopts=

Or place 1758574535267.pdf at the repository root and omit the env var.

file:// URLs are accepted, same as CASSTRAINER_TEST_PDF in test_1031351_pdf_smoke.py.
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

DEFAULT_BASENAME = "1758574535267.pdf"
ENV_PDF = "CASSTRAINER_TEST_PDF_1758574535267"


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
    env = (os.environ.get(ENV_PDF) or "").strip()
    if env:
        p = _file_uri_or_path_to_path(env)
        return p if p.is_file() else None
    root = Path(__file__).resolve().parent.parent
    cand = root / DEFAULT_BASENAME
    return cand if cand.is_file() else None


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.local_pdf
@pytest.mark.timeout(600)
def test_extract_citations_from_1758574535267_pdf():
    pdf = _resolve_pdf_path()
    if pdf is None:
        pytest.skip(
            f"Place {DEFAULT_BASENAME} at repo root or set {ENV_PDF} to a PDF path or file:// URL."
        )

    text, _method = extract_text_from_file_unified(str(pdf), verbose=False)
    assert len(text) > 5_000, "Expected a substantial extract from this survey-style PDF"

    cfg = ProcessingConfig(enable_verification=False)
    result = extract_citations_unified(text, cfg)
    citations = result.get("citations", result) if isinstance(result, dict) else result
    if not isinstance(citations, list):
        citations = list(citations) if citations else []

    assert len(citations) >= 25, f"Expected many citations from survey PDF; got {len(citations)}"

    joined = " ".join(
        f"{getattr(c, 'citation', '')} {getattr(c, 'extracted_case_name', '')}" for c in citations
    ).lower()
    text_l = text.lower()
    # Loose anchors: document should mention copyright doctrine and familiar survey cases
    assert "copyright" in text_l or "fair" in text_l
    assert any(
        token in joined or token in text_l
        for token in ("feist", "napster", "harper", "campbell", "acuff", "sony", "google")
    ), "Expected at least one hallmark case name in text or extraction payload"
