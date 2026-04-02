#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.chdir(REPO)

def post_analyze_text_as_file(
    base_url: str,
    text: str,
    *,
    timeout_s: int,
    filename: str,
    enable_verification: bool,
) -> Dict[str, Any]:
    url = f"{base_url}/casestrainer/api/analyze"
    files = {"file": (filename, (text or "").encode("utf-8"), "text/plain")}
    data = {
        "type": "file",
        "force_mode": "async",
        "enable_verification": "true" if enable_verification else "false",
        "client_request_id": f"adhoc-unverified-lookup-{int(time.time()*1000)}-{Path(filename).stem[:20]}",
    }
    r = requests.post(url, files=files, data=data, timeout=timeout_s)
    r.raise_for_status()
    return r.json()


def poll_task_status(base_url: str, task_id: str, *, timeout_s: int) -> Dict[str, Any]:
    url = f"{base_url}/casestrainer/api/task_status/{task_id}"
    deadline = time.time() + timeout_s
    last: Optional[Dict[str, Any]] = None
    while time.time() < deadline:
        r = requests.get(url, timeout=timeout_s)
        if r.status_code == 404:
            time.sleep(1.0)
            continue
        r.raise_for_status()
        last = r.json()
        if last.get("is_finished") is True or last.get("status") in {"completed", "failed"}:
            return last
        time.sleep(1.0)
    raise TimeoutError(f"Timed out polling task status for {task_id}. last={json.dumps(last)[:300]}")


def _row_from_citation(file_name: str, c: Dict[str, Any]) -> Dict[str, Any]:
    case_name = (
        str(c.get("extracted_case_name") or "").strip()
        or str(c.get("cluster_case_name") or "").strip()
        or str(c.get("case_name") or "").strip()
        or "Unknown Case"
    )
    year = str(c.get("extracted_date") or c.get("extracted_year") or "").strip() or "N/A"
    return {
        "file": file_name,
        "case_name": case_name,
        "citation": str(c.get("citation") or "").strip(),
        "year": year,
        "verification_status": c.get("verification_status"),
        "verification_error": c.get("verification_error"),
    }


def run_citation_lookup(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from src.verification.batch import BatchVerifier

    citations = [str(r["citation"]) for r in rows]
    names = [str(r["case_name"]) for r in rows]
    years = [str(r["year"]) if str(r["year"]) != "N/A" else None for r in rows]

    verifier = BatchVerifier()
    results = verifier.verify_batch_sync(
        citations=citations,
        case_names_list=names,
        dates_list=years,
        timeout_per_batch=90,
        progress_callback=None,
    )
    out: List[Dict[str, Any]] = []
    for src, res in zip(rows, results):
        out.append(
            {
                **src,
                "lookup_verified": bool(res.get("verified", False)),
                "lookup_canonical_name": res.get("canonical_name"),
                "lookup_canonical_date": res.get("canonical_date"),
                "lookup_canonical_url": res.get("canonical_url"),
                "lookup_source": res.get("source"),
                "lookup_error": res.get("error"),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:5000")
    ap.add_argument("--dir", type=Path, default=Path("downloaded_briefs") / "naag_amicus")
    ap.add_argument("--cache-dir", type=Path, default=Path("downloaded_briefs") / "naag_amicus" / "_ocr_cache")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--enable-verification", action="store_true", help="Use backend verification while generating unverified list.")
    ap.add_argument("--output-json", type=Path, default=Path("scripts") / "adhoc" / "unverified_cases_with_lookup.json")
    ap.add_argument("--output-csv", type=Path, default=Path("scripts") / "adhoc" / "unverified_cases_with_lookup.csv")
    ap.add_argument("--unverified-only-json", type=Path, default=Path("scripts") / "adhoc" / "unverified_cases_only.json")
    ap.add_argument("--from-unverified-json", action="store_true", help="Skip extraction and read rows from --unverified-only-json")
    args = ap.parse_args()

    unverified_rows: List[Dict[str, Any]] = []
    if args.from_unverified_json and args.unverified_only_json.exists():
        unverified_rows = json.loads(args.unverified_only_json.read_text(encoding="utf-8"))
    else:
        pdfs = sorted(args.dir.glob("*.pdf"))
        if args.limit > 0:
            pdfs = pdfs[: args.limit]
        for pdf in pdfs:
            cache_path = args.cache_dir / f"{pdf.name}.txt"
            if not cache_path.exists():
                continue
            text = cache_path.read_text(encoding="utf-8")
            init = post_analyze_text_as_file(
                args.base_url,
                text,
                timeout_s=args.timeout,
                filename=f"{pdf.stem}.txt",
                enable_verification=bool(args.enable_verification),
            )
            task_id = str(init.get("task_id") or init.get("request_id") or "")
            if not task_id:
                continue
            final = poll_task_status(args.base_url, task_id, timeout_s=args.timeout)
            cits = final.get("citations") or []
            for c in cits:
                if not isinstance(c, dict):
                    continue
                if c.get("verified") is False:
                    row = _row_from_citation(pdf.name, c)
                    if row["citation"]:
                        unverified_rows.append(row)

    # De-duplicate by normalized triple (case,cite,year)
    dedup: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for r in unverified_rows:
        key = (r["case_name"].strip().lower(), r["citation"].strip().lower(), str(r["year"]).strip())
        dedup[key] = r
    unverified_rows = list(dedup.values())
    args.unverified_only_json.parent.mkdir(parents=True, exist_ok=True)
    args.unverified_only_json.write_text(json.dumps(unverified_rows, indent=2), encoding="utf-8")

    lookup_rows = run_citation_lookup(unverified_rows) if unverified_rows else []

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(lookup_rows, indent=2), encoding="utf-8")

    with args.output_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "case_name",
                "citation",
                "year",
                "verification_status",
                "verification_error",
                "lookup_verified",
                "lookup_canonical_name",
                "lookup_canonical_date",
                "lookup_canonical_url",
                "lookup_source",
                "lookup_error",
            ],
        )
        w.writeheader()
        for r in lookup_rows:
            w.writerow(r)

    verified_after_lookup = sum(1 for r in lookup_rows if r.get("lookup_verified"))
    print(
        json.dumps(
            {
                "unverified_rows": len(lookup_rows),
                "verified_by_citation_lookup": verified_after_lookup,
                "output_json": str(args.output_json),
                "output_csv": str(args.output_csv),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

