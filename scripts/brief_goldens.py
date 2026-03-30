#!/usr/bin/env python3
"""
Golden expectations workflow for saved brief PDFs (e.g. under downloaded_briefs/).

1) Dump actual pipeline output (for manual review / authoring expectations)::

     python scripts/brief_goldens.py dump --pdf path/to/brief.pdf --out run.json

   Or every PDF under a directory (limit with --max-files)::

     python scripts/brief_goldens.py dump --dir downloaded_briefs --out-dir data/brief_goldens/runs

   CourtListener verification (slow; use for a subset, not hundreds of PDFs)::

     python scripts/brief_goldens.py dump --pdf downloaded_briefs/your.pdf \\
       --out data/brief_goldens/runs/one_verified.json --verify

2) Use ``data/brief_goldens/manifest.json`` (gitignored) or copy ``scripts/brief_goldens.manifest.example.json``.
   Each ``file`` is relative to the **repository root** (e.g. ``downloaded_briefs/...``, ``wa_briefs/...``).

3) Verify the tool matches those expectations (manifest paths are relative to repo root by default)::

     python scripts/brief_goldens.py verify --manifest data/brief_goldens/manifest.json

4) Tabulate a whole run as CSV::

     python scripts/report_brief_golden_dumps.py --runs-dir data/brief_goldens/runs/YOUR_RUN \\
       --out data/brief_goldens/runs/summary.csv

See ``src/utils/brief_golden_expectations.py`` for the full manifest schema.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_repo_path() -> None:
    import os

    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    os.chdir(REPO_ROOT)


def _serialize_result(result: dict[str, Any]) -> dict[str, Any]:
    citations = result.get("citations") or []
    clusters = result.get("clusters") or []
    cit_out = []
    for c in citations:
        if hasattr(c, "to_dict"):
            cit_out.append(c.to_dict())
        elif isinstance(c, dict):
            cit_out.append(dict(c))
        else:
            cit_out.append({"citation": str(getattr(c, "citation", c))})
    cl_out = []
    for cl in clusters:
        if isinstance(cl, dict):
            cl_out.append(
                {
                    "cluster_id": cl.get("cluster_id"),
                    "cluster_case_name": cl.get("cluster_case_name") or cl.get("case_name"),
                    "size": len(cl.get("citations") or []),
                    "citations": [
                        (m.get("citation") if isinstance(m, dict) else str(m))
                        for m in (cl.get("citations") or [])
                    ],
                }
            )
    return {
        "citation_count": len(cit_out),
        "cluster_count": len(cl_out),
        "citations": cit_out,
        "clusters": cl_out,
        "statistics": result.get("statistics"),
        "metadata": result.get("metadata"),
    }


async def _run_pipeline(
    text: str,
    *,
    enable_verification: bool,
    enable_parallel_verification: bool,
) -> dict[str, Any]:
    from src.unified_processing_pipeline import process_citations_unified

    return await process_citations_unified(
        text,
        enable_verification=enable_verification,
        enable_parallel_verification=enable_parallel_verification,
    )


def cmd_dump(args: argparse.Namespace) -> int:
    _ensure_repo_path()
    from src.unified_text_extractor import extract_text_from_file_unified

    out_dir = args.out_dir
    if args.pdf:
        paths = [Path(args.pdf)]
    else:
        d = Path(args.dir)
        paths = sorted(d.rglob("*.pdf"))
        if args.max_files:
            paths = paths[: int(args.max_files)]
    if not paths:
        print("No PDFs found.", file=sys.stderr)
        return 2
    if len(paths) > 1 and not args.out_dir:
        print("dump: use --out-dir when dumping multiple PDFs", file=sys.stderr)
        return 2

    for pdf_path in paths:
        text, method = extract_text_from_file_unified(str(pdf_path), verbose=False)
        result = asyncio.run(
            _run_pipeline(
                text,
                enable_verification=bool(args.verify),
                enable_parallel_verification=not args.no_parallel,
            )
        )
        if result.get("error"):
            print(f"[WARN] {pdf_path}: {result.get('error')}", file=sys.stderr)
        payload = {
            "source_pdf": str(pdf_path.resolve()),
            "text_length": len(text),
            "extract_method": method,
            **_serialize_result(result),
        }
        if args.out and len(paths) == 1:
            outp = Path(args.out)
        elif out_dir:
            outp = Path(out_dir) / (pdf_path.stem + "_pipeline.json")
        else:
            print(json.dumps(payload, indent=2)[:12000])
            if len(json.dumps(payload)) > 12000:
                print("\n... use --out or --out-dir", file=sys.stderr)
            continue
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {outp}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    _ensure_repo_path()
    from src.unified_text_extractor import extract_text_from_file_unified
    from src.utils.brief_golden_expectations import verify_expectation

    manifest_path = Path(args.manifest)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if int(data.get("version", 0)) != 1:
        print("Unsupported manifest version", file=sys.stderr)
        return 2

    defaults = data.get("defaults") or {}
    briefs_dir = Path(args.briefs_dir).resolve()
    failures = 0

    for doc in data.get("documents") or []:
        if doc.get("skip"):
            print(f"SKIP (skip:true) {doc.get('id', doc.get('file'))}")
            continue
        fname = doc.get("file")
        if not fname:
            print("document missing file", doc, file=sys.stderr)
            failures += 1
            continue
        pdf_path = Path(fname)
        if not pdf_path.is_file():
            pdf_path = briefs_dir / fname
        if not pdf_path.is_file():
            print(f"SKIP missing file: {fname}", file=sys.stderr)
            failures += 1
            continue

        ev = doc.get("enable_verification")
        if ev is None:
            ev = bool(defaults.get("enable_verification", False))
        epv = doc.get("enable_parallel_verification")
        if epv is None:
            epv = bool(defaults.get("enable_parallel_verification", True))

        text, _m = extract_text_from_file_unified(str(pdf_path), verbose=False)
        result = asyncio.run(_run_pipeline(text, enable_verification=ev, enable_parallel_verification=epv))
        citations = result.get("citations") or []
        clusters = result.get("clusters") or []

        expect = doc.get("expect") or {}
        errs = verify_expectation(
            expect,
            text_length=len(text),
            citations=citations,
            clusters=clusters if isinstance(clusters, list) else [],
        )
        did = doc.get("id") or fname
        if errs:
            failures += 1
            print(f"FAIL {did} ({pdf_path.name})")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {did} ({pdf_path.name})  citations={len(citations)} clusters={len(clusters)}")

    return 1 if failures else 0


def main() -> int:
    p = argparse.ArgumentParser(description="Brief PDF golden dump / verify workflow")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dump", help="Run pipeline on PDF(s) and write JSON snapshot")
    d.add_argument("--pdf", help="Single PDF path")
    d.add_argument("--dir", help="Directory of PDFs (recursive)")
    d.add_argument("--out", help="Write single JSON for one PDF")
    d.add_argument("--out-dir", help="Write one JSON per PDF under this directory")
    d.add_argument("--max-files", type=int, default=0, help="Limit files when using --dir")
    d.add_argument("--verify", action="store_true", help="Enable CourtListener verification (slow)")
    d.add_argument("--no-parallel", action="store_true", help="Disable parallel verification stage")
    d.set_defaults(func=cmd_dump)

    v = sub.add_parser("verify", help="Check manifest expectations against pipeline output")
    v.add_argument("--manifest", required=True, type=Path)
    v.add_argument(
        "--briefs-dir",
        default=str(REPO_ROOT),
        help="Base directory for manifest file paths (default: repo root; use e.g. downloaded_briefs/ and wa_briefs/ prefixes in file)",
    )
    v.set_defaults(func=cmd_verify)

    args = p.parse_args()
    if args.cmd == "dump" and not args.pdf and not args.dir:
        print("dump requires --pdf or --dir", file=sys.stderr)
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
