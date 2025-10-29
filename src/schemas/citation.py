from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class CitationDTO:
    citation: str
    case_name: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    confidence: float = 0.0
    method: Optional[str] = None
    pattern: Optional[str] = None
    context: Optional[str] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    is_parallel: bool = False
    is_cluster: bool = False
    parallel_citations: List[str] = field(default_factory=list)
    cluster_members: List[str] = field(default_factory=list)
    pinpoint_pages: List[str] = field(default_factory=list)
    docket_numbers: List[str] = field(default_factory=list)
    case_history: List[str] = field(default_factory=list)
    publication_status: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cluster_id: Optional[str] = None
    cluster_case_name: Optional[str] = None
    true_by_parallel: bool = False
    name_mismatch: bool = False
    date_mismatch: bool = False
    mismatch_confidence: float = 0.0
    possible_match: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # case_name fallback: canonical > extracted > N/A
        fallback = self.canonical_name or self.extracted_case_name or 'N/A'
        d['case_name'] = self.case_name or fallback
        # ensure verified is bool
        d['verified'] = bool(self.verified)
        # alias for backward compatibility
        d['is_verified'] = d['verified']
        return d


def normalize_citation_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a citation-like dict to stable DTO shape without requiring callers to import DTO class."""
    if not isinstance(d, dict):
        try:
            # best-effort: use object's dict if present
            d = d.to_dict() if hasattr(d, 'to_dict') else dict(d)
        except Exception:
            return {'citation': str(d), 'case_name': 'N/A', 'verified': False}

    citation_text = str(d.get('citation') or d.get('text') or '').strip()
    extracted_case_name = d.get('extracted_case_name')
    canonical_name = d.get('canonical_name') or d.get('canonical_case_name')
    case_name = d.get('case_name') or canonical_name or extracted_case_name or 'N/A'

    normalized = {
        'citation': citation_text,
        'case_name': case_name,
        'extracted_case_name': extracted_case_name,
        'extracted_date': d.get('extracted_date'),
        'canonical_name': canonical_name,
        'canonical_date': d.get('canonical_date'),
        'canonical_url': d.get('canonical_url'),
        'verified': bool(d.get('verified', False)),
        'url': d.get('url'),
        'court': d.get('court'),
        'docket_number': d.get('docket_number'),
        'confidence': float(d.get('confidence', 0.0) or 0.0),
        'method': d.get('method'),
        'pattern': d.get('pattern'),
        'context': d.get('context'),
        'start_index': d.get('start_index'),
        'end_index': d.get('end_index'),
        'is_parallel': bool(d.get('is_parallel', False)),
        'is_cluster': bool(d.get('is_cluster', False)),
        'parallel_citations': list(d.get('parallel_citations') or []),
        'cluster_members': list(d.get('cluster_members') or []),
        'pinpoint_pages': list(d.get('pinpoint_pages') or []),
        'docket_numbers': list(d.get('docket_numbers') or []),
        'case_history': list(d.get('case_history') or []),
        'publication_status': d.get('publication_status'),
        'source': d.get('source'),
        'error': d.get('error'),
        'metadata': dict(d.get('metadata') or {}),
        'cluster_id': d.get('cluster_id'),
        'cluster_case_name': d.get('cluster_case_name') or (d.get('metadata') or {}).get('cluster_case_name'),
        'true_by_parallel': bool(d.get('true_by_parallel', False)),
        'name_mismatch': bool(d.get('name_mismatch', False)),
        'date_mismatch': bool(d.get('date_mismatch', False)),
        'mismatch_confidence': float(d.get('mismatch_confidence', 0.0) or 0.0),
        'possible_match': bool(d.get('possible_match', False)),
        'is_verified': bool(d.get('verified', False)),  # alias
    }
    return normalized
