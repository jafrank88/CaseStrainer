from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class CitationResult:
    citation: str
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    confidence: float = 0.0
    method: str = "unified_processor"
    pattern: str = ""
    context: str = ""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    is_parallel: bool = False
    is_cluster: bool = False
    parallel_citations: List[str] = None
    cluster_members: List[str] = None
    pinpoint_pages: List[str] = None
    docket_numbers: List[str] = None
    case_history: List[str] = None
    publication_status: Optional[str] = None
    source: str = "Unknown"
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    cluster_id: Optional[str] = None

    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []
        if self.cluster_members is None:
            self.cluster_members = []
        if self.pinpoint_pages is None:
            self.pinpoint_pages = []
        if self.docket_numbers is None:
            self.docket_numbers = []
        if self.case_history is None:
            self.case_history = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingConfig:
    use_eyecite: bool = True
    use_regex: bool = True
    extract_case_names: bool = True
    extract_dates: bool = True
    enable_clustering: bool = True
    enable_deduplication: bool = True
    enable_verification: bool = True
    context_window: int = 400
    min_confidence: float = 0.5
    max_citations_per_text: int = 1000
    debug_mode: bool = False 