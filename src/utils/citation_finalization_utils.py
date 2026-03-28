"""
Shared finalization helpers for citation verification metadata.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping, Protocol

from src.utils.verification_display_utils import is_proprietary_citation


class LoggerLike(Protocol):
    def warning(self, msg: str) -> Any:
        ...


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _set(item: Any, key: str, value: Any) -> None:
    if isinstance(item, dict):
        item[key] = value
    else:
        setattr(item, key, value)


def apply_final_year_alignment(
    item: Any,
    *,
    evaluate_year_alignment: Callable[..., Mapping[str, Any]],
    logger: LoggerLike,
    log_tag: str,
) -> int:
    """
    Apply final year alignment checks to a citation-like object or dict.
    Returns 1 when a hard mismatch causes unverification, else 0.
    """
    verified = _get(item, "verified", None)
    canonical_date = _get(item, "canonical_date", None)

    # Clear date mismatch flag when no canonical date exists to compare against.
    if not canonical_date:
        if isinstance(item, dict) or hasattr(item, "date_mismatch"):
            _set(item, "date_mismatch", False)

    if verified is not True:
        return 0

    # Strict proprietary-year guard:
    # For WL/LEXIS citations the year is explicit in citation text. If it conflicts with
    # canonical year, treat as a hard mismatch to avoid false-positive verification.
    citation_text = str(_get(item, "citation", "") or "")
    if is_proprietary_citation(citation_text):
        m_cit = re.search(r"\b((?:19|20)\d{2})\s+(?:WL|(?:U\.S\.?\s+)?LEXIS)\s+\d+\b", citation_text, re.IGNORECASE)
        m_can = re.search(r"\b((?:19|20)\d{2})\b", str(canonical_date or ""))
        if m_cit and m_can and m_cit.group(1) != m_can.group(1):
            _set(item, "verified", False)
            _set(
                item,
                "verification_error",
                f"Year mismatch: citation {m_cit.group(1)} vs canonical {m_can.group(1)}",
            )
            logger.warning(
                f"[ERROR] [{log_tag}] {citation_text}: Unverified due to WL/LEXIS year mismatch "
                f"(citation={m_cit.group(1)}, canonical={m_can.group(1)})"
            )
            return 1

    extracted_date = _get(item, "extracted_date", None)
    if not (extracted_date and canonical_date):
        return 0

    metadata = _get(item, "metadata", {}) or {}
    year_eval = evaluate_year_alignment(
        citation_text=str(_get(item, "citation", "") or ""),
        extracted_date=extracted_date,
        canonical_date=canonical_date,
        verification_source=_get(item, "source", None),
        in_toa_section=bool((metadata or {}).get("in_toa_section", False)),
    )
    metadata["year_source"] = year_eval.get("compare_source")
    metadata["year_compare_value"] = year_eval.get("compare_year")
    if year_eval.get("soft_mismatch"):
        metadata["year_mismatch_type"] = "soft"
    elif year_eval.get("hard_mismatch"):
        metadata["year_mismatch_type"] = "hard"
    else:
        metadata["year_mismatch_type"] = None
    _set(item, "metadata", metadata)

    if year_eval.get("hard_mismatch"):
        _set(item, "verified", False)
        _set(
            item,
            "verification_error",
            f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}",
        )
        logger.warning(
            f"[ERROR] [{log_tag}] {_get(item, 'citation')}: Unverified due to hard year mismatch "
            f"(extracted={extracted_date}, canonical={canonical_date}, "
            f"compare_source={year_eval.get('compare_source')}, diff={year_eval.get('year_diff')})"
        )
        return 1
    return 0


def apply_proprietary_status(item: Any) -> tuple[int, int]:
    """
    Apply/clear proprietary status for WL/LEXIS citations.
    Returns (marked_count, cleared_count) deltas for counters.
    """
    citation_text = str(_get(item, "citation", "") or "")
    # Use citation-type flag when set (pipeline integration); else fall back to string check
    if not (_get(item, "is_proprietary_only") is True or is_proprietary_citation(citation_text)):
        return (0, 0)

    is_verified = bool(_get(item, "verified", False))
    is_verified_by_parallel = bool(_get(item, "true_by_parallel", False))
    has_canonical_url = bool((_get(item, "canonical_url", None) or _get(item, "url", None)))
    verification_status = str(_get(item, "verification_status", "") or "").strip().lower()

    # If citation is effectively verified-ish (or a deliberate possible-match/year-mismatch lane),
    # clear stale proprietary messaging.
    keep_non_proprietary_reason = verification_status in {"possible_match_with_url", "year_mismatch"}
    if is_verified or is_verified_by_parallel or keep_non_proprietary_reason:
        cleared = 0
        if _get(item, "verification_status", None) == "proprietary_format":
            _set(item, "verification_status", "verified" if is_verified else "verified_with_url")
            cleared += 1
        existing_error = str(_get(item, "error", "") or "")
        existing_verification_error = str(_get(item, "verification_error", "") or "")
        if "Westlaw/Lexis only" in existing_error:
            _set(item, "error", None)
            cleared += 1
        if "proprietary format" in existing_verification_error.lower():
            _set(item, "verification_error", None)
            cleared += 1
        return (0, cleared)

    # URL-only is not enough to suppress proprietary status.
    # Some paths can leave transient/stale URLs on unresolved citations.
    if has_canonical_url and not is_verified and not is_verified_by_parallel and not keep_non_proprietary_reason:
        _set(item, "canonical_url", None)
        _set(item, "url", None)

    # Truly unverified proprietary citation.
    # Always show the proprietary user-facing reason (single source of truth),
    # rather than leaving generic "No result" style errors.
    _set(item, "verification_status", "proprietary_format")
    _set(item, "verification_error", "Unverified due to proprietary format")
    _set(item, "error", "Proprietary format - not available in free databases (Westlaw/Lexis only)")
    return (1, 0)

