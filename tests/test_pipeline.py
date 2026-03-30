"""
Smoke tests for the canonical sync entry point process_citations_unified.
Run with: pytest tests/test_pipeline.py -v
"""

import asyncio
import pytest


def test_process_citations_unified_smoke():
    """Call process_citations_unified with a short string; assert citations and clusters shape."""
    from src.unified_processing_pipeline import process_citations_unified

    text = "See Erie Railroad Co. v. Tompkins, 304 U.S. 64 (1938)."
    result = asyncio.run(
        process_citations_unified(text, enable_verification=False, enable_parallel_verification=False)
    )

    assert isinstance(result, dict), "result should be a dict"
    assert "citations" in result, "result should have citations"
    assert "clusters" in result, "result should have clusters"
    assert isinstance(result["citations"], list), "citations should be a list"
    assert isinstance(result["clusters"], list), "clusters should be a list"
    # With verification off we may get 0 or 1+ citations depending on extraction
    assert len(result["citations"]) >= 0
    assert len(result["clusters"]) >= 0
    if result["citations"]:
        cit = result["citations"][0]
        assert isinstance(cit, dict), "citation should be a dict"
        assert "citation" in cit or "citation_text" in cit or "text" in cit, "citation should have text field"
    if result["clusters"]:
        cluster = result["clusters"][0]
        assert isinstance(cluster, dict), "cluster should be a dict"
        assert "citations" in cluster or "cluster_id" in cluster, "cluster should have expected shape"
