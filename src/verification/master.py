"""
Unified Verification Master (Modular)
======================================

Main verification class using modular components.
"""

import asyncio
import logging
import time
import re
from typing import Dict, Any, Optional, List, Callable, Tuple
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
from .known_citations import _lookup_known_federal, _lookup_known_slip
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
        """Initialize the master verification engine. API key comes from env via config (COURTLISTENER_API_KEY)."""
        # Single source: env -> config. Used for both citation-lookup and search APIs.
        self.api_key = (api_key or COURTLISTENER_API_KEY) or ""
        # CRITICAL FIX: Create a requests.Session when none is provided
        # Without this, all verifiers get session=None and every HTTP call
        # fails with AttributeError: 'NoneType' object has no attribute 'post'
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
            logger.info("[VERIFICATION-MASTER] Created default requests.Session (none was provided)")
        self.session = session
        self.fast_verification = fast_verification
        
        # Citation-lookup (batch + single) and search API all use the same key from config/env
        self.courtlistener = CourtListenerVerifier(self.api_key, self.session)
        self.fallback = FallbackVerifier(self.session, fast_verification)
        self.batch_verifier = BatchVerifier(self.api_key, self.session)
        
        if self.api_key:
            logger.info("[VERIFICATION-MASTER] Using COURTLISTENER_API_KEY from config (env) for citation-lookup and search APIs")
        else:
            logger.warning("[VERIFICATION-MASTER] COURTLISTENER_API_KEY not set (check env/config); citation-lookup and search will return unverified")

    @staticmethod
    def _citation_core_key(text: str) -> str:
        s = str(text or "")
        m = re.search(r"\b((?:17|18|19|20)\d{2})\s*(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s*(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"{m.group(1)} {m.group(2).lower()} {m.group(3)}"
        m = re.search(
            r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?|Tenn\.?)\s+\d+\b",
            s,
            re.IGNORECASE,
        )
        if m:
            return re.sub(r"\s+", " ", m.group(0).strip()).lower()
        # Normalize state reporter abbreviations for gate comparison (e.g. 19 Wn. App. 2d 113 vs 19 Wash. App. 2d 113)
        s = re.sub(r"\bWn\.?\s*", "Wash. ", s, flags=re.IGNORECASE)
        s = re.sub(r"\bWash\.?\s*", "Wash. ", s, flags=re.IGNORECASE)
        # Normalize P.3d/P.2d spacing (e.g. "P. 3d" vs "P.3d")
        s = re.sub(r"\bP\.\s*3d\b", "P.3d", s, flags=re.IGNORECASE)
        s = re.sub(r"\bP\.\s*2d\b", "P.2d", s, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", s.strip()).lower()

    def _candidate_citation_text(self, candidate: Dict[str, Any]) -> str:
        """Best-effort extraction of candidate citation text from a verifier payload."""
        if not isinstance(candidate, dict):
            return ""
        direct = candidate.get("candidate_citation") or candidate.get("citation") or candidate.get("short_citation")
        if direct:
            return str(direct)
        cits = candidate.get("citations") or candidate.get("cites") or candidate.get("citations_text")
        if isinstance(cits, list):
            for item in cits:
                if item:
                    return str(item)
        if isinstance(cits, str):
            return cits
        return ""

    def _evaluate_two_point_gate(
        self,
        submitted_citation: str,
        extracted_case_name: Optional[str],
        extracted_date: Optional[str],
        candidate: Dict[str, Any],
    ) -> str:
        """
        Evaluate candidate against two-point gate. Returns:
          "accept" - strong match (>75% name similarity + year): treat as verified
          "possible_match" - weak match: 50-75% similarity, or year correct + canonical_url with low name overlap.
            Not verified; expose canonical URL for display as probable match (below unverified, above verified).
          "reject" - insufficient match
        """
        source = str(candidate.get("source") or "")
        use_loose_gate = bool(source and "CourtListener" in source)
        extracted_name_text = str(extracted_case_name or "").strip()
        name_tokens = [t for t in extracted_name_text.replace(".", " ").split() if t]
        has_strong_name = (
            bool(extracted_name_text)
            and extracted_name_text.upper() != "N/A"
            and (" v" in extracted_name_text.lower())
            and len(name_tokens) >= 3
        )
        has_extracted_year = bool(extracted_date)

        # When extraction metadata is weak/missing, do not block verification here.
        if not has_strong_name and not has_extracted_year:
            return "accept"

        candidate_citation = self._candidate_citation_text(candidate)
        citation_match = bool(candidate_citation) and (
            self._citation_core_key(submitted_citation) == self._citation_core_key(candidate_citation)
        )

        candidate_name = str(candidate.get("canonical_name") or "")
        name_overlap = calculate_case_name_overlap(str(extracted_case_name or ""), candidate_name)

        year_match = False
        year_tolerance = 1
        if extracted_date and candidate.get("canonical_date"):
            year_match, _ = validate_year_match(str(extracted_date), str(candidate.get("canonical_date")), tolerance=year_tolerance)
        elif not candidate.get("canonical_date"):
            year_match = True

        # Citation core match: accept
        if citation_match:
            return "accept"

        # First-party surname shortcut: accept when year matches
        if has_strong_name and year_match:
            ecn_parts = re.split(r"\s+v\.?\s+", extracted_name_text, maxsplit=1)
            if ecn_parts:
                first_party_words = ecn_parts[0].strip().split()
                if first_party_words:
                    surname = first_party_words[-1].lower()
                    if len(surname) >= 3 and surname in candidate_name.lower():
                        return "accept"

        # Name + year: tier by overlap
        # >75%: probable match (accept/verified)
        # 50-75%: possible match (not verified, show canonical URL)
        # <50%: year correct + canonical_url -> possible_match (weak match, not verified)
        if year_match and candidate_name and extracted_name_text:
            if name_overlap > 0.75:
                return "accept"
            if 0.50 <= name_overlap <= 0.75:
                return "possible_match"
            # <50%: year correct + canonical_url -> possible_match (weak name, not verified)
            if name_overlap < 0.50:
                if candidate.get("canonical_url"):
                    return "possible_match"
                stop = {"v", "the", "of", "and", "in", "for", "on", "at", "to", "a", "an", "re"}
                ext_tokens = [
                    t for t in extracted_name_text.replace(".", " ").split()
                    if len(t) >= 3 and t.lower() not in stop
                ]
                for t in ext_tokens:
                    if t.lower() in candidate_name.lower():
                        return "possible_match"
                return "reject"

        # Year correct + canonical_url but weak/missing name: possible_match (not verified)
        if year_match and candidate.get("canonical_url"):
            return "possible_match"

        return "reject"

    def _passes_two_point_gate(
        self,
        submitted_citation: str,
        extracted_case_name: Optional[str],
        extracted_date: Optional[str],
        candidate: Dict[str, Any],
    ) -> bool:
        """True when gate returns accept (probable match)."""
        return self._evaluate_two_point_gate(submitted_citation, extracted_case_name, extracted_date, candidate) == "accept"
    
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
        
        Strategy (in order):
        1. Check cache
        2. Known federal/slip table (small set of frequently misresolved cites; skip if not found)
        3. Validate citation format
        4. CourtListener lookup (main API)
        5. CourtListener search fallback (by case name)
        6. Fallback sources (Justia, Cornell LII, OpenJurist) if enabled
        
        Citations not in the table are verified via CourtListener and fallbacks only.
        
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

        # Known federal citation (exact match) or known slip (volume+year + name match)
        known_federal = _lookup_known_federal(citation)
        if known_federal:
            logger.info(f"[KNOWN-FEDERAL] Resolved '{citation}'")
            cache.set(citation, known_federal)
            return VerificationResult(
                citation=citation,
                verified=True,
                canonical_name=known_federal.get("canonical_name"),
                canonical_date=known_federal.get("canonical_date") or known_federal.get("canonical_year"),
                canonical_url=known_federal.get("canonical_url"),
                source="known_federal",
                confidence=1.0,
                method="known_federal",
            )
        known_slip = _lookup_known_slip(citation, extracted_case_name, extracted_date)
        if known_slip:
            logger.info(f"[KNOWN-SLIP] Resolved '{citation}' -> {known_slip.get('canonical_name')}")
            cache.set(citation, known_slip)
            return VerificationResult(
                citation=citation,
                verified=True,
                canonical_name=known_slip.get("canonical_name"),
                canonical_date=known_slip.get("canonical_date"),
                canonical_url=known_slip.get("canonical_url"),
                source="known_slip",
                confidence=1.0,
                method="known_slip",
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
        if time.time() - start_time < timeout:
            logger.debug(f"[VERIFY] Trying CL search fallback for '{citation}'")
            search_result = await cl_search_fallback(
                self.session, self.api_key, citation,
                extracted_case_name, extracted_date,
                timeout - (time.time() - start_time)
            )
            if search_result.get("verified"):
                gate_result = self._evaluate_two_point_gate(citation, extracted_case_name, extracted_date, search_result)
                candidate_url = search_result.get("canonical_url")
                if gate_result == "accept":
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
                if gate_result == "possible_match" and candidate_url:
                    logger.info(
                        f"[GATE-POSSIBLE] CL search possible match (50-75% similarity): '{citation}' -> "
                        f"'{search_result.get('canonical_name')}'"
                    )
                    return VerificationResult(
                        citation=citation,
                        verified=False,
                        canonical_name=search_result.get("canonical_name"),
                        canonical_date=search_result.get("canonical_date"),
                        canonical_url=candidate_url,
                        method="courtlistener_search_possible_match",
                        possible_match=True,
                        source=search_result.get("source", "CourtListener-Search"),
                        confidence=0.7,
                    )
                logger.warning(
                    f"[GATE-REJECT] CL search rejected for '{citation}': "
                    f"candidate='{search_result.get('canonical_name')}', date='{search_result.get('canonical_date')}'"
                )
                return VerificationResult(
                    citation=citation,
                    verified=False,
                    canonical_name=search_result.get("canonical_name") if candidate_url else None,
                    canonical_date=search_result.get("canonical_date") if candidate_url else None,
                    canonical_url=candidate_url,
                    error="Verification rejected by strict citation/year gate",
                    method="courtlistener_search_gate_reject",
                    possible_match=bool(candidate_url),
                    source=search_result.get("source", "CourtListener-Search"),
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
                gate_result = self._evaluate_two_point_gate(citation, extracted_case_name, extracted_date, fallback_result)
                candidate_url = fallback_result.get("canonical_url")
                if gate_result == "accept":
                    return VerificationResult(
                        citation=citation,
                        verified=True,
                        canonical_name=fallback_result.get("canonical_name"),
                        canonical_date=fallback_result.get("canonical_date"),
                        canonical_url=fallback_result.get("canonical_url"),
                        source=fallback_result.get("source") or "",
                        confidence=fallback_result.get("confidence", 0.7),
                        method=fallback_result.get("method", "fallback"),
                    )
                if gate_result == "possible_match" and candidate_url:
                    logger.info(
                        f"[GATE-POSSIBLE] Fallback possible match (50-75% similarity): '{citation}' -> "
                        f"'{fallback_result.get('canonical_name')}'"
                    )
                    return VerificationResult(
                        citation=citation,
                        verified=False,
                        canonical_name=fallback_result.get("canonical_name"),
                        canonical_date=fallback_result.get("canonical_date"),
                        canonical_url=candidate_url,
                        method="fallback_possible_match",
                        possible_match=True,
                        source=fallback_result.get("source") or "",
                        confidence=0.6,
                    )
                logger.warning(
                    f"[GATE-REJECT] Fallback rejected for '{citation}': "
                    f"candidate='{fallback_result.get('canonical_name')}', date='{fallback_result.get('canonical_date')}'"
                )
                return VerificationResult(
                    citation=citation,
                    verified=False,
                    canonical_name=fallback_result.get("canonical_name") if candidate_url else None,
                    canonical_date=fallback_result.get("canonical_date") if candidate_url else None,
                    canonical_url=candidate_url,
                    error="Verification rejected by strict citation/year gate",
                    method="fallback_gate_reject",
                    possible_match=bool(candidate_url),
                    source=fallback_result.get("source", ""),
                )

        # Step 4: Last resort - search by case name and date only (no citation)
        if enable_fallback and time.time() - start_time < timeout:
            name = (extracted_case_name or "").strip()
            has_v = name and (" v" in name.lower() or " v." in name.lower())
            single_party = False
            if name and name.upper() != "N/A" and extracted_date and re.search(r"(19|20)\d{2}", str(extracted_date)):
                nd_name = re.sub(r",?\s*(19|20)\d{2}\s*$", "", name).strip() or name
                nd_tokens = [t for t in re.sub(r",?\s+", " ", nd_name).strip().split() if t]
                single_party = 1 <= len(nd_tokens) <= 4 and not any(re.search(r"^(19|20)\d{2}$", t) for t in nd_tokens)
            if name and name.upper() != "N/A" and (has_v or single_party):
                if extracted_date and re.search(r"(19|20)\d{2}", str(extracted_date)):
                    logger.debug(f"[VERIFY] Trying name+date-only fallback for '{name}' {extracted_date}")
                    name_date_result = await self.fallback.verify_name_and_date_only(
                        extracted_case_name,
                        extracted_date,
                        timeout - (time.time() - start_time),
                    )
                    if name_date_result.get("verified"):
                        # Always flag as Possible Match: show canonical name, year, and URL in display
                        return VerificationResult(
                            citation=citation,
                            verified=False,
                            possible_match=True,
                            canonical_name=name_date_result.get("canonical_name"),
                            canonical_date=name_date_result.get("canonical_date"),
                            canonical_url=name_date_result.get("canonical_url"),
                            source=name_date_result.get("source") or "",
                            confidence=name_date_result.get("confidence", 0.6),
                            method=name_date_result.get("method", "fallback_name_date_only"),
                            error="Possible match (name and date only; citation not verified)",
                        )
        
        # All methods failed
        return VerificationResult(
            citation=citation,
            verified=False,
            error="All verification methods failed",
            method="all_failed",
        )

    async def _run_single_citation_fallback(
        self,
        result: Dict[str, Any],
        case_name: Optional[str],
        date: Optional[str],
        is_proprietary: bool,
        cl_canonical_name: Optional[str],
        fallback_deadline: float,
        timeout_per_citation: float,
    ) -> int:
        """Run the full fallback chain for one citation. Mutates result in place. Returns 1 if fallback recovered, 0 else."""
        verified = result.get("verified", False)
        needs_url = bool(result.get("canonical_name") and not result.get("canonical_url"))
        success_delta = 0

        # Name+date-only for proprietary (WL/Lexis)
        name_date_done = False
        if is_proprietary and not verified and case_name and date and re.search(r"(19|20)\d{2}", str(date or "")):
            _nd_name = str(case_name or "").strip()
            _nd_has_v = (" v" in _nd_name.lower()) or (" v." in _nd_name.lower())
            _nd_name_clean = re.sub(r",?\s*(19|20)\d{2}\s*$", "", _nd_name).strip() or _nd_name
            _nd_tokens = [t for t in re.sub(r",?\s+", " ", _nd_name_clean).strip().split() if t] if _nd_name else []
            _nd_ok = _nd_name.upper() != "N/A" and (1 <= len(_nd_tokens) <= 4) and not any(re.search(r"^(19|20)\d{2}$", t) for t in _nd_tokens)
            if _nd_has_v or _nd_ok:
                remaining_nd = max(0.0, fallback_deadline - time.time())
                if remaining_nd > 2.0:
                    try:
                        name_date_result = await self.fallback.verify_name_and_date_only(
                            case_name, date, min(remaining_nd, 12.0),
                        )
                        if name_date_result.get("verified"):
                            result.update(name_date_result)
                            result["verified"] = False
                            result["possible_match"] = True
                            result["error"] = "Possible match (name and date only; citation not verified)"
                            name_date_done = True
                            needs_url = False
                            success_delta = 1
                    except Exception:
                        pass

        # Step A: CL search API fallback
        if not name_date_done:
            remaining_time = max(0.0, fallback_deadline - time.time())
        else:
            remaining_time = 0.0
        if remaining_time > 0:
            try:
                search_result = await cl_search_fallback(
                    self.session, self.api_key, result["citation"],
                    case_name, date, min(timeout_per_citation, remaining_time, 8.0),
                )
                if search_result.get("verified"):
                    gate_result = self._evaluate_two_point_gate(result["citation"], case_name, date, search_result)
                    candidate_url = search_result.get("canonical_url")
                    if gate_result == "accept":
                        result.update(search_result)
                        if cl_canonical_name and not search_result.get("canonical_name"):
                            result["canonical_name"] = cl_canonical_name
                        verified = True
                        needs_url = bool(not result.get("canonical_url"))
                        if not needs_url:
                            success_delta = 1
                    elif gate_result == "possible_match" and candidate_url:
                        result.update({
                            "verified": False,
                            "possible_match": True,
                            "canonical_name": search_result.get("canonical_name"),
                            "canonical_date": search_result.get("canonical_date"),
                            "canonical_url": candidate_url,
                            "source": search_result.get("source", "CourtListener-Search"),
                            "method": "courtlistener_search_possible_match",
                        })
                        success_delta = 1
                    else:
                        result.update({
                            "verified": False,
                            "error": "Verification rejected by strict citation/year gate",
                            "method": "courtlistener_search_gate_reject",
                            "possible_match": bool(candidate_url),
                            "canonical_name": search_result.get("canonical_name") if candidate_url else None,
                            "canonical_date": search_result.get("canonical_date") if candidate_url else None,
                            "canonical_url": candidate_url,
                            "source": search_result.get("source", "CourtListener-Search"),
                        })
            except Exception:
                pass

        # Step B: Web fallback
        if (not verified or needs_url) and not name_date_done:
            _name_txt = str(case_name or "").strip()
            _name_tokens = [t for t in _name_txt.replace(".", " ").split() if t]
            _has_v = (" v" in _name_txt.lower()) or (" v." in _name_txt.lower())
            _strong_name = bool(_name_txt and _name_txt.upper() != "N/A" and len(_name_tokens) >= 3 and _has_v)
            _cit_txt = str(result.get("citation", "") or "")
            _is_proprietary = (" WL " in _cit_txt) or (" Lexis " in _cit_txt) or (" U.S. Lexis " in _cit_txt)
            skip_web_fallback = not _strong_name and not _is_proprietary
            _weak_name = (not _name_txt) or (_name_txt.upper() == "N/A") or (len(_name_tokens) <= 1) or (" v" not in _name_txt.lower())
            if _is_proprietary and _weak_name:
                skip_web_fallback = True
            if not skip_web_fallback:
                remaining_time = max(0.0, fallback_deadline - time.time())
                if remaining_time > 0:
                    try:
                        fallback_result = await self.fallback.verify(
                            result["citation"], case_name, date,
                            min(timeout_per_citation, remaining_time, 8.0),
                        )
                        if fallback_result.get("verified"):
                            if self._passes_two_point_gate(result["citation"], case_name, date, fallback_result):
                                if cl_canonical_name:
                                    fallback_result.setdefault("canonical_name", cl_canonical_name)
                                result.update(fallback_result)
                                success_delta = 1
                            else:
                                candidate_url = fallback_result.get("canonical_url")
                                result.update({
                                    "verified": False,
                                    "error": "Verification rejected by strict citation/year gate",
                                    "method": "fallback_gate_reject",
                                    "possible_match": bool(candidate_url),
                                    "canonical_name": fallback_result.get("canonical_name") if candidate_url else None,
                                    "canonical_date": fallback_result.get("canonical_date") if candidate_url else None,
                                    "canonical_url": candidate_url,
                                    "source": fallback_result.get("source", ""),
                                })
                    except Exception:
                        pass

        # Last resort: name+date-only
        if not result.get("verified") and case_name and date and re.search(r"(19|20)\d{2}", str(date or "")):
            _nd_name = str(case_name or "").strip()
            _nd_has_v = (" v" in _nd_name.lower()) or (" v." in _nd_name.lower())
            _nd_name_clean = re.sub(r",?\s*(19|20)\d{2}\s*$", "", _nd_name).strip() or _nd_name
            _nd_tokens = [t for t in re.sub(r",?\s+", " ", _nd_name_clean).strip().split() if t] if _nd_name else []
            _nd_ok = _nd_name and _nd_name.upper() != "N/A" and (1 <= len(_nd_tokens) <= 4) and not any(re.search(r"^(19|20)\d{2}$", t) for t in _nd_tokens)
            if (_nd_has_v or _nd_ok):
                remaining_nd = max(0.0, fallback_deadline - time.time())
                if remaining_nd > 2.0:
                    try:
                        name_date_result = await self.fallback.verify_name_and_date_only(
                            case_name, date, min(remaining_nd, 12.0),
                        )
                        if name_date_result.get("verified"):
                            result.update(name_date_result)
                            result["verified"] = False
                            result["possible_match"] = True
                            result["error"] = "Possible match (name and date only; citation not verified)"
                            success_delta = 1
                    except Exception:
                        pass

        return success_delta

    async def verify_citations_batch(
        self,
        citations: List[str],
        extracted_case_names: Optional[List[str]] = None,
        extracted_dates: Optional[List[str]] = None,
        proprietary_flags: Optional[List[bool]] = None,
        batch_size: int = 250,
        timeout_per_citation: float = 10.0,
        progress_callback: Optional[Callable[[int, str, str], None]] = None,
        enable_fallback: bool = True,
        max_fallback_citations: int = 100,
        fallback_time_budget_seconds: float = 300.0,
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
            fallback_time_budget_seconds: Total wall-clock budget for all fallback attempts
            
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
        fallback_start_time = time.time()
        fallback_deadline = fallback_start_time + max(0.0, float(fallback_time_budget_seconds or 0.0))
        skipped_due_time_budget = 0
        skipped_due_count_cap = 0
        skipped_due_noisy_citation = 0

        def _is_noisy_for_fallback(cit: str) -> bool:
            """Skip expensive fallback calls for malformed/prose-like citation strings."""
            txt = (cit or "").strip()
            if not txt:
                return True
            if len(txt) > 180:
                return True
            markers = (
                "...",
                "TABLE OF AUTHORITIES",
                "Cases-Continued",
                "VIII Miscellaneous",
                "Resp't",
                "Resp’t",
                "Obj.",
            )
            if any(m in txt for m in markers):
                return True
            return False

        need_fallback: List[Tuple[Dict[str, Any], Optional[str], Optional[str], bool, Optional[str]]] = []
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

            # Deterministic rescue: known federal citation table (works even when CL lookup/search misses).
            # This is intentionally applied in batch mode too, not only single-citation verification.
            if not verified:
                known_federal = _lookup_known_federal(str(result.get("citation", "")))
                if known_federal:
                    result["verified"] = True
                    result["canonical_name"] = known_federal.get("canonical_name")
                    result["canonical_date"] = known_federal.get("canonical_date") or known_federal.get("canonical_year")
                    result["canonical_url"] = known_federal.get("canonical_url")
                    result["source"] = "known_federal"
                    result["confidence"] = 1.0
                    result["method"] = "known_federal"
                    result["error"] = None
                    verified = True
                    needs_url = False
                    logger.info(
                        f"[BATCH-KNOWN-FEDERAL] Resolved '{result.get('citation')}' -> "
                        f"'{result.get('canonical_name')}'"
                    )
            
            should_try_fallback = (not verified or needs_url) and enable_fallback
            if should_try_fallback and _is_noisy_for_fallback(str(result.get("citation", ""))):
                should_try_fallback = False
                skipped_due_noisy_citation += 1
                logger.info(
                    f"[BATCH-FALLBACK] Skipping noisy citation: "
                    f"'{str(result.get('citation', ''))[:80]}'"
                )
            if should_try_fallback and len(need_fallback) >= max_fallback_citations:
                skipped_due_count_cap += 1
            if should_try_fallback and time.time() >= fallback_deadline:
                skipped_due_time_budget += 1

            if (
                should_try_fallback
                and len(need_fallback) < max_fallback_citations
                and time.time() < fallback_deadline
            ):
                unverified_count += 1
                idx = result_idx if result_idx < len(citations) else None
                case_name = extracted_case_names[idx] if (extracted_case_names and idx is not None and idx < len(extracted_case_names)) else None
                date = extracted_dates[idx] if (extracted_dates and idx is not None and idx < len(extracted_dates)) else None
                _cit_txt_early = str(result.get("citation", "") or "")
                is_proprietary = (
                    proprietary_flags[idx]
                    if (proprietary_flags and idx is not None and idx < len(proprietary_flags))
                    else bool(re.match(r"^\s*\d{4}\s+WL\s+\d+\s*$", _cit_txt_early.strip()))
                )
                cl_canonical_name = result.get("canonical_name") if needs_url else None
                need_fallback.append((result, case_name, date, is_proprietary, cl_canonical_name))

        fallback_attempted = len(need_fallback)
        if need_fallback:
            try:
                from src.config import VERIFICATION_FALLBACK_CONCURRENCY
                concurrency = max(1, int(VERIFICATION_FALLBACK_CONCURRENCY))
            except Exception:
                concurrency = 1
            if concurrency <= 1:
                for (result, case_name, date, is_proprietary, cl_canonical_name) in need_fallback:
                    if time.time() >= fallback_deadline:
                        break
                    fallback_success_count += await self._run_single_citation_fallback(
                        result, case_name, date, is_proprietary, cl_canonical_name,
                        fallback_deadline, timeout_per_citation,
                    )
            else:
                sem = asyncio.Semaphore(concurrency)

                async def run_with_sem(item):
                    result, case_name, date, is_proprietary, cl_canonical_name = item
                    async with sem:
                        if time.time() >= fallback_deadline:
                            return 0
                        return await self._run_single_citation_fallback(
                            result, case_name, date, is_proprietary, cl_canonical_name,
                            fallback_deadline, timeout_per_citation,
                        )

                deltas = await asyncio.gather(*[run_with_sem(item) for item in need_fallback])
                fallback_success_count = sum(deltas)

        for result in batch_results:
            verified = result.get("verified", False)
            err = result.get("error")
            if not verified and not err:
                err = "No results"
            results.append(VerificationResult(
                citation=result["citation"],
                verified=verified,
                canonical_name=result.get("canonical_name"),
                canonical_date=result.get("canonical_date"),
                canonical_url=result.get("canonical_url"),
                source=result.get("source", "unknown"),
                confidence=result.get("confidence", 0.0),
                method=result.get("method", "unknown"),
                error=err,
                possible_match=bool(result.get("possible_match", False)),
                raw_data=result.get("raw_data"),
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
                f"{f', {skipped_due_count_cap} skipped (max_fallback={max_fallback_citations})' if skipped_due_count_cap else ''}"
                f"{f', {skipped_due_time_budget} skipped (time_budget={fallback_time_budget_seconds}s)' if skipped_due_time_budget else ''}"
                f"{f', {skipped_due_noisy_citation} skipped (noisy-citation gate)' if skipped_due_noisy_citation else ''}"
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


# Singleton for get_master_verifier()
_master_instance: Optional[UnifiedVerificationMaster] = None


def get_master_verifier() -> UnifiedVerificationMaster:
    """Return the shared UnifiedVerificationMaster instance (used by citation_extraction_endpoint, etc.)."""
    global _master_instance
    if _master_instance is None:
        _master_instance = UnifiedVerificationMaster()
    return _master_instance
