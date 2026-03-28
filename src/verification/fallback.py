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

from .sources import JustiaVerifier, CornellLIIVerifier, OpenJuristVerifier, GoogleScholarVerifier, FindLawVerifier, CaseMineVerifier
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
            "casemine": CaseMineVerifier(self.session),
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
                            tolerance=1
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

    async def verify_name_and_date_only(
        self,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Last-resort verification using only case name and date (no citation).
        Tries Google Scholar and FindLaw with query like "Webber v. Zimmerlein 2025".
        """
        name = (extracted_case_name or "").strip()
        if not name or name.upper() == "N/A":
            return {"verified": False, "error": "No case name for name+date-only search"}
        year = None
        if extracted_date:
            m = re.search(r"(19|20)\d{2}", str(extracted_date))
            if m:
                year = m.group(0)
        if not year:
            return {"verified": False, "error": "No year for name+date-only search"}
        # Allow "Case v. Defendant" or single-party names (e.g. "Zimmerlein", "Zimmerlein, 2025") when we have a year
        has_v = (" v" in name.lower()) or (" v." in name.lower())
        name_for_query = name
        if not has_v:
            # Strip trailing ", YYYY" or " YYYY" so "Zimmerlein, 2025" is treated as "Zimmerlein"
            name_for_query = re.sub(r",?\s*(19|20)\d{2}\s*$", "", name).strip() or name
            tokens = [t for t in re.sub(r",?\s+", " ", name_for_query).strip().split() if t]
            # Reject long prose; allow 1-4 word party names
            if len(tokens) > 4 or not tokens:
                return {"verified": False, "error": "Case name too weak for name+date-only search"}
            # Allow if no token is a 4-digit year (avoid "Smith 2024" as name)
            if any(re.search(r"^(19|20)\d{2}$", t) for t in tokens):
                return {"verified": False, "error": "Case name too weak for name+date-only search"}

        query = f"{name_for_query} {year}"
        time_per_source = timeout / 2.0 if timeout else 5.0  # Scholar and FindLaw
        sources = ["google_scholar", "findlaw"]

        for source_name in sources:
            try:
                if self._is_source_cooled_down(source_name):
                    continue
                verifier = self.verifiers.get(source_name)
                if not verifier:
                    continue
                # Scholar: search by query string (citation param is the search query)
                # FindLaw: pass year as citation so search_query = name + " " + citation
                if source_name == "google_scholar":
                    result = await verifier.verify(
                        citation=query,
                        extracted_case_name=name,
                        timeout=time_per_source,
                    )
                else:
                    result = await verifier.verify(
                        citation=year,
                        extracted_case_name=name,
                        timeout=time_per_source,
                    )
                if result.get("verified"):
                    canonical_date = result.get("canonical_date")
                    if canonical_date:
                        is_valid, _ = validate_year_match(year, canonical_date, tolerance=1)
                        if not is_valid:
                            continue
                    result["method"] = f"fallback_{source_name}_name_date_only"
                    logger.info(
                        f"[FALLBACK] Name+date-only verified via {source_name}: '{name}' {year}"
                    )
                    return result
            except Exception as e:
                logger.debug(f"Name+date-only {source_name} failed: {e}")
                continue
        return {"verified": False, "error": "Name+date-only search found no match"}

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
        # CaseMine second - good coverage, fast response (~0.4s)
        sources = ["google_scholar", "casemine"]
        
        # Supreme Court citations: Cornell LII and OpenJurist work for U.S. Reports
        if is_supreme_court_citation(citation):
            sources.extend(["cornell_lii", "openjurist", "findlaw", "justia"])
        elif is_federal_citation(citation):
            sources.extend(["findlaw", "justia", "cornell_lii"])
        else:
            sources.extend(["findlaw", "justia"])
        
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
