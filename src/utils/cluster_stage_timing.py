"""
Optional millisecond timing for cluster pipeline stages.

Enable with either:
  - Environment variable ``CLUSTER_STAGE_TIMING=1`` (or ``true`` / ``yes`` / ``on``), or
  - ``CLUSTER_STAGE_TIMING`` in ``config.json`` / process environment via ``get_config_value``.

Logs use the ``[CLUSTER-TIMING]`` prefix at INFO so they are easy to grep in backend logs.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def cluster_stage_timing_enabled() -> bool:
    try:
        from src.config import get_config_value

        raw = get_config_value("CLUSTER_STAGE_TIMING")
    except Exception:
        raw = None
    if raw is None:
        return False
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def log_cluster_stage(name: str, t0: float, **kwargs: Any) -> None:
    if not cluster_stage_timing_enabled():
        return
    ms = (time.perf_counter() - t0) * 1000.0
    parts = [f"{k}={v}" for k, v in kwargs.items() if v is not None and v != ""]
    tail = (" " + " ".join(parts)) if parts else ""
    logger.info(f"[CLUSTER-TIMING] {name}: {ms:.1f} ms{tail}")
