from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ProgressState:
    progress: int
    status: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
