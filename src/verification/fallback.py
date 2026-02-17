"""
Fallback Verification Module
=============================

Fallback verification using multiple external sources.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

from .sources import JustiaVerifier, CornellLIIVerifier, OpenJuristVerifier, GoogleScholarVerifier, FindLawVerifier
from .utils import is_federal_citation, is_supreme_court_citation, validate_year_match

logger = logging.getLogger(__name__)


class VerificationSource(Enum):
    """Enumeration of verification sources in priority order."""
    COURTLISTENER_LOOKUP = "courtlistener_lookup"
    COURTLISTENER_SEARCH = "courtlistener_search"
    CASEMINE = "casemine"
    LEAGLE = "leagle"
    VLEX = "vlex"
    LAW_RESOURCE = "law_resource"
    JUSTIA = "justia"
    OPENJURIST = "openjurist"
    CORNELL_LII = "cornell_lii"
    GOOGLE_SCHOLAR = "google_scholar"
    BING = "bing"
    FINDLAW = "findlaw"


class FallbackVerifier:
    """Fallback verification using multiple external sources."""
    
    def __init__(self, session=None, fast_mode: bool = True):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
        self.fast_mode = fast_mode
        self._init_verifiers()
    
    def _init_verifiers(self):
        """Initialize source verifiers."""
        self.verifiers = {
            "google_scholar": GoogleScholarVerifier(self.session),
            "findlaw": FindLawVerifier(self.session),
            "justia": JustiaVerifier(self.session),
            "cornell_lii": CornellLIIVerifier(self.session),
            "openjurist": OpenJuristVerifier(self.session),
        }
    
    async def verify(
        self, 
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Verify citation using fallback sources.
        
        Args:
            citation: Citation to verify
            extracted_case_name: Case name from document
            extracted_date: Date from document
            timeout: Maximum time to spend
            
        Returns:
            Verification result dict
        """
        # Determine which sources to try based on citation type
        sources = self._select_sources(citation)
        
        # Calculate time per source
        time_per_source = timeout / len(sources) if sources else 0
        if time_per_source <= 0:
            time_per_source = 0.5
        
        # Try each source
        for source_name in sources:
            try:
                verifier = self.verifiers.get(source_name)
                if not verifier:
                    continue
                
                result = await verifier.verify(
                    citation, 
                    extracted_case_name, 
                    time_per_source
                )
                
                if result.get("verified"):
                    # Validate year match
                    canonical_date = result.get("canonical_date")
                    if extracted_date and canonical_date:
                        is_valid, year_diff = validate_year_match(
                            extracted_date, 
                            canonical_date, 
                            tolerance=0
                        )
                        if not is_valid:
                            logger.warning(
                                f"Year mismatch for {citation}: "
                                f"extracted={extracted_date}, canonical={canonical_date}"
                            )
                            continue
                    
                    result["method"] = f"fallback_{source_name}"
                    return result
                
            except Exception as e:
                logger.debug(f"Fallback source {source_name} failed: {e}")
                continue
        
        return {"verified": False, "error": "All fallback sources failed"}
    
    def _select_sources(self, citation: str) -> List[str]:
        """Select appropriate sources based on citation type."""
        # Google Scholar first - best hit rate across all citation types
        sources = ["google_scholar"]
        
        # Supreme Court citations prioritize Cornell LII
        if is_supreme_court_citation(citation):
            sources.extend(["findlaw", "cornell_lii", "justia", "openjurist"])
        elif is_federal_citation(citation):
            sources.extend(["findlaw", "justia", "cornell_lii", "openjurist"])
        else:
            sources.extend(["findlaw", "justia", "openjurist"])
        
        return sources


async def verify_with_fallback_sources(
    citation: str,
    extracted_case_name: Optional[str] = None,
    extracted_date: Optional[str] = None,
    session=None,
    timeout: float = 30.0,
    fast_mode: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for fallback verification.
    
    Args:
        citation: Citation to verify
        extracted_case_name: Case name from document
        extracted_date: Date from document
        session: HTTP session
        timeout: Maximum time
        fast_mode: Use fast mode (fewer sources)
        
    Returns:
        Verification result
    """
    verifier = FallbackVerifier(session, fast_mode)
    return await verifier.verify(
        citation, 
        extracted_case_name, 
        extracted_date, 
        timeout
    )
