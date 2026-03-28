import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _is_statute_name(name: str) -> bool:
    """Return True if name is a statute/act (e.g. Administrative Procedure Act), not a case name."""
    if not name or len(name.strip()) < 5:
        return False
    n = name.strip().lower()
    if not n.endswith((" act", " code", " statute", " regulation", " rule")):
        return False
    statute_phrases = [
        "administrative procedure",
        "freedom of information",
        "civil rights",
        "voting rights",
        "fair housing",
    ]
    return any(p in n for p in statute_phrases)


_GENERIC_FALLBACK_NAMES = [
    "U.S. Supreme Court Case",
    "Federal Appeals Case",
    "Federal District Case",
    "Washington State Case",
    "Pacific Reporter Case",
    "Unknown Case",
    "Case (",
    "Legal Citation (",
]


def _is_generic_fallback_name(name: str) -> bool:
    """Check if name is a generic fallback (extraction failed)"""
    if not name or name == "N/A":
        return True
    return any(name.startswith(gen) or name == gen for gen in _GENERIC_FALLBACK_NAMES)


@dataclass
class ProcessingContext:
    """Context object to track processing state and enable debugging"""

    trace_id: str
    start_time: float
    input_text: str
    processing_mode: str
    current_stage: str = "initialized"
    stages_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Nothing needed; defaults handled by default_factory
        pass

    def trace_stage(self, stage_name: str, data: Any = None):
        """Track processing stage for debugging"""
        self.current_stage = stage_name
        self.stages_completed.append(stage_name)
        _ = data  # Reserved for future structured tracing
        elapsed = time.time() - self.start_time
        logger.debug("Stage %s completed in %.3fs", stage_name, elapsed)

    def add_error(self, error: str, stage: Optional[str] = None):
        """Record error for debugging"""
        error_msg = f"Error in {stage or self.current_stage}: {error}"
        self.errors.append(error_msg)
        logger.error(error_msg)

    def add_warning(self, message: str, stage: Optional[str] = None):
        """Record warning for debugging (e.g. verification timeout)."""
        warn_msg = f"Warning in {stage or self.current_stage}: {message}"
        self.warnings.append(warn_msg)
        logger.warning(warn_msg)


__all__ = [
    "ProcessingContext",
    "_is_statute_name",
    "_is_generic_fallback_name",
    "_GENERIC_FALLBACK_NAMES",
]

