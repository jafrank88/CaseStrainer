#!/usr/bin/env python3
"""
Summarize ``*_pipeline.json`` files produced by ``brief_goldens.py dump``.

Writes a CSV (default under ``data/brief_goldens/``, which is gitignored) for
sorting and spotting suspicious rows (very short text, zero citations, etc.).

Example::

    python scripts/report_brief_golden_dumps.py \\
      --runs-dir data/brief_goldens/runs/full_downloaded_briefs \\
      --out data/brief_goldens/runs/summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    p = argparse.ArgumentParser(description="CSV summary of brief golden pipeline JSON dumps")
    p.add_argument(
        "--runs-dir",
        type=Path,
        default=REPO_ROOT / "data/brief_goldens/runs/full_downloaded_briefs",
        help="Directory containing *_pipeline.json files",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data/brief_goldens/runs/summary.csv",
        help="Output CSV path",
    )
    args = p.parse_args()

    runs_dir: Path = args.runs_dir
    if not runs_dir.is_dir():
        print(f"Not a directory: {runs_dir}", file=sys.stderr)
        return 2

    json_files = sorted(runs_dir.glob("*_pipeline.json"))
    if not json_files:
        print(f"No *_pipeline.json under {runs_dir}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "json_file",
        "source_pdf",
        "text_length",
        "citation_count",
        "cluster_count",
        "clusters_per_citation",
        "extract_method",
        "suspicious_reason",
    ]

    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for jp in json_files:
            data = json.loads(jp.read_text(encoding="utf-8"))
            tl = int(data.get("text_length") or 0)
            cc = int(data.get("citation_count") or 0)
            cl = int(data.get("cluster_count") or 0)
            em = data.get("extract_method") or ""
            src = data.get("source_pdf") or ""
            ratio = f"{cl / cc:.4f}" if cc else ""
            reasons: list[str] = []
            if tl < 4000 and cc == 0:
                reasons.append("short_text_zero_cites")
            if tl < 2500:
                reasons.append("very_short_text")
            if "%20" in Path(src).name and cc == 0:
                reasons.append("percent20_filename_zero_cites")
            w.writerow(
                {
                    "json_file": jp.name,
                    "source_pdf": src,
                    "text_length": tl,
                    "citation_count": cc,
                    "cluster_count": cl,
                    "clusters_per_citation": ratio,
                    "extract_method": em,
                    "suspicious_reason": ";".join(reasons),
                }
            )

    print(f"Wrote {len(json_files)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
