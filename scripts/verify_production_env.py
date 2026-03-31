#!/usr/bin/env python3
"""
Validate env vars before production deploy (same rules as src.config at import time).

Usage:
  ENVIRONMENT=production SECRET_KEY=... REDIS_URL=... COURTLISTENER_API_KEY=... python scripts/verify_production_env.py

Exit 0 if OK; non-zero with message if not. Does not print secret values.
"""
from __future__ import annotations

import os
import sys


def _truthy(s: str | None) -> bool:
    if not s:
        return False
    return s.strip().lower() in ("1", "true", "yes", "on")


def main() -> int:
    env = (os.environ.get("ENVIRONMENT") or os.environ.get("FLASK_ENV") or "development").lower()
    if env != "production":
        print("verify_production_env: ENVIRONMENT is not 'production' — nothing to verify (OK).")
        return 0

    errors: list[str] = []

    sk = (os.environ.get("SECRET_KEY") or "").strip()
    if not sk or sk == "devkey" or len(sk) < 16:
        errors.append("SECRET_KEY must be set to a random string of at least 16 characters (32+ recommended).")

    redis_url = (os.environ.get("REDIS_URL") or "").strip()
    if not redis_url:
        errors.append("REDIS_URL must be set (e.g. redis://:password@host:6379/0).")
    elif "***REDACTED_REDIS_PASSWORD***" in redis_url and _truthy(os.environ.get("CASSTRAINER_FAIL_ON_WEAK_REDIS_PASSWORD")):
        errors.append(
            "REDIS_URL uses the repository example password; set a unique REDIS_PASSWORD "
            "(or unset CASSTRAINER_FAIL_ON_WEAK_REDIS_PASSWORD)."
        )

    verify_on = os.environ.get("ENABLE_VERIFICATION", "true")
    if verify_on.strip().lower() not in ("0", "false", "no", "off"):
        if not (os.environ.get("COURTLISTENER_API_KEY") or "").strip():
            errors.append("COURTLISTENER_API_KEY is required when ENABLE_VERIFICATION is true.")

    if errors:
        print("verify_production_env: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("verify_production_env: OK (production env vars present; values not shown).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
