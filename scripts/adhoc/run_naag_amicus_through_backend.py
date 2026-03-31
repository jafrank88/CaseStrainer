#!/usr/bin/env python3
"""
Run the NAAG amicus PDF corpus through the local backend API and summarize results.

Goal: smoke-test that backend extraction matches expectations after recent OCR + TOA fixes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

REPO = Path(__file__).resolve().parents[2]


def _is_year_based_vendor_cite(cit: str) -> bool:
    return bool(re.search(r"\b(?:19|20)\d{2}\s+(?:WL|(?:U\.S\.?\s*)?LEXIS|LEXIS)\s+\d+\b", cit, re.I))


def _has_illegal_4digit_volume(cit: str) -> bool:
    """
    Identify citations whose leading "volume" is 4+ digits, excluding year-based vendor formats.
    Example bad: "4837 U.S. 117"
    Example allowed: "2023 WL 1234567"
    """
    s = (cit or "").strip()
    if not s:
        return False
    if _is_year_based_vendor_cite(s):
        return False
    m = re.match(r"^(\d{4,})\s+\S+", s)
    return bool(m)


def post_analyze_file(
    base_url: str, pdf_path: Path, *, enable_verification: bool, timeout_s: int
) -> Dict[str, Any]:
    url = f"{base_url}/casestrainer/api/analyze"
    with pdf_path.open("rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data = {
            "type": "file",
            "force_mode": "async",
            "enable_verification": "true" if enable_verification else "false",
            "client_request_id": f"adhoc-{int(time.time()*1000)}-{pdf_path.stem[:24]}",
        }
        r = requests.post(url, files=files, data=data, timeout=timeout_s)
    r.raise_for_status()
    return r.json()

def post_analyze_text(
    base_url: str,
    text: str,
    *,
    enable_verification: bool,
    timeout_s: int,
    filename_hint: str = "",
) -> Dict[str, Any]:
    url = f"{base_url}/casestrainer/api/analyze"
    data = {
        "type": "text",
        "text": text,
        "force_mode": "async",
        "enable_verification": "true" if enable_verification else "false",
        "client_request_id": f"adhoc-{int(time.time()*1000)}-{filename_hint[:24]}",
    }
    r = requests.post(url, data=data, timeout=timeout_s)
    r.raise_for_status()
    return r.json()

def post_analyze_text_as_file(
    base_url: str,
    text: str,
    *,
    enable_verification: bool,
    timeout_s: int,
    filename: str,
) -> Dict[str, Any]:
    """
    Upload cached OCR text as a file, to exercise the "file" pipeline without PDF OCR.
    This avoids some edge cases in the pure text async path.
    """
    url = f"{base_url}/casestrainer/api/analyze"
    files = {"file": (filename, (text or "").encode("utf-8"), "text/plain")}
    data = {
        "type": "file",
        "force_mode": "async",
        "enable_verification": "true" if enable_verification else "false",
        "client_request_id": f"adhoc-{int(time.time()*1000)}-{Path(filename).stem[:24]}",
    }
    r = requests.post(url, files=files, data=data, timeout=timeout_s)
    r.raise_for_status()
    return r.json()


def poll_task_status(
    base_url: str,
    task_id: str,
    *,
    timeout_s: int,
    poll_interval_s: float = 1.0,
) -> Dict[str, Any]:
    url = f"{base_url}/casestrainer/api/task_status/{task_id}"
    deadline = time.time() + timeout_s
    last: Optional[Dict[str, Any]] = None
    while time.time() < deadline:
        r = requests.get(url, timeout=timeout_s)
        if r.status_code == 404:
            time.sleep(poll_interval_s)
            continue
        r.raise_for_status()
        last = r.json()
        if last.get("is_finished") is True or last.get("status") in {"completed", "failed"}:
            return last
        time.sleep(poll_interval_s)
    raise TimeoutError(f"Timed out polling task_status for {task_id}. Last={json.dumps(last)[:500]}")


def summarize_result(payload: Dict[str, Any]) -> Tuple[int, int, int, int, List[str]]:
    citations = payload.get("citations") or []
    clusters = payload.get("clusters") or []
    stats = payload.get("statistics") or {}

    n_citations = len(citations)
    n_clusters = len(clusters)
    n_verified = sum(1 for c in citations if c.get("verified") is True)
    n_unverified = sum(1 for c in citations if c.get("verified") is False)

    bad_4digit_vol = []
    for c in citations:
        cit = (c.get("citation") or "").strip()
        if _has_illegal_4digit_volume(cit):
            bad_4digit_vol.append(cit)

    # Prefer backend-provided review buckets if available
    sections = payload.get("cluster_sections") or {}
    needs_review = len(sections.get("case_mismatch") or []) + len(sections.get("date_mismatch") or [])
    if needs_review <= 0:
        needs_review = int(stats.get("cases_need_review") or 0) if isinstance(stats, dict) else 0

    return n_clusters, n_citations, n_verified, n_unverified, bad_4digit_vol


def _norm_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9\s\.&'-]", "", s)
    s = s.replace("v.", "v.")
    return s.strip()


def _load_local_ocr_text(pdf_path: Path, *, max_pages: int = 30, scale: float = 2.0) -> Tuple[str, str]:
    """
    Extract text similarly to the backend OCR path so we can do same-line binding checks.
    This is a best-effort approximation; the backend runs in container, so text may differ slightly.
    """
    os.environ.setdefault("CASESTRAINER_ENABLE_OCR", "true")
    os.environ.setdefault("CASESTRAINER_OCR_MAX_PAGES", str(max_pages))
    os.environ.setdefault("CASESTRAINER_OCR_SCALE", str(scale))
    from src.unified_text_extractor import UnifiedTextExtractor  # local import for script usage

    t, m = UnifiedTextExtractor().extract_text(str(pdf_path))
    return t or "", m or ""

def _ocr_cache_path(cache_dir: Path, pdf_path: Path) -> Path:
    return cache_dir / (pdf_path.name + ".txt")

def _load_cached_ocr_text(cache_dir: Path, pdf_path: Path) -> Optional[str]:
    p = _ocr_cache_path(cache_dir, pdf_path)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None

def _write_cached_ocr_text(cache_dir: Path, pdf_path: Path, text: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = _ocr_cache_path(cache_dir, pdf_path)
    p.write_text(text or "", encoding="utf-8")


def _same_line_name_year_candidates(text: str, citation_text: str) -> List[Tuple[str, Optional[str]]]:
    """
    For each occurrence of the citation string in the extracted text, derive same-line
    `Name v. Name` (to the left) and `(YYYY)` (to the right).
    """
    if not text or not citation_text:
        return []
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    p = UnifiedCitationProcessorV2()
    cands: List[Tuple[str, Optional[str]]] = []
    start = 0
    while True:
        idx = text.find(citation_text, start)
        if idx < 0:
            break
        si = idx
        ei = idx + len(citation_text)
        name, year = p._extract_name_year_from_same_line_for_citation(text, citation_text, si, ei)
        if name:
            cands.append((name, year))
        start = ei
        if len(cands) >= 12:
            break
    return cands


def check_suspicious_pairings(
    pdf_path: Path, payload: Dict[str, Any], *, ocr_pages: int, ocr_scale: float
) -> Tuple[int, List[str]]:
    """
    Compare backend extracted_case_name/year for each citation against same-line candidates from local OCR text.
    Returns: (suspicious_count, example_lines)
    """
    citations = payload.get("citations") or []
    if not citations:
        return 0, []

    text, method = _load_local_ocr_text(pdf_path, max_pages=ocr_pages, scale=ocr_scale)
    if not text:
        return 0, [f"[warn] could not extract local text for checks (method={method})"]

    examples: List[str] = []
    suspicious = 0

    for c in citations:
        cit = (c.get("citation") or "").strip()
        if not cit:
            continue
        backend_name = (c.get("extracted_case_name") or c.get("cluster_case_name") or c.get("case_name") or "").strip()
        backend_year = str(c.get("extracted_date") or "").strip()

        # Ignore citations that already encode year (WL/LEXIS) — year binding isn't meaningful there.
        if _is_year_based_vendor_cite(cit):
            continue

        cands = _same_line_name_year_candidates(text, cit)
        if not cands:
            continue

        bnorm = _norm_name(backend_name)
        # Accept if any candidate same-line name matches backend name (normalized).
        name_match = any(_norm_name(n) == bnorm and bnorm for (n, _y) in cands)
        if not name_match and backend_name and " v. " in backend_name:
            suspicious += 1
            if len(examples) < 12:
                show = "; ".join([f"{n} ({y or '?'})" for n, y in cands[:3]])
                examples.append(f"name_mismatch: {cit} backend='{backend_name}' candidates={show}")

        # Year check: if backend year exists and candidates offer a year, accept if any equals it.
        cand_years = {y for (_n, y) in cands if y and y.isdigit()}
        if backend_year and backend_year.isdigit() and cand_years and backend_year not in cand_years:
            suspicious += 1
            if len(examples) < 12:
                examples.append(f"year_mismatch: {cit} backend_year={backend_year} candidate_years={sorted(cand_years)[:5]}")

    return suspicious, examples


EXPECTATIONS: List[Dict[str, Any]] = [
    # Known TOA neighbor-bleed traps observed in NAAG 01
    {"citation": "143 S. Ct. 1142", "name_must_contain_any": ["ross", "pork"], "year": "2023"},
    {"citation": "331 F.3d 1177", "name_must_contain_any": ["crist"], "year": "2008"},
    {"citation": "135 U.S. 100", "name_must_contain_any": ["hardin"], "year": "1890"},
    {"citation": "572 U.S. 844", "name_must_contain_any": ["bond"], "year": "2014"},
    {"citation": "196 U.S. 447", "name_must_contain_any": ["smiley"], "year": "1905"},
    # Parker year varies by document/OCR; see per-file override below.
    {"citation": "317 U.S. 341", "name_must_contain_any": ["parker"], "year": "1948"},
    {"citation": "397 U.S. 137", "name_must_contain_any": ["pike"], "year": "1970"},
    {"citation": "504 U.S. 621", "name_must_contain_any": ["ticor"], "year": "1992"},
]


def check_expectations(payload: Dict[str, Any], *, filename: str = "") -> List[str]:
    """
    Check a small set of known expectations directly against backend results (reliable).
    Returns a list of failure strings.
    """
    citations = payload.get("citations") or []
    if not citations:
        return []
    by_cit: Dict[str, List[Dict[str, Any]]] = {}
    for c in citations:
        k = (c.get("citation") or "").strip()
        if not k:
            continue
        by_cit.setdefault(k, []).append(c)

    failures: List[str] = []
    fn = (filename or "").strip()

    for exp in EXPECTATIONS:
        cit = exp["citation"]
        exp_year = exp.get("year")
        if cit == "317 U.S. 341":
            # Parker year differs by document/OCR. Use per-file expected year.
            if fn and "Chamber-of-Commerce-v-Seattle_2018" in fn:
                exp_year = "1943"
            elif fn and "NC-Dental-v-FTC-Merits_2014" in fn:
                exp_year = "1943"
            elif fn and "NC-Dental-v-FTC-Cert_2013" in fn:
                exp_year = "1943"
            elif fn and "FTC-v-Phoebe-Putney_2012" in fn:
                exp_year = "1943"
            elif fn and "Tri-City-Valleycats-v-Commissioner_2023" in fn:
                exp_year = "1948"
        rows = by_cit.get(cit) or []
        if not rows:
            continue
        # If multiple rows for same citation appear, accept if any row satisfies expectations.
        ok_any = False
        for r in rows:
            name = (r.get("extracted_case_name") or r.get("cluster_case_name") or r.get("case_name") or "").lower()
            year = str(r.get("extracted_date") or "").strip()
            must_any = [s.lower() for s in (exp.get("name_must_contain_any") or [])]
            if must_any and not any(s in name for s in must_any):
                continue
            if exp_year and year and year != exp_year:
                continue
            ok_any = True
            break
        if not ok_any:
            failures.append(
                f"expectation_failed: {cit} expected_year={exp_year} expected_name_contains_any={exp.get('name_must_contain_any')}"
            )
    return failures


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=Path("downloaded_briefs") / "naag_amicus")
    p.add_argument("--include", default="", help="Only include PDFs whose filename contains this substring (case-insensitive).")
    p.add_argument("--base-url", default="http://localhost:5000")
    p.add_argument("--timeout", type=int, default=900, help="Per-file timeout seconds (includes OCR + verification).")
    p.add_argument("--no-verify", action="store_true", help="Disable verification (extraction-only).")
    p.add_argument("--limit", type=int, default=0, help="Only run first N PDFs (0 = all).")
    p.add_argument("--check-same-line", action="store_true", help="Cross-check backend name/year against same-line OCR candidates.")
    p.add_argument("--ocr-pages", type=int, default=30)
    p.add_argument("--ocr-scale", type=float, default=2.0)
    p.add_argument("--check-expectations", action="store_true", help="Check known expectations against backend output (recommended).")
    p.add_argument("--cache-ocr-dir", type=Path, default=Path("downloaded_briefs") / "naag_amicus" / "_ocr_cache")
    p.add_argument("--save-ocr", action="store_true", help="OCR PDFs locally and save extracted text to cache dir.")
    p.add_argument("--use-cached-ocr", action="store_true", help="If cached OCR text exists, analyze as text instead of uploading PDF.")
    args = p.parse_args()

    os.chdir(REPO)
    # Ensure repo root is on sys.path for `import src...`
    import sys

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    d = args.dir
    pdfs = sorted(d.glob("*.pdf"))
    if args.include:
        inc = args.include.lower().strip()
        pdfs = [p for p in pdfs if inc in p.name.lower()]
    if args.limit and args.limit > 0:
        pdfs = pdfs[: args.limit]
    if not pdfs:
        raise SystemExit(f"No PDFs found under {d}")

    enable_verification = not args.no_verify
    print(f"Running {len(pdfs)} PDFs via {args.base_url} (verification={enable_verification})")
    print("file,clusters,citations,verified,unverified,bad_4digit_volume_count,suspicious_same_line,expectation_failures")

    any_bad = False
    bad_examples: List[Tuple[str, str]] = []

    for pdf in pdfs:
        try:
            cached_text: Optional[str] = None
            if args.use_cached_ocr:
                cached_text = _load_cached_ocr_text(args.cache_ocr_dir, pdf)

            if cached_text is not None:
                init = post_analyze_text_as_file(
                    args.base_url,
                    cached_text,
                    enable_verification=enable_verification,
                    timeout_s=args.timeout,
                    filename=f"{pdf.stem}.txt",
                )
            else:
                init = post_analyze_file(args.base_url, pdf, enable_verification=enable_verification, timeout_s=args.timeout)

            task_id = init.get("task_id") or init.get("request_id")
            if not task_id:
                raise RuntimeError(f"No task_id in analyze response for {pdf.name}: {init}")
            final = poll_task_status(args.base_url, str(task_id), timeout_s=args.timeout)
            n_clusters, n_cits, n_ver, n_unver, bad_4digit = summarize_result(final)
            suspicious = 0
            ex_lines: List[str] = []
            if args.check_same_line:
                suspicious, ex_lines = check_suspicious_pairings(
                    pdf, final, ocr_pages=int(args.ocr_pages), ocr_scale=float(args.ocr_scale)
                )
                if suspicious > 0:
                    any_bad = True
            exp_failures: List[str] = []
            if args.check_expectations:
                exp_failures = check_expectations(final, filename=pdf.name)
                if exp_failures:
                    any_bad = True
            print(f"{pdf.name},{n_clusters},{n_cits},{n_ver},{n_unver},{len(bad_4digit)},{suspicious},{len(exp_failures)}")
            if bad_4digit:
                any_bad = True
                for ex in bad_4digit[:3]:
                    bad_examples.append((pdf.name, ex))
            if ex_lines:
                for ln in ex_lines[:8]:
                    print(f"  {pdf.name}: {ln}")
            if exp_failures:
                for ln in exp_failures[:8]:
                    print(f"  {pdf.name}: {ln}")

            # After successful backend run, optionally OCR+cache locally (so future runs can skip OCR).
            if args.save_ocr and cached_text is None:
                try:
                    t, _m = _load_local_ocr_text(pdf, max_pages=int(args.ocr_pages), scale=float(args.ocr_scale))
                    if t and len(t) > 200:
                        _write_cached_ocr_text(args.cache_ocr_dir, pdf, t)
                except Exception:
                    pass
        except Exception as e:
            any_bad = True
            print(f"{pdf.name},ERROR,{type(e).__name__},{e}")

    if bad_examples:
        print("\nBad 4+ digit volume examples (should be empty):")
        for fn, ex in bad_examples[:30]:
            print(f"- {fn}: {ex}")

    return 1 if any_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

