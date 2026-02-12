"""
Verification Package for CaseStrainer
=======================================

This package provides modular citation verification functionality,
breaking down unified_verification_master.py into focused modules.

Usage:
    from src.verification import UnifiedVerificationMaster
    from src.verification.sources import CourtListenerVerifier
    from src.verification.fallback import FallbackVerifier
"""

from .master import UnifiedVerificationMaster, VerificationResult, VerificationSource
from .sources import (
    CourtListenerVerifier,
    JustiaVerifier,
    CornellLIIVerifier,
    OpenJuristVerifier,
)
from .fallback import FallbackVerifier, verify_with_fallback_sources
from .batch import BatchVerifier
from .utils import calculate_case_name_overlap, validate_year_match
from src.utils.similarity_utils import calculate_name_similarity

__all__ = [
    # Main class
    "UnifiedVerificationMaster",
    "VerificationResult",
    "VerificationSource",
    # Sources
    "CourtListenerVerifier",
    "JustiaVerifier",
    "CornellLIIVerifier",
    "OpenJuristVerifier",
    # Fallback
    "FallbackVerifier",
    "verify_with_fallback_sources",
    # Batch
    "BatchVerifier",
    # Utils
    "calculate_case_name_overlap",
    "validate_year_match",
    "calculate_name_similarity",
]
