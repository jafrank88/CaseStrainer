"""
Scoring and matching mixin for UnifiedVerificationMaster.

Contains confidence scoring, name similarity, date matching,
two-point match validation, search result ranking, rate limiting,
and invalid citation detection.
Extracted from unified_verification_master.py (P1 refactoring).
"""

import re
import time
import asyncio
import logging
from typing import Dict, List, Optional

from src.verification.models import VerificationSource
from src.verification.utils import calculate_case_name_overlap
from src.utils.similarity_utils import calculate_name_similarity

logger = logging.getLogger(__name__)


class ScoringMixin:
    """Mixin providing scoring, matching, and rate-limiting helpers."""

    def _normalize_citation_for_matching(self, citation: str) -> str:
        """
        Normalize citations for equality checks in two-point matching.
        Uses the host class normalizer when available; otherwise falls back to
        a lightweight local normalization.
        """
        if not citation:
            return ""

        # Prefer host implementation when present (e.g., UnifiedVerificationMaster).
        normalizer = getattr(self, "_normalize_citation_comprehensive", None)
        if callable(normalizer):
            try:
                return str(normalizer(str(citation), purpose="comparison"))
            except TypeError:
                # Compatibility with older signatures that don't accept purpose.
                try:
                    return str(normalizer(str(citation)))
                except Exception:
                    logger.debug("Suppressed exception", exc_info=True)
            except Exception:
                logger.debug("Suppressed exception", exc_info=True)

        # Local fallback normalization.
        normalized = str(citation).strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.replace("u. s.", "u.s.")
        normalized = normalized.replace("s. ct.", "s.ct.")
        normalized = normalized.replace("f. supp.", "f.supp.")
        normalized = normalized.replace("f. 3d", "f.3d")
        normalized = normalized.replace("f. 2d", "f.2d")
        normalized = re.sub(r"\s*,\s*", ", ", normalized)
        return normalized

    def _calculate_confidence(
        self,
        citation: str,
        canonical_name: Optional[str],
        extracted_case_name: Optional[str],
        canonical_date: Optional[str],
        extracted_date: Optional[str],
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
        return calculate_name_similarity(name1, name2)

    def _dates_match(self, date1: str, date2: str) -> bool:
        """Check if two dates match (year-based comparison)."""
        if not date1 or not date2:
            return False

        # Extract years
        year1_match = re.search(r"(\d{4})", str(date1))
        year2_match = re.search(r"(\d{4})", str(date2))

        if year1_match and year2_match:
            return year1_match.group(1) == year2_match.group(1)

        return False

    def _two_point_match_ok(
        self,
        *,
        extracted_name: Optional[str],
        canonical_name: Optional[str],
        extracted_date: Optional[str],
        canonical_date: Optional[str],
        requested_citation: Optional[str],
        canonical_citation: Optional[str],
    ) -> bool:
        """
        Enforce the rule that at least two of {name, citation, year} must align
        before we treat a result as fully verified.

        - Name: sufficient overlap between extracted and canonical names.
        - Citation: normalized primary citation equality.
        - Year: exact year match unless the extracted year is clearly contaminated.
        """
        name_match = False
        year_match = False
        citation_match = False

        # 1) Name match via existing overlap logic
        if extracted_name and canonical_name:
            try:
                overlap = calculate_case_name_overlap(extracted_name, canonical_name)
                name_match = overlap >= 0.4  # Reuse existing search threshold
            except Exception:
                name_match = False

        # 2) Year match with "clearly wrong extracted year" escape hatch (supports 1600-2100, e.g. 18xx)
        if extracted_date and canonical_date:
            from src.utils.date_utils import extract_year_value
            ext_str = extract_year_value(extracted_date)
            can_str = extract_year_value(canonical_date)
            if ext_str and can_str:
                ext_year = int(ext_str)
                can_year = int(can_str)
                diff = abs(ext_year - can_year)

                is_extracted_clearly_wrong = (
                    (ext_year < 1900 <= can_year)
                    or (ext_year >= 2015 and can_year < 1950)
                    or diff > 50
                )

                if not is_extracted_clearly_wrong and ext_year == can_year:
                    year_match = True

        # 3) Citation match using normalized citations
        if requested_citation and canonical_citation:
            try:
                norm_req = self._normalize_citation_for_matching(requested_citation)
                norm_can = self._normalize_citation_for_matching(canonical_citation)
                citation_match = norm_req == norm_can
            except Exception:
                citation_match = False

        count = int(name_match) + int(citation_match) + int(year_match)
        return count >= 2

    def _find_best_search_result(
        self, results: List[Dict], citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str]
    ) -> Optional[Dict]:
        """Find the best result from search API results."""
        # FIX #56C: Add strict validation to prevent wrong matches
        # Search results can contain unrelated cases that just mention the citation

        if not extracted_case_name or extracted_case_name == "N/A":
            return None

        best_result = None
        best_score = 0.0
        best_overlap = 0.0

        for result in results:
            canonical_name = result.get("caseName", "")

            # FIX #56C: Check name overlap BEFORE calculating confidence
            extracted_words = set(extracted_case_name.lower().split())
            canonical_words = set(canonical_name.lower().split())
            common_words = {
                "v",
                "v.",
                "vs",
                "vs.",
                "the",
                "of",
                "in",
                "a",
                "an",
                "&",
                "and",
                "inc",
                "inc.",
                "llc",
                "ltd",
                "ltd.",
                "co",
                "co.",
                "corp",
                "corp.",
            }
            extracted_words -= common_words
            canonical_words -= common_words

            if not extracted_words:
                continue

            # CRITICAL FIX: Use Jaccard similarity (intersection/union) instead of intersection/extracted
            # This handles cases where canonical name is longer (e.g., "Chalkley v. Atlantic Coast Line Railroad")
            # vs extracted name ("Chalkley v. Atlantic Coast Line")
            intersection = len(extracted_words & canonical_words)
            union = len(extracted_words | canonical_words)
            overlap = intersection / union if union > 0 else 0.0

            # Also check for substring match (extracted name contained in canonical)
            # This is a strong indicator of a valid match when canonical is longer
            extracted_norm = extracted_case_name.lower().strip()
            canonical_norm = canonical_name.lower().strip()
            if extracted_norm in canonical_norm:
                # Extracted name is substring of canonical - boost overlap
                overlap = max(overlap, 0.8)  # Strong match when extracted is contained in canonical

            # STRICTER VALIDATION: Require higher overlap for better matches
            # Only consider matches with reasonable word overlap
            if overlap < 0.4:  # Require at least 40% word overlap
                continue

            # ADDITIONAL CHECK: Require at least one unique word to match
            unique_matches = extracted_words & canonical_words
            if len(unique_matches) < 2:  # Require at least 2 unique words to match
                continue

            # ADDITIONAL CHECK: Reject completely different party names
            # For cases like "Foss v. Nat'l Marine Fisheries Serv" vs "Berst v. Snohomish County"
            # The party names should have some similarity
            extracted_party_words = extracted_words - {
                "marine",
                "fisheries",
                "service",
                "dept",
                "department",
                "correction",
                "corrections",
            }
            canonical_party_words = canonical_words - {"county", "city", "state", "town", "village", "municipality"}

            if extracted_party_words and canonical_party_words:
                party_overlap = len(extracted_party_words & canonical_party_words) / max(
                    len(extracted_party_words), len(canonical_party_words)
                )
                if party_overlap == 0:  # No party words in common at all
                    continue

            # FIX #64: Special validation for "State v. X" and criminal cases
            # Problem: "State v. M.Y.G." and "State v. Olsen" have high overlap (50%+) but are different cases
            # Solution: For criminal cases, require party names to match, not just "State v."
            is_criminal_case = False
            criminal_patterns = [
                r"\bstate\s+v\.?\s+",
                r"\bpeople\s+v\.?\s+",
                r"\bcommonwealth\s+v\.?\s+",
                r"\bunited\s+states\s+v\.?\s+",
                r"\bcity\s+of\s+\w+\s+v\.?\s+",
            ]

            for pattern in criminal_patterns:
                if re.search(pattern, extracted_case_name, re.IGNORECASE):
                    is_criminal_case = True
                    break

            if is_criminal_case:
                # For criminal cases, extract and compare the defendant/party names
                extracted_party = re.sub(
                    r"^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+",
                    "",
                    extracted_case_name,
                    flags=re.IGNORECASE,
                ).strip()
                canonical_party = re.sub(
                    r"^(state|people|commonwealth|united\s+states|city\s+of\s+\w+)\s+v\.?\s+",
                    "",
                    canonical_name,
                    flags=re.IGNORECASE,
                ).strip()

                # Remove common suffixes and punctuation for better matching
                extracted_party = re.sub(r"[,\.].*$", "", extracted_party).strip().lower()
                canonical_party = re.sub(r"[,\.].*$", "", canonical_party).strip().lower()

                # Calculate similarity between party names
                if not extracted_party or not canonical_party:
                    logger.warning(
                        f"[WARNING]  [FIX #64] Could not extract party names from '{extracted_case_name}' vs '{canonical_name}'"
                    )
                    continue

                party_similarity = self._calculate_name_similarity(extracted_party, canonical_party)

                # Require high similarity for criminal cases (different defendants = different cases!)
                if party_similarity < 0.7:
                    logger.warning(
                        f"[WARNING]  [FIX #64] CRIMINAL CASE MISMATCH: '{extracted_party}' vs '{canonical_party}' (similarity: {party_similarity:.2f})"
                    )
                    logger.warning(f"   Full names: '{extracted_case_name}' vs '{canonical_name}'")
                    logger.warning("   Different defendants = different cases! Rejecting.")
                    continue

                logger.info(
                    f"[OK] [FIX #64] Criminal case party names match: '{extracted_party}' vs '{canonical_party}' (similarity: {party_similarity:.2f})"
                )

            # FIX #56C: Require at least 30% word overlap (lowered from 50% to catch valid matches)
            # When we have citation + case name + year in the search query, we have high confidence
            # CRITICAL FIX: Also check substring match - if extracted name is contained in canonical,
            # that's a strong match even if word overlap is lower
            is_substring_match = extracted_norm in canonical_norm or canonical_norm in extracted_norm
            if is_substring_match:
                # Substring match detected - boost overlap to pass threshold
                overlap = max(overlap, 0.7)  # Strong match when one name contains the other
                logger.error(
                    f"[OK] [FIX #56C] Substring match detected - boosting overlap to {overlap:.2f}: '{canonical_name}' contains '{extracted_case_name}'"
                )

            if overlap < 0.3:
                logger.warning(
                    f"[WARNING]  [FIX #56C] Rejected search result - low overlap ({overlap:.0%}): '{canonical_name}' vs '{extracted_case_name}'"
                )
                continue

            score = self._calculate_confidence(
                citation, canonical_name, extracted_case_name, result.get("dateFiled"), extracted_date
            )

            if score > best_score or (score == best_score and overlap > best_overlap):
                best_score = score
                best_overlap = overlap
                best_result = result
                logger.info(
                    f"[OK] [FIX #56C] Valid search result: '{canonical_name}' (overlap: {overlap:.0%}, confidence: {score:.0%})"
                )


        return best_result if best_score > 0.5 else None

    async def _enforce_rate_limit(self, source: VerificationSource):
        """Enforce rate limiting for API calls."""
        if source not in self.rate_limits:
            return

        rate_info = self.rate_limits[source]
        calls_per_minute = rate_info["calls_per_minute"]
        last_call = rate_info["last_call"]

        current_time = time.time()
        time_since_last = current_time - last_call
        min_interval = 60.0 / calls_per_minute

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.rate_limits[source]["last_call"] = time.time()

    def _is_obviously_invalid_citation(self, citation: str) -> bool:
        """
        Detect obviously invalid/test citations to skip external fallback.
        This saves time by not trying to verify citations that clearly don't exist.
        """
        # Skip test citations with very high reporter numbers
        # Real U.S. Supreme Court cases currently go up to about 600+ U.S.
        # Only reject volumes > 650 to leave room for recent/future cases
        if re.search(r"\b([7-9]\d\d|\d{4,})\s+U\.S\.\s+\d+", citation):
            return True

        # Skip citations with "Test Case" in the name (we check this in the fallback logic)
        # This is handled elsewhere

        # Skip citations with obviously invalid patterns
        if re.search(r"\b000\b", citation):  # Page number 000
            return True

        return False
