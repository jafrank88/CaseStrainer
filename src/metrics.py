from __future__ import annotations
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from src.redis_helper import get_redis_connection


def _today(date_str: Optional[str] = None) -> str:
    return date_str or datetime.utcnow().strftime("%Y-%m-%d")


def record_submission(citation_count: int = 0, date_str: Optional[str] = None) -> None:
    try:
        r = get_redis_connection()
        day = _today(date_str)
        r.incr(f"metrics:documents:{day}")
        if citation_count and citation_count > 0:
            r.incrby(f"metrics:citations:{day}", int(citation_count))
            r.incrby("metrics:citations:total", int(citation_count))
        r.incr("metrics:documents:total")
    except Exception:
        pass


def record_citations(citation_count: int, date_str: Optional[str] = None) -> None:
    try:
        if not citation_count or citation_count <= 0:
            return
        r = get_redis_connection()
        day = _today(date_str)
        r.incrby(f"metrics:citations:{day}", int(citation_count))
        r.incrby("metrics:citations:total", int(citation_count))
    except Exception:
        pass


def record_document(date_str: Optional[str] = None) -> None:
    try:
        r = get_redis_connection()
        day = _today(date_str)
        r.incr(f"metrics:documents:{day}")
        r.incr("metrics:documents:total")
    except Exception:
        pass


def get_daily_counts(date_str: Optional[str] = None) -> Dict[str, int]:
    try:
        r = get_redis_connection()
        day = _today(date_str)
        docs = r.get(f"metrics:documents:{day}")
        cites = r.get(f"metrics:citations:{day}")
        return {
            "date": day,  # type: ignore
            "documents": int(docs or 0),
            "citations": int(cites or 0),
        }
    except Exception:
        return {"date": _today(date_str), "documents": 0, "citations": 0}


def get_totals() -> Dict[str, int]:
    """Return total counters for all time (best-effort)."""
    try:
        r = get_redis_connection()
        docs = r.get("metrics:documents:total")
        cites = r.get("metrics:citations:total")
        return {
            "documents": int(docs or 0),
            "citations": int(cites or 0),
        }
    except Exception:
        return {"documents": 0, "citations": 0}


def get_counts_last_n_days(days: int = 30, end_date: Optional[str] = None) -> List[Dict[str, int]]:
    """Return a list of per-day counts for the last N days ending at end_date (UTC)."""
    try:
        days = max(1, int(days))
    except Exception:
        days = 30

    try:
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.utcnow()
        # Build date list from oldest to newest
        dates = [(end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in reversed(range(days))]

        r = get_redis_connection()
        doc_keys = [f"metrics:documents:{d}" for d in dates]
        cite_keys = [f"metrics:citations:{d}" for d in dates]
        doc_vals = r.mget(doc_keys)
        cite_vals = r.mget(cite_keys)
        series: List[Dict[str, int]] = []
        for i, d in enumerate(dates):
            dv = int(doc_vals[i] or 0)
            cv = int(cite_vals[i] or 0)
            series.append({"date": d, "documents": dv, "citations": cv})
        return series
    except Exception:
        # Fallback: compute naively
        return [get_daily_counts(d) for d in dates] if "dates" in locals() else []
