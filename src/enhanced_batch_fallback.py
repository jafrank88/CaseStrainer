#!/usr/bin/env python3
"""
Enhanced batch fallback verification that can handle more unverified citations
"""

import asyncio
import logging
from typing import List, Optional
from src.unified_verification_master import UnifiedVerificationMaster
from src.schemas.verification import VerificationResult

logger = logging.getLogger(__name__)

async def enhanced_batch_fallback(
    verifier: UnifiedVerificationMaster,
    citations: List[str],
    results: List[VerificationResult],
    case_names: Optional[List[str]] = None,
    dates: Optional[List[str]] = None,
    max_fallback_citations: int = 50,
    timeout_per_citation: float = 5.0,
) -> List[VerificationResult]:
    """
    Enhanced fallback verification for batch processing.
    
    Instead of limiting to 5 citations, this:
    1. Prioritizes citations with case names (higher success rate)
    2. Uses parallel processing with semaphore to limit concurrent requests
    3. Tries multiple sources in order of likelihood of success
    """
    
    # Find unverified citations
    unverified_indices = []
    for i, result in enumerate(results):
        if not result.verified:
            unverified_indices.append(i)
    
    if not unverified_indices:
        return results
    
    logger.info(f"🔄 ENHANCED FALLBACK: {len(unverified_indices)} citations need fallback verification")
    
    # Prioritize citations with case names (higher success rate)
    def has_case_name(idx):
        return case_names and idx < len(case_names) and case_names[idx] and case_names[idx] != "N/A"
    
    # Sort: citations with case names first
    unverified_indices.sort(key=has_case_name, reverse=True)
    
    # Limit to max_fallback_citations
    if len(unverified_indices) > max_fallback_citations:
        logger.warning(f"⚠️ Limiting fallback to {max_fallback_citations} of {len(unverified_indices)} unverified citations")
        unverified_indices = unverified_indices[:max_fallback_citations]
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent fallback requests
    
    async def verify_with_fallback(idx: int) -> tuple[int, Optional[VerificationResult]]:
        """Verify a single citation with fallback sources"""
        async with semaphore:
            citation = citations[idx]
            extracted_name = case_names[idx] if case_names and idx < len(case_names) else None
            extracted_date = dates[idx] if dates and idx < len(dates) else None
            
            # Skip obviously invalid citations
            if verifier._is_obviously_invalid_citation(citation):
                return idx, None
            
            # Try fallback sources in order of preference
            # 1. CaseMine (highest success for recent cases)
            # 2. VLex (if case name available)
            # 3. Justia (direct URL)
            # 4. Law Resource.org (for F.2d/F.3d/F.4th)
            
            sources_to_try = []
            
            # Always try CaseMine first
            sources_to_try.append(("CaseMine", verifier._verify_with_casemine))
            
            # Add VLex if we have a case name
            if extracted_name and extracted_name != "N/A":
                sources_to_try.append(("VLex", verifier._verify_with_vlex))
            
            # Add Justia
            sources_to_try.append(("Justia", verifier._verify_with_justia))
            
            # Add Law Resource for Federal citations
            if any(x in citation for x in ["F.2d", "F.3d", "F.4th"]):
                sources_to_try.append(("Law_Resource", verifier._verify_with_law_resource))
            
            # Try each source with short timeout
            for source_name, verify_func in sources_to_try:
                try:
                    result = await verify_func(
                        citation=citation,
                        extracted_case_name=extracted_name,
                        extracted_date=extracted_date,
                        timeout=timeout_per_citation
                    )
                    
                    if result.verified:
                        logger.info(f"✅ FALLBACK SUCCESS: {citation} verified via {source_name}")
                        return idx, result
                    elif getattr(result, "possible_match", False):
                        logger.info(f"🔶 FALLBACK POSSIBLE: {citation} possible match via {source_name}")
                        return idx, result
                        
                except Exception as e:
                    logger.debug(f"Fallback {source_name} failed for {citation}: {e}")
                    continue
            
            return idx, None
    
    # Run fallback verifications in parallel
    tasks = [verify_with_fallback(idx) for idx in unverified_indices]
    fallback_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Update results
    fallback_success_count = 0
    for result in fallback_results:
        if isinstance(result, Exception):
            logger.error(f"Fallback task failed: {result}")
            continue
            
        idx, verification_result = result
        if verification_result:
            results[idx] = verification_result
            if verification_result.verified:
                fallback_success_count += 1
    
    logger.info(f"✅ ENHANCED FALLBACK COMPLETE: {fallback_success_count}/{len(unverified_indices)} citations verified")
    
    return results


# Example usage in batch verification
async def verify_citations_batch_enhanced(
    verifier: UnifiedVerificationMaster,
    citations: List[str],
    extracted_case_names: Optional[List[str]] = None,
    extracted_dates: Optional[List[str]] = None,
    enable_fallback: bool = True,
    max_fallback_citations: int = 50,
) -> List[VerificationResult]:
    """
    Enhanced batch verification with better fallback support.
    """
    # First run CourtListener batch lookup
    results = await verifier.verify_citations_batch(
        citations=citations,
        extracted_case_names=extracted_case_names,
        extracted_dates=extracted_dates
    )
    
    # Then run enhanced fallback for unverified citations
    if enable_fallback:
        results = await enhanced_batch_fallback(
            verifier=verifier,
            citations=citations,
            results=results,
            case_names=extracted_case_names,
            dates=extracted_dates,
            max_fallback_citations=max_fallback_citations,
            timeout_per_citation=5.0
        )
    
    return results
