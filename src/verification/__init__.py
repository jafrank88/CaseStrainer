"""
Verification Package for CaseStrainer
=======================================

This package provides modular citation verification functionality,
breaking down unified_verification_master.py into focused modules.

Usage:
    from src.verification import UnifiedVerificationMaster, get_master_verifier
    from src.verification import apply_last_mile_cluster_display_sync, apply_known_federal_to_citation_objects
    from src.verification.sources import CourtListenerVerifier
"""

from .master import (
    UnifiedVerificationMaster,
    VerificationResult,
    VerificationSource,
    get_master_verifier,
)
from .sources import (
    BaseURLVerifier,
    CourtListenerVerifier,
    JustiaVerifier,
    CornellLIIVerifier,
    OpenJuristVerifier,
)
from .fallback import FallbackVerifier, verify_with_fallback_sources
from .batch import BatchVerifier
from .utils import (
    calculate_case_name_overlap,
    validate_year_match,
    years_match_for_verification,
    is_citation_likely_valid,
)
from .result_processing import (
    apply_known_federal_to_citation_objects,
    apply_last_mile_cluster_display_sync,
    apply_known_federal_citations_and_clear_verified_without_url,
    apply_verification_paradox_fix,
)
from .known_citations import _normalize_citation_for_known_lookup
from src.utils.similarity_utils import calculate_name_similarity

__all__ = [
    # Main class and factory
    "UnifiedVerificationMaster",
    "VerificationResult",
    "VerificationSource",
    "get_master_verifier",
    # Sources
    "BaseURLVerifier",
    "CourtListenerVerifier",
    "JustiaVerifier",
    "CornellLIIVerifier",
    "OpenJuristVerifier",
    # Fallback
    "FallbackVerifier",
    "verify_with_fallback_sources",
    # Batch
    "BatchVerifier",
    # Result processing
    "apply_known_federal_to_citation_objects",
    "apply_last_mile_cluster_display_sync",
    "apply_known_federal_citations_and_clear_verified_without_url",
    "apply_verification_paradox_fix",
    # Known citations
    "_normalize_citation_for_known_lookup",
    # Utils
    "calculate_case_name_overlap",
    "validate_year_match",
    "years_match_for_verification",
    "is_citation_likely_valid",
    "calculate_name_similarity",
]
