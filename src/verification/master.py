"""
Unified Verification Master (Modular)
======================================

Main verification class using modular components.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from .sources import CourtListenerVerifier
from .fallback import FallbackVerifier, verify_with_fallback_sources
from .batch import BatchVerifier
from .cl_search_fallback import cl_search_fallback
from .utils import (
    calculate_case_name_overlap,
    validate_year_match,
    is_citation_likely_valid,
)
from src.config import COURTLISTENER_API_KEY


class _SimpleCache:
    """Simple in-memory verification cache."""
    def __init__(self):
        self._data = {}
    def get(self, key):
        return self._data.get(key)
    def set(self, key, value):
        self._data[key] = value

_verification_cache = _SimpleCache()

def get_verification_cache():
    return _verification_cache

logger = logging.getLogger(__name__)


class VerificationSource(Enum):
    """Enumeration of verification sources."""
    COURTLISTENER_LOOKUP = "courtlistener_lookup"
    COURTLISTENER_SEARCH = "courtlistener_search"
    FALLBACK = "fallback"


@dataclass
class VerificationResult:
    """Standardized verification result."""
    citation: str
    verified: bool
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    source: str = ""
    confidence: float = 0.0
    method: str = ""
    error: Optional[str] = None
    possible_match: bool = False
    validation_warning: Optional[str] = None
    raw_data: Optional[Dict] = None


class UnifiedVerificationMaster:
    """
    THE SINGLE, AUTHORITATIVE verification implementation (MODULAR VERSION).
    
    Uses modular components:
    - sources: Individual source verifiers
    - fallback: Fallback verification
    - batch: Batch verification
    - utils: Utility functions
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        session=None,
        fast_verification: bool = True
    ):
        """Initialize the master verification engine."""
        self.api_key = api_key or COURTLISTENER_API_KEY
        # CRITICAL FIX: Create a requests.Session when none is provided
        # Without this, all verifiers get session=None and every HTTP call
        # fails with AttributeError: 'NoneType' object has no attribute 'post'
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
            logger.info("[VERIFICATION-MASTER] Created default requests.Session (none was provided)")
        self.session = session
        self.fast_verification = fast_verification
        
        # Initialize components
        self.courtlistener = CourtListenerVerifier(self.api_key, self.session)
        self.fallback = FallbackVerifier(self.session, fast_verification)
        self.batch_verifier = BatchVerifier(self.api_key, self.session)
        
        logger.info(f"UnifiedVerificationMaster initialized (modular version)")
    
    async def verify_citation(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
        enable_fallback: bool = True
    ) -> VerificationResult:
        """
        Verify a single citation.
        
        Strategy:
        1. Check cache
        2. CourtListener lookup
        3. CourtListener search (if lookup fails)
        4. Fallback sources (if enabled)
        
        Returns:
            VerificationResult
        """
        start_time = time.time()
        
        # Check cache first
        cache = get_verification_cache()
        cached_result = cache.get(citation)
        if cached_result:
            logger.info(f"[CACHE] Using cached verification for '{citation}'")
            return VerificationResult(
                citation=citation,
                verified=True,
                canonical_name=cached_result.get("canonical_name"),
                canonical_date=cached_result.get("canonical_date"),
                canonical_url=cached_result.get("canonical_url"),
                source=cached_result.get("source"),
                confidence=cached_result.get("confidence", 1.0),
                method="cache",
            )
        
        # Validate citation format
        if not is_citation_likely_valid(citation):
            return VerificationResult(
                citation=citation,
                verified=False,
                error="Invalid citation format",
                method="validation",
            )
        
        # Step 1: CourtListener lookup
        logger.debug(f"[VERIFY] Trying CourtListener lookup for '{citation}'")
        result = await self.courtlistener.verify(citation, timeout=timeout)
        
        if result.get("verified"):
            # Validate year match
            canonical_date = result.get("canonical_date")
            if extracted_date and canonical_date:
                is_valid, year_diff = validate_year_match(
                    extracted_date, canonical_date, tolerance=1
                )
                if not is_valid:
                    logger.warning(
                        f"[YEAR-MISMATCH] {citation}: "
                        f"extracted={extracted_date}, canonical={canonical_date}"
                    )
                    return VerificationResult(
                        citation=citation,
                        verified=False,
                        canonical_name=result.get("canonical_name"),
                        canonical_date=canonical_date,
                        canonical_url=result.get("canonical_url"),
                        error=f"Year mismatch: {year_diff} years",
                        method="courtlistener_lookup",
                    )
            
            # Cache successful verification
            cache.set(citation, result)
            
            return VerificationResult(
                citation=citation,
                verified=True,
                canonical_name=result.get("canonical_name"),
                canonical_date=canonical_date,
                canonical_url=result.get("canonical_url"),
                source="CourtListener",
                confidence=result.get("confidence", 0.95),
                method="courtlistener_lookup",
            )
        
        # Step 2: CourtListener search API fallback (by case name)
        if extracted_case_name and time.time() - start_time < timeout:
            logger.debug(f"[VERIFY] Trying CL search fallback for '{citation}'")
            search_result = await cl_search_fallback(
                self.session, self.api_key, citation,
                extracted_case_name, extracted_date,
                timeout - (time.time() - start_time)
            )
            if search_result.get("verified"):
                cache.set(citation, search_result)
                return VerificationResult(
                    citation=citation,
                    verified=True,
                    canonical_name=search_result.get("canonical_name"),
                    canonical_date=search_result.get("canonical_date"),
                    canonical_url=search_result.get("canonical_url"),
                    source=search_result.get("source", "CourtListener-Search"),
                    confidence=search_result.get("confidence", 0.85),
                    method="courtlistener_search",
                )

        # Step 3: Fallback verification (Justia, Cornell LII, OpenJurist)
        if enable_fallback and time.time() - start_time < timeout:
            logger.debug(f"[VERIFY] Trying fallback sources for '{citation}'")
            
            fallback_result = await self.fallback.verify(
                citation,
                extracted_case_name,
                extracted_date,
                timeout - (time.time() - start_time)
            )
            
            if fallback_result.get("verified"):
                return VerificationResult(
                    citation=citation,
                    verified=True,
                    canonical_name=fallback_result.get("canonical_name"),
                    canonical_date=fallback_result.get("canonical_date"),
                    canonical_url=fallback_result.get("canonical_url"),
                    source=fallback_result.get("source"),
                    confidence=fallback_result.get("confidence", 0.7),
                    method=fallback_result.get("method", "fallback"),
                )
        
        # All methods failed
        return VerificationResult(
            citation=citation,
            verified=False,
            error="All verification methods failed",
            method="all_failed",
        )
    
    async def verify_citations_batch(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None,
        batch_size: int = 250,
        timeout_per_citation: float = 10.0,
        progress_callback: Optional[Callable[[int, str, str], None]] = None,
        enable_fallback: bool = True,
        max_fallback_citations: int = 100
    ) -> List[VerificationResult]:
        """
        Batch verify citations.
        
        Args:
            citations: List of citations
            extracted_case_names: Optional case names
            extracted_dates: Optional dates
            batch_size: Citations per batch
            timeout_per_citation: Timeout per citation
            progress_callback: Progress callback
            enable_fallback: Enable fallback verification
            
        Returns:
            List of VerificationResult
        """
        logger.info(f"[BATCH] Starting batch verification of {len(citations)} citations")
        
        # Use batch verifier for CourtListener
        batch_results = await self.batch_verifier.verify_batch(
            citations,
            extracted_case_names,
            extracted_dates,
            batch_size,
            timeout_per_citation * batch_size,
            progress_callback
        )
        
        # Convert to VerificationResult and run fallback for unverified
        results = []
        total = len(batch_results)
        unverified_count = 0
        fallback_success_count = 0
        fallback_attempted = 0
        for result_idx, result in enumerate(batch_results):
            # Report progress for each citation processed
            if progress_callback:
                try:
                    progress_callback(
                        result_idx, "Verifying",
                        f"Verifying citations... ({result_idx}/{total} citations)"
                    )
                except Exception:
                    pass
            verified = result.get("verified", False)
            # Also try fallback when CL returned a name but no URL
            needs_url = verified and result.get("canonical_name") and not result.get("canonical_url")
            
            if (not verified or needs_url) and enable_fallback and fallback_attempted < max_fallback_citations:
                unverified_count += 1
                fallback_attempted += 1
                # Aggressive memory cleanup every 5 fallback attempts
                # to prevent HTTP response data from accumulating (OOM fix)
                if fallback_attempted % 5 == 0:
                    try:
                        import gc as _gc_fb
                        _gc_fb.collect()
                        try:
                            import ctypes
                            _libc_fb = ctypes.CDLL("libc.so.6")
                            _libc_fb.malloc_trim(0)
                        except Exception:
                            pass
                    except Exception:
                        pass
                if fallback_attempted % 5 == 1:
                    try:
                        import psutil, os
                        _fb_mem = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
                        logger.warning(f"[BATCH-FALLBACK-MEM] After {fallback_attempted} fallbacks: {_fb_mem}MB")
                    except Exception:
                        pass
                # Try fallback for unverified citations
                try:
                    idx = citations.index(result["citation"])
                except ValueError:
                    logger.warning(f"[BATCH-FALLBACK] Citation not found in list: '{result['citation']}'")
                    idx = None
                case_name = extracted_case_names[idx] if (extracted_case_names and idx is not None) else None
                date = extracted_dates[idx] if (extracted_dates and idx is not None) else None

                cl_canonical_name = result.get("canonical_name") if needs_url else None
                logger.warning(
                    f"[BATCH-FALLBACK] {'Needs URL' if needs_url else 'Unverified'}: '{result['citation'][:60]}' "
                    f"case_name='{case_name}' cl_canonical='{cl_canonical_name}' - trying fallbacks..."
                )

                # Step A: CL search API fallback (by case name)
                if case_name and case_name != "N/A":
                    search_result = await cl_search_fallback(
                        self.session, self.api_key, result["citation"],
                        case_name, date, timeout_per_citation
                    )
                    if search_result.get("verified"):
                        result.update(search_result)
                        # Preserve CL canonical name if it was better
                        if cl_canonical_name and not search_result.get("canonical_name"):
                            result["canonical_name"] = cl_canonical_name
                        verified = True
                        # If CL search found the case but still no URL, try web fallback for URL
                        needs_url = bool(not result.get("canonical_url"))
                        if not needs_url:
                            fallback_success_count += 1
                        cl_canonical_name = cl_canonical_name or result.get("canonical_name")
                        logger.warning(
                            f"[BATCH-FALLBACK] CL search succeeded: '{result['citation'][:60]}' -> "
                            f"'{search_result.get('canonical_name')}' url={'yes' if result.get('canonical_url') else 'MISSING'}"
                        )

                # Step B: Web fallback (Google Scholar, Justia, Cornell LII, OpenJurist)
                if not verified or needs_url:
                    fallback_result = await self.fallback.verify(
                        result["citation"],
                        case_name,
                        date,
                        min(timeout_per_citation, 5.0)
                    )
                    if fallback_result.get("verified"):
                        # Preserve CL canonical name when fallback only adds URL
                        if cl_canonical_name:
                            fallback_result.setdefault("canonical_name", cl_canonical_name)
                        result.update(fallback_result)
                        verified = True
                        needs_url = False
                        fallback_success_count += 1
                        logger.warning(
                            f"[BATCH-FALLBACK] Web fallback succeeded: '{result['citation'][:60]}' -> "
                            f"'{fallback_result.get('canonical_name')}' via {fallback_result.get('source')}"
                        )
                    else:
                        logger.warning(
                            f"[BATCH-FALLBACK] All fallbacks failed for '{result['citation'][:60]}': "
                            f"{fallback_result.get('error', 'unknown')}"
                        )

            results.append(VerificationResult(
                citation=result["citation"],
                verified=verified,
                canonical_name=result.get("canonical_name"),
                canonical_date=result.get("canonical_date"),
                canonical_url=result.get("canonical_url"),
                source=result.get("source", "unknown"),
                confidence=result.get("confidence", 0.0),
                method=result.get("method", "unknown"),
                error=result.get("error"),
            ))
        
        # Final progress update
        if progress_callback:
            try:
                progress_callback(total, "Verifying", f"Verification complete ({total}/{total} citations)")
            except Exception:
                pass

        if unverified_count > 0:
            logger.info(
                f"[BATCH-FALLBACK] Summary: {unverified_count} unverified, "
                f"{fallback_success_count} recovered by fallback"
                f"{f', {total - fallback_attempted - (total - unverified_count)} skipped (max_fallback={max_fallback_citations})' if fallback_attempted >= max_fallback_citations else ''}"
            )

        # Aggressive memory cleanup after all verification
        try:
            import gc
            gc.collect()
            try:
                import ctypes
                _libc_final = ctypes.CDLL("libc.so.6")
                _libc_final.malloc_trim(0)
            except Exception:
                pass
            # Close the session to release connection pool memory
            try:
                if self.session:
                    self.session.close()
                    logger.info("[BATCH-FALLBACK] Closed requests.Session to release connection pool")
            except Exception:
                pass
            gc.collect()
            try:
                _libc_final.malloc_trim(0)
            except Exception:
                pass
        except Exception:
            pass
        # Log final memory
        try:
            import psutil, os
            _final_mem = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
            logger.warning(f"[BATCH-FALLBACK-MEM] Final after gc+malloc_trim+session.close: {_final_mem}MB (processed {total} citations, {fallback_attempted} fallbacks)")
        except Exception:
            pass

        return results
    
    def verify_citation_sync(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 60.0,
        enable_fallback: bool = True
    ) -> VerificationResult:
        """Synchronous wrapper for verify_citation."""
        from concurrent.futures import ThreadPoolExecutor
        
        def run_in_new_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.verify_citation(
                        citation,
                        extracted_case_name,
                        extracted_date,
                        timeout,
                        enable_fallback
                    )
                )
                return result
            finally:
                loop.close()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_new_loop)
            return future.result(timeout=timeout + 5.0)
