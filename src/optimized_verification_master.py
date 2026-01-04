"""
Optimized Verification Master - Enhanced efficiency for citation verification.

This module improves upon UnifiedVerificationMaster with:
1. Parallel fallback verification
2. Smart source selection based on citation type
3. Result caching to avoid duplicate API calls
4. Early termination on successful verification
5. Adaptive timeout management
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib

from src.unified_verification_master import get_master_verifier, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationCache:
    """Simple in-memory cache for verification results."""

    cache: Dict[str, Tuple[VerificationResult, float]] = None
    ttl_seconds: int = 3600  # 1 hour cache

    def __post_init__(self):
        if self.cache is None:
            self.cache = {}

    def _get_key(self, citation: str, source: str) -> str:
        """Generate cache key for citation-source pair."""
        return f"{source}:{hashlib.md5(citation.lower().strip().encode('utf-8'), usedforsecurity=False).hexdigest()}"

    def get(self, citation: str, source: str) -> Optional[VerificationResult]:
        """Get cached result if valid."""
        key = self._get_key(citation, source)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.debug(f"Cache hit for {citation} from {source}")
                return result
            else:
                del self.cache[key]
        return None

    def set(self, citation: str, source: str, result: VerificationResult):
        """Cache verification result."""
        key = self._get_key(citation, source)
        self.cache[key] = (result, time.time())

    def clear(self):
        """Clear all cached results."""
        self.cache.clear()


class OptimizedVerificationMaster:
    """
    Optimized verification engine with enhanced efficiency.

    Key improvements:
    1. Parallel fallback verification (up to 3 sources simultaneously)
    2. Smart source selection based on citation patterns
    3. Result caching to avoid duplicate API calls
    4. Early termination on high-confidence matches
    5. Adaptive timeouts based on source reliability
    """

    def __init__(self):
        """Initialize the optimized verification engine."""
        self.base_verifier = get_master_verifier()
        self.cache = VerificationCache()

        # Source reliability scores (0-1, higher is better)
        self.source_reliability = {
            "courtlistener": 0.95,  # Most reliable
            "justia": 0.85,
            "openjurist": 0.80,
            "cornell_lii": 0.75,
            "google_scholar": 0.60,  # Often blocked
        }

        # Adaptive timeouts based on source reliability
        self.source_timeouts = {
            "courtlistener": 15.0,
            "justia": 12.0,
            "openjurist": 10.0,
            "cornell_lii": 8.0,
            "google_scholar": 20.0,  # Longer due to potential blocks
        }

        # Parallel verification settings
        self.max_parallel_sources = 3  # Don't overwhelm APIs
        self.early_confidence_threshold = 0.9  # Stop early if very confident

        logger.info("OptimizedVerificationMaster initialized with parallel verification")

    def _select_optimal_sources(self, citation: str) -> List[str]:
        """
        Select optimal verification sources based on citation patterns.

        This reduces unnecessary API calls by choosing sources most likely
        to have the citation based on its characteristics.
        """
        citation_lower = citation.lower()

        # Supreme Court citations - CourtListener is best
        if "u.s." in citation_lower or "s. ct." in citation_lower:
            return ["courtlistener", "justia", "openjurist"]

        # Federal appellate citations - CourtListener + Justia
        if "f." in citation_lower or "f.2d" in citation_lower or "f.3d" in citation_lower:
            return ["courtlistener", "justia", "cornell_lii"]

        # Federal district citations - Justia + Cornell
        if "f. supp." in citation_lower or "f. supp." in citation_lower:
            return ["justia", "cornell_lii", "openjurist"]

        # State court citations - Justia is usually best
        if any(state in citation_lower for state in ["cal.", "n.y.", "tex.", "fla.", "ill."]):
            return ["justia", "openjurist", "google_scholar"]

        # Historical citations - Try multiple sources
        if any(year in citation for year in ["18__", "19__"]):
            return ["courtlistener", "justia", "openjurist"]

        # Default selection - prioritize by reliability
        return sorted(self.source_reliability.keys(), key=lambda x: self.source_reliability[x], reverse=True)[
            : self.max_parallel_sources
        ]

    async def _verify_with_source(
        self,
        citation: str,
        source: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = None,
    ) -> Tuple[VerificationResult, str]:
        """
        Verify citation with a specific source.

        Returns tuple of (result, source_name)
        """
        # Check cache first
        cached_result = self.cache.get(citation, source)
        if cached_result:
            return cached_result, source

        # Use source-specific timeout
        if timeout is None:
            timeout = self.source_timeouts.get(source, 15.0)

        try:
            # Route to appropriate verification method
            if source == "courtlistener":
                result = await self.base_verifier._verify_with_courtlistener_lookup(
                    citation, extracted_case_name, extracted_date
                )
            elif source == "justia":
                result = await self.base_verifier._verify_with_justia(citation, extracted_case_name, extracted_date)
            elif source == "openjurist":
                result = await self.base_verifier._verify_with_openjurist(citation, extracted_case_name, extracted_date)
            elif source == "cornell_lii":
                result = await self.base_verifier._verify_with_cornell_lii(
                    citation, extracted_case_name, extracted_date
                )
            elif source == "google_scholar":
                result = await self.base_verifier._verify_with_google_scholar(
                    citation, extracted_case_name, extracted_date
                )
            else:
                # Fallback to base verifier
                result = await self.base_verifier.verify_citation(
                    citation, extracted_case_name, extracted_date, timeout
                )
                result.source = source

            # Cache the result
            if result:
                self.cache.set(citation, source, result)

            return result, source

        except Exception as e:
            logger.warning(f"Verification failed for {citation} with {source}: {str(e)}")
            # Return failed result
            failed_result = VerificationResult(
                citation=citation, verified=False, possible_match=False, source=source, error=str(e)
            )
            return failed_result, source

    async def verify_citation_optimized(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
        enable_parallel: bool = True,
    ) -> VerificationResult:
        """
        Optimized single citation verification.

        Strategy: Use CourtListener batch API for single citations too,
        then fallback to parallel sources if needed.
        """
        logger.info(f"🚀 Optimized verification: {citation}")

        # Try CourtListener first (most reliable)
        try:
            result = await self.base_verifier._verify_with_courtlistener_lookup(
                citation, extracted_case_name, extracted_date
            )
            if result.verified or result.possible_match:
                logger.info(f"   ✅ CourtListener success: {result.source}")
                return result
        except Exception as e:
            logger.warning(f"   CourtListener failed: {str(e)}")

        # If CourtListener failed and parallel is enabled, try parallel fallback
        if enable_parallel:
            logger.info(f"   🔄 Trying parallel fallback...")
            return await self._parallel_fallback_verification(citation, extracted_case_name, extracted_date, timeout)

        # Default fallback
        return VerificationResult(
            citation=citation,
            verified=False,
            possible_match=False,
            source="none",
            error="All verification methods failed",
        )

    async def _parallel_fallback_verification(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
    ) -> VerificationResult:
        """Parallel fallback verification when CourtListener fails."""
        # Select optimal sources (excluding CourtListener since we already tried)
        optimal_sources = self._select_optimal_sources(citation)
        fallback_sources = [s for s in optimal_sources if s != "courtlistener"]

        if not fallback_sources:
            return VerificationResult(
                citation=citation,
                verified=False,
                possible_match=False,
                source="none",
                error="No fallback sources available",
            )

        # Try fallback sources in parallel
        tasks = []
        for source in fallback_sources[:2]:  # Limit to 2 for fallback
            task = self._verify_with_source(citation, source, extracted_case_name, extracted_date, timeout / 2)
            tasks.append(task)

        # Wait for first successful result
        try:
            for coro in asyncio.as_completed(tasks, timeout=timeout):
                result, source = await coro
                logger.info(
                    f"   Fallback {source}: {'✅' if result.verified else '⚠️' if result.possible_match else '❌'}"
                )

                if result.verified or result.possible_match:
                    logger.info(f"   ✅ Using fallback result from {source}")
                    return result

            # No successful fallback
            return VerificationResult(
                citation=citation,
                verified=False,
                possible_match=False,
                source="none",
                error="All fallback sources failed",
            )

        except asyncio.TimeoutError:
            return VerificationResult(
                citation=citation,
                verified=False,
                possible_match=False,
                source="timeout",
                error="Fallback verification timeout",
            )

    async def verify_citations_batch_optimized(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None,
        batch_size: int = 50,  # Use CourtListener's optimal batch size
        timeout_per_citation: float = 10.0,
        progress_callback: Optional[callable] = None,
        enable_parallel: bool = True,
    ) -> List[VerificationResult]:
        """
        Optimized batch verification using CourtListener batch API first.

        Strategy:
        1. Use CourtListener batch API for all citations (most efficient)
        2. For failed citations, use parallel fallback verification
        3. Cache all results to avoid duplicate API calls
        """
        if not citations:
            return []

        logger.info(f"🚀 Optimized batch verification: {len(citations)} citations")

        # Prepare data
        if extracted_case_names is None:
            extracted_case_names = [None] * len(citations)
        if extracted_dates is None:
            extracted_dates = [None] * len(citations)

        # Step 1: Try CourtListener batch API first (most efficient)
        logger.info(f"   Step 1: Using CourtListener batch API...")
        courtlistener_results = await self._try_courtlistener_batch(
            citations, extracted_case_names, extracted_dates, batch_size, timeout_per_citation, progress_callback
        )

        # Step 2: Identify failed citations for fallback
        failed_indices = []
        for i, result in enumerate(courtlistener_results):
            if not result.verified and not result.possible_match:
                failed_indices.append(i)

        logger.info(f"   CourtListener verified: {len([r for r in courtlistener_results if r.verified])}")
        logger.info(f"   Failed citations for fallback: {len(failed_indices)}")

        # Step 3: Parallel fallback for failed citations
        if failed_indices and enable_parallel:
            logger.info(f"   Step 2: Parallel fallback for {len(failed_indices)} failed citations...")
            fallback_results = await self._parallel_fallback_batch(
                [citations[i] for i in failed_indices],
                [extracted_case_names[i] for i in failed_indices],
                [extracted_dates[i] for i in failed_indices],
                timeout_per_citation,
            )

            # Merge fallback results
            for i, failed_idx in enumerate(failed_indices):
                if i < len(fallback_results):
                    courtlistener_results[failed_idx] = fallback_results[i]

        # Step 4: Cache all results
        for i, result in enumerate(courtlistener_results):
            if result and result.source:
                self.cache.set(citations[i], result.source, result)

        logger.info(f"   ✅ Batch verification complete")
        return courtlistener_results

    async def _try_courtlistener_batch(
        self,
        citations: List[str],
        case_names: List[str],
        dates: List[str],
        batch_size: int,
        timeout_per_citation: float,
        progress_callback: Optional[callable],
    ) -> List[VerificationResult]:
        """Try CourtListener batch API for all citations."""
        try:
            # Use the actual CourtListener batch method that sends all citations in one request
            results = await self.base_verifier._verify_with_courtlistener_lookup_batch(citations, case_names, dates)

            # Count successful verifications
            verified_count = sum(1 for r in results if r.verified)
            possible_count = sum(1 for r in results if r.possible_match)

            logger.info(f"   CourtListener batch: {verified_count} verified, {possible_count} possible matches")
            return results

        except Exception as e:
            logger.error(f"   CourtListener batch failed: {str(e)}")
            # Return all failed results
            return [
                VerificationResult(
                    citation=citations[i],
                    verified=False,
                    possible_match=False,
                    source="error",
                    error=f"Batch API failed: {str(e)}",
                )
                for i in range(len(citations))
            ]

    async def _parallel_fallback_batch(
        self, citations: List[str], case_names: List[str], dates: List[str], timeout_per_citation: float
    ) -> List[VerificationResult]:
        """Parallel fallback verification for failed citations."""
        if not citations:
            return []

        logger.info(f"   Running parallel fallback for {len(citations)} citations...")

        # Create tasks for parallel verification
        tasks = []
        for i, citation in enumerate(citations):
            task = self._parallel_fallback_verification(citation, case_names[i], dates[i], timeout_per_citation)
            tasks.append(task)

        # Wait for all tasks to complete
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to failed results
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append(
                        VerificationResult(
                            citation=citations[i],
                            verified=False,
                            possible_match=False,
                            source="error",
                            error=str(result),
                        )
                    )
                else:
                    final_results.append(result)

            # Count successes
            verified_count = sum(1 for r in final_results if r.verified)
            possible_count = sum(1 for r in final_results if r.possible_match)

            logger.info(f"   Parallel fallback: {verified_count} verified, {possible_count} possible matches")
            return final_results

        except Exception as e:
            logger.error(f"   Parallel fallback failed: {str(e)}")
            return [
                VerificationResult(
                    citation=citations[i],
                    verified=False,
                    possible_match=False,
                    source="error",
                    error=f"Fallback failed: {str(e)}",
                )
                for i in range(len(citations))
            ]

    def verify_citation_sync_optimized(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
        enable_parallel: bool = True,
    ) -> VerificationResult:
        """
        Synchronous wrapper for optimized verification.
        """
        from concurrent.futures import ThreadPoolExecutor

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.verify_citation_optimized(
                        citation, extracted_case_name, extracted_date, timeout, enable_parallel
                    )
                )
            finally:
                loop.close()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async)
            return future.result(timeout=timeout + 10)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "cache_size": len(self.cache.cache),
            "ttl_seconds": self.cache.ttl_seconds,
            "source_reliability": self.source_reliability,
            "source_timeouts": self.source_timeouts,
        }

    def clear_cache(self):
        """Clear verification cache."""
        self.cache.clear()
        logger.info("Verification cache cleared")


# Global instance for reuse
_optimized_verifier = None


def get_optimized_verifier() -> OptimizedVerificationMaster:
    """Get or create the global optimized verifier instance."""
    global _optimized_verifier
    if _optimized_verifier is None:
        _optimized_verifier = OptimizedVerificationMaster()
    return _optimized_verifier


# Convenience functions for easy migration
async def verify_citation_optimized(citation: str, **kwargs) -> Dict[str, Any]:
    """
    Optimized citation verification function.

    This is a drop-in replacement for verify_citation_unified_master
    with enhanced performance.
    """
    verifier = get_optimized_verifier()
    result = await verifier.verify_citation_optimized(citation, **kwargs)

    return {
        "citation": result.citation,
        "verified": result.verified,
        "possible_match": result.possible_match,
        "canonical_name": result.canonical_name,
        "canonical_date": result.canonical_date,
        "canonical_url": result.canonical_url,
        "url": result.url,
        "source": result.source,
        "confidence": getattr(result, "confidence", 0.0),
        "method": "optimized_parallel",
        "raw_data": getattr(result, "raw_data", {}),
        "warnings": getattr(result, "warnings", []),
        "error": result.error,
    }


def verify_citation_sync_optimized(citation: str, **kwargs) -> Dict[str, Any]:
    """Synchronous version of optimized verification."""
    verifier = get_optimized_verifier()
    result = verifier.verify_citation_sync_optimized(citation, **kwargs)

    return {
        "citation": result.citation,
        "verified": result.verified,
        "possible_match": result.possible_match,
        "canonical_name": result.canonical_name,
        "canonical_date": result.canonical_date,
        "canonical_url": result.canonical_url,
        "url": result.url,
        "source": result.source,
        "confidence": getattr(result, "confidence", 0.0),
        "method": "optimized_sync",
        "raw_data": getattr(result, "raw_data", {}),
        "warnings": getattr(result, "warnings", []),
        "error": result.error,
    }
