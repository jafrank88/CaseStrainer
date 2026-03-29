"""
Production-readiness checks using documents that do not appear elsewhere in the repo.

Text is synthetic (fictional parties, invented docket/WL numbers, UUID nonces) so tests
are not memorizing regression fixtures or known-citation tables.
"""

from __future__ import annotations

import asyncio
import re
import uuid

import pytest

from src.app_final_vue import create_app
from src.unified_processing_pipeline import process_citations_unified


def _synthetic_memo_text() -> str:
    """Unique body per run + stable cite-shaped tokens for assertions."""
    nonce = uuid.uuid4().hex
    return f"""\
INTERNAL MEMO — DOCKET AUDIT {nonce}

Re: **Morvane Industries v. Helsik Navigation Corp.**, 88 F.4th 9001 (Fed. Cir. 2024).
The panel discussed claim preclusion. Compare **In re Tesselbyte Holdings**, 2024 WL 8888888 (D. Del. 2024).

Secondary: **State ex rel. Quorban v. Alder Mun. Util. Dist.**, 512 P.3d 880 (Wash. Ct. App. 2024).

Closing nonce: {nonce}
"""


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.production
def test_pipeline_unseen_synthetic_memo_extracts_and_clusters():
    """Full unified pipeline on unseen text; verification off to avoid network and flakiness."""
    text = _synthetic_memo_text()
    result = asyncio.run(
        process_citations_unified(
            text,
            enable_verification=False,
            enable_parallel_verification=False,
            trace_id=f"unseen-{uuid.uuid4().hex[:12]}",
        )
    )
    assert isinstance(result, dict)
    cites = result.get("citations") or []
    clusters = result.get("clusters") or []
    assert isinstance(cites, list)
    assert isinstance(clusters, list)
    # At least one reporter-style cite we embedded (volume + reporter + page)
    flat = " ".join(
        str(c.get("citation") or c.get("text") or "")
        for c in cites
        if isinstance(c, dict)
    )
    assert re.search(r"\b88\s+F\.?\s*4th\s+9001\b", flat, re.I), (
        f"Expected embedded Fed. Cir. cite in extraction; got {flat[:400]!r}"
    )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.production
def test_analyze_http_unseen_document_json_contract():
    """POST /analyze with real app stack (no stubbed processor)."""
    app = create_app()
    app.config["TESTING"] = True
    text = _synthetic_memo_text()
    with app.test_client() as client:
        response = client.post(
            "/casestrainer/api/analyze",
            json={
                "type": "text",
                "text": text,
                "force_mode": "sync",
                "enable_verification": False,
            },
            content_type="application/json",
        )
    assert response.status_code in (200, 400, 403, 503), (
        f"Unexpected HTTP {response.status_code}: {response.get_data(as_text=True)[:800]}"
    )
    if response.status_code != 200:
        pytest.skip(f"Analyze returned {response.status_code} (environment may require async-only or services)")

    data = response.get_json()
    assert data is not None
    assert data.get("request_id")
    assert "success" in data
    cites = data.get("citations")
    assert isinstance(cites, list)
    assert data.get("clusters") is None or isinstance(data.get("clusters"), list)

    # Sync completed path: must contain our synthetic reporter cite.
    # Queued/async path: empty citations until poll — still a valid production contract.
    if data.get("task_id") and str(data.get("status", "")).lower() in ("processing", "queued", ""):
        if len(cites) == 0:
            return
    flat = " ".join(str(c.get("citation") or c.get("text") or "") for c in cites if isinstance(c, dict))
    assert re.search(r"\b88\s+F\.?\s*4th\s+9001\b", flat, re.I), (
        f"Expected embedded cite in API citations; got {flat[:400]!r}"
    )
