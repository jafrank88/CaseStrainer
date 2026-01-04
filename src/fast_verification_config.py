"""
Fast verification configuration that uses CourtListener lookup, CaseMine, and Law.Resource.org for Federal citations
"""

import logging
from typing import Optional, List
from src.unified_verification_master import VerificationResult, VerificationSource
import re

logger = logging.getLogger(__name__)


class FastVerificationConfig:
    """
    Configuration for fast verification using CourtListener lookup, CaseMine, and Law.Resource.org for Federal citations
    """

    def __init__(self):
        # Use fast sources including Law.Resource.org for Federal citations
        self.enabled_sources = [
            VerificationSource.COURTLISTENER_LOOKUP,
            VerificationSource.CASEMINE,
            "LAW_RESOURCE",  # Law.Resource.org for Federal citations
        ]
        self.timeout_per_source = 8.0  # 8 seconds per source
        self.total_timeout = 20.0  # 20 seconds total

    def is_federal_citation(self, citation: str) -> bool:
        """
        Check if citation is Federal Reporter (F./F.2d/F.3d)

        Args:
            citation: Citation string to check

        Returns:
            True if Federal Reporter citation
        """
        # Federal Reporter patterns
        federal_patterns = [
            r"\b\d+\s+F\.\s*\d+",  # F.1d, F.2d, F.3d, etc.
            r"\b\d+\s+F\.\s*[23]d\.\s*\d+",  # F.2d, F.3d
            r"\b\d+\s+F\.\s*Sup\.\s*\d+",  # F. Sup.
        ]

        for pattern in federal_patterns:
            if re.search(pattern, citation, re.IGNORECASE):
                return True
        return False

    async def verify_with_law_resource(
        self, citation: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify citation using Law.Resource.org (Federal citations only)

        Args:
            citation: Citation string to verify
            extracted_case_name: Optional extracted case name
            extracted_date: Optional extracted date

        Returns:
            VerificationResult with verification status
        """
        if not self.is_federal_citation(citation):
            return VerificationResult(citation=citation, verified=False, error="Not a Federal Reporter citation")

        try:
            # Import Law Resource verifier
            from src.unified_verification_master import UnifiedVerificationMaster

            verifier = UnifiedVerificationMaster()

            result = await verifier._verify_with_law_resource(citation, extracted_case_name, extracted_date)
            if result.verified:
                logger.info(f"[FAST-VERIFY] Law.Resource.org succeeded for '{citation}'")
                return result
            else:
                logger.info(f"[FAST-VERIFY] Law.Resource.org failed for '{citation}'")

        except Exception as e:
            logger.warning(f"[FAST-VERIFY] Law.Resource.org error for '{citation}': {e}")

        return VerificationResult(citation=citation, verified=False, error="Law.Resource.org verification failed")

    async def verify_citation_fast(
        self, citation: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None
    ) -> VerificationResult:
        """
        Fast verification using CourtListener lookup, CaseMine, and Law.Resource.org

        Priority order:
        1. CourtListener lookup (fastest)
        2. CaseMine (good for Federal citations)
        3. Law.Resource.org (Federal citations only)

        Args:
            citation: Citation string to verify
            extracted_case_name: Optional extracted case name
            extracted_date: Optional extracted date

        Returns:
            VerificationResult with verification status
        """
        logger.info(f"[FAST-VERIFY] Starting fast verification for '{citation}'")

        # Try CourtListener lookup first (fastest)
        try:
            from src.unified_verification_master import UnifiedVerificationMaster

            verifier = UnifiedVerificationMaster()

            result = await verifier._verify_with_courtlistener_lookup(citation, extracted_case_name, extracted_date)
            if result.verified:
                logger.info(f"[FAST-VERIFY] CourtListener lookup succeeded for '{citation}'")
                return result
            else:
                logger.info(f"[FAST-VERIFY] CourtListener lookup failed for '{citation}'")
        except Exception as e:
            logger.warning(f"[FAST-VERIFY] CourtListener lookup error for '{citation}': {e}")

        # Try CaseMine second
        try:
            from src.unified_verification_master import UnifiedVerificationMaster

            verifier = UnifiedVerificationMaster()

            result = await verifier._verify_with_casemine(
                citation, extracted_case_name, extracted_date, min(self.timeout_per_source, 12.0)
            )
            if result.verified or getattr(result, "possible_match", False):
                logger.info(f"[FAST-VERIFY] CaseMine succeeded for '{citation}'")
                return result
            else:
                logger.info(f"[FAST-VERIFY] CaseMine failed for '{citation}'")
        except Exception as e:
            logger.warning(f"[FAST-VERIFY] CaseMine error for '{citation}': {e}")

        # Try Law.Resource.org for Federal citations
        if self.is_federal_citation(citation):
            try:
                result = await self.verify_with_law_resource(citation, extracted_case_name, extracted_date)
                if result.verified:
                    logger.info(f"[FAST-VERIFY] Law.Resource.org succeeded for '{citation}'")
                    return result
                else:
                    logger.info(f"[FAST-VERIFY] Law.Resource.org failed for '{citation}'")
            except Exception as e:
                logger.warning(f"[FAST-VERIFY] Law.Resource.org error for '{citation}': {e}")

        # All sources failed
        logger.warning(f"[FAST-VERIFY] All fast sources failed for '{citation}'")
        return VerificationResult(
            citation=citation, verified=False, error="Fast verification failed - all sources failed"
        )

    async def verify_citations_batch_fast(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None,
    ) -> List[VerificationResult]:
        """
        Batch verification using fast sources

        Args:
            citations: List of citations to verify
            extracted_case_names: Optional list of extracted case names
            extracted_dates: Optional list of extracted dates

        Returns:
            List of VerificationResult objects
        """
        logger.info(f"[FAST-VERIFY] Starting batch verification for {len(citations)} citations")

        # Prepare data
        case_names = extracted_case_names or [None] * len(citations)
        dates = extracted_dates or [None] * len(citations)

        # First try CourtListener batch lookup (fastest for multiple citations)
        try:
            from src.unified_verification_master import UnifiedVerificationMaster

            verifier = UnifiedVerificationMaster()

            batch_results = await verifier._verify_with_courtlistener_lookup_batch(citations, case_names, dates)

            # Check which citations need CaseMine or Law.Resource.org fallback
            results = []
            additional_needed = []

            for i, citation in enumerate(citations):
                result = batch_results.get(citation)
                if result and result.verified:
                    results.append(result)
                else:
                    # Create unverified result for now
                    results.append(
                        VerificationResult(citation=citation, verified=False, error="CourtListener lookup failed")
                    )
                    additional_needed.append((i, citation, case_names[i], dates[i]))

            # Try CaseMine and Law.Resource.org for failed citations
            if additional_needed:
                logger.info(f"[FAST-VERIFY] Trying additional sources for {len(additional_needed)} failed citations")

                for idx, citation, case_name, date in additional_needed:
                    try:
                        # Try fast verification which includes Law.Resource.org for Federal citations
                        additional_result = await self.verify_citation_fast(citation, case_name, date)
                        if additional_result.verified or getattr(additional_result, "possible_match", False):
                            results[idx] = additional_result
                    except Exception as e:
                        logger.warning(f"[FAST-VERIFY] Additional sources failed for '{citation}': {e}")

            return results

        except Exception as e:
            logger.error(f"[FAST-VERIFY] Batch verification failed: {e}")
            # Fall back to individual verification
            results = []
            for i, citation in enumerate(citations):
                result = await self.verify_citation_fast(citation, case_names[i], dates[i])
                results.append(result)
            return results


# Singleton instance
fast_verification = FastVerificationConfig()
