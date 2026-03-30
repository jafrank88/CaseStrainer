#!/usr/bin/env python3
"""
Run extraction and/or comparison in separate steps to avoid OOM.

Step 1 (extract): Run extraction in subprocess, save to JSON.
Step 2 (compare): Compare actual JSON to expected fixture.

Usage:
  # Extract only (saves to JSON; run in separate process to limit memory)
  python scripts/run_extract_and_compare.py extract <pdf_path> <output.json>

  # Compare only (lightweight; no extraction)
  python scripts/run_extract_and_compare.py compare <expected.json> <actual.json>

  # Both: extract then compare (extract runs in subprocess)
  python scripts/run_extract_and_compare.py both <pdf_path> <expected.json> [output.json]
"""

import subprocess
import sys
from pathlib import Path


def run_extract(pdf_path: Path, output_path: Path) -> int:
    """Run extraction in subprocess. Returns exit code."""
    script = Path(__file__).resolve().parent / "_extract_pdf_to_json.py"
    cmd = [sys.executable, str(script), str(pdf_path), str(output_path)]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parent.parent)
    return result.returncode


def run_compare(expected_path: Path, actual_path: Path) -> int:
    """Run comparison. Returns exit code."""
    script = Path(__file__).resolve().parent / "compare_extraction_to_expected.py"
    cmd = [sys.executable, str(script), str(expected_path), str(actual_path)]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parent.parent)
    return result.returncode


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    mode = sys.argv[1].lower()

    if mode == "extract":
        if len(sys.argv) < 4:
            print("Usage: python run_extract_and_compare.py extract <pdf_path> <output.json>")
            return 1
        pdf_path = Path(sys.argv[2])
        output_path = Path(sys.argv[3])
        if not pdf_path.exists():
            print(f"Error: PDF not found: {pdf_path}")
            return 1
        return run_extract(pdf_path, output_path)

    if mode == "compare":
        if len(sys.argv) < 4:
            print("Usage: python run_extract_and_compare.py compare <expected.json> <actual.json>")
            return 1
        expected_path = Path(sys.argv[2])
        actual_path = Path(sys.argv[3])
        if not expected_path.exists():
            print(f"Error: Expected file not found: {expected_path}")
            return 1
        if not actual_path.exists():
            print(f"Error: Actual file not found: {actual_path}")
            return 1
        return run_compare(expected_path, actual_path)

    if mode == "both":
        if len(sys.argv) < 4:
            print("Usage: python run_extract_and_compare.py both <pdf_path> <expected.json> [output.json]")
            return 1
        pdf_path = Path(sys.argv[2])
        expected_path = Path(sys.argv[3])
        output_path = Path(sys.argv[4]) if len(sys.argv) > 4 else Path(f"{pdf_path.stem}_actual.json")
        if not pdf_path.exists():
            print(f"Error: PDF not found: {pdf_path}")
            return 1
        if not expected_path.exists():
            print(f"Error: Expected file not found: {expected_path}")
            return 1
        print("Step 1: Extracting (subprocess)...")
        code = run_extract(pdf_path, output_path)
        if code != 0:
            return code
        print("\nStep 2: Comparing...")
        return run_compare(expected_path, output_path)

    print(f"Unknown mode: {mode}. Use extract, compare, or both.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
