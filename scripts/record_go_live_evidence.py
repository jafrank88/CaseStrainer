#!/usr/bin/env python3
"""
Append a timestamped `scripts/ci_regression.py` run to docs/go-live-evidence/REGRESSION_LOG.md.

Run from repo root after manual QA to preserve evidence for the go-live checklist.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs" / "go-live-evidence" / "REGRESSION_LOG.md"


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text(
            "# Regression / automated gate evidence\n\n"
            "Append-only log from `scripts/record_go_live_evidence.py`.\n",
            encoding="utf-8",
        )
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ci_regression.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    block = (
        f"\n## {ts}\n\n"
        f"Command: `python scripts/ci_regression.py`\n\n"
        f"```\n{out}\n{err}\n```\n\n"
        f"Exit code: {proc.returncode}\n"
    )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(block)
    print(block)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
