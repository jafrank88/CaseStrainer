"""
Batch process all 25 naag_amicus OCR text files through the CaseStrainer pipeline.
Saves per-file JSON output to batch_results/ and a summary report to batch_report.json.
Run from the casestrainer repo root:
    python batch_analyze.py
"""
import asyncio
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

# Repo root on sys.path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# Load .env so CourtListener API key etc. are available
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

OCR_DIR   = REPO_ROOT / "downloaded_briefs" / "naag_amicus" / "_ocr_cache"
OUT_DIR   = REPO_ROOT / "batch_results"
OUT_DIR.mkdir(exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def _stem(path: Path) -> str:
    """Return filename without the final .txt, e.g. '02_Robinson...pdf'."""
    return path.stem  # already drops .txt; stem = "02_Robinson...pdf"


def _flag_issues(result: dict, doc_text: str) -> list[dict]:
    """
    Heuristic scan of a pipeline result for common bug patterns.
    Returns a list of issue dicts: {type, cluster_id, detail}
    """
    issues = []
    clusters = result.get("clusters") or []
    citations = result.get("citations") or []

    for cl in clusters:
        cid = cl.get("cluster_id", "?")
        submitted = cl.get("submitted_display_name") or ""
        canonical = cl.get("canonical_name") or ""
        verified  = cl.get("verified", False)
        cl_cits   = cl.get("citations") or cl.get("cluster_members") or []

        # 1. Cluster with no case name at all
        if not submitted or submitted == "N/A":
            if not canonical:
                issues.append({"type": "missing_name", "cluster_id": cid,
                                "detail": f"No extracted or canonical name; citations={cl_cits[:3]}"})

        # 2. Name still contains a lone entity-type prefix → truncated plaintiff
        if re.match(r'^(?:Inc|Corp|LLC|Ltd|Co|Corporation)\.?\s+v\.\s+', submitted or ""):
            issues.append({"type": "truncated_plaintiff", "cluster_id": cid,
                           "detail": f"submitted='{submitted[:80]}'"})

        # 3. Verified mismatch: submitted ≠ canonical (names_are_same_case=False proxy)
        if verified and canonical and submitted and submitted != "N/A":
            import html
            # Decode HTML entities and normalize text before comparison
            canonical_clean = html.unescape(canonical)
            # Normalize common abbreviations and spacing
            canonical_clean = re.sub(r'\bI\.?\s*N\.?\s*S\.?\b', 'INS', canonical_clean)
            canonical_clean = re.sub(r'\bComm\'?n\b', 'Commission', canonical_clean)
            canonical_clean = re.sub(r'\bDep\'?t\b', 'Department', canonical_clean)
            
            from src.utils.same_case import names_are_same_case
            if not names_are_same_case(submitted, canonical_clean):
                issues.append({"type": "name_mismatch_verified", "cluster_id": cid,
                                "detail": f"submitted='{submitted[:60]}' | canonical='{canonical[:60]}'"})

        # 4. Cluster with multiple distinct canonical URLs (bad merge)
        urls = {c.get("canonical_url") for c in (cl.get("citations") or [])
                if isinstance(c, dict) and c.get("canonical_url")}
        if len(urls) > 1:
            issues.append({"type": "multi_canonical_cluster", "cluster_id": cid,
                           "detail": f"canonical_urls={list(urls)[:4]}"})

        # 5. Year mismatch: submitted_display_date ≠ verifying_display_date
        sub_date = str(cl.get("submitted_display_date") or "")
        ver_date = str(cl.get("verifying_display_date") or "")
        if sub_date and ver_date and sub_date != ver_date:
            if re.match(r'^\d{4}$', sub_date) and re.match(r'^\d{4}$', ver_date):
                # Suppress 1-3yr gaps — these are legitimate reporting delays
                try:
                    _gap = abs(int(sub_date) - int(ver_date))
                except ValueError:
                    _gap = 0
                if _gap >= 4:
                    # Suppress when canonical name confirms it's the right case
                    # (correct verification of a genuinely old case whose extracted_date
                    # leaked the document year).  Use BOTH same-case check AND overlap
                    # to avoid suppressing "Grinnell" vs "Microsoft" which share only
                    # the generic plaintiff "United States".
                    from src.utils.same_case import names_are_same_case as _nsc_ym
                    from src.verification.utils import calculate_case_name_overlap as _overlap
                    _sub_nm = submitted or ""
                    _can_nm = canonical or ""
                    _name_ok = (
                        _sub_nm and _can_nm
                        and _nsc_ym(_sub_nm, _can_nm)
                        and _overlap(_sub_nm, _can_nm) >= 0.3
                    )
                    if not _name_ok:
                        issues.append({"type": "year_mismatch", "cluster_id": cid,
                                       "detail": f"extracted_year={sub_date} canonical_year={ver_date} gap={_gap}yr"})

        # 6. Very large cluster (likely wrong transitive merge)
        n = cl.get("cluster_size") or len(cl.get("citations") or [])
        if n >= 6:
            issues.append({"type": "oversized_cluster", "cluster_id": cid,
                           "detail": f"size={n} submitted='{submitted[:60]}'"})

        # 7. PDF '!' artifact still present in submitted name
        if "'" in (submitted or "") and "!" in (submitted or ""):
            issues.append({"type": "pdf_apostrophe_bang_artifact", "cluster_id": cid,
                           "detail": f"submitted='{submitted[:80]}'"})

        # 8. Cluster key looks like a citation number (failed name extraction)
        if re.match(r'^\d{1,4}\s+(?:U\.S\.|F\.\d|S\.\s*Ct\.)', submitted or ""):
            issues.append({"type": "citation_as_name", "cluster_id": cid,
                           "detail": f"submitted='{submitted[:80]}'"})

    # 9. Per-citation: wrong In re display (contains "In re" in citation.citation but
    #    extracted_case_name is very short / fragments)
    # Build a cluster_id -> submitted_display_name lookup so we can skip
    # citations whose cluster already shows the correct name.
    _cluster_name: dict[str, str] = {}
    for cl in clusters:
        cid2 = cl.get("cluster_id") or ""
        sdn  = cl.get("submitted_display_name") or ""
        if cid2:
            _cluster_name[cid2] = sdn
    _seen_ecn_flags: set[tuple] = set()
    for c in citations:
        if not isinstance(c, dict):
            continue
        ct   = c.get("citation") or ""
        ecn  = c.get("extracted_case_name") or ""
        # Short ECN (<=12 chars) on an eyecite citation that includes a long name prefix
        if len(ct) > 40 and (not ecn or ecn == "N/A" or len(ecn.strip()) <= 12):
            cit_cid = c.get("cluster_id") or ""
            # Deduplicate: same cluster + same citation prefix already flagged
            dedup_key = (cit_cid, ct[:50])
            if dedup_key in _seen_ecn_flags:
                continue
            _seen_ecn_flags.add(dedup_key)
            # Skip if the cluster already has a meaningful name (has 'v.' or 'In re')
            cluster_name = _cluster_name.get(cit_cid, "")
            _has_good_cluster_name = bool(
                re.search(r"\bv\.\s", cluster_name)
                or re.search(r"\b(?:In\s+re|Ex\s+parte)\b", cluster_name, re.IGNORECASE)
                or re.search(r"\b(?:Antitrust|Litig\.?)\b", cluster_name, re.IGNORECASE)
            )
            if _has_good_cluster_name:
                continue
            issues.append({"type": "short_ecn_on_long_citation",
                           "cluster_id": cit_cid or None,
                           "detail": f"citation='{ct[:60]}' ecn='{ecn}'"})

    # 10. Duplicate cluster_ids
    seen_ids: dict[str, int] = {}
    for cl in clusters:
        cid = cl.get("cluster_id", "")
        seen_ids[cid] = seen_ids.get(cid, 0) + 1
    for cid, cnt in seen_ids.items():
        if cnt > 1:
            issues.append({"type": "duplicate_cluster_id",
                           "cluster_id": cid, "detail": f"appears {cnt}x"})

    return issues


# ── main ─────────────────────────────────────────────────────────────────────

async def process_one(txt_path: Path) -> dict:
    from src.unified_processing_pipeline import process_citations_unified

    doc_name = txt_path.stem          # e.g. "02_Robinson...pdf"
    out_path = OUT_DIR / f"{txt_path.stem}.json"

    print(f"\n{'='*70}")
    print(f"  Processing: {doc_name}")
    print(f"{'='*70}")

    if out_path.exists():
        print(f"  [SKIP] Already processed → {out_path.name}")
        with open(out_path, encoding="utf-8") as f:
            cached = json.load(f)
        # Re-run _flag_issues so updated checker logic applies without reprocessing.
        doc_text = txt_path.read_text(encoding="utf-8", errors="replace")
        issues = _flag_issues(cached, doc_text)
        ana = cached.get("_analysis") or {}
        ana["issues"] = issues
        cached["_analysis"] = ana
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cached, f, indent=2, default=str, ensure_ascii=False)
        return cached

    text = txt_path.read_text(encoding="utf-8", errors="replace")
    t0   = time.time()
    try:
        result = await process_citations_unified(
            text,
            processing_mode="enhanced_sync",
            enable_verification=True,
            enable_parallel_verification=True,
            trace_id=doc_name,
        )
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"  ERROR after {elapsed:.1f}s: {exc}")
        result = {"error": str(exc), "traceback": traceback.format_exc(),
                  "citations": [], "clusters": []}

    elapsed = time.time() - t0
    n_cits    = len(result.get("citations") or [])
    n_clusters= len(result.get("clusters")  or [])
    print(f"  Done in {elapsed:.1f}s — {n_cits} citations, {n_clusters} clusters")

    issues = _flag_issues(result, text)
    result["_analysis"] = {"doc": doc_name, "elapsed_s": round(elapsed, 1),
                            "n_citations": n_cits, "n_clusters": n_clusters,
                            "issues": issues}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)

    print(f"  Issues found: {len(issues)}")
    for iss in issues[:10]:
        print(f"    [{iss['type']}] {iss['cluster_id']}: {iss['detail'][:80]}")

    return result


async def main():
    txt_files = sorted(OCR_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} OCR text files to process.\n")

    all_issues: list[dict] = []
    summary = []

    for txt_path in txt_files:
        result = await process_one(txt_path)
        an = result.get("_analysis") or {}
        for iss in (an.get("issues") or []):
            all_issues.append({"doc": txt_path.stem, **iss})
        summary.append({
            "doc":         txt_path.stem,
            "elapsed_s":   an.get("elapsed_s"),
            "n_citations": an.get("n_citations"),
            "n_clusters":  an.get("n_clusters"),
            "n_issues":    len(an.get("issues") or []),
            "error":       result.get("error"),
        })

    # ── aggregate report ──────────────────────────────────────────────────
    from collections import Counter
    type_counts = Counter(i["type"] for i in all_issues)

    report = {
        "summary_per_doc": summary,
        "total_issues": len(all_issues),
        "issues_by_type": dict(type_counts.most_common()),
        "all_issues": all_issues,
    }

    report_path = REPO_ROOT / "batch_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"BATCH COMPLETE")
    print(f"  Total issues: {len(all_issues)}")
    print(f"  By type:")
    for t, c in type_counts.most_common():
        print(f"    {t:<40} {c:>4}")
    print(f"\n  Full report: {report_path}")
    print(f"  Per-file JSON: {OUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
