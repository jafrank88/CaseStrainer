"""
Fallback Verification Module
=============================

Fallback verification using multiple external sources.
"""

import asyncio
import logging
import time
import re
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
        # Cool down sources that are actively rate-limiting/captcha blocking.
        self._source_cooldowns: Dict[str, float] = {}
        self._init_verifiers()

    def _is_source_cooled_down(self, source_name: str) -> bool:
        cooldown_until = self._source_cooldowns.get(source_name, 0.0)
        return cooldown_until > time.time()

    def _mark_source_rate_limited(self, source_name: str, error: str):
        err = (error or "").lower()
        # Detect anti-automation / rate-limit signals and back off that source.
        rate_limit_signals = (
            "rate limit",
            "rate-limited",
            "captcha",
            "unusual traffic",
            "too many requests",
            "http 429",
            "forbidden",
            "access denied",
            "blocked",
            "automated",
        )
        if any(sig in err for sig in rate_limit_signals):
            cooldown_seconds = 600.0  # 10 minutes
            until = time.time() + cooldown_seconds
            self._source_cooldowns[source_name] = until
            logger.warning(
                f"[FALLBACK-COOLDOWN] Source '{source_name}' cooled down for "
                f"{int(cooldown_seconds)}s after error: {error}"
            )
    
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
        sources = self._select_sources(citation, extracted_case_name)
        
        # Calculate time per source
        time_per_source = timeout / len(sources) if sources else 0
        if time_per_source <= 0:
            time_per_source = 0.5
        
        # Try each source
        attempted_any_source = False
        for source_name in sources:
            try:
                if self._is_source_cooled_down(source_name):
                    continue
                verifier = self.verifiers.get(source_name)
                if not verifier:
                    continue
                attempted_any_source = True
                
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
                self._mark_source_rate_limited(source_name, str(result.get("error", "")))
                
            except Exception as e:
                logger.debug(f"Fallback source {source_name} failed: {e}")
                self._mark_source_rate_limited(source_name, str(e))
                continue

        if not attempted_any_source:
            return {"verified": False, "error": "All fallback sources temporarily rate-limited"}
        return {"verified": False, "error": "All fallback sources failed"}
    
    def _select_sources(self, citation: str, extracted_case_name: Optional[str] = None) -> List[str]:
        """Select appropriate sources based on citation type."""
        citation_text = str(citation or "")
        name_text = str(extracted_case_name or "").strip()
        name_tokens = [t for t in name_text.replace(".", " ").split() if t]
        has_v = (" v" in name_text.lower()) or (" v." in name_text.lower())
        weak_name = (not name_text) or (name_text.upper() == "N/A") or (len(name_tokens) < 3) or (not has_v)
        is_wl = bool(re.search(r"\b\d{4}\s+WL\s+\d+\b", citation_text, re.IGNORECASE))

        # WL-only citation-first lane: when case name is weak, avoid broad multi-source
        # crawling that can contaminate matches. Scholar can still resolve by citation text.
        if is_wl and weak_name:
            return ["google_scholar"]

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
