#!/usr/bin/env python3
"""Compare rough reporter-pattern counts in extracted text vs pipeline citation count (NAAG corpus)."""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SKIP_DEFAULT = frozenset(
    {
        "01_Tri-City-Valleycats-v-Commissioner_2023.pdf",
        "02_Robinson-v-Jackson-Hewitt_2023.pdf",
        "24_DDAVP-2d-Cir_2007.pdf",
    }
)

PATS = [
    re.compile(r"\b\d{1,3}\s+U\.?\s*S\.?\s+\d+\b", re.I),
    re.compile(r"\b\d{1,3}\s+F\.\s*(?:Supp\.?|2d|3d|4th)\s+\d+\b", re.I),
    re.compile(r"\b\d{1,3}\s+F\.\s*\d+[a-z]{0,2}\s+\d+\b", re.I),
    re.compile(r"\b\d{3,4}\s+WL\s+\d+\b", re.I),
    re.compile(r"\b\d{1,3}\s+A\.\s*2d\s+\d+\b", re.I),
    re.compile(r"\b\d{1,3}\s+N\.\s*E\.\s*2d\s+\d+\b", re.I),
]


def naive_hits(text: str) -> int:
    spans: list[tuple[int, int]] = []
    for p in PATS:
        for m in p.finditer(text):
            spans.append((m.start(), m.end()))
    if not spans:
        return 0
    spans.sort()
    merged = 1
    _, cur_e = spans[0]
    for s, e in spans[1:]:
        if s <= cur_e + 2:
            cur_e = max(cur_e, e)
        else:
            merged += 1
            cur_e = e
    return merged


async def pipe_count(text: str) -> int:
    from src.unified_processing_pipeline import process_citations_unified

    r = await process_citations_unified(
        text,
        enable_verification=False,
        enable_parallel_verification=False,
    )
    return len(r.get("citations") or [])


def main() -> int:
    os.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=REPO / "downloaded_briefs" / "naag_amicus")
    args = p.parse_args()
    d = args.dir.resolve()
    if not d.is_dir():
        print(f"Missing {d}", file=sys.stderr)
        return 2

    from src.unified_text_extractor import extract_text_from_file_unified

    print("file,chars,naive_patterns,tool_citations,ratio")
    for pdf in sorted(d.glob("*.pdf")):
        if pdf.name in SKIP_DEFAULT:
            continue
        text, _method = extract_text_from_file_unified(str(pdf), verbose=False)
        n_naive = naive_hits(text)
        n_tool = asyncio.run(pipe_count(text))
        ratio = round(n_tool / n_naive, 3) if n_naive else None
        rstr = "" if ratio is None else str(ratio)
        print(f"{pdf.name},{len(text)},{n_naive},{n_tool},{rstr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
