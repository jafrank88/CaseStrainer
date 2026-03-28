"""
Case Extraction Package for CaseStrainer
========================================

This package provides modular case name and date extraction functionality,
breaking down unified_case_extraction_master.py into focused modules.

Usage:
    from src.extraction import UnifiedCaseExtractionMaster
    from src.extraction.strategies import ProximityStrategy, PatternStrategy
"""

from .master import (
    UnifiedCaseExtractionMaster,
    MasterExtractionResult,
    extract_case_name_and_date_unified_master,
    get_master_extractor,
)
from .strategies import ProximityStrategy, PatternStrategy, MLStrategy
from .validation import validate_case_name, is_valid_case_name
from .utils import extract_year_from_text, clean_case_name, calculate_name_similarity
from src.utils.strict_context_isolator import extract_case_name_from_strict_context

__all__ = [
    # Main class and factory
    "UnifiedCaseExtractionMaster",
    "MasterExtractionResult",
    "extract_case_name_and_date_unified_master",
    "get_master_extractor",
    # Strict-context (re-export for single import path)
    "extract_case_name_from_strict_context",
    # Strategies
    "ProximityStrategy",
    "PatternStrategy",
    "MLStrategy",
    # Validation
    "validate_case_name",
    "is_valid_case_name",
    # Utils
    "extract_year_from_text",
    "clean_case_name",
    "calculate_name_similarity",
]
