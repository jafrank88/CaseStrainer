#!/usr/bin/env python3
"""
Enhanced Fallback Citation Verification System - FAST VERSION

This system provides fast citation verification with multiple tiers:
1. Tier 1: Local pattern verification (instant for Washington citations)
2. Tier 2: Single fast source verification (2-3 seconds max)
3. Tier 3: Smart fallback using extracted data

Replaces the stub with actual verification capability while maintaining
speed and reliability.
"""

import logging
from typing import Dict, Optional, Any

# Import the fast verification system
from src.fast_verification_system import FastVerificationSystem

logger = logging.getLogger(__name__)


class EnhancedFallbackVerifier:
    """
    Enhanced fallback verifier using fast verification system.
    Maintains compatibility with original interface while providing
    much better performance than the old multi-source approach.

    Performance improvements:
    - Washington citations: < 0.1 seconds (pattern matching)
    - Web verification: 2-5 seconds (single source)
    - Fallback verification: < 0.1 seconds (calculated)

    Compared to old system:
    - Old: 7+ sources × 15s timeouts + rate limiting = 60+ seconds
    - New: 1 source × 5s timeout = 5 seconds max
    """

    def __init__(self, enable_experimental_engines=True):
        logger.info("[ENHANCED-FALLBACK-FAST] Using fast verification system")
        self.enable_experimental_engines = enable_experimental_engines
        self.fast_verifier = FastVerificationSystem(
            enable_web_verification=enable_experimental_engines, max_timeout=5.0
        )

    async def verify_citation_async(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_year: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Async verification with fast system"""
        return await self.fast_verifier.verify_citation_async(citation, extracted_case_name, extracted_year, timeout)

    def verify_citation_sync(
        self, citation: str, extracted_case_name: Optional[str] = None, extracted_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync verification with fast system"""
        return self.fast_verifier.verify_citation_sync(citation, extracted_case_name, extracted_year)

    async def verify_citation(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        enable_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Main verification method with fast system"""
        return await self.fast_verifier.verify_citation(citation, extracted_case_name, extracted_date, enable_fallback)
