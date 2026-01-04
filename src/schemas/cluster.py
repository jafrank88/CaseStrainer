from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class ClusterDTO:
    cluster_id: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    representative_citation: Optional[str] = None
    has_name_mismatch: bool = False
    has_date_mismatch: bool = False
    mismatch_indices: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_cluster_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a cluster-like dict to a stable DTO shape while preserving important fields."""
    if not isinstance(d, dict):
        try:
            d = d.to_dict() if hasattr(d, "to_dict") else dict(d)
        except Exception:
            return {"citations": []}

    from .citation import normalize_citation_dict

    citations_raw = d.get("citations") or []
    citations = [normalize_citation_dict(c) for c in citations_raw]

    # Start with the basic DTO fields
    result = {
        "cluster_id": d.get("cluster_id"),
        "citations": citations,
        "canonical_name": d.get("canonical_name") or d.get("canonical_case_name"),
        "canonical_date": d.get("canonical_date"),
        "representative_citation": d.get("representative_citation"),
        "has_name_mismatch": bool(d.get("has_name_mismatch", False)),
        "has_date_mismatch": bool(d.get("has_date_mismatch", False)),
        "mismatch_indices": list(d.get("mismatch_indices") or []),
        "metadata": dict(d.get("metadata") or {}),
    }

    # CRITICAL FIX: Preserve important cluster fields that were being stripped
    # These fields are needed for proper cluster display and validation
    important_fields = [
        "cluster_case_name",
        "cluster_year",
        "cluster_size",
        "confidence",
        "verification_status",
        "verification_source",
        "cluster_members",
        "name_similarity",
        "names_equivalent",
        "name_mismatch",
        "date_mismatch",
        "submitted_display_name",
        "submitted_display_date",
        "verifying_display_name",
        "verifying_display_date",
    ]

    for field in important_fields:
        if field in d:
            result[field] = d[field]

    return result
