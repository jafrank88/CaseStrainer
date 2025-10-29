from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class VerificationResultDTO:
    source: Optional[str] = None
    status: Optional[str] = None  # e.g., 'queued','processing','completed','failed'
    progress_percent: int = 0
    message: Optional[str] = None

    verified: bool = False
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    confidence: float = 0.0

    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['verified'] = bool(self.verified)
        return d
