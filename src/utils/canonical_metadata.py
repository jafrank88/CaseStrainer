"""Reusable helpers for canonical citation metadata handling."""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

try:
    from src.services.verification_manager import VerificationManager
except Exception:  # pragma: no cover - optional dependency
    VerificationManager = None


def normalize_citation_key(citation: Optional[str]) -> Optional[str]:
    """Normalize a citation string so it can be used as a dictionary key."""
    if not citation:
        return None
    normalized = citation.strip().lower()
    return normalized or None


def get_canonical_metadata(
    citation: Optional[str],
    citation_metadata_cache: Optional[Mapping[str, Dict[str, Any]]] = None,
    verified_citation_lookup: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Fetch canonical metadata from any available caches."""
    key = normalize_citation_key(citation)
    if not key:
        return {}

    if citation_metadata_cache:
        data = citation_metadata_cache.get(key)
        if data:
            return data

    if verified_citation_lookup:
        data = verified_citation_lookup.get(key)
        if data:
            return data

    return {}


# Re-export from canonical location
from src.utils.date_utils import extract_year_value  # noqa: F401


def prefer_canonical_name(
    extracted: Optional[str],
    canonical_metadata: Dict[str, Any],
    validator: Optional[Callable[[str], bool]] = None,
) -> Optional[str]:
    """Prefer canonical case names while honoring optional validation logic."""
    canonical_name = canonical_metadata.get("canonical_name")
    canonical_name = canonical_name.strip() if isinstance(canonical_name, str) else canonical_name

    extracted_name = extracted.strip() if isinstance(extracted, str) else extracted

    if validator:
        if canonical_name and validator(canonical_name):
            return canonical_name
        if extracted_name and validator(extracted_name):
            return extracted_name
    else:
        if canonical_name:
            return canonical_name
        if extracted_name:
            return extracted_name

    return canonical_name or extracted_name or None


def prefer_canonical_year(
    extracted_year: Optional[str],
    canonical_metadata: Dict[str, Any],
) -> Optional[str]:
    """Prefer canonical years while gracefully handling various formats."""
    canonical_raw = canonical_metadata.get("canonical_year") or canonical_metadata.get("canonical_date")
    canonical_year = extract_year_value(canonical_raw)
    extracted_year_value = extract_year_value(extracted_year)

    return canonical_year or extracted_year_value or canonical_raw or extracted_year


def fetch_canonical_metadata_on_demand(citation: str) -> Dict[str, Any]:
    """Best-effort lookup for canonical metadata when caches miss.

    Supports all citations including slip opinions (e.g. 592 U.S. ___).
    FastVerificationSystem has slip-opinion paths (CourtListener/Cornell by name;
    when extracted name is generic, main verification uses volume+year).
    """
    if not citation or not isinstance(citation, str):
        return {}

    # Try FastVerificationSystem first (the actual working verification)
    try:
        from src.fast_verification_system import FastVerificationSystem
        import asyncio

        verifier = FastVerificationSystem()
        # Run the async verification synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use asyncio.run
                # Fall back to sync method if available
                if hasattr(verifier, 'verify_citation_sync'):
                    result = verifier.verify_citation_sync(citation)
                else:
                    return {}
            else:
                result = asyncio.run(verifier.verify_citation(citation))
        except RuntimeError:
            # No event loop, create one
            result = asyncio.run(verifier.verify_citation(citation))

        if result and isinstance(result, dict):
            canonical_name = result.get("canonical_name")
            canonical_date = result.get("canonical_date")

            if canonical_name or canonical_date:
                payload: Dict[str, Any] = {}
                if canonical_name:
                    payload["canonical_name"] = canonical_name
                if canonical_date:
                    payload["canonical_date"] = canonical_date
                if result.get("url"):
                    payload["canonical_url"] = result["url"]
                return payload
    except Exception:
        pass  # Fall through to legacy path

    # Legacy fallback using VerificationManager (may not work)
    if VerificationManager is None:
        return {}

    try:
        manager = VerificationManager()
    except Exception:
        return {}

    try:
        result = manager.verify_single_citation(citation)
    except Exception:
        return {}

    if not result or not isinstance(result, dict):
        return {}

    canonical_name = result.get("canonical_name")
    canonical_date = result.get("canonical_date")

    if not canonical_name and not canonical_date:
        return {}

    payload: Dict[str, Any] = {}
    if canonical_name:
        payload["canonical_name"] = canonical_name
    if canonical_date:
        payload["canonical_date"] = canonical_date
    if result.get("url"):
        payload["canonical_url"] = result["url"]

    return payload


__all__ = [
    "normalize_citation_key",
    "get_canonical_metadata",
    "extract_year_value",
    "prefer_canonical_name",
    "prefer_canonical_year",
    "fetch_canonical_metadata_on_demand",
]
