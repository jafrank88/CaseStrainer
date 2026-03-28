"""Tests for shared API/worker response finalization."""

from src.utils.response_finalize import (
    merge_dedupe_and_refinalize_clusters,
    run_final_display_guard_worker,
)


def test_merge_dedupe_combines_same_url_and_rebuilds_display_citations():
    url = "https://www.courtlistener.com/opinion/42/combined/"
    clusters = [
        {
            "cluster_id": "1",
            "citations": [
                {
                    "citation": "1 F.2d 1",
                    "verified": True,
                    "canonical_url": url,
                    "canonical_name": "Alpha v. Beta",
                    "canonical_date": "1999",
                }
            ],
        },
        {
            "cluster_id": "2",
            "citations": [
                {
                    "citation": "2 F.2d 2",
                    "verified": True,
                    "canonical_url": url,
                    "canonical_name": "Alpha v. Beta",
                    "canonical_date": "1999",
                }
            ],
        },
    ]
    out = merge_dedupe_and_refinalize_clusters(
        clusters,
        clean_names=False,
        rebuild_display_citations=True,
    )
    assert len(out) == 1
    assert "display_citations" in out[0]
    cites = {c.get("citation") for c in (out[0].get("citations") or [])}
    assert "1 F.2d 1" in cites
    assert "2 F.2d 2" in cites


def test_run_final_display_guard_worker_runs_without_error_on_minimal_cluster():
    citations = [
        {
            "citation": "2025 WL 1000",
            "verified": False,
            "canonical_url": None,
            "url": None,
        }
    ]
    clusters = [
        {
            "cluster_id": "x",
            "citations": list(citations),
        }
    ]
    out = run_final_display_guard_worker(
        citations,
        clusters,
        log_prefix="[test] ",
    )
    assert isinstance(out, list)
    assert len(out) >= 1
