"""
Universal State Court Verifier - supports all 50 US states
"""

import re
import requests
import logging
from typing import Optional, Dict, Any
from rapidfuzz import fuzz

from ..utils.state_court_mapping import (
    identify_state_from_citation,
    get_verification_strategy,
    STATES_WITH_FREE_DATABASES,
)

logger = logging.getLogger(__name__)


class UniversalStateCourtVerifier:
    """Verifies citations from all 50 US state courts."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def verify_state_citation(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Verify a state court citation using the best available sources.

        Args:
            citation: The citation to verify (e.g., "385 N.C. 419")
            extracted_case_name: The case name extracted from document
            extracted_date: The date extracted from document
            timeout: Maximum time to spend on verification

        Returns:
            dict: Verification result with keys: verified, canonical_name, canonical_url, source, confidence
        """
        logger.info(f"[DEBUG] [UNIVERSAL-STATE] Verifying: {citation}")

        # Identify state
        state_name, court_url = identify_state_from_citation(citation)

        if not state_name:
            logger.warning(f"[WARNING] [UNIVERSAL-STATE] Cannot identify state for: {citation}")
            return {"verified": False, "error": "Cannot identify state"}

        logger.info(f"📍 [UNIVERSAL-STATE] Identified state: {state_name}")

        # Get verification strategy
        strategy = get_verification_strategy(state_name)

        # Try verification sources in priority order
        sources_to_try = [
            ("Casetext", self._verify_with_casetext),
            ("CaseMine", self._verify_with_casemine),
            ("Justia", self._verify_with_justia),
            ("FindLaw", self._verify_with_findlaw),
        ]

        # Add state-specific source if available
        if strategy["has_free_database"]:
            logger.info(f"✨ [UNIVERSAL-STATE] {state_name} has free database!")
            sources_to_try.insert(0, (f"{state_name}_Courts", self._verify_with_state_database))

        time_per_source = timeout / len(sources_to_try)

        for source_name, verify_func in sources_to_try:
            try:
                logger.info(f"[DEBUG] [UNIVERSAL-STATE] Trying {source_name}...")
                result = verify_func(
                    citation=citation,
                    state_name=state_name,
                    court_url=court_url,
                    extracted_case_name=extracted_case_name,
                    timeout=time_per_source,
                )

                if result.get("verified") or result.get("possible_match"):
                    logger.info(f"[SUCCESS] [UNIVERSAL-STATE] {source_name} succeeded!")
                    return result

            except Exception as e:
                logger.warning(f"[WARNING] [UNIVERSAL-STATE] {source_name} failed: {e}")
                continue

        logger.warning(f"[ERROR] [UNIVERSAL-STATE] All sources failed for: {citation}")
        return {"verified": False, "error": "All verification sources failed"}

    def _verify_with_casetext(
        self, citation: str, state_name: str, court_url: str, extracted_case_name: Optional[str], timeout: float
    ) -> Dict[str, Any]:
        """Verify using Casetext (excellent for all states)."""

        search_url = f"https://casetext.com/search?q={citation}"
        if extracted_case_name:
            search_url += f"+{extracted_case_name.replace(' ', '+')}"

        try:
            response = self.session.get(search_url, timeout=timeout)

            if response.status_code == 200 and citation in response.text:
                # Try to extract case name
                case_name_match = re.search(r"<h2[^>]*>([^<]+v\.?[^<]+)</h2>", response.text, re.IGNORECASE)
                if not case_name_match:
                    case_name_match = re.search(r"<title>([^<]+v\.?[^<]+)", response.text, re.IGNORECASE)

                if case_name_match:
                    found_name = case_name_match.group(1).strip()

                    # Verify similarity
                    if extracted_case_name and extracted_case_name != "N/A":
                        similarity = fuzz.ratio(extracted_case_name.lower(), found_name.lower()) / 100.0

                        if similarity >= 0.5:
                            return {
                                "verified": True,
                                "canonical_name": found_name,
                                "canonical_url": search_url,
                                "source": "Casetext",
                                "confidence": 0.8,
                                "state": state_name,
                            }

                    return {
                        "possible_match": True,
                        "canonical_name": found_name,
                        "canonical_url": search_url,
                        "source": "Casetext",
                        "confidence": 0.6,
                        "state": state_name,
                    }

        except Exception as e:
            logger.debug(f"Casetext error: {e}")

        return {"verified": False}

    def _verify_with_casemine(
        self, citation: str, state_name: str, court_url: str, extracted_case_name: Optional[str], timeout: float
    ) -> Dict[str, Any]:
        """Verify using CaseMine."""

        search_url = f"https://www.casemine.com/search/us?q={citation}"

        try:
            response = self.session.get(search_url, timeout=timeout)

            if response.status_code == 200 and citation in response.text:
                # Try to extract case name
                case_name_match = re.search(r"<h2[^>]*>([^<]+v\.?[^<]+)</h2>", response.text, re.IGNORECASE)
                if not case_name_match:
                    case_name_match = re.search(r"<title>([^<]+v\.?[^<]+)", response.text, re.IGNORECASE)

                if case_name_match:
                    found_name = case_name_match.group(1).strip()

                    if extracted_case_name and extracted_case_name != "N/A":
                        similarity = fuzz.ratio(extracted_case_name.lower(), found_name.lower()) / 100.0

                        if similarity >= 0.5:
                            return {
                                "verified": True,
                                "canonical_name": found_name,
                                "canonical_url": search_url,
                                "source": "CaseMine",
                                "confidence": 0.7,
                                "state": state_name,
                            }

                    return {
                        "possible_match": True,
                        "canonical_name": found_name,
                        "canonical_url": search_url,
                        "source": "CaseMine",
                        "confidence": 0.6,
                        "state": state_name,
                    }

        except Exception as e:
            logger.debug(f"CaseMine error: {e}")

        return {"verified": False}

    def _verify_with_justia(
        self, citation: str, state_name: str, court_url: str, extracted_case_name: Optional[str], timeout: float
    ) -> Dict[str, Any]:
        """Verify using Justia."""

        # Justia has state-specific URLs
        state_abbrev = state_name.lower().replace(" ", "-")
        search_url = f"https://law.justia.com/cases/{state_abbrev}/?q={citation}"

        try:
            response = self.session.get(search_url, timeout=timeout)

            if response.status_code == 200 and citation in response.text:
                case_name_match = re.search(r"<h1[^>]*>([^<]+v\.?[^<]+)</h1>", response.text, re.IGNORECASE)

                if case_name_match:
                    found_name = case_name_match.group(1).strip()

                    if extracted_case_name and extracted_case_name != "N/A":
                        similarity = fuzz.ratio(extracted_case_name.lower(), found_name.lower()) / 100.0

                        if similarity >= 0.5:
                            return {
                                "verified": True,
                                "canonical_name": found_name,
                                "canonical_url": search_url,
                                "source": "Justia",
                                "confidence": 0.8,
                                "state": state_name,
                            }

                    return {
                        "possible_match": True,
                        "canonical_name": found_name,
                        "canonical_url": search_url,
                        "source": "Justia",
                        "confidence": 0.6,
                        "state": state_name,
                    }

        except Exception as e:
            logger.debug(f"Justia error: {e}")

        return {"verified": False}

    def _verify_with_findlaw(
        self, citation: str, state_name: str, court_url: str, extracted_case_name: Optional[str], timeout: float
    ) -> Dict[str, Any]:
        """Verify using FindLaw."""

        search_url = f"https://caselaw.findlaw.com/search.html?q={citation}"

        try:
            response = self.session.get(search_url, timeout=timeout)

            if response.status_code == 200 and citation in response.text:
                case_name_match = re.search(r"<h2[^>]*>([^<]+v\.?[^<]+)</h2>", response.text, re.IGNORECASE)

                if case_name_match:
                    found_name = case_name_match.group(1).strip()

                    if extracted_case_name and extracted_case_name != "N/A":
                        similarity = fuzz.ratio(extracted_case_name.lower(), found_name.lower()) / 100.0

                        if similarity >= 0.5:
                            return {
                                "verified": True,
                                "canonical_name": found_name,
                                "canonical_url": search_url,
                                "source": "FindLaw",
                                "confidence": 0.7,
                                "state": state_name,
                            }

                    return {
                        "possible_match": True,
                        "canonical_name": found_name,
                        "canonical_url": search_url,
                        "source": "FindLaw",
                        "confidence": 0.5,
                        "state": state_name,
                    }

        except Exception as e:
            logger.debug(f"FindLaw error: {e}")

        return {"verified": False}

    def _verify_with_state_database(
        self, citation: str, state_name: str, court_url: str, extracted_case_name: Optional[str], timeout: float
    ) -> Dict[str, Any]:
        """Verify using state-specific free databases."""

        if state_name not in STATES_WITH_FREE_DATABASES:
            return {"verified": False}

        database_url = STATES_WITH_FREE_DATABASES[state_name]

        try:
            # State-specific logic for free databases
            if state_name == "Oklahoma":
                # OSCN has excellent search
                search_url = f"{database_url}search.aspx?q={citation}"
            elif state_name == "Montana":
                search_url = f"{database_url}?q={citation}"
            elif state_name == "Alaska":
                search_url = f"{database_url}?search={citation}"
            elif state_name == "Arkansas":
                search_url = f"{database_url}?citation={citation}"
            else:
                search_url = f"{database_url}?q={citation}"

            response = self.session.get(search_url, timeout=timeout)

            if response.status_code == 200 and citation in response.text:
                case_name_match = re.search(r"<h[123][^>]*>([^<]+v\.?[^<]+)</h[123]>", response.text, re.IGNORECASE)

                if case_name_match:
                    found_name = case_name_match.group(1).strip()

                    if extracted_case_name and extracted_case_name != "N/A":
                        similarity = fuzz.ratio(extracted_case_name.lower(), found_name.lower()) / 100.0

                        if similarity >= 0.5:
                            return {
                                "verified": True,
                                "canonical_name": found_name,
                                "canonical_url": search_url,
                                "source": f"{state_name}_Courts",
                                "confidence": 0.9,  # High confidence for official sources
                                "state": state_name,
                            }

                    return {
                        "possible_match": True,
                        "canonical_name": found_name,
                        "canonical_url": search_url,
                        "source": f"{state_name}_Courts",
                        "confidence": 0.7,
                        "state": state_name,
                    }

        except Exception as e:
            logger.debug(f"{state_name} database error: {e}")

        return {"verified": False}
