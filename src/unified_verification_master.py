"""
Unified Verification Master
===========================

This module provides THE SINGLE, AUTHORITATIVE verification implementation
that consolidates the best features from all 80+ duplicate verification functions.

ALL OTHER VERIFICATION FUNCTIONS SHOULD BE DEPRECATED AND REPLACED WITH THIS ONE.

Key Features Consolidated:
- CourtListener citation-lookup API v4 (primary)
- CourtListener search API (fallback)
- Enhanced fallback verification (10+ sources)
- Batch processing with rate limiting
- Async/sync variants
- Comprehensive error handling
- Caching and performance optimization
- Strict validation criteria
- Multiple citation format handling
"""

import asyncio
import logging
import time
import requests
import os
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote

# CRITICAL: Import from config to ensure .env files are loaded
from src.config import COURTLISTENER_API_KEY, get_bool_config_value

logger = logging.getLogger(__name__)

class VerificationSource(Enum):
    """Enumeration of verification sources in priority order."""
    COURTLISTENER_LOOKUP = "courtlistener_lookup"
    COURTLISTENER_SEARCH = "courtlistener_search"
    JUSTIA = "justia"
    GOOGLE_SCHOLAR = "google_scholar"
    FINDLAW = "findlaw"
    LEAGLE = "leagle"
    CASEMINE = "casemine"
    VLEX = "vlex"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    SCRAPINGBEE = "scrapingbee"

@dataclass
class VerificationResult:
    """Standardized result from verification."""
    citation: str
    verified: bool = False
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 0.0
    method: str = "none"
    raw_data: Optional[Dict] = None
    validation_warning: Optional[str] = None  # Warning if canonical/extracted names don't match
    warnings: List[str] = None
    error: Optional[str] = None

class UnifiedVerificationMaster:
    """
    THE SINGLE, AUTHORITATIVE verification implementation.
    
    This class consolidates the best features from:
    - enhanced_fallback_verifier.py (20+ functions)
    - enhanced_courtlistener_verification.py (15+ functions)
    - services/citation_verifier.py (8+ functions)
    - unified_citation_processor_v2.py (10+ functions)
    - async_verification_worker.py (8+ functions)
    - All other duplicate verification functions
    
    ALL verification should go through this class.
    """
    
    def __init__(self):
        """Initialize the master verification engine."""
        # CRITICAL FIX: Use config import instead of os.getenv to ensure .env is loaded
        self.api_key = COURTLISTENER_API_KEY
        self.session = requests.Session()
        self._setup_session()
        self._setup_rate_limits()
        
        # CRITICAL FIX: Add retry tracking to prevent infinite loops on rate limits
        self.retry_tracker = {}  # citation -> retry count
        self.MAX_VERIFICATION_RETRIES = 3  # Max attempts per citation
        
        if self.api_key:
            logger.info(f"UnifiedVerificationMaster initialized - API key loaded (length: {len(self.api_key)})")
        else:
            logger.error("🔥 UnifiedVerificationMaster initialized - NO API KEY FOUND!")
            logger.error("   CourtListener verification will not work without COURTLISTENER_API_KEY")
            logger.error("   Check .env, .env.production, or config.env files")
        logger.info("All duplicate verifiers deprecated")
        logger.info(f"Max verification retries set to: {self.MAX_VERIFICATION_RETRIES}")
    
    def _setup_session(self):
        """Setup HTTP session with optimal settings."""
        self.session.headers.update({
            'User-Agent': 'CaseStrainer/1.0 (https://github.com/casestrainer/casestrainer)',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        if self.api_key:
            self.session.headers['Authorization'] = f'Token {self.api_key}'
    
    def _setup_rate_limits(self):
        """Setup rate limiting for different sources."""
        self.rate_limits = {
            VerificationSource.COURTLISTENER_LOOKUP: {'calls_per_minute': 180, 'last_call': 0},
            VerificationSource.COURTLISTENER_SEARCH: {'calls_per_minute': 180, 'last_call': 0},
            VerificationSource.GOOGLE_SCHOLAR: {'calls_per_minute': 30, 'last_call': 0},
            VerificationSource.BING: {'calls_per_minute': 60, 'last_call': 0},
            # Add other sources as needed
        }
    
    async def verify_citation(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
        enable_fallback: bool = True
    ) -> VerificationResult:
        """
        THE MASTER VERIFICATION FUNCTION
        
        This is THE ONLY function that should be used for citation verification.
        It consolidates all the best features from duplicate functions.
        
        Args:
            citation: Citation text to verify
            extracted_case_name: Optional extracted case name for validation
            extracted_date: Optional extracted date for validation
            timeout: Maximum time to spend on verification
            enable_fallback: Whether to use fallback sources if primary fails
            
        Returns:
            VerificationResult with comprehensive verification data
        """
        # FIX #62: Diagnostic logging to verify async method is reached
        logger.error(f"🔥 [FIX #62] ASYNC verify_citation REACHED for '{citation}'")
        logger.error(f"   📌 Extracted: '{extracted_case_name}' ({extracted_date})")
        logger.error(f"   🚀 Starting verification strategies...")
        
        # CRITICAL FIX: Check retry limit to prevent infinite loops
        retry_count = self.retry_tracker.get(citation, 0)
        if retry_count >= self.MAX_VERIFICATION_RETRIES:
            logger.warning(f"⚠️ RETRY_LIMIT: Skipping '{citation}' - max retries ({self.MAX_VERIFICATION_RETRIES}) reached")
            return VerificationResult(
                citation=citation,
                verified=False,
                error=f"Max verification retries ({self.MAX_VERIFICATION_RETRIES}) exceeded - likely rate limited",
                warnings=["This citation was skipped to prevent infinite retry loops"]
            )
        
        start_time = time.time()
        
        logger.info(f"🎯 MASTER_VERIFY: Starting verification for '{citation}' (attempt {retry_count + 1}/{self.MAX_VERIFICATION_RETRIES})")
        
        # Strategy 1: CourtListener APIs (citation-lookup + search)
        # OPTIMIZATION: Skip both if rate limited, since they're the same service
        is_rate_limited = False
        
        # Try citation-lookup first
        logger.error(f"🔥 [VERIFY-STRATEGY-1A] Calling CourtListener citation-lookup for '{citation}'")
        result = await self._verify_with_courtlistener_lookup(citation, extracted_case_name, extracted_date)
        logger.error(f"🔥 [VERIFY-STRATEGY-1A] Result: verified={result.verified}, error={result.error}")
        
        # Check if we hit rate limit
        is_rate_limited = result.error and "rate limit" in result.error.lower()
        
        if result.verified:
            # Clear retry counter on success
            if citation in self.retry_tracker:
                del self.retry_tracker[citation]
            logger.info(f"✅ MASTER_VERIFY: CourtListener lookup succeeded for '{citation}'")
            return result
        elif is_rate_limited:
            # OPTIMIZATION: Skip search API - it will also be rate limited
            logger.warning(f"⚠️ MASTER_VERIFY: CourtListener rate limited - skipping search API, going straight to fallback sources")
            # Continue to fallback verification below
        else:
            # Not found but not rate limited - try search API as fallback within CourtListener
            logger.error(f"🔥 [VERIFY-STRATEGY-1A] FAILED - trying search API")
            
            if time.time() - start_time < timeout:
                logger.error(f"🔥 [VERIFY-STRATEGY-1B] Calling CourtListener search API for '{citation}'")
                result = await self._verify_with_courtlistener_search(citation, extracted_case_name, extracted_date)
                logger.error(f"🔥 [VERIFY-STRATEGY-1B] Result: verified={result.verified}, error={result.error}")
                
                # Check for rate limit
                is_rate_limited = result.error and "rate limit" in result.error.lower()
                
                if result.verified:
                    logger.info(f"✅ MASTER_VERIFY: CourtListener search succeeded for '{citation}'")
                    return result
                elif is_rate_limited:
                    logger.warning(f"⚠️ MASTER_VERIFY: CourtListener search also rate limited")
                    # Continue to fallback
        
        # Strategy 2: Enhanced fallback verification (if enabled)
        # Call fallback even if CourtListener is rate limited (fallback has 9+ other sources)
        if enable_fallback and time.time() - start_time < timeout:
            result = await self._verify_with_enhanced_fallback(citation, extracted_case_name, extracted_date, timeout - (time.time() - start_time))
            if result.verified:
                logger.info(f"✅ MASTER_VERIFY: Fallback verification succeeded for '{citation}'")
                return result
        
        # No verification succeeded - increment retry counter
        self.retry_tracker[citation] = retry_count + 1
        logger.warning(f"⚠️ MASTER_VERIFY: All verification strategies failed for '{citation}' (retry {self.retry_tracker[citation]}/{self.MAX_VERIFICATION_RETRIES})")
        return VerificationResult(
            citation=citation,
            verified=False,
            error="All verification strategies failed",
            warnings=["No sources could verify this citation"]
        )
    
    def verify_citation_sync(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0,
        enable_fallback: bool = True
    ) -> VerificationResult:
        """
        Synchronous wrapper for the master verification function.
        
        This provides backward compatibility for synchronous callers.
        FIXED: Now works correctly in RQ workers and other async contexts.
        """
        # FIX #62: Diagnostic logging to verify this method is called
        logger.error(f"🔥 [FIX #62] verify_citation_sync CALLED for '{citation}'")
        logger.error(f"   📌 Extracted: '{extracted_case_name}' ({extracted_date})")
        logger.error(f"   ⏱️  Timeout: {timeout}s, Fallback: {enable_fallback}")
        
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        def run_in_new_loop():
            """Run verification in a new event loop in a separate thread"""
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.verify_citation(citation, extracted_case_name, extracted_date, timeout, enable_fallback)
                )
                return result
            finally:
                loop.close()
        
        # Run in a thread pool to avoid event loop conflicts
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_new_loop)
            return future.result(timeout=timeout + 5.0)  # Add 5s buffer to timeout
    
    async def verify_citations_batch(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None,
        batch_size: int = 50,
        timeout_per_citation: float = 10.0
    ) -> List[VerificationResult]:
        """
        Batch verification with optimal rate limiting and performance.
        
        Uses CourtListener's batch citation-lookup API which accepts multiple
        citations in a single request, dramatically improving performance.
        
        Args:
            citations: List of citations to verify
            extracted_case_names: Optional list of extracted case names
            extracted_dates: Optional list of extracted dates
            batch_size: Number of citations to process in each API call (default 50)
            timeout_per_citation: Maximum time per citation
            
        Returns:
            List of VerificationResult objects
        """
        logger.info(f"🎯 MASTER_BATCH_VERIFY: Starting batch verification of {len(citations)} citations")
        
        # Prepare data
        case_names = extracted_case_names or [None] * len(citations)
        dates = extracted_dates or [None] * len(citations)
        
        # Process in batches using the batch API
        results = []
        batches = [citations[i:i + batch_size] for i in range(0, len(citations), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} citations)")
            
            # Get case names and dates for this batch
            start_idx = batch_idx * batch_size
            end_idx = start_idx + len(batch)
            batch_case_names = case_names[start_idx:end_idx]
            batch_dates = dates[start_idx:end_idx]
            
            # Use batch API - much more efficient than individual requests
            batch_results = await self._verify_with_courtlistener_lookup_batch(
                batch,
                batch_case_names,
                batch_dates
            )
            
            results.extend(batch_results)
            
            # Rate limiting between batches
            if batch_idx < len(batches) - 1:  # Don't sleep after last batch
                await asyncio.sleep(1.0)  # 1 second between batches
        
        verified_count = sum(1 for r in results if r.verified)
        unverified_count = len(results) - verified_count
        logger.info(f"✅ MASTER_BATCH_VERIFY: Completed {len(results)} verifications ({verified_count} verified, {(verified_count/len(results)*100):.1f}%)")
        
        # CRITICAL: Run fallback verification for unverified citations
        if unverified_count > 0:
            logger.info(f"🔄 FALLBACK: Starting fallback verification for {unverified_count} unverified citations")
            
            for i, result in enumerate(results):
                if not result.verified:
                    citation = citations[i]
                    extracted_name = case_names[i] if i < len(case_names) else None
                    extracted_date = dates[i] if i < len(dates) else None
                    
                    logger.info(f"🔍 FALLBACK: Attempting fallback for '{citation}'")
                    
                    try:
                        fallback_result = await self._verify_with_enhanced_fallback(
                            citation,
                            extracted_name,
                            extracted_date,
                            remaining_timeout=10.0  # 10 seconds per fallback attempt
                        )
                        
                        if fallback_result.verified:
                            logger.info(f"✅ FALLBACK SUCCESS: Verified '{citation}' via {fallback_result.source}")
                            results[i] = fallback_result
                        else:
                            logger.info(f"⚠️ FALLBACK FAILED: Could not verify '{citation}'")
                    except Exception as e:
                        logger.error(f"❌ FALLBACK ERROR for '{citation}': {e}")
            
            # Log final stats
            final_verified_count = sum(1 for r in results if r.verified)
            fallback_verified = final_verified_count - verified_count
            logger.info(f"🎯 FALLBACK COMPLETE: {fallback_verified} additional citations verified via fallback ({final_verified_count}/{len(results)} total)")
        
        return results
    
    async def _verify_with_courtlistener_lookup_batch(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None
    ) -> List[VerificationResult]:
        """
        Batch verify using CourtListener citation-lookup API v4.
        
        The API supports passing multiple citations in the text field separated by spaces.
        This is much more efficient than individual requests.
        """
        if not self.api_key:
            return [VerificationResult(citation=c, error="No CourtListener API key") for c in citations]
        
        # Rate limiting
        await self._enforce_rate_limit(VerificationSource.COURTLISTENER_LOOKUP)
        
        try:
            # CRITICAL: Normalize citations for API compatibility
            # 1. Remove newlines/tabs (API fails on "161 U.S.\n519")
            # 2. Normalize dash-separated format (e.g., "123-Ohio-456" → "123 Ohio 456")
            from src.citation_patterns import normalize_dashed_citation
            import re
            
            normalized_citations = []
            for cit in citations:
                # Remove newlines, tabs, and collapse whitespace
                clean_cit = re.sub(r'[\n\r\t]+', ' ', cit)  # Replace newlines/tabs with space
                clean_cit = re.sub(r'\s+', ' ', clean_cit)  # Collapse multiple spaces
                clean_cit = clean_cit.strip()  # Trim edges
                # Apply dash normalization
                clean_cit = normalize_dashed_citation(clean_cit)
                normalized_citations.append(clean_cit)
            
            # BATCH OPTIMIZATION: Pass all citations in one request
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            # Join normalized citations with spaces - API will parse all of them
            combined_text = " ".join(normalized_citations)
            payload = {"text": combined_text}
            
            logger.info(f" Normalized {len(citations)} citations for batch verification")
            if citations != normalized_citations:
                logger.info(f"   Dash-separated citations normalized")
            
            # DEBUG: Log what we're sending
            logger.error(f"[BATCH-API-DEBUG] Sending {len(normalized_citations)} citations")
            logger.error(f"[BATCH-API-DEBUG] First 3: {normalized_citations[:3]}")
            logger.error(f"[BATCH-API-DEBUG] API Key set: {bool(self.api_key)}")
            logger.error(f"[BATCH-API-DEBUG] Session has Auth header: {'Authorization' in self.session.headers}")
            if 'Authorization' in self.session.headers:
                auth_val = self.session.headers['Authorization']
                logger.error(f"[BATCH-API-DEBUG] Auth header: {auth_val[:20]}...")
            
            try:
                response = self.session.post(url, json=payload, timeout=30)
                logger.error(f"[BATCH-API-DEBUG] Response status: {response.status_code}")
                
                # Handle 429 rate limit - fall back to enhanced fallback verifier
                if response.status_code == 429:
                    logger.warning(f"⚠️  CourtListener rate limited (429) - falling back to enhanced verifier for {len(citations)} citations")
                    from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
                    fallback = EnhancedFallbackVerifier()
                    fallback_results = []
                    for i, citation in enumerate(citations):
                        extracted_name = extracted_case_names[i] if extracted_case_names and i < len(extracted_case_names) else None
                        extracted_date = extracted_dates[i] if extracted_dates and i < len(extracted_dates) else None
                        fallback_result = await fallback.verify_citation_async(
                            citation, 
                            extracted_case_name=extracted_name,
                            extracted_date=extracted_date
                        )
                        fallback_results.append(fallback_result)
                    logger.info(f"✅ Fallback verification completed for {len(fallback_results)} citations")
                    return fallback_results
                
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Check if it's a 429 that wasn't caught above
                if hasattr(e, 'response') and e.response.status_code == 429:
                    logger.warning(f"⚠️  CourtListener rate limited (429) - falling back to enhanced verifier")
                    from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
                    fallback = EnhancedFallbackVerifier()
                    fallback_results = []
                    for i, citation in enumerate(citations):
                        extracted_name = extracted_case_names[i] if extracted_case_names and i < len(extracted_case_names) else None
                        extracted_date = extracted_dates[i] if extracted_dates and i < len(extracted_dates) else None
                        fallback_result = await fallback.verify_citation_async(
                            citation,
                            extracted_case_name=extracted_name,
                            extracted_date=extracted_date
                        )
                        fallback_results.append(fallback_result)
                    return fallback_results
                
                logger.error(f"[BATCH-API-DEBUG] HTTP Error: {e}")
                logger.error(f"[BATCH-API-DEBUG] Response text: {response.text[:200]}")
                raise
            data = response.json()
            
            # DEBUG: Log what we got back
            if isinstance(data, list):
                returned_citations = [item.get('citation') for item in data if isinstance(item, dict)]
                logger.error(f"[BATCH-API-DEBUG] Received {len(data)} results")
                logger.error(f"[BATCH-API-DEBUG] First 3 returned: {returned_citations[:3]}")
            
            # CRITICAL FIX #9: The API returns an ARRAY of citation results, not a dict with 'clusters'
            # Each item in the array has: {citation, status, error_message, clusters: [...]}
            # We need to match each citation to its corresponding result in the array
            if not isinstance(data, list):
                logger.error(f" UNEXPECTED API RESPONSE FORMAT: Expected list, got {type(data)}")
                logger.error(f"❌ UNEXPECTED API RESPONSE FORMAT: Expected list, got {type(data)}")
                return [VerificationResult(citation=c, error="Unexpected API response format") for c in citations]
            
            # Map each citation to its result from the API
            results = []
            for i, citation in enumerate(citations):
                extracted_name = extracted_case_names[i] if extracted_case_names and i < len(extracted_case_names) else None
                extracted_date = extracted_dates[i] if extracted_dates and i < len(extracted_dates) else None
                
                # CRITICAL FIX: Match using NORMALIZED citations, not original
                # We sent normalized_citations to the API, so we need to match against those
                normalized_citation = normalized_citations[i]
                
                # Find the corresponding result for this citation in the API response
                citation_result = None
                for result_item in data:
                    if isinstance(result_item, dict) and result_item.get('citation') == normalized_citation:
                        citation_result = result_item
                        break
                
                if not citation_result:
                    # Citation not found in API response
                    # DEBUG: Show what we got vs what we're looking for
                    api_citations = [item.get('citation') for item in data if isinstance(item, dict)]
                    logger.error(f"[BATCH-DEBUG] Looking for: '{citation}'")
                    logger.error(f"[BATCH-DEBUG] API returned: {api_citations[:5]}")
                    logger.warning(f"⚠️  No clusters found with exact citation match for {citation}")
                    results.append(VerificationResult(citation=citation, error="No match found in batch lookup"))
                    continue
                
                # Check the status of this specific citation
                status_code = citation_result.get('status', 0)
                error_message = citation_result.get('error_message', '')
                clusters_for_citation = citation_result.get('clusters', [])
                
                logger.error(f"[BATCH-DEBUG] {citation}: status={status_code}, clusters={len(clusters_for_citation)}")
                
                if status_code == 404 or not clusters_for_citation:
                    # Citation not found in CourtListener
                    logger.error(f"[BATCH-DEBUG] Citation '{citation}' returned 404 or no clusters: {error_message}")
                    results.append(VerificationResult(citation=citation, error=error_message or "Citation not found"))
                    continue
                
                # CRITICAL FIX: If there's only one cluster, use it directly
                # The CourtListener API already did the matching for us
                if len(clusters_for_citation) == 1:
                    matched_cluster = clusters_for_citation[0]
                    logger.error(f"[BATCH-DEBUG] {citation}: Using single cluster directly")
                else:
                    # Use improved matching logic for multiple clusters
                    matched_cluster = self._find_best_matching_cluster_sync(
                        clusters_for_citation, 
                        citation, 
                        extracted_name, 
                        extracted_date
                    )
                    logger.error(f"[BATCH-DEBUG] {citation}: Selected from {len(clusters_for_citation)} clusters")
                
                logger.error(f"[BATCH-DEBUG] {citation}: matched_cluster={'YES' if matched_cluster else 'NO'}")
                
                if matched_cluster:
                    # CRITICAL FIX: Try both camelCase and snake_case field names
                    # CourtListener v4 API uses different formats: batch lookup may use snake_case, search uses camelCase
                    canonical_name = matched_cluster.get('caseName') or matched_cluster.get('case_name')
                    canonical_date = matched_cluster.get('dateFiled') or matched_cluster.get('date_filed')
                    
                    # If not at top level, try to extract from docket object (try both formats)
                    if not canonical_name:
                        docket = matched_cluster.get('docket', {})
                        if isinstance(docket, dict):
                            canonical_name = docket.get('caseName') or docket.get('case_name')
                            if not canonical_date:
                                canonical_date = docket.get('dateFiled') or docket.get('date_filed')
                            logger.error(f"🔍 [DOCKET-EXTRACT] {citation}: Extracted from docket - case_name={canonical_name}")
                        else:
                            logger.warning(f"⚠️ [DOCKET-EXTRACT] {citation}: docket is not a dict, type={type(docket)}")
                    else:
                        logger.error(f"🔍 [TOP-LEVEL] {citation}: Found case_name = {canonical_name}")
                    
                    canonical_url = f"https://www.courtlistener.com{matched_cluster.get('absolute_url', '')}"
                    
                    # CRITICAL: Validate that canonical name makes sense with extracted name
                    # If they're completely different, log warning and reduce confidence
                    confidence = self._calculate_confidence(citation, canonical_name, extracted_name, canonical_date, extracted_date)
                    
                    # Additional validation: Check for obvious mismatches
                    validation_warning = None
                    if extracted_name and extracted_name != "N/A" and canonical_name:
                        similarity = self._calculate_name_similarity(canonical_name, extracted_name)
                        if similarity < 0.3:  # Very different names
                            validation_warning = f"Low similarity ({similarity:.2f}) between canonical '{canonical_name}' and extracted '{extracted_name}'"
                            logger.warning(f"⚠️  SUSPICIOUS MATCH for {citation}: {validation_warning}")
                            confidence = min(confidence, 0.5)  # Cap confidence for suspicious matches
                    
                    # FIX #61: COMPREHENSIVE LOGGING - Track every verification result
                    logger.error(f"🔍 [FIX #61] VERIFICATION: '{citation}'")
                    logger.error(f"   ✅ VERIFIED via courtlistener_lookup_batch")
                    logger.error(f"   📝 Canonical: '{canonical_name}' ({canonical_date})")
                    logger.error(f"   🔗 URL: {canonical_url}")
                    logger.error(f"   📊 Confidence: {confidence:.2f}")
                    if validation_warning:
                        logger.error(f"   ⚠️  Warning: {validation_warning}")
                    
                    results.append(VerificationResult(
                        citation=citation,
                        verified=True,
                        canonical_name=canonical_name,
                        canonical_date=canonical_date,
                        canonical_url=canonical_url,
                        source="courtlistener_lookup_batch",
                        confidence=confidence,
                        method="citation_lookup_v4_batch",
                        raw_data=matched_cluster,
                        validation_warning=validation_warning
                    ))
                else:
                    results.append(VerificationResult(
                        citation=citation,
                        verified=False,
                        error="No match found in batch lookup"
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"CourtListener batch lookup error: {e}")
            return [VerificationResult(citation=c, verified=False, error=str(e)) for c in citations]
    
    async def _verify_with_courtlistener_lookup(
        self, 
        citation: str, 
        extracted_case_name: Optional[str], 
        extracted_date: Optional[str]
    ) -> VerificationResult:
        """Verify using CourtListener citation-lookup API v4 (single citation)."""
        if not self.api_key:
            logger.error(f"🔥 [API-KEY-MISSING] CourtListener API key not found! Cannot verify '{citation}'")
            logger.error(f"   Set COURTLISTENER_API_KEY environment variable")
            return VerificationResult(citation=citation, error="No CourtListener API key")
        
        # Rate limiting
        await self._enforce_rate_limit(VerificationSource.COURTLISTENER_LOOKUP)
        
        try:
            # CRITICAL: Normalize citations for API compatibility
            # 1. Remove newlines/tabs (API fails on "161 U.S.\n519")
            # 2. Normalize dash-separated format
            from src.citation_patterns import normalize_dashed_citation
            import re
            
            # Remove newlines, tabs, and collapse whitespace
            normalized_citation = re.sub(r'[\n\r\t]+', ' ', citation)
            normalized_citation = re.sub(r'\s+', ' ', normalized_citation)
            normalized_citation = normalized_citation.strip()
            # Apply dash normalization
            normalized_citation = normalize_dashed_citation(normalized_citation)
            
            if normalized_citation != citation:
                logger.info(f"🔄 Normalized citation: '{citation}' → '{normalized_citation}'")
            
            # CRITICAL FIX: Use citation-lookup endpoint with POST (not citations/ with GET)
            # API requires "text" field, not "citation"
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            payload = {"text": normalized_citation}
            
            logger.error(f"🔥 [API-CALL] POST {url}")
            logger.error(f"   Payload: {payload}")
            logger.error(f"   Headers: Authorization={'Token' if self.api_key else 'None'}")
            
            response = self.session.post(url, json=payload, timeout=5)  # CRITICAL: Reduced to 5s to allow time for fallback
            logger.error(f"🔥 [API-RESPONSE] Status: {response.status_code}")
            
            # CRITICAL FIX: Return immediately on 429 to save time for fallback
            if response.status_code == 429:
                logger.error(f"🚨 RATE LIMIT 429 - returning immediately to allow fallback")
                raise requests.exceptions.HTTPError(response=response)
            
            response.raise_for_status()
            data = response.json()
            logger.error(f"🔥 [API-DATA] Received {len(str(data))} bytes of data")
            
            # CRITICAL FIX #11: The API returns a list with status codes for each citation
            # Check for 404 errors BEFORE trying to extract clusters
            if isinstance(data, list) and len(data) > 0:
                first_result = data[0]
                
                # Check for 404 or error responses
                status_code = first_result.get('status', 200)
                error_message = first_result.get('error_message')
                
                if status_code == 404 or error_message:
                    logger.debug(f"API returned 404 for '{citation}': {error_message}")
                    return VerificationResult(
                        citation=citation,
                        verified=False,
                        error=error_message or f"Citation not found (status: {status_code})"
                    )
                
                # Only extract clusters if status is 200
                clusters = first_result.get('clusters', [])
            elif isinstance(data, dict):
                # Dict format - check for clusters or results
                if 'clusters' in data:
                    clusters = data['clusters']
                elif 'results' in data and len(data['results']) > 0:
                    first_result = data['results'][0]
                    if isinstance(first_result, dict) and 'clusters' in first_result:
                        clusters = first_result['clusters']
                else:
                    clusters = []
            else:
                clusters = []
            
            if clusters and len(clusters) > 0:
                # CRITICAL FIX: Find the cluster that actually contains our citation
                # Don't blindly take the first one!
                # FIX #26: Pass extracted_name and extracted_date for validation
                cluster = await self._find_matching_cluster(clusters, citation, extracted_case_name, extracted_date)
                
                if not cluster:
                    # FIX #26: If no cluster matched (including rejected due to low similarity or N/A name),
                    # don't fall back to first cluster! Return unverified.
                    logger.warning(f"No matching cluster found for {citation} (rejected or N/A extraction)")
                    return VerificationResult(
                        citation=citation,
                        verified=False,
                        error="No matching cluster found or cluster rejected due to low similarity/N/A extraction"
                    )
                
                # CRITICAL FIX: Use camelCase field names for search API responses
                # CourtListener v4 Search API returns caseName/dateFiled (camelCase), not case_name/date_filed
                canonical_name = cluster.get('caseName') or cluster.get('case_name')
                canonical_date = cluster.get('dateFiled') or cluster.get('date_filed')
                
                # If not found, try docket object (might have either format)
                if not canonical_name:
                    docket = cluster.get('docket', {})
                    if isinstance(docket, dict):
                        canonical_name = docket.get('caseName') or docket.get('case_name')
                        if not canonical_date:
                            canonical_date = docket.get('dateFiled') or docket.get('date_filed')
                        logger.error(f"🔍 [DOCKET-EXTRACT-ASYNC] {citation}: Extracted from docket - case_name={canonical_name}")
                    else:
                        logger.warning(f"⚠️ [DOCKET-EXTRACT-ASYNC] {citation}: docket is not a dict, type={type(docket)}")
                else:
                    logger.error(f"🔍 [TOP-LEVEL-ASYNC] {citation}: Found case_name = {canonical_name}")
                
                canonical_url = f"https://www.courtlistener.com{cluster.get('absolute_url', '')}"
                
                # IMPROVEMENT: Detect and handle truncated canonical names
                # CRITICAL FIX: Don't flag short names as truncated - some cases have short names!
                # "Raines v. Byrd" is 14 chars and is COMPLETE, not truncated
                if canonical_name and extracted_case_name:
                    # Check if canonical name appears truncated
                    # Only flag as truncated if it has clear truncation indicators
                    is_truncated = (
                        canonical_name.endswith('...') or
                        canonical_name.endswith('..') or
                        (extracted_case_name and len(extracted_case_name) > len(canonical_name) + 20)  # Much larger threshold
                    )
                    
                    if is_truncated:
                        logger.warning(f"TRUNCATION_DETECTED: CourtListener returned truncated name '{canonical_name}' for {citation}")
                        logger.warning(f"  Extracted name: '{extracted_case_name}' (length: {len(extracted_case_name)})")
                        logger.warning(f"  Canonical name: '{canonical_name}' (length: {len(canonical_name)})")
                        
                        # Prefer extracted name if it's significantly longer and appears complete
                        if extracted_case_name and len(extracted_case_name) > len(canonical_name) + 10:
                            logger.info(f"  Using extracted name instead of truncated canonical name")
                            canonical_name = extracted_case_name
                    else:
                        # ALWAYS prefer verified canonical name over extraction
                        logger.info(f"  Using verified canonical name: '{canonical_name}' (not truncated)")
                
                # Validate result quality
                confidence = self._calculate_confidence(citation, canonical_name, extracted_case_name, canonical_date, extracted_date)
                logger.error(f"🔥 [CONFIDENCE] Calculated confidence: {confidence:.3f} (threshold: 0.7)")
                logger.error(f"   Canonical: '{canonical_name}' ({canonical_date})")
                logger.error(f"   Extracted: '{extracted_case_name}' ({extracted_date})")
                
                if confidence >= 0.7:  # High confidence threshold (>= not > to include 0.7)
                    return VerificationResult(
                        citation=citation,
                    verified=True,
                    canonical_name=canonical_name,
                    canonical_date=canonical_date,
                    canonical_url=canonical_url,
                    source="courtlistener_lookup",  # FIX #65: Specific source
                    confidence=confidence,
                    method="citation_lookup_v4",
                    raw_data=cluster
                    )
            
            return VerificationResult(citation=citation, error="No high-confidence results from CourtListener lookup")
            
        except requests.exceptions.HTTPError as e:
            # CRITICAL FIX: Handle 429 rate limit errors gracefully with user-friendly message
            if e.response is not None and e.response.status_code == 429:
                # Log full 429 response for debugging rate limit reset time
                logger.error(f"🚨 RATE LIMIT 429 for {citation}")
                logger.error(f"   Response Headers: {dict(e.response.headers)}")
                logger.error(f"   Response Body: {e.response.text[:500]}")
                
                # Extract rate limit reset time if available
                reset_time = e.response.headers.get('X-RateLimit-Reset') or e.response.headers.get('Retry-After') or e.response.headers.get('X-Rate-Limit-Reset')
                if reset_time:
                    logger.error(f"   ⏰ Rate limit resets at: {reset_time}")
                else:
                    logger.error(f"   ⏰ Rate limit reset time not provided in headers")
                
                logger.warning(f"⚠️ Rate limit hit for {citation} - skipping verification")
                return VerificationResult(
                    citation=citation, 
                    verified=False,
                    error=f"CourtListener rate limit (429). Reset time: {reset_time or 'unknown'}. This citation will be verified via alternative sources."
                )
            logger.warning(f"CourtListener lookup failed for {citation}: {e}")
            return VerificationResult(citation=citation, error=f"CourtListener API error. Trying alternative sources...")
        except requests.exceptions.Timeout as e:
            logger.warning(f"CourtListener lookup timed out for {citation}")
            return VerificationResult(
                citation=citation,
                verified=False,
                error="CourtListener is taking longer than usual to respond. Please try again later. (This citation will be verified via alternative sources.)"
            )
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"CourtListener connection failed for {citation}")
            return VerificationResult(
                citation=citation,
                verified=False,
                error="Unable to connect to CourtListener. Please check your internet connection or try again later. (This citation will be verified via alternative sources.)"
            )
        except Exception as e:
            logger.warning(f"CourtListener lookup failed for {citation}: {e}")
            return VerificationResult(citation=citation, error=f"Verification error. Trying alternative sources...")
    
    async def _find_matching_cluster(
        self, 
        clusters: List[Dict[str, Any]], 
        target_citation: str,
        extracted_name: Optional[str] = None,
        extracted_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the cluster that actually contains the target citation.
        
        FIX #26 (ASYNC FIX #24): Apply the same logic as _find_best_matching_cluster_sync
        to prevent blindly accepting wrong API matches, especially when extracted_name is N/A.
        
        This prevents the bug where we blindly take the first cluster when
        CourtListener returns multiple clusters for a citation.
        
        Args:
            clusters: List of cluster dictionaries from CourtListener
            target_citation: The citation we're looking for (e.g., "521 U.S. 811")
            extracted_name: The case name extracted from the document (for validation)
            extracted_date: The date extracted from the document (for validation)
        
        Returns:
            The matching cluster, or None if no match found (or if match is rejected due to low similarity)
        """
        # FIX #52: Add extensive logging to diagnose matching failure
        logger.error(f"🔍 [FIX #52] _find_matching_cluster called:")
        logger.error(f"   target_citation: '{target_citation}' (type: {type(target_citation).__name__})")
        logger.error(f"   extracted_name: '{extracted_name}'")
        logger.error(f"   extracted_date: '{extracted_date}'")
        logger.error(f"   clusters count: {len(clusters) if clusters else 0}")
        if clusters and len(clusters) > 0:
            logger.error(f"   first cluster keys: {list(clusters[0].keys())[:10]}")
            logger.error(f"   first cluster case_name: {clusters[0].get('case_name', 'N/A')}")
        
        if not clusters or not target_citation:
            logger.error(f"🚫 [FIX #52] Returning None: clusters={bool(clusters)}, target_citation={bool(target_citation)}")
            return None
        
        # FIX #26: If we have no extracted name, we CANNOT validate which cluster is correct!
        # Better to leave unverified than to verify incorrectly.
        if not extracted_name or extracted_name == "N/A":
            logger.warning(f"❌ CANNOT VERIFY {target_citation}: No extracted name available")
            logger.warning(f"   API returned {len(clusters)} possible clusters, but we can't pick the right one")
            logger.warning(f"   Leaving citation unverified (better than wrong verification)")
            return None
        
        normalized_target = self._normalize_citation_for_matching(target_citation)
        logger.error(f"🔍 [FIX #55-START] Starting cluster matching for {target_citation}")
        logger.error(f"   Normalized target: '{normalized_target}'")
        logger.error(f"   Total clusters to check: {len(clusters)}")
        matching_clusters = []
        
        for cluster in clusters:
            try:
                # CRITICAL FIX: Use resource_uri (API endpoint), not absolute_url (web page)
                # resource_uri = "https://www.courtlistener.com/api/rest/v4/clusters/xxx/"
                # absolute_url = "/opinion/xxx/case-name/" (returns HTML, not JSON!)
                cluster_url = cluster.get('resource_uri') or cluster.get('absolute_url')
                if not cluster_url:
                    logger.error(f"🚫 [FIX #55] No resource_uri or absolute_url in cluster!")
                    continue
                
                # Fetch full cluster details to check citations
                # resource_uri already includes full URL, absolute_url needs domain prepended
                if cluster_url.startswith('http'):
                    full_url = cluster_url  # Already complete
                else:
                    full_url = f"https://www.courtlistener.com{cluster_url}"
                logger.error(f"🌐 [FIX #55] Fetching cluster details from: {full_url}")
                response = self.session.get(full_url, timeout=20)  # FIX #66: Increased from 10s to 20s
                logger.error(f"📡 [FIX #55] Response status: {response.status_code}")
                
                # ONLY accept 200 (OK) - 202 (Accepted) means processing, no data yet
                if response.status_code == 200:
                    cluster_data = response.json()
                    
                    # Check if this cluster contains our target citation (EXACT match, not substring)
                    cluster_citations = cluster_data.get('citations', [])
                    for cit in cluster_citations:
                        cit_text = None
                        if isinstance(cit, str):
                            cit_text = cit
                        elif isinstance(cit, dict):
                            cit_text = cit.get('cite', '') or cit.get('citation', '')
                        
                        if cit_text:
                            normalized_cit = self._normalize_citation_for_matching(cit_text)
                            # FIX #55: Diagnostic logging for citation matching
                            logger.error(f"🔍 [FIX #55] Comparing citations for {target_citation}:")
                            logger.error(f"   Target normalized: '{normalized_target}'")
                            logger.error(f"   API cit normalized: '{normalized_cit}'")
                            logger.error(f"   Match: {normalized_target == normalized_cit}")
                            if normalized_target == normalized_cit:  # EXACT match
                                matching_clusters.append(cluster_data)
                                logger.error(f"✅ [FIX #55] MATCH FOUND!")
                                break
            
            except Exception as e:
                logger.error(f"❌ [FIX #55] Exception checking cluster: {e}")
                logger.error(f"❌ [FIX #55] Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ [FIX #55] Traceback: {traceback.format_exc()}")
                continue
        
        if not matching_clusters:
            logger.warning(f"⚠️  No cluster found matching {target_citation} in citation-lookup")
            
            # FIX #56: Fallback to Search API using case name
            # Many cases exist in CourtListener but aren't findable by citation-lookup
            # FIX #56B: Add quality checks - only use if extraction is good
            if extracted_name and extracted_name != "N/A":
                # Quality check: name must be at least 10 chars and contain "v." or "v "
                name_quality_ok = (
                    len(extracted_name) >= 10 and 
                    (' v.' in extracted_name.lower() or ' v ' in extracted_name.lower())
                )
                
                if not name_quality_ok:
                    logger.warning(f"⚠️  [FIX #56B] Skipping Search API - extracted name too short or malformed: '{extracted_name}'")
                    return None
                
                logger.error(f"🔄 [FIX #56] Trying Search API fallback with case name: '{extracted_name}'")
                try:
                    # Use Search API to find case by name
                    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
                    search_params = {
                        "q": extracted_name,
                        "type": "o",  # Opinion search
                    }
                    if extracted_date:
                        # Add date filter if available
                        search_params["filed_after"] = f"{extracted_date}-01-01"
                        search_params["filed_before"] = f"{extracted_date}-12-31"
                    
                    search_response = self.session.get(search_url, params=search_params, timeout=20)  # FIX #66: Increased from 10s to 20s
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        results = search_data.get('results', [])
                        logger.error(f"🔍 [FIX #56] Search API returned {len(results)} results")
                        
                        if results:
                            # FIX #56B: Validate the result before accepting
                            for result in results[:3]:  # Check top 3 results
                                result_name = result.get('caseName', '')
                                
                                # Check if result name has reasonable overlap with extracted name
                                extracted_words = set(extracted_name.lower().split())
                                result_words = set(result_name.lower().split())
                                common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and'}
                                extracted_words -= common_words
                                result_words -= common_words
                                
                                if not extracted_words:
                                    continue
                                
                                overlap = len(extracted_words & result_words) / len(extracted_words)
                                
                                # FIX #64: Special validation for criminal cases (same as async path)
                                is_criminal_case = False
                                criminal_patterns = [
                                    r'\bstate\s+v\.?\s+',
                                    r'\bpeople\s+v\.?\s+',
                                    r'\bcommonwealth\s+v\.?\s+',
                                    r'\bunited\s+states\s+v\.?\s+',
                                    r'\bcity\s+of\s+\w+\s+v\.?\s+'
                                ]
                                
                                for pattern in criminal_patterns:
                                    if re.search(pattern, extracted_name, re.IGNORECASE):
                                        is_criminal_case = True
                                        break
                                
                                if is_criminal_case:
                                    # For criminal cases, extract and compare defendant/party names
                                    extracted_party = re.sub(r'^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+', '', extracted_name, flags=re.IGNORECASE).strip()
                                    result_party = re.sub(r'^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+', '', result_name, flags=re.IGNORECASE).strip()
                                    
                                    # Remove common suffixes and punctuation
                                    extracted_party = re.sub(r'[,\.].*$', '', extracted_party).strip().lower()
                                    result_party = re.sub(r'[,\.].*$', '', result_party).strip().lower()
                                    
                                    if not extracted_party or not result_party:
                                        logger.warning(f"⚠️  [FIX #64] Could not extract party names from '{extracted_name}' vs '{result_name}'")
                                        continue
                                    
                                    party_similarity = self._calculate_name_similarity(extracted_party, result_party)
                                    
                                    if party_similarity < 0.7:
                                        logger.warning(f"⚠️  [FIX #64] CRIMINAL CASE MISMATCH: '{extracted_party}' vs '{result_party}' (similarity: {party_similarity:.2f})")
                                        logger.warning(f"   Full names: '{extracted_name}' vs '{result_name}'")
                                        logger.warning(f"   Different defendants = different cases! Rejecting.")
                                        continue
                                    
                                    logger.info(f"✅ [FIX #64] Criminal case party names match: '{extracted_party}' vs '{result_party}' (similarity: {party_similarity:.2f})")
                                
                                if overlap >= 0.5:  # At least 50% word overlap
                                    logger.error(f"✅ [FIX #56B] Valid match via Search API: {result_name} (overlap: {overlap:.0%})")
                                    return result
                                else:
                                    logger.warning(f"⚠️  [FIX #56B] Rejected result - low overlap ({overlap:.0%}): {result_name}")
                            
                            logger.warning(f"⚠️  [FIX #56B] No results passed validation (min 50% word overlap)")
                        else:
                            logger.warning(f"⚠️  [FIX #56] Search API found no results for '{extracted_name}'")
                    else:
                        logger.warning(f"⚠️  [FIX #56] Search API returned status {search_response.status_code}")
                except Exception as e:
                    logger.error(f"❌ [FIX #56] Search API fallback failed: {e}")
            
            return None
        
        # FIX #50: Filter by jurisdiction BEFORE validating extracted names (ASYNC VERSION)
        # This catches cases like '9 P.3d 655' matching Mississippi instead of WA
        expected_jurisdiction = self._detect_jurisdiction_from_citation(target_citation)
        logger.error(f"🔥 [FIX #50 ASYNC] Detected jurisdiction for {target_citation}: {expected_jurisdiction}")
        
        if expected_jurisdiction:
            # Filter out clusters that don't match the jurisdiction
            jurisdiction_filtered = []
            for cluster in matching_clusters:
                if self._validate_jurisdiction_match(cluster, expected_jurisdiction, target_citation):
                    jurisdiction_filtered.append(cluster)
                else:
                    logger.warning(f"🚫 [FIX #50 ASYNC] Filtered out cluster due to jurisdiction mismatch: {cluster.get('case_name', 'Unknown')}")
            
            if not jurisdiction_filtered:
                logger.warning(f"❌ [FIX #50 ASYNC] ALL clusters failed jurisdiction filtering for {target_citation}")
                return None
            
            matching_clusters = jurisdiction_filtered
            logger.error(f"✅ [FIX #50 ASYNC] {len(matching_clusters)} cluster(s) passed jurisdiction filter")
        
        # If only one match, validate it before returning
        if len(matching_clusters) == 1:
            single_cluster = matching_clusters[0]
            canonical_name = single_cluster.get('case_name', '')
            logger.info(f"Single cluster match for {target_citation}: {canonical_name}")
            
            # FIX #26: Validate this single cluster against extracted data
            if extracted_name and extracted_name != "N/A" and canonical_name:
                similarity = self._calculate_name_similarity(canonical_name, extracted_name)
                logger.info(f"  Validating single match: similarity = {similarity:.2f}")
                
                if similarity < 0.6:
                    logger.warning(f"❌ REJECTED single cluster: similarity {similarity:.2f} too low for {target_citation}")
                    logger.warning(f"   Canonical: {canonical_name}")
                    logger.warning(f"   Extracted: {extracted_name}")
                    return None  # Reject low-similarity match
            
            # FIX #26: Validate date if available
            if extracted_date and extracted_date != "N/A":
                canonical_date = single_cluster.get('date_filed', '')
                if canonical_date:
                    extracted_year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                    canonical_year_match = re.search(r'(19|20)\d{2}', str(canonical_date))
                    
                    if extracted_year_match and canonical_year_match:
                        extracted_year = int(extracted_year_match.group(0))
                        canonical_year = int(canonical_year_match.group(0))
                        year_diff = abs(extracted_year - canonical_year)
                        
                        if year_diff > 2:
                            logger.warning(f"❌ REJECTED single cluster: year mismatch for {target_citation}")
                            logger.warning(f"   Extracted year: {extracted_year} vs Canonical year: {canonical_year} (diff: {year_diff} years)")
                            return None  # Reject date mismatch
            
            logger.info(f"✅ Validated single cluster match for {target_citation}")
            return single_cluster
        
        # Multiple matches - use case name similarity to pick the best one
        logger.info(f"Multiple cluster matches ({len(matching_clusters)}) for {target_citation}, using case name similarity")
        
        best_cluster = None
        best_similarity = 0.0
        
        for cluster in matching_clusters:
            canonical_name = cluster.get('case_name', '')
            if canonical_name and extracted_name and extracted_name != "N/A":
                similarity = self._calculate_name_similarity(canonical_name, extracted_name)
                logger.info(f"  Cluster '{canonical_name[:50]}...': similarity = {similarity:.2f}")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster
        
        # FIX #26: Reject if best similarity is too low
        if best_similarity < 0.6:
            logger.warning(f"❌ REJECTED: Best similarity {best_similarity:.2f} too low for {target_citation}")
            logger.warning(f"   Canonical: {best_cluster.get('case_name') if best_cluster else 'None'}")
            logger.warning(f"   Extracted: {extracted_name}")
            logger.warning(f"   This suggests the API returned the wrong case!")
            return None  # Reject suspicious matches
        
        # FIX #26: Validate date of best match
        if best_cluster and extracted_date and extracted_date != "N/A":
            canonical_date = best_cluster.get('date_filed', '')
            if canonical_date:
                extracted_year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                canonical_year_match = re.search(r'(19|20)\d{2}', str(canonical_date))
                
                if extracted_year_match and canonical_year_match:
                    extracted_year = int(extracted_year_match.group(0))
                    canonical_year = int(canonical_year_match.group(0))
                    year_diff = abs(extracted_year - canonical_year)
                    
                    if year_diff > 2:
                        logger.warning(f"❌ REJECTED: Year mismatch too large for {target_citation}")
                        logger.warning(f"   Extracted year: {extracted_year} vs Canonical year: {canonical_year} (diff: {year_diff} years)")
                        logger.warning(f"   Canonical: {best_cluster.get('case_name')}")
                        logger.warning(f"   Extracted: {extracted_name}")
                        return None  # Reject date mismatches
        
        logger.info(f"✅ Best match for {target_citation}: '{best_cluster.get('case_name', '')[:50]}...' (similarity: {best_similarity:.2f})")
        return best_cluster
    
    def _find_best_matching_cluster_sync(
        self, 
        clusters: List[Dict[str, Any]], 
        target_citation: str,
        extracted_name: Optional[str] = None,
        extracted_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Synchronous version of cluster matching for batch operations.
        
        CRITICAL FIX: This method solves the problem of blindly taking the first cluster
        when CourtListener returns multiple clusters. It:
        1. Normalizes citations for exact matching (not substring)
        2. Finds ALL clusters that contain the citation
        3. If multiple matches, uses case name similarity to pick the best one
        4. Rejects matches with very low similarity to extracted name
        
        Args:
            clusters: List of cluster dictionaries from CourtListener API
            target_citation: The citation we're looking for (e.g., "199 Wn.2d 528")
            extracted_name: The case name extracted from the document
            extracted_date: The date extracted from the document
        
        Returns:
            The best matching cluster, or None if no good match found
        """
        if not clusters or not target_citation:
            return None
        
        # Normalize the target citation for comparison
        normalized_target = self._normalize_citation_for_matching(target_citation)
        
        # HYBRID APPROACH: Try exact matching first, but if it fails, trust the API
        matching_clusters = []
        for cluster in clusters:
            cluster_citations = cluster.get('citations', [])
            
            # Check each citation in the cluster for exact match
            for cit in cluster_citations:
                cit_text = str(cit)
                normalized_cit = self._normalize_citation_for_matching(cit_text)
                
                # EXACT match (after normalization), not substring
                if normalized_target == normalized_cit:
                    matching_clusters.append(cluster)
                    logger.info(f"✅ Cluster matches {target_citation}: {cluster.get('case_name', 'Unknown')}")
                    break
        
        # If no exact match found BUT the batch API returned clusters, trust the API
        if not matching_clusters and clusters:
            logger.warning(f"⚠️  No exact citation match found, but API returned {len(clusters)} cluster(s)")
            logger.error(f"[CLUSTER-DEBUG] Trusting API results for ambiguous citation: '{target_citation}'")
            matching_clusters = clusters  # Trust the API when exact matching fails
            
            for i, cluster in enumerate(matching_clusters):
                logger.error(f"[CLUSTER-DEBUG] API Cluster {i+1}: '{cluster.get('case_name', 'Unknown')[:60]}' ({cluster.get('date_filed', 'N/A')})")
        
        if not matching_clusters:
            logger.warning(f"⚠️  No clusters found for {target_citation}")
            return None
        
        # FIX #50: Filter by jurisdiction BEFORE validating extracted names
        # This catches cases like '9 P.3d 655' matching Mississippi instead of WA
        expected_jurisdiction = self._detect_jurisdiction_from_citation(target_citation)
        logger.error(f"🔥 [FIX #50] Detected jurisdiction for {target_citation}: {expected_jurisdiction}")
        
        if expected_jurisdiction:
            # Filter out clusters that don't match the jurisdiction
            jurisdiction_filtered = []
            for cluster in matching_clusters:
                if self._validate_jurisdiction_match(cluster, expected_jurisdiction, target_citation):
                    jurisdiction_filtered.append(cluster)
                else:
                    logger.warning(f"🚫 [FIX #50] Filtered out cluster due to jurisdiction mismatch: {cluster.get('case_name', 'Unknown')}")
            
            if not jurisdiction_filtered:
                logger.warning(f"❌ [FIX #50] ALL clusters failed jurisdiction filtering for {target_citation}")
                return None
            
            matching_clusters = jurisdiction_filtered
            logger.info(f"✅ [FIX #50] {len(matching_clusters)} cluster(s) passed jurisdiction filter")
        
        # FIX #20: Even with single cluster, validate it against extracted data!
        # Don't blindly accept API results - they might be wrong
        if len(matching_clusters) == 1:
            single_cluster = matching_clusters[0]
            canonical_name = single_cluster.get('case_name', '')
            logger.info(f"Single cluster match for {target_citation}: {canonical_name}")
            
            # Validate this single cluster against extracted data
            if extracted_name and extracted_name != "N/A" and canonical_name:
                similarity = self._calculate_name_similarity(canonical_name, extracted_name)
                logger.info(f"  Validating single match: similarity = {similarity:.2f}")
                
                if similarity < 0.6:
                    logger.warning(f"❌ REJECTED single cluster: similarity {similarity:.2f} too low for {target_citation}")
                    logger.warning(f"   Canonical: {canonical_name}")
                    logger.warning(f"   Extracted: {extracted_name}")
                    return None  # Reject low-similarity match
            
            # Validate date if available
            if extracted_date and extracted_date != "N/A":
                canonical_date = single_cluster.get('date_filed', '')
                if canonical_date:
                    extracted_year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                    canonical_year_match = re.search(r'(19|20)\d{2}', str(canonical_date))
                    
                    if extracted_year_match and canonical_year_match:
                        extracted_year = int(extracted_year_match.group(0))
                        canonical_year = int(canonical_year_match.group(0))
                        year_diff = abs(extracted_year - canonical_year)
                        
                        if year_diff > 2:
                            logger.warning(f"❌ REJECTED single cluster: year mismatch for {target_citation}")
                            logger.warning(f"   Extracted year: {extracted_year} vs Canonical year: {canonical_year} (diff: {year_diff} years)")
                            return None  # Reject date mismatch
            
            return single_cluster
        
        # Multiple clusters match - use extracted name to pick the best one
        logger.warning(f"⚠️  {len(matching_clusters)} clusters match {target_citation}, using similarity to pick best")
        
        if not extracted_name or extracted_name == "N/A":
            # FIX #24 (SYNC MODE): Do NOT verify if we have no extracted name!
            # Without an extracted name, we can't validate which cluster is correct.
            # Taking the first match blindly leads to wrong verifications (e.g., "Lopez Demetrio" issue)
            # Better to leave unverified than to verify incorrectly.
            logger.warning(f"❌ CANNOT VERIFY {target_citation}: No extracted name available")
            logger.warning(f"   API returned {len(matching_clusters)} possible matches, but we can't pick the right one")
            logger.warning(f"   Leaving citation UNVERIFIED to avoid contamination")
            return None  # FIX: Return None instead of blindly taking first match
        
        # FIX #2: Score each cluster using COMPOSITE SCORE (name + date + court)
        # This helps disambiguate when multiple clusters have similar names
        best_cluster = None
        best_score = 0.0
        
        for cluster in matching_clusters:
            canonical_name = cluster.get('case_name', '')
            canonical_date = cluster.get('date_filed', '')
            canonical_court = cluster.get('court_citation_string', '')
            
            # Component 1: Name similarity (60% weight)
            name_similarity = self._calculate_name_similarity(canonical_name, extracted_name)
            name_score = name_similarity * 0.6
            
            # Component 2: Date match (20% weight)
            date_score = 0.0
            if extracted_date and extracted_date != "N/A" and canonical_date:
                extracted_year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                canonical_year_match = re.search(r'(19|20)\d{2}', str(canonical_date))
                
                if extracted_year_match and canonical_year_match:
                    extracted_year = int(extracted_year_match.group(0))
                    canonical_year = int(canonical_year_match.group(0))
                    year_diff = abs(extracted_year - canonical_year)
                    
                    # Perfect match = 0.2, 1 year off = 0.15, 2 years = 0.1, 3+ years = 0.0
                    if year_diff == 0:
                        date_score = 0.2
                    elif year_diff == 1:
                        date_score = 0.15
                    elif year_diff == 2:
                        date_score = 0.1
            
            # Component 3: Court/jurisdiction match (20% weight)
            court_score = 0.0
            expected_jurisdiction = self._detect_jurisdiction_from_citation(target_citation)
            if expected_jurisdiction and canonical_court:
                # Simple check: if jurisdiction keyword appears in court string
                if expected_jurisdiction.lower() in canonical_court.lower():
                    court_score = 0.2
            
            # Composite score
            composite_score = name_score + date_score + court_score
            
            logger.info(f"  Cluster: {canonical_name[:50]}... | Name:{name_similarity:.2f} Date:{date_score:.2f} Court:{court_score:.2f} => Total:{composite_score:.2f}")
            
            if composite_score > best_score:
                best_score = composite_score
                best_cluster = cluster
        
        # CRITICAL: Reject matches with very low composite score
        # Threshold lowered from 0.6 to 0.5 because we're now using composite scoring
        if best_score < 0.5:
            logger.warning(f"❌ REJECTED: Best composite score {best_score:.2f} too low for {target_citation}")
            logger.warning(f"   Canonical: {best_cluster.get('case_name') if best_cluster else 'None'}")
            logger.warning(f"   Extracted: {extracted_name}")
            logger.warning(f"   This suggests the API returned the wrong case!")
            return None  # Reject suspicious matches
        
        # FIX #20: Validate dates if available
        if best_cluster and extracted_date and extracted_date != "N/A":
            canonical_date = best_cluster.get('date_filed', '')
            if canonical_date:
                # Extract years from both dates
                extracted_year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                canonical_year_match = re.search(r'(19|20)\d{2}', str(canonical_date))
                
                if extracted_year_match and canonical_year_match:
                    extracted_year = int(extracted_year_match.group(0))
                    canonical_year = int(canonical_year_match.group(0))
                    year_diff = abs(extracted_year - canonical_year)
                    
                    # CRITICAL: Reject if years are more than 2 years apart
                    # This catches cases like 2015 vs 2003 (Lopez Demetrio mismatch)
                    if year_diff > 2:
                        logger.warning(f"❌ REJECTED: Year mismatch too large for {target_citation}")
                        logger.warning(f"   Extracted year: {extracted_year} vs Canonical year: {canonical_year} (diff: {year_diff} years)")
                        logger.warning(f"   Canonical: {best_cluster.get('case_name')}")
                        logger.warning(f"   Extracted: {extracted_name}")
                        logger.warning(f"   This is likely a different case with the same citation!")
                        return None  # Reject date mismatches
        
        logger.info(f"✅ Selected cluster with similarity {best_similarity:.2f}: {best_cluster.get('case_name')}")
        return best_cluster
    
    def _detect_jurisdiction_from_citation(self, citation: str) -> Optional[str]:
        """
        FIX #50: Detect the expected jurisdiction from the citation text.
        
        Washington citations:
        - "Wn." or "Wash." = Washington Supreme Court
        - "P." or "P.2d" or "P.3d" = Pacific Reporter (primarily Washington, Oregon, Alaska, etc.)
        
        Federal citations:
        - "U.S." = US Supreme Court
        - "F." or "F.2d" or "F.3d" = Federal Reporter
        - "S. Ct." = Supreme Court Reporter
        - "L. Ed." = Lawyers Edition
        
        Returns:
            'washington' for WA cases, 'federal' for federal, 'pacific' for Pacific Reporter, None for unknown
        """
        citation_lower = citation.lower()
        
        # Washington state reporters
        if re.search(r'\bwn\b|\bwash\b', citation_lower):
            return 'washington'
        
        # Federal reporters
        if re.search(r'\bu\.?s\.?\b|\bs\.?\s*ct\.?\b|\bl\.?\s*ed\.?\b|\bf\.?\s*(2d|3d)?\b', citation_lower):
            return 'federal'
        
        # Pacific Reporter (primarily western states, but need to be careful)
        if re.search(r'\bp\.?\s*(2d|3d)?\b', citation_lower):
            return 'pacific'
        
        # WL (unpublished) - could be any jurisdiction
        if re.search(r'\bwl\b', citation_lower):
            return 'westlaw'
        
        return None
    
    def _validate_jurisdiction_match(self, cluster: Dict[str, Any], expected_jurisdiction: Optional[str], citation: str) -> bool:
        """
        FIX #50: Validate that a cluster matches the expected jurisdiction.
        
        Args:
            cluster: The CourtListener cluster data
            expected_jurisdiction: The expected jurisdiction from _detect_jurisdiction_from_citation
            citation: The target citation text
        
        Returns:
            True if jurisdiction matches or can't be determined, False if clear mismatch
        """
        if not expected_jurisdiction:
            return True  # Can't validate, assume OK
        
        # Get cluster citations to check jurisdiction
        cluster_citations = cluster.get('citations', [])
        
        if expected_jurisdiction == 'washington':
            # FIX #60C: Skip cluster_citations check if empty (Search API path)
            if cluster_citations:
                # For Washington citations, require at least one WA reporter in the cluster
                has_wa_citation = any(
                    re.search(r'\bwn\b|\bwash\b', str(cit).lower()) 
                    for cit in cluster_citations
                )
                if not has_wa_citation:
                    logger.warning(f"🚫 [FIX #50] JURISDICTION MISMATCH: {citation} expects Washington, but cluster has no WA reporters")
                    logger.warning(f"   Cluster citations: {cluster_citations}")
                    logger.warning(f"   Case: {cluster.get('case_name', 'Unknown')}")
                    return False
        
        elif expected_jurisdiction == 'federal':
            # FIX #60C: Skip cluster_citations check if empty (Search API path)
            if cluster_citations:
                # For federal citations, require at least one federal reporter in the cluster
                has_federal_citation = any(
                    re.search(r'\bu\.?s\.?\b|\bs\.?\s*ct\.?\b|\bl\.?\s*ed\.?\b|\bf\.?\s*(2d|3d)?\b', str(cit).lower())
                    for cit in cluster_citations
                )
                if not has_federal_citation:
                    logger.warning(f"🚫 [FIX #50] JURISDICTION MISMATCH: {citation} expects Federal, but cluster has no federal reporters")
                    logger.warning(f"   Cluster citations: {cluster_citations}")
                    return False
        
        elif expected_jurisdiction == 'pacific':
            # FIX #60: Pacific Reporter covers 14 western states
            # Valid: WA, OR, CA, MT, ID, NV, AZ, HI, AK, KS, CO, WY, NM, UT
            # INVALID: Iowa (N.W.), Texas (S.W.), Florida (So.), etc.
            
            # Check canonical URL and case name for wrong-region states
            canonical_url = cluster.get('canonical_url', '') or ''
            canonical_name = cluster.get('case_name', '') or ''
            case_info = (canonical_url + ' ' + canonical_name).lower()
            
            # States that should NEVER match P.2d/P.3d (they use different reporters)
            wrong_region_states = [
                'iowa', 'texas', 'florida', 'new-york', 'illinois', 'ohio', 
                'michigan', 'minnesota', 'wisconsin', 'nebraska', 'north-dakota',
                'south-dakota', 'indiana', 'pennsylvania', 'new-jersey',
                'georgia', 'virginia', 'north-carolina', 'south-carolina',
                'alabama', 'mississippi', 'louisiana', 'tennessee', 'kentucky',
                'arkansas', 'missouri', 'oklahoma', 'connecticut', 'massachusetts',
                'rhode-island', 'vermont', 'new-hampshire', 'maine', 'maryland',
                'delaware', 'west-virginia'
            ]
            
            for wrong_state in wrong_region_states:
                if wrong_state in case_info:
                    logger.error(f"🚫 [FIX #60] WRONG REPORTER SYSTEM: {citation} (Pacific Reporter) matched to {wrong_state.upper()} case!")
                    logger.error(f"   Pacific Reporter covers: WA/OR/CA/MT/ID/NV/AZ/HI/AK/KS/CO/WY/NM/UT")
                    logger.error(f"   URL: {canonical_url}")
                    logger.error(f"   Case: {canonical_name}")
                    return False
            
            # Optional: warn if no P. citation but don't reject (case might have parallel cites)
            has_pacific_citation = any(
                re.search(r'\bp\.?\s*(2d|3d)?\b', str(cit).lower())
                for cit in cluster_citations
            )
            if not has_pacific_citation:
                logger.info(f"⚠️  [FIX #60] Pacific Reporter citation {citation}, but cluster has no P. reporter (may be parallel cites)")
        
        return True
    
    def _normalize_citation_for_matching(self, citation: str) -> str:
        """
        Normalize a citation string for exact matching.
        
        Examples:
            "199 Wn.2d 528" -> "199wn2d528"
            "199\nWn.2d 528" -> "199wn2d528"
            "199  Wn.2d  528" -> "199wn2d528"
        """
        # Remove all whitespace, newlines, and periods
        normalized = re.sub(r'[\s\.\n\r]+', '', citation)
        # Convert to lowercase for case-insensitive comparison
        normalized = normalized.lower()
        return normalized
    
    async def _verify_with_courtlistener_search(
        self, 
        citation: str, 
        extracted_case_name: Optional[str], 
        extracted_date: Optional[str]
    ) -> VerificationResult:
        """Verify using CourtListener search API (fallback method)."""
        if not self.api_key:
            return VerificationResult(citation=citation, error="No CourtListener API key")
        
        # Rate limiting
        await self._enforce_rate_limit(VerificationSource.COURTLISTENER_SEARCH)
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                'q': citation,
                'type': 'o',  # Opinions
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=5)  # CRITICAL: Reduced to 5s to allow time for fallback
            
            # CRITICAL FIX: Return immediately on 429 to save time for fallback
            if response.status_code == 429:
                logger.error(f"🚨 RATE LIMIT 429 (search) - returning immediately to allow fallback")
                raise requests.exceptions.HTTPError(response=response)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                # Find best match
                best_result = self._find_best_search_result(data['results'], citation, extracted_case_name, extracted_date)
                
                if best_result:
                    # CRITICAL FIX: Extract from docket if not at top level (same as batch lookup)
                    canonical_name = best_result.get('caseName')  # Search API uses camelCase
                    canonical_date = best_result.get('dateFiled')
                    
                    # If not at top level, try docket object
                    if not canonical_name:
                        docket = best_result.get('docket', {})
                        if isinstance(docket, dict):
                            canonical_name = docket.get('case_name') or docket.get('caseName')
                            if not canonical_date:
                                canonical_date = docket.get('date_filed') or docket.get('dateFiled')
                            logger.error(f"🔍 [DOCKET-EXTRACT-SEARCH] {citation}: Extracted from docket - case_name={canonical_name}")
                        else:
                            logger.warning(f"⚠️ [DOCKET-EXTRACT-SEARCH] {citation}: docket is not a dict, type={type(docket)}")
                    else:
                        logger.error(f"🔍 [TOP-LEVEL-SEARCH] {citation}: Found caseName at top level = {canonical_name}")
                    
                    canonical_url = f"https://www.courtlistener.com{best_result.get('absolute_url', '')}"
                    
                    # FIX #60B: Validate jurisdiction BEFORE accepting Search API results
                    expected_jurisdiction = self._detect_jurisdiction_from_citation(citation)
                    if expected_jurisdiction:
                        # Create minimal cluster dict for validation
                        mock_cluster = {
                            'case_name': canonical_name,
                            'absolute_url': canonical_url,
                            'citations': []  # Will be validated by URL/name
                        }
                        if not self._validate_jurisdiction_match(mock_cluster, expected_jurisdiction, citation):
                            logger.warning(f"🚫 [FIX #60B SEARCH API] Rejected search result due to jurisdiction mismatch: {canonical_name} for {citation}")
                            return VerificationResult(citation=citation, error="Jurisdiction mismatch (search API)")
                    
                    # IMPROVEMENT: Detect and handle truncated canonical names
                    if canonical_name and extracted_case_name:
                        is_truncated = (
                            canonical_name.endswith('...') or
                            len(canonical_name) < 20 or
                            (extracted_case_name and len(extracted_case_name) > len(canonical_name) + 10)
                        )
                        
                        if is_truncated:
                            logger.warning(f"TRUNCATION_DETECTED (search): CourtListener returned truncated name '{canonical_name}'")
                            if extracted_case_name and len(extracted_case_name) > len(canonical_name) + 5:
                                logger.info(f"  Using extracted name '{extracted_case_name}' instead")
                                canonical_name = extracted_case_name
                    
                    confidence = self._calculate_confidence(citation, canonical_name, extracted_case_name, canonical_date, extracted_date)
                    
                    if confidence > 0.6:  # Lower threshold for search API
                        # FIX #61: COMPREHENSIVE LOGGING - Track Search API results
                        logger.error(f"🔍 [FIX #61] VERIFICATION: '{citation}'")
                        logger.error(f"   ✅ VERIFIED via search_api_fallback")
                        logger.error(f"   📝 Canonical: '{canonical_name}' ({canonical_date})")
                        logger.error(f"   🔗 URL: {canonical_url}")
                        logger.error(f"   📊 Confidence: {confidence:.2f}")
                        logger.error(f"   📌 Extracted: '{extracted_case_name}' ({extracted_date})")
                        
                        return VerificationResult(
                            citation=citation,
                            verified=True,
                            canonical_name=canonical_name,
                        canonical_date=canonical_date,
                        canonical_url=canonical_url,
                        source="courtlistener_search",  # FIX #65: Specific source for Search API fallback
                        confidence=confidence,
                        method="search_api_v4",
                            raw_data=best_result
                        )
            
            return VerificationResult(citation=citation, error="No good results from CourtListener search")
            
        except requests.exceptions.HTTPError as e:
            # CRITICAL FIX: Handle 429 rate limit errors gracefully with user-friendly message
            if e.response is not None and e.response.status_code == 429:
                # Log full 429 response for debugging rate limit reset time
                logger.error(f"🚨 RATE LIMIT 429 for {citation} (search)")
                logger.error(f"   Response Headers: {dict(e.response.headers)}")
                logger.error(f"   Response Body: {e.response.text[:500]}")
                
                # Extract rate limit reset time if available
                reset_time = e.response.headers.get('X-RateLimit-Reset') or e.response.headers.get('Retry-After') or e.response.headers.get('X-Rate-Limit-Reset')
                if reset_time:
                    logger.error(f"   ⏰ Rate limit resets at: {reset_time}")
                else:
                    logger.error(f"   ⏰ Rate limit reset time not provided in headers")
                
                logger.warning(f"⚠️ Rate limit hit for {citation} (search) - skipping verification")
                return VerificationResult(
                    citation=citation, 
                    verified=False,
                    error=f"CourtListener rate limit (429). Reset time: {reset_time or 'unknown'}. This citation will be verified via alternative sources."
                )
            logger.warning(f"CourtListener search failed for {citation}: {e}")
            return VerificationResult(citation=citation, error=f"CourtListener API error. Trying alternative sources...")
        except requests.exceptions.Timeout as e:
            logger.warning(f"CourtListener search timed out for {citation}")
            return VerificationResult(
                citation=citation,
                verified=False,
                error="CourtListener is taking longer than usual to respond. Please try again later. (This citation will be verified via alternative sources.)"
            )
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"CourtListener search connection failed for {citation}")
            return VerificationResult(
                citation=citation,
                verified=False,
                error="Unable to connect to CourtListener. Please check your internet connection or try again later. (This citation will be verified via alternative sources.)"
            )
        except Exception as e:
            logger.warning(f"CourtListener search failed for {citation}: {e}")
            return VerificationResult(citation=citation, error=f"Verification error. Trying alternative sources...")
    
    async def _verify_with_enhanced_fallback(
        self, 
        citation: str, 
        extracted_case_name: Optional[str], 
        extracted_date: Optional[str],
        remaining_timeout: float
    ) -> VerificationResult:
        """Enhanced fallback verification using EnhancedFallbackVerifier with 9+ sources."""
        logger.info(f"🔄 FALLBACK_VERIFY: Starting enhanced fallback for '{citation}'")
        
        try:
            # CRITICAL: Use EnhancedFallbackVerifier which has CaseMine, Leagle, DuckDuckGo, etc.
            from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
            
            verifier = EnhancedFallbackVerifier()
            
            # Use synchronous verification (more reliable for fallback)
            result = verifier.verify_citation_sync(
                citation_text=citation,
                extracted_case_name=extracted_case_name,
                extracted_date=extracted_date
            )
            
            if result and result.get('verified'):
                logger.info(f"✅ FALLBACK SUCCESS: Verified '{citation}' via {result.get('source', 'enhanced_fallback')}")
                return VerificationResult(
                    citation=citation,
                    verified=True,
                    canonical_name=result.get('canonical_name'),
                    canonical_date=result.get('canonical_date'),
                    canonical_url=result.get('canonical_url') or result.get('url'),
                    source=result.get('source', 'enhanced_fallback'),
                    confidence=result.get('confidence', 0.8)
                )
            else:
                logger.info(f"⚠️ FALLBACK FAILED: All enhanced sources exhausted for '{citation}'")
                return VerificationResult(citation=citation, error="Enhanced fallback sources exhausted")
                
        except Exception as e:
            logger.error(f"❌ FALLBACK ERROR for '{citation}': {e}")
            return VerificationResult(citation=citation, error=f"Fallback error: {e}")
        
        # Try fallback sources in priority order
        # Updated with working direct URL sources
        fallback_sources = [
            (VerificationSource.JUSTIA, self._verify_with_justia),
            ('OpenJurist', self._verify_with_openjurist),  # NEW: Direct URL access
            ('Cornell_LII', self._verify_with_cornell_lii),  # NEW: Cornell Legal Information Institute
            (VerificationSource.GOOGLE_SCHOLAR, self._verify_with_google_scholar),
            (VerificationSource.FINDLAW, self._verify_with_findlaw),
            (VerificationSource.BING, self._verify_with_bing),
        ]
        
        time_per_source = remaining_timeout / len(fallback_sources)
        
        for source, verify_func in fallback_sources:
            if remaining_timeout <= 0:
                break
            
            try:
                source_start = time.time()
                result = await verify_func(citation, extracted_case_name, extracted_date, time_per_source)
                
                if result.verified:
                    logger.info(f"✅ FALLBACK_VERIFY: {source.value} succeeded for '{citation}'")
                    return result
                
                remaining_timeout -= (time.time() - source_start)
                
            except Exception as e:
                logger.warning(f"Fallback source {source.value} failed for {citation}: {e}")
                continue
        
        return VerificationResult(citation=citation, error="All fallback sources failed")
    
    async def _verify_with_justia(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using Justia legal database via DIRECT URL construction (bypasses anti-bot)."""
        logger.info(f"🔍 [JUSTIA-DIRECT] Verifying {citation} with Justia direct URL")
        
        try:
            # CRITICAL FIX: Build direct URL from citation instead of searching
            # This bypasses anti-bot protection (403 Forbidden on search)
            direct_url = self._build_justia_url(citation)
            
            if not direct_url:
                logger.warning(f"⚠️  [JUSTIA-DIRECT] Cannot build URL for citation format: {citation}")
                return VerificationResult(citation=citation, error="Unsupported citation format for Justia direct access")
            
            logger.info(f"🔗 [JUSTIA-DIRECT] Trying direct URL: {direct_url}")
            
            # Add better headers to appear more like a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Extract case name from page title or heading
                # Justia pages have the case name in <h1> or <title>
                case_name_patterns = [
                    r'<h1[^>]*>([^<]+v\.?[^<]+)</h1>',
                    r'<title>([^<]+v\.?[^<]+)\s*\|',
                    r'<meta\s+property="og:title"\s+content="([^"]+v\.?[^"]+)"',
                ]
                
                canonical_name = None
                for pattern in case_name_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        canonical_name = match.group(1).strip()
                        # Clean up HTML entities and extra whitespace
                        canonical_name = re.sub(r'\s+', ' ', canonical_name)
                        break
                
                if canonical_name:
                    # Extract date from page
                    canonical_date = extracted_date
                    date_patterns = [
                        r'Decided:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})',
                        r'Date Filed:\s*(\d{2}/\d{2}/\d{4})',
                        r'\b(\d{4})\b',  # Fallback: any 4-digit year
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, content)
                        if date_match:
                            canonical_date = date_match.group(1)
                            break
                    
                    logger.info(f"✅ [JUSTIA-DIRECT] Found case: '{canonical_name}'")
                    
                    # Validate if we have an extracted name
                    if extracted_case_name and extracted_case_name != "N/A":
                        extracted_words = set(extracted_case_name.lower().split())
                        canonical_words = set(canonical_name.lower().split())
                        common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and'}
                        extracted_words -= common_words
                        canonical_words -= common_words
                        
                        if extracted_words:
                            overlap = len(extracted_words & canonical_words) / len(extracted_words)
                            if overlap < 0.3:  # Lower threshold for direct URL access
                                logger.warning(f"⚠️  [JUSTIA-DIRECT] Name mismatch: '{canonical_name}' vs '{extracted_case_name}' (overlap: {overlap:.0%})")
                                # Still return it but with lower confidence
                                confidence = 0.6
                            else:
                                confidence = 0.85
                        else:
                            confidence = 0.75
                    else:
                        # No extracted name to validate against, trust the direct URL
                        confidence = 0.80
                    
                    return VerificationResult(
                        citation=citation,
                        verified=True,
                        canonical_name=canonical_name,
                        canonical_date=canonical_date,
                        canonical_url=direct_url,
                        source="Justia",
                        confidence=confidence,
                        method="justia_direct_url"
                    )
                else:
                    logger.warning(f"⚠️  [JUSTIA-DIRECT] Page loaded but couldn't extract case name")
                    return VerificationResult(citation=citation, error="Could not extract case name from Justia page")
            
            elif response.status_code == 404:
                logger.warning(f"⚠️  [JUSTIA-DIRECT] Case not found on Justia: {citation}")
                return VerificationResult(citation=citation, error="Case not found on Justia (404)")
            else:
                logger.warning(f"⚠️  [JUSTIA-DIRECT] HTTP {response.status_code} for {citation}")
                return VerificationResult(citation=citation, error=f"Justia returned status {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ [JUSTIA-DIRECT] Error: {e}")
            return VerificationResult(citation=citation, error=f"Justia error: {e}")
    
    def _build_justia_url(self, citation: str) -> Optional[str]:
        """Build direct Justia URL from citation (bypasses search anti-bot protection)."""
        citation = citation.strip()
        
        # Federal Supreme Court: {volume} U.S. {page}
        us_match = re.search(r'(\d+)\s+U\.?S\.?\s+(\d+)', citation, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://law.justia.com/cases/federal/us/{volume}/{page}/"
        
        # Federal Appellate: {volume} F.{series} {page}
        f_match = re.search(r'(\d+)\s+F\.?\s*(\d?)d?\s+(\d+)', citation, re.IGNORECASE)
        if f_match:
            volume, series, page = f_match.groups()
            series_name = f"f{series}d" if series else "f"
            return f"https://law.justia.com/cases/federal/appellate-courts/{series_name}/{volume}/{page}/"
        
        # State courts - Washington
        wash_match = re.search(r'(\d+)\s+Wn\.?\s*2d\s+(\d+)', citation, re.IGNORECASE)
        if wash_match:
            volume, page = wash_match.groups()
            # Justia WA URLs need year - try to extract from extracted_date or estimate
            # For now, return None as we need more info
            # Could be enhanced with year parameter
            logger.debug(f"Washington citation detected but needs year: {citation}")
            return None
        
        # California
        cal_match = re.search(r'(\d+)\s+Cal\.?\s*(\d?)(?:d|th)?\s+(\d+)', citation, re.IGNORECASE)
        if cal_match:
            volume, series, page = cal_match.groups()
            # Similar to WA - needs year
            return None
        
        # Add more patterns as needed
        logger.debug(f"No URL pattern matched for: {citation}")
        return None
    
    async def _verify_with_openjurist(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using OpenJurist via DIRECT URL construction (federal cases only)."""
        logger.info(f"🔍 [OPENJURIST-DIRECT] Verifying {citation}")
        
        try:
            # Build direct URL from citation
            direct_url = self._build_openjurist_url(citation)
            
            if not direct_url:
                logger.warning(f"⚠️  [OPENJURIST-DIRECT] Cannot build URL for: {citation}")
                return VerificationResult(citation=citation, error="Unsupported citation format for OpenJurist")
            
            logger.info(f"🔗 [OPENJURIST-DIRECT] Trying: {direct_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Extract case name from title
                title_match = re.search(r'<title>([^<]+?)\s*\|', content)
                if title_match:
                    title = title_match.group(1).strip()
                    # Clean up: "410 US 113 Roe v. Wade" -> "Roe v. Wade"
                    canonical_name = re.sub(r'^\d+\s+[A-Z\.]+\s+\d+\s+', '', title).strip()
                    
                    if canonical_name and 'v' in canonical_name.lower():
                        logger.info(f"✅ [OPENJURIST-DIRECT] Found: '{canonical_name}'")
                        
                        # Extract date if available
                        canonical_date = extracted_date
                        date_match = re.search(r'\b(19|20)\d{2}\b', content[:2000])
                        if date_match:
                            canonical_date = date_match.group(0)
                        
                        # Validate against extracted name if available
                        confidence = 0.80  # Default for direct URL
                        if extracted_case_name and extracted_case_name != "N/A":
                            extracted_words = set(extracted_case_name.lower().split())
                            canonical_words = set(canonical_name.lower().split())
                            common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and'}
                            extracted_words -= common_words
                            canonical_words -= common_words
                            
                            if extracted_words:
                                overlap = len(extracted_words & canonical_words) / len(extracted_words)
                                if overlap >= 0.3:
                                    confidence = 0.85
                                elif overlap < 0.2:
                                    logger.warning(f"⚠️  [OPENJURIST-DIRECT] Name mismatch: '{canonical_name}' vs '{extracted_case_name}'")
                                    confidence = 0.60
                        
                        return VerificationResult(
                            citation=citation,
                            verified=True,
                            canonical_name=canonical_name,
                            canonical_date=canonical_date,
                            canonical_url=direct_url,
                            source="OpenJurist",
                            confidence=confidence,
                            method="openjurist_direct_url"
                        )
                    else:
                        logger.warning(f"⚠️  [OPENJURIST-DIRECT] Invalid case name: '{canonical_name}'")
                else:
                    logger.warning(f"⚠️  [OPENJURIST-DIRECT] Couldn't extract case name")
                
                return VerificationResult(citation=citation, error="Could not extract case name from OpenJurist")
            
            elif response.status_code == 404:
                logger.warning(f"⚠️  [OPENJURIST-DIRECT] Not found: {citation}")
                return VerificationResult(citation=citation, error="Case not found on OpenJurist (404)")
            else:
                logger.warning(f"⚠️  [OPENJURIST-DIRECT] HTTP {response.status_code}")
                return VerificationResult(citation=citation, error=f"OpenJurist returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ [OPENJURIST-DIRECT] Error: {e}")
            return VerificationResult(citation=citation, error=f"OpenJurist error: {e}")
    
    def _build_openjurist_url(self, citation: str) -> Optional[str]:
        """Build direct OpenJurist URL from citation (federal cases only)."""
        citation = citation.strip()
        
        # Federal Supreme Court: {volume} U.S. {page}
        us_match = re.search(r'(\d+)\s+U\.?S\.?\s+(\d+)', citation, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://openjurist.org/{volume}/us/{page}"
        
        # Federal Appellate: {volume} F.{series}d {page}
        # Examples: 163 F.3d 952, 100 F.2d 500
        f_match = re.search(r'(\d+)\s+F\.?\s*(\d?)d\s+(\d+)', citation, re.IGNORECASE)
        if f_match:
            volume, series, page = f_match.groups()
            if series:
                reporter = f"f{series}d"
            else:
                reporter = "f"  # Old F. reporter
            return f"https://openjurist.org/{volume}/{reporter}/{page}"
        
        # Federal Reporter: {volume} F. {page} (without series number)
        f_old_match = re.search(r'(\d+)\s+F\.\s+(\d+)', citation, re.IGNORECASE)
        if f_old_match:
            volume, page = f_old_match.groups()
            return f"https://openjurist.org/{volume}/f/{page}"
        
        logger.debug(f"No OpenJurist URL pattern matched for: {citation}")
        return None
    
    async def _verify_with_cornell_lii(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using Cornell Legal Information Institute via DIRECT URL construction."""
        logger.info(f"🔍 [CORNELL-LII] Verifying {citation}")
        
        try:
            # Build direct URL from citation
            direct_url = self._build_cornell_lii_url(citation)
            
            if not direct_url:
                logger.warning(f"⚠️  [CORNELL-LII] Cannot build URL for: {citation}")
                return VerificationResult(citation=citation, error="Unsupported citation format for Cornell LII")
            
            logger.info(f"🔗 [CORNELL-LII] Trying: {direct_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Extract case name from title
                # Cornell format: "Jane ROE, et al., Appellants, v. Henry WADE. | Supreme Court | US Law | LII / Legal Information Institute"
                title_match = re.search(r'<title>([^|]+?)\s*\|', content)
                if title_match:
                    title_text = title_match.group(1).strip()
                    
                    # Try to extract case name (look for "v." pattern)
                    # Handle formats like "Jane ROE, et al., Appellants, v. Henry WADE."
                    # Try pattern 1: With comma (captures name before comma)
                    case_match = re.search(r'^(.+?),.*?\s+v\.?\s+(.+?)\.?\s*$', title_text, re.IGNORECASE)
                    
                    if not case_match:
                        # Pattern 2: Simple "X v. Y" format
                        case_match = re.search(r'^(.+?)\s+v\.?\s+(.+?)\.?\s*$', title_text, re.IGNORECASE)
                    
                    if case_match:
                        plaintiff = case_match.group(1).strip()
                        defendant = case_match.group(2).strip()
                        canonical_name = f"{plaintiff} v. {defendant}"
                        
                        # Clean up common Cornell formatting
                        canonical_name = re.sub(r',?\s*et al\.?,?', '', canonical_name)
                        canonical_name = re.sub(r',?\s*Appellant[s]?,?', '', canonical_name)
                        canonical_name = re.sub(r',?\s*Appellee[s]?,?', '', canonical_name)
                        canonical_name = re.sub(r'\s+', ' ', canonical_name).strip()
                        
                        logger.info(f"✅ [CORNELL-LII] Found: '{canonical_name}'")
                        
                        # Extract date if available
                        canonical_date = extracted_date
                        date_patterns = [
                            r'Decided\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
                            r'Argued.*?(\d{4})',
                            r'\b(19|20)\d{2}\b'
                        ]
                        
                        for pattern in date_patterns:
                            date_match = re.search(pattern, content[:3000])
                            if date_match:
                                canonical_date = date_match.group(1) if ',' in date_match.group(0) else date_match.group(0)
                                break
                        
                        # Validate against extracted name if available
                        confidence = 0.85  # High confidence for Cornell (official source)
                        if extracted_case_name and extracted_case_name != "N/A":
                            extracted_words = set(extracted_case_name.lower().split())
                            canonical_words = set(canonical_name.lower().split())
                            common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and', 'et', 'al'}
                            extracted_words -= common_words
                            canonical_words -= common_words
                            
                            if extracted_words:
                                overlap = len(extracted_words & canonical_words) / len(extracted_words)
                                if overlap >= 0.4:
                                    confidence = 0.90  # Very high for Cornell + name match
                                elif overlap < 0.2:
                                    logger.warning(f"⚠️  [CORNELL-LII] Name mismatch: '{canonical_name}' vs '{extracted_case_name}'")
                                    confidence = 0.70
                        
                        return VerificationResult(
                            citation=citation,
                            verified=True,
                            canonical_name=canonical_name,
                            canonical_date=canonical_date,
                            canonical_url=direct_url,
                            source="Cornell_LII",
                            confidence=confidence,
                            method="cornell_lii_direct_url"
                        )
                    else:
                        logger.warning(f"⚠️  [CORNELL-LII] Couldn't parse case name from title")
                else:
                    logger.warning(f"⚠️  [CORNELL-LII] Couldn't extract title")
                
                return VerificationResult(citation=citation, error="Could not extract case name from Cornell LII")
            
            elif response.status_code == 404:
                logger.warning(f"⚠️  [CORNELL-LII] Not found: {citation}")
                return VerificationResult(citation=citation, error="Case not found on Cornell LII (404)")
            else:
                logger.warning(f"⚠️  [CORNELL-LII] HTTP {response.status_code}")
                return VerificationResult(citation=citation, error=f"Cornell LII returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ [CORNELL-LII] Error: {e}")
            return VerificationResult(citation=citation, error=f"Cornell LII error: {e}")
    
    def _build_cornell_lii_url(self, citation: str) -> Optional[str]:
        """Build direct Cornell LII URL from citation (Supreme Court cases only)."""
        citation = citation.strip()
        
        # Supreme Court: {volume} U.S. {page}
        us_match = re.search(r'(\d+)\s+U\.?S\.?\s+(\d+)', citation, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://www.law.cornell.edu/supremecourt/text/{volume}/{page}"
        
        # Cornell LII primarily has Supreme Court cases
        # Could be extended for other courts if patterns are discovered
        
        logger.debug(f"No Cornell LII URL pattern matched for: {citation}")
        return None
    
    async def _verify_with_google_scholar(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using Google Scholar with strict validation."""
        # FIX #57: Integrate with Fix #56C validation
        logger.info(f"🔍 [FIX #57-SCHOLAR] Verifying {citation} with Google Scholar")
        
        if not extracted_case_name or extracted_case_name == "N/A" or len(extracted_case_name) < 10:
            logger.warning(f"⚠️  [FIX #57-SCHOLAR] Skipping - no valid extracted name")
            return VerificationResult(citation=citation, error="No extracted name for validation")
        
        try:
            search_query = f'"{citation}" "{extracted_case_name}"'
            search_url = f"https://scholar.google.com/scholar?hl=en&q={quote(search_query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(search_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Extract case names from result titles
                title_pattern = r'<h3[^>]*class="gs_rt"[^>]*>(?:<a[^>]*>)?([^<]+)</h3>'
                titles = re.findall(title_pattern, content, re.IGNORECASE)
                
                for title in titles[:5]:  # Check top 5 results
                    # Clean title
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    # Extract case name
                    case_name_match = re.search(r'([^,\[]+\s+v\.?\s+[^,\[]+)', title, re.IGNORECASE)
                    if not case_name_match:
                        continue
                    
                    canonical_name = case_name_match.group(1).strip()
                    
                    # FIX #56C: Validate name overlap
                    extracted_words = set(extracted_case_name.lower().split())
                    canonical_words = set(canonical_name.lower().split())
                    common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and', 'inc', 'inc.', 'llc', 'ltd', 'ltd.', 'co', 'co.', 'corp', 'corp.'}
                    extracted_words -= common_words
                    canonical_words -= common_words
                    
                    if not extracted_words:
                        continue
                    
                    overlap = len(extracted_words & canonical_words) / len(extracted_words)
                    
                    if overlap < 0.5:
                        logger.warning(f"⚠️  [FIX #57-SCHOLAR] Rejected - low overlap ({overlap:.0%}): '{canonical_name}'")
                        continue
                    
                    # Extract URL
                    url_pattern = rf'<a[^>]*href="([^"]+)"[^>]*>{re.escape(title)}'
                    url_match = re.search(url_pattern, content)
                    canonical_url = url_match.group(1) if url_match else search_url
                    
                    logger.info(f"✅ [FIX #57-SCHOLAR] Valid match: '{canonical_name}' (overlap: {overlap:.0%})")
                    return VerificationResult(
                        citation=citation,
                        verified=True,
                        canonical_name=canonical_name,
                        canonical_date=extracted_date,
                        canonical_url=canonical_url,
                        source="Google Scholar",
                        confidence=0.75,
                        method="google_scholar"
                    )
            
            logger.warning(f"⚠️  [FIX #57-SCHOLAR] No valid results found")
            return VerificationResult(citation=citation, error="No results in Google Scholar")
            
        except Exception as e:
            logger.error(f"❌ [FIX #57-SCHOLAR] Error: {e}")
            return VerificationResult(citation=citation, error=f"Google Scholar error: {e}")
    
    async def _verify_with_findlaw(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using FindLaw with strict validation."""
        # FIX #57: Integrate with Fix #56C validation
        logger.info(f"🔍 [FIX #57-FINDLAW] Verifying {citation} with FindLaw")
        
        if not extracted_case_name or extracted_case_name == "N/A" or len(extracted_case_name) < 10:
            logger.warning(f"⚠️  [FIX #57-FINDLAW] Skipping - no valid extracted name")
            return VerificationResult(citation=citation, error="No extracted name for validation")
        
        try:
            search_query = f"{citation} {extracted_case_name}"
            search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links
                case_link_pattern = r'<a[^>]*href="([^"]*court[^"]+)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    if citation.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Extract case name
                        case_name_match = re.search(r'([^,]+\s+v\.?\s+[^,]+)', link_text, re.IGNORECASE)
                        canonical_name = case_name_match.group(1).strip() if case_name_match else link_text.strip()
                        
                        # FIX #56C: Validate name overlap
                        extracted_words = set(extracted_case_name.lower().split())
                        canonical_words = set(canonical_name.lower().split())
                        common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and', 'inc', 'inc.', 'llc', 'ltd', 'ltd.', 'co', 'co.', 'corp', 'corp.'}
                        extracted_words -= common_words
                        canonical_words -= common_words
                        
                        if not extracted_words:
                            continue
                        
                        overlap = len(extracted_words & canonical_words) / len(extracted_words)
                        
                        if overlap < 0.5:
                            logger.warning(f"⚠️  [FIX #57-FINDLAW] Rejected - low overlap ({overlap:.0%}): '{canonical_name}'")
                            continue
                        
                        full_url = link_url if link_url.startswith('http') else f"https://caselaw.findlaw.com{link_url}"
                        
                        logger.info(f"✅ [FIX #57-FINDLAW] Valid match: '{canonical_name}' (overlap: {overlap:.0%})")
                        return VerificationResult(
                            citation=citation,
                            verified=True,
                            canonical_name=canonical_name,
                            canonical_date=extracted_date,
                            canonical_url=full_url,
                            source="FindLaw",
                            confidence=0.80,
                            method="findlaw_search"
                        )
            
            logger.warning(f"⚠️  [FIX #57-FINDLAW] No valid results found")
            return VerificationResult(citation=citation, error="No results in FindLaw")
            
        except Exception as e:
            logger.error(f"❌ [FIX #57-FINDLAW] Error: {e}")
            return VerificationResult(citation=citation, error=f"FindLaw error: {e}")
    
    async def _verify_with_bing(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
        """Verify using Bing search with strict validation."""
        # FIX #57: Integrate with Fix #56C validation  
        logger.info(f"🔍 [FIX #57-BING] Verifying {citation} with Bing")
        
        if not extracted_case_name or extracted_case_name == "N/A" or len(extracted_case_name) < 10:
            logger.warning(f"⚠️  [FIX #57-BING] Skipping - no valid extracted name")
            return VerificationResult(citation=citation, error="No extracted name for validation")
        
        try:
            search_query = f'"{citation}" "{extracted_case_name}" site:(.gov OR .edu OR justia.com OR findlaw.com)'
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(search_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                
                # Extract result titles and links
                result_pattern = r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
                matches = re.findall(result_pattern, content, re.IGNORECASE | re.DOTALL)
                
                for link_url, title in matches[:5]:  # Check top 5
                    # Clean title
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    # Extract case name
                    case_name_match = re.search(r'([^,\-|]+\s+v\.?\s+[^,\-|]+)', title, re.IGNORECASE)
                    if not case_name_match:
                        continue
                    
                    canonical_name = case_name_match.group(1).strip()
                    
                    # FIX #56C: Validate name overlap
                    extracted_words = set(extracted_case_name.lower().split())
                    canonical_words = set(canonical_name.lower().split())
                    common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and', 'inc', 'inc.', 'llc', 'ltd', 'ltd.', 'co', 'co.', 'corp', 'corp.'}
                    extracted_words -= common_words
                    canonical_words -= common_words
                    
                    if not extracted_words:
                        continue
                    
                    overlap = len(extracted_words & canonical_words) / len(extracted_words)
                    
                    if overlap < 0.5:
                        logger.warning(f"⚠️  [FIX #57-BING] Rejected - low overlap ({overlap:.0%}): '{canonical_name}'")
                        continue
                    
                    logger.info(f"✅ [FIX #57-BING] Valid match: '{canonical_name}' (overlap: {overlap:.0%})")
                    return VerificationResult(
                        citation=citation,
                        verified=True,
                        canonical_name=canonical_name,
                        canonical_date=extracted_date,
                        canonical_url=link_url,
                        source="Bing",
                        confidence=0.70,
                        method="bing_search"
                    )
            
            logger.warning(f"⚠️  [FIX #57-BING] No valid results found")
            return VerificationResult(citation=citation, error="No results in Bing")
            
        except Exception as e:
            logger.error(f"❌ [FIX #57-BING] Error: {e}")
            return VerificationResult(citation=citation, error=f"Bing error: {e}")
    
    def _calculate_confidence(
        self, 
        citation: str, 
        canonical_name: Optional[str], 
        extracted_case_name: Optional[str],
        canonical_date: Optional[str], 
        extracted_date: Optional[str]
    ) -> float:
        """Calculate confidence score for verification result."""
        confidence = 0.5  # Base confidence
        
        # Citation match (always required)
        if citation:
            confidence += 0.2
        
        # Case name validation
        if canonical_name and extracted_case_name:
            name_similarity = self._calculate_name_similarity(canonical_name, extracted_case_name)
            confidence += name_similarity * 0.2
        elif canonical_name:
            confidence += 0.1  # Some points for having canonical name
        
        # Date validation
        if canonical_date and extracted_date:
            if self._dates_match(canonical_date, extracted_date):
                confidence += 0.1
        elif canonical_date:
            confidence += 0.05  # Some points for having canonical date
        
        return min(1.0, confidence)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _dates_match(self, date1: str, date2: str) -> bool:
        """Check if two dates match (year-based comparison)."""
        if not date1 or not date2:
            return False
        
        # Extract years
        import re
        year1_match = re.search(r'(\d{4})', str(date1))
        year2_match = re.search(r'(\d{4})', str(date2))
        
        if year1_match and year2_match:
            return year1_match.group(1) == year2_match.group(1)
        
        return False
    
    def _find_best_search_result(self, results: List[Dict], citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str]) -> Optional[Dict]:
        """Find the best result from search API results."""
        # FIX #56C: Add strict validation to prevent wrong matches
        # Search results can contain unrelated cases that just mention the citation
        
        if not extracted_case_name or extracted_case_name == "N/A":
            logger.warning(f"⚠️  [FIX #56C] Skipping search validation - no extracted name for {citation}")
            return None
        
        best_result = None
        best_score = 0.0
        best_overlap = 0.0
        
        for result in results:
            canonical_name = result.get('caseName', '')
            
            # FIX #56C: Check name overlap BEFORE calculating confidence
            extracted_words = set(extracted_case_name.lower().split())
            canonical_words = set(canonical_name.lower().split())
            common_words = {'v', 'v.', 'vs', 'vs.', 'the', 'of', 'in', 'a', 'an', '&', 'and', 'inc', 'inc.', 'llc', 'ltd', 'ltd.', 'co', 'co.', 'corp', 'corp.'}
            extracted_words -= common_words
            canonical_words -= common_words
            
            if not extracted_words:
                continue
            
            overlap = len(extracted_words & canonical_words) / len(extracted_words)
            
            # FIX #64: Special validation for "State v. X" and criminal cases
            # Problem: "State v. M.Y.G." and "State v. Olsen" have high overlap (50%+) but are different cases
            # Solution: For criminal cases, require party names to match, not just "State v."
            is_criminal_case = False
            criminal_patterns = [
                r'\bstate\s+v\.?\s+',
                r'\bpeople\s+v\.?\s+',
                r'\bcommonwealth\s+v\.?\s+',
                r'\bunited\s+states\s+v\.?\s+',
                r'\bcity\s+of\s+\w+\s+v\.?\s+'
            ]
            
            for pattern in criminal_patterns:
                if re.search(pattern, extracted_case_name, re.IGNORECASE):
                    is_criminal_case = True
                    break
            
            if is_criminal_case:
                # For criminal cases, extract and compare the defendant/party names
                extracted_party = re.sub(r'^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+', '', extracted_case_name, flags=re.IGNORECASE).strip()
                canonical_party = re.sub(r'^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+', '', canonical_name, flags=re.IGNORECASE).strip()
                
                # Remove common suffixes and punctuation for better matching
                extracted_party = re.sub(r'[,\.].*$', '', extracted_party).strip().lower()
                canonical_party = re.sub(r'[,\.].*$', '', canonical_party).strip().lower()
                
                # Calculate similarity between party names
                if not extracted_party or not canonical_party:
                    logger.warning(f"⚠️  [FIX #64] Could not extract party names from '{extracted_case_name}' vs '{canonical_name}'")
                    continue
                
                party_similarity = self._calculate_name_similarity(extracted_party, canonical_party)
                
                # Require high similarity for criminal cases (different defendants = different cases!)
                if party_similarity < 0.7:
                    logger.warning(f"⚠️  [FIX #64] CRIMINAL CASE MISMATCH: '{extracted_party}' vs '{canonical_party}' (similarity: {party_similarity:.2f})")
                    logger.warning(f"   Full names: '{extracted_case_name}' vs '{canonical_name}'")
                    logger.warning(f"   Different defendants = different cases! Rejecting.")
                    continue
                
                logger.info(f"✅ [FIX #64] Criminal case party names match: '{extracted_party}' vs '{canonical_party}' (similarity: {party_similarity:.2f})")
            
            # FIX #56C: Require at least 50% word overlap (for non-criminal or after party validation)
            if overlap < 0.5:
                logger.warning(f"⚠️  [FIX #56C] Rejected search result - low overlap ({overlap:.0%}): '{canonical_name}' vs '{extracted_case_name}'")
                continue
            
            score = self._calculate_confidence(
                citation,
                canonical_name,
                extracted_case_name,
                result.get('dateFiled'),
                extracted_date
            )
            
            if score > best_score or (score == best_score and overlap > best_overlap):
                best_score = score
                best_overlap = overlap
                best_result = result
                logger.info(f"✅ [FIX #56C] Valid search result: '{canonical_name}' (overlap: {overlap:.0%}, confidence: {score:.0%})")
        
        if best_result is None:
            logger.warning(f"⚠️  [FIX #56C] No search results passed validation for {citation}")
        
        return best_result if best_score > 0.5 else None
    
    async def _enforce_rate_limit(self, source: VerificationSource):
        """Enforce rate limiting for API calls."""
        if source not in self.rate_limits:
            return
        
        rate_info = self.rate_limits[source]
        calls_per_minute = rate_info['calls_per_minute']
        last_call = rate_info['last_call']
        
        current_time = time.time()
        time_since_last = current_time - last_call
        min_interval = 60.0 / calls_per_minute
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.rate_limits[source]['last_call'] = time.time()

# Global singleton instance
_master_verifier = None

def get_master_verifier() -> UnifiedVerificationMaster:
    """Get the singleton master verifier instance."""
    global _master_verifier
    if _master_verifier is None:
        _master_verifier = UnifiedVerificationMaster()
    return _master_verifier

async def verify_citation_unified_master(
    citation: str,
    extracted_case_name: Optional[str] = None,
    extracted_date: Optional[str] = None,
    timeout: float = 30.0,
    enable_fallback: bool = True
) -> Dict[str, Any]:
    """
    THE SINGLE, UNIFIED VERIFICATION FUNCTION
    
    This function replaces ALL 80+ duplicate verification functions.
    Use this instead of:
    - verify_citation()
    - verify_citation_enhanced()
    - _verify_with_courtlistener()
    - verify_citations_batch()
    - All other duplicate verification functions
    
    Returns:
        Dictionary with verification results
    """
    # EMERGENCY FIX: Check if verification is disabled
    if not get_bool_config_value('ENABLE_VERIFICATION', True):
        logger.info(f"⚠️ Verification disabled by config - skipping {citation}")
        return {
            'citation': citation,
            'verified': False,
            'canonical_name': extracted_case_name,
            'canonical_date': extracted_date,
            'canonical_url': None,
            'url': None,
            'source': 'disabled',
            'confidence': 0.0,
            'method': 'disabled',
            'raw_data': {},
            'warnings': ['Verification disabled in configuration'],
            'error': None
        }
    
    verifier = get_master_verifier()
    result = await verifier.verify_citation(citation, extracted_case_name, extracted_date, timeout, enable_fallback)
    
    return {
        'citation': result.citation,
        'verified': result.verified,
        'canonical_name': result.canonical_name,
        'canonical_date': result.canonical_date,
        'canonical_url': result.canonical_url,
        'url': result.canonical_url,  # Backward compatibility
        'source': result.source,
        'confidence': result.confidence,
        'method': result.method,
        'raw_data': result.raw_data,
        'warnings': result.warnings or [],
        'error': result.error
    }

def verify_citation_unified_master_sync(
    citation: str,
    extracted_case_name: Optional[str] = None,
    extracted_date: Optional[str] = None,
    timeout: float = 30.0,
    enable_fallback: bool = True
) -> Dict[str, Any]:
    """
    Synchronous version of the unified verification master function.
    
    This provides backward compatibility for synchronous callers.
    """
    # EMERGENCY FIX: Check if verification is disabled
    if not get_bool_config_value('ENABLE_VERIFICATION', True):
        logger.info(f"⚠️ Verification disabled by config - skipping {citation}")
        return {
            'citation': citation,
            'verified': False,
            'canonical_name': extracted_case_name,
            'canonical_date': extracted_date,
            'canonical_url': None,
            'url': None,
            'source': 'disabled',
            'confidence': 0.0,
            'method': 'disabled',
            'raw_data': {},
            'warnings': ['Verification disabled in configuration'],
            'error': None
        }
    
    verifier = get_master_verifier()
    result = verifier.verify_citation_sync(citation, extracted_case_name, extracted_date, timeout, enable_fallback)
    
    return {
        'citation': result.citation,
        'verified': result.verified,
        'canonical_name': result.canonical_name,
        'canonical_date': result.canonical_date,
        'canonical_url': result.canonical_url,
        'url': result.canonical_url,  # Backward compatibility
        'source': result.source,
        'confidence': result.confidence,
        'method': result.method,
        'raw_data': result.raw_data,
        'warnings': result.warnings or [],
        'error': result.error
    }












