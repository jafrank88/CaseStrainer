#!/usr/bin/env python3
"""
Compare extraction results for a Washington Courts opinion served via URL vs the local file copy.

This uses the server-side URL extraction logic (content-type aware, robust fetch) and the
local smart extractor for the file, then prints lengths and a small digest of content.
"""

import os
import sys
import hashlib

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from unified_input_processor import UnifiedInputProcessor, extract_text_from_pdf_smart  # type: ignore


def digest_preview(text: str, n: int = 300) -> str:
    s = (text or '').strip()
    head = s[:n]
    h = hashlib.sha256(s.encode('utf-8', errors='ignore')).hexdigest()[:16]
    return f"{len(s)} chars | sha256[:16]={h} | preview=\n{head}"


def main() -> None:
    url = "https://www.courts.wa.gov/opinions/pdf/D2%2060382-9-II%20Published%20Opinion.pdf"
    local_path = r"D:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"

    processor = UnifiedInputProcessor()
    req_id = "URLVSFILE-TEST"

    print("=== URL extraction ===")
    url_result = processor._extract_text_from_input(url, 'url', req_id)
    print({k: url_result.get(k) for k in ('success', 'error')})
    url_text = url_result.get('text') or ''
    print(digest_preview(url_text))

    print("\n=== FILE extraction ===")
    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return
    try:
        file_text = extract_text_from_pdf_smart(local_path) or ''
    except Exception as e:
        print(f"File extract error: {e}")
        return
    print(digest_preview(file_text))

    print("\n=== Comparison ===")
    len_url = len(url_text.strip())
    len_file = len(file_text.strip())
    if len_file == 0 and len_url == 0:
        print("Both empty → likely image-based PDF; OCR required.")
    elif len_url < max(50, int(0.1 * len_file)):
        print(f"URL extraction is much smaller than file (url={len_url}, file={len_file}).")
    else:
        print(f"URL extraction comparable (url={len_url}, file={len_file}).")


if __name__ == "__main__":
    main()


