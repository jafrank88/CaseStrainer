"""
Pytest configuration and shared fixtures for CaseStrainer tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Wolf / CI parity: use local Redis for pytest unless explicitly disabled ---
# Shell or .env may set REDIS_URL to casestrainer-redis-prod (Docker network only). Tests use the
# same code paths as wolf; Redis must resolve on the machine running pytest. Set
# CASSTRAINER_USE_TEST_REDIS=0 to skip forcing these values.
def _apply_test_redis_env() -> None:
    v = os.environ.get("CASSTRAINER_USE_TEST_REDIS", "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return
    os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"
    os.environ["REDIS_HOST"] = "127.0.0.1"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["CACHE_REDIS_URL"] = "redis://127.0.0.1:6379/1"


_apply_test_redis_env()

_TESTS_DIR = Path(__file__).resolve().parent
# tests/unit and other subtrees hold scripts and experiments; wolf regression is top-level test_*.py only.
collect_ignore = [
    str(_TESTS_DIR / "unit"),
    str(_TESTS_DIR / "analysis"),
    str(_TESTS_DIR / "debug"),
    str(_TESTS_DIR / "clustering"),
    str(_TESTS_DIR / "extraction"),
    str(_TESTS_DIR / "integration"),
    str(_TESTS_DIR / "performance"),
    str(_TESTS_DIR / "validation"),
    str(_TESTS_DIR / "verification"),
    str(_TESTS_DIR / "e2e"),
    str(_TESTS_DIR / "integration_test.py"),
    str(_TESTS_DIR / "test_analyze_smoke.py"),
    str(_TESTS_DIR / "test_pipeline.py"),
    str(_TESTS_DIR / "test_webber_extraction.py"),
    str(_TESTS_DIR / "extraction_comparison.py"),
]

# Ensure project root is on path so "src" imports work
ROOT = str(_TESTS_DIR.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
