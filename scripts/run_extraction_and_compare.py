#!/usr/bin/env python3
"""
Run extraction then compare to expected fixture.
Uses subprocess for extraction to isolate OOM - if extraction fails, comparison is skipped.

Usage:
  python scripts/run_extraction_and_compare.py <pdf_path> <expected_fixture.json>

Example:
  python scripts/run_extraction_and_compare.py 1033397.pdf tests/fixtures/1033397_expected.json

Steps:
  1. Run extract_save_json.py (subprocess) -> saves to <pdf_stem>_actual.json
  2. Run compare_extraction_to_expected.py (subprocess) -> prints report
"""

import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_extraction_and_compare.py <pdf_path> <expected.json>")
        print("Example: python scripts/run_extraction_and_compare.py 1033397.pdf tests/fixtures/1033397_expected.json")
        sys.exit(1)

    base = Path(__file__).resolve().parent.parent
    pdf_path = Path(sys.argv[1])
    expected_path = Path(sys.argv[2])

    if not pdf_path.is_absolute():
        pdf_path = base / pdf_path
    if not expected_path.is_absolute():
        expected_path = base / expected_path

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)
    if not expected_path.exists():
        print(f"Expected fixture not found: {expected_path}")
        sys.exit(1)

    actual_path = base / f"{pdf_path.stem}_actual.json"

    scripts_dir = base / "scripts"
    extract_script = scripts_dir / "extract_save_json.py"
    compare_script = scripts_dir / "compare_extraction_to_expected.py"

    print("=" * 60)
    print("Step 1: Extract citations from PDF")
    print("=" * 60)
    r1 = subprocess.run(
        [sys.executable, str(extract_script), str(pdf_path), str(actual_path)],
        cwd=str(base),
    )
    if r1.returncode != 0:
        print("Extraction failed (possibly OOM). Skipping comparison.")
        sys.exit(r1.returncode)

    if not actual_path.exists():
        print("Extraction did not produce output file.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Step 2: Compare to expected fixture")
    print("=" * 60)
    r2 = subprocess.run(
        [sys.executable, str(compare_script), "--expected", str(expected_path), "--actual", str(actual_path)],
        cwd=str(base),
    )
    sys.exit(r2.returncode)


if __name__ == "__main__":
    main()
