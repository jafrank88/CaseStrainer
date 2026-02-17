"""
Unified Verification Master - Compatibility Layer
====================================================

This module now serves as a compatibility layer that delegates to
the modular verification package in src.verification/.

The original implementation has been moved to:
- src.verification/master.py
- src.verification/sources.py
- src.verification/fallback.py
- src.verification/batch.py
- src.verification/utils.py

For new code, import directly from src.verification:
    from src.verification import UnifiedVerificationMaster
    from src.verification.sources import CourtListenerVerifier
"""

import warnings
import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

# Issue deprecation warning
warnings.warn(
    "unified_verification_master.py is deprecated. "
    "Use src.verification module instead. "
    "Import: from src.verification import UnifiedVerificationMaster",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from modular package (prefer importing from src.verification directly)
from src.verification import (
    UnifiedVerificationMaster,
    VerificationResult,
    VerificationSource,
    get_master_verifier,
    CourtListenerVerifier,
    JustiaVerifier,
    CornellLIIVerifier,
    OpenJuristVerifier,
    FallbackVerifier,
    verify_with_fallback_sources,
    BatchVerifier,
    calculate_name_similarity,
    validate_year_match,
    is_citation_likely_valid,
    calculate_case_name_overlap,
    apply_known_federal_to_citation_objects,
    apply_last_mile_cluster_display_sync,
    apply_known_federal_citations_and_clear_verified_without_url,
    apply_verification_paradox_fix,
    _normalize_citation_for_known_lookup,
)

__all__ = [
    "UnifiedVerificationMaster",
    "VerificationResult",
    "VerificationSource",
    "get_master_verifier",
    "CourtListenerVerifier",
    "JustiaVerifier",
    "CornellLIIVerifier",
    "OpenJuristVerifier",
    "FallbackVerifier",
    "verify_with_fallback_sources",
    "BatchVerifier",
    "calculate_name_similarity",
    "validate_year_match",
    "is_citation_likely_valid",
    "calculate_case_name_overlap",
    "apply_known_federal_to_citation_objects",
    "apply_last_mile_cluster_display_sync",
    "apply_known_federal_citations_and_clear_verified_without_url",
    "apply_verification_paradox_fix",
    "_normalize_citation_for_known_lookup",
]

logger.info("unified_verification_master.py loaded via compatibility layer (modular verification)")
