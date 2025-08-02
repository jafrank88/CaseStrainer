"""
Citation Verifier

This module contains citation verification logic using various sources
including CourtListener API and other verification methods.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from src.models import CitationResult
from src.citation_types import CitationList, VerificationResult
from src.citation_utils import (
    get_extracted_case_name, get_unverified_citations, 
    apply_verification_result, normalize_citation
)

logger = logging.getLogger(__name__)

# Import verification functions
from src.courtlistener_verification import verify_with_courtlistener
from src.citation_verification import (
    verify_citations_with_canonical_service,
    verify_citations_with_legal_websearch
)

class CitationVerifier:
    """Citation verification functionality."""
    
    def __init__(self, courtlistener_api_key: Optional[str] = None):
        self.courtlistener_api_key = courtlistener_api_key
        self._init_landmark_cases()
    
    def _init_landmark_cases(self):
        """Initialize known landmark cases for quick verification."""
        self.landmark_cases = {
            "410 U.S. 113": {
                "case_name": "Roe v. Wade",
                "date": "1973",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/"
            },
            "347 U.S. 483": {
                "case_name": "Brown v. Board of Education",
                "date": "1954", 
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
            },
            "5 U.S. 137": {
                "case_name": "Marbury v. Madison",
                "date": "1803",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/84759/marbury-v-madison/"
            },
        }
    
    def verify_with_landmark_cases(self, citation: str) -> VerificationResult:
        """Verify a citation against known landmark cases."""
        if not citation:
            return {"verified": False, "source": "Landmark Cases", "error": "Empty citation"}
        
        # Normalize citation for lookup
        normalized = normalize_citation(citation)
        if normalized in self.landmark_cases:
            case_info = self.landmark_cases[normalized]
            return {
                "verified": True,
                "case_name": case_info["case_name"],
                "canonical_name": case_info["case_name"],
                "canonical_date": case_info["date"],
                "url": case_info["url"],
                "source": "Landmark Cases",
                "confidence": 0.9
            }
        
        return {
            "verified": False,
            "source": "Landmark Cases",
            "error": "Citation not found in landmark cases"
        }
    
    def verify_citation_with_courtlistener(self, citation: CitationResult) -> bool:
        """Verify a citation using CourtListener API."""
        if not citation or not self.courtlistener_api_key:
            return False
        
        extracted_case_name = get_extracted_case_name(citation)
        
        try:
            verify_result = verify_with_courtlistener(
                self.courtlistener_api_key, 
                citation.citation, 
                extracted_case_name
            )
            
            return apply_verification_result(citation, verify_result, "CourtListener")
            
        except Exception as e:
            logger.error(f"Error verifying citation with CourtListener: {e}")
            return False
    
    def verify_citations_with_canonical_service(self, citations: CitationList) -> None:
        """Verify citations using canonical service."""
        if not citations:
            return
        
        try:
            verify_citations_with_canonical_service(citations)
        except Exception as e:
            logger.error(f"Error verifying citations with canonical service: {e}")
    
    async def verify_citations_with_legal_websearch(self, citations: CitationList) -> None:
        """Verify citations using legal web search."""
        if not citations:
            return
        
        try:
            await verify_citations_with_legal_websearch(citations)
        except Exception as e:
            logger.error(f"Error verifying citations with legal web search: {e}")
    
    async def verify_citations(self, citations: CitationList, text: Optional[str] = None) -> CitationList:
        """
        Verify citations asynchronously using multiple verification methods.
        
        Args:
            citations: List of CitationResult objects to verify
            text: Optional original text for context
            
        Returns:
            List of verified CitationResult objects
        """
        if not citations:
            return citations
            
        logger.info(f"[VERIFY_CITATIONS] ENTERED with {len(citations)} citations")
        
        # Step 1: Try CourtListener individual verification
        logger.info("[VERIFY_CITATIONS] Step 1: CourtListener individual verification")
        for citation in get_unverified_citations(citations):
            self.verify_citation_with_courtlistener(citation)
        
        # Step 2: Try canonical service for unverified citations
        unverified = get_unverified_citations(citations)
        logger.info(f"[VERIFY_CITATIONS] Step 2: {len(unverified)} unverified citations after CourtListener")
        if unverified:
            self.verify_citations_with_canonical_service(unverified)
        
        # Step 3: Try legal websearch for still unverified citations
        still_unverified = get_unverified_citations(citations)
        logger.info(f"[VERIFY_CITATIONS] Step 3: {len(still_unverified)} still unverified citations after canonical service")
        if still_unverified:
            await self.verify_citations_with_legal_websearch(still_unverified)
        
        # Step 4: Mark remaining as fallback
        final_unverified = [c for c in citations if not getattr(c, 'verified', False)]
        logger.info(f"[VERIFY_CITATIONS] Step 4: {len(final_unverified)} citations marked as fallback")
        for citation in citations:
            if not getattr(citation, 'verified', False):
                citation.source = 'fallback'
        
        verified_count = len([c for c in citations if getattr(c, 'verified', False)])
        logger.info(f"[VERIFY_CITATIONS] COMPLETED - {verified_count} verified citations")
        return citations
    
    def verify_single_citation(self, citation: CitationResult, apply_state_filter: bool = True) -> bool:
        """Verify a single citation using available methods."""
        if not citation:
            return False
        
        # Try landmark cases first (fastest)
        landmark_result = self.verify_with_landmark_cases(citation.citation)
        if landmark_result.get("verified"):
            return apply_verification_result(citation, landmark_result, "Landmark Cases")
        
        # Try CourtListener
        if self.courtlistener_api_key:
            return self.verify_citation_with_courtlistener(citation)
        
        return False
    
    def validate_verification_result(self, citation: CitationResult, source: str) -> Dict[str, Any]:
        """Validate a verification result for a citation."""
        if not citation:
            return {"valid": False, "error": "No citation provided"}
        
        validation_result = {
            "valid": True,
            "source": source,
            "issues": []
        }
        
        # Check if citation has required fields
        if not citation.citation:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing citation text")
        
        # Check if verification was successful
        if getattr(citation, 'verified', False):
            if not citation.canonical_name:
                validation_result["issues"].append("Verified but missing canonical name")
            
            if not citation.canonical_date:
                validation_result["issues"].append("Verified but missing canonical date")
        else:
            validation_result["issues"].append("Citation not verified")
        
        return validation_result 