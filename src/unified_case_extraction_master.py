"""
Unified Case Extraction Master - Compatibility Layer
======================================================

This module now serves as a compatibility layer that delegates to
the modular extraction package in src/extraction/.

The original implementation has been moved to:
- src/extraction/master.py
- src/extraction/strategies.py
- src/extraction/validation.py
- src/extraction/utils.py

For new code, import directly from src.extraction:
    from src.extraction import UnifiedCaseExtractionMaster
    from src.extraction.strategies import ProximityStrategy
"""

import warnings
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# Issue deprecation warning
warnings.warn(
    "unified_case_extraction_master.py is deprecated. "
    "Use src.extraction module instead. "
    "Import: from src.extraction import UnifiedCaseExtractionMaster",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from modular package
from src.extraction import (
    UnifiedCaseExtractionMaster,
    MasterExtractionResult,
    extract_case_name_and_date_unified_master,
    ProximityStrategy,
    PatternStrategy,
    MLStrategy,
    validate_case_name,
    is_valid_case_name,
    extract_year_from_text,
    clean_case_name,
    calculate_name_similarity,
)

from src.extraction.strategies import ExtractionStrategy

from src.extraction.utils import (
    extract_date_from_text,
    extract_context_around_citation,
    find_case_name_in_context,
    is_likely_statute,
)

__all__ = [
    # Main class and function
    "UnifiedCaseExtractionMaster",
    "MasterExtractionResult",
    "extract_case_name_and_date_unified_master",
    # Strategies
    "ExtractionStrategy",
    "ProximityStrategy",
    "PatternStrategy",
    "MLStrategy",
    # Validation
    "validate_case_name",
    "is_valid_case_name",
    # Utils
    "extract_year_from_text",
    "extract_date_from_text",
    "clean_case_name",
    "calculate_name_similarity",
    "extract_context_around_citation",
    "find_case_name_in_context",
    "is_likely_statute",
]

logger.info("unified_case_extraction_master.py loaded via compatibility layer (modular extraction)")
