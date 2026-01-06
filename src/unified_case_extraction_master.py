"""
Unified Case Extraction Master
=============================

This module provides THE SINGLE, AUTHORITATIVE case name extraction function
that consolidates the best features from all duplicate functions across the codebase.

ALL OTHER EXTRACTION FUNCTIONS SHOULD BE DEPRECATED AND REPLACED WITH THIS ONE.

Key Features:
- Position-aware extraction (prevents bleeding)
- Context-optimized windows (prevents contamination)
- Advanced pattern matching (handles all citation formats)
- Comprehensive fallback logic (minimizes N/A results)
- Unicode-aware text processing
- Performance optimized
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.utils.canonical_metadata import (
    normalize_citation_key,
    get_canonical_metadata,
    prefer_canonical_name,
    prefer_canonical_year,
    extract_year_value,
    fetch_canonical_metadata_on_demand,
)

logger = logging.getLogger(__name__)


@dataclass
class MasterExtractionResult:
    """Standardized result from the master extraction function."""

    case_name: str
    year: str
    confidence: float
    method: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    context: str = ""
    debug_info: Optional[Dict[str, Any]] = None
    canonical_name: Optional[str] = None
    canonical_year: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_year: Optional[str] = None


class UnifiedCaseExtractionMaster:
    """
    THE SINGLE, AUTHORITATIVE case name extraction implementation.

    This class consolidates the best features from:
    - extract_case_name_and_date_master()
    - extract_case_name_and_year_unified()
    - _extract_case_name_enhanced()
    - All other duplicate functions

    ALL extraction should go through this class.
    """

    def __init__(self, document_primary_case_name: Optional[str] = None):
        """Initialize the master extraction engine.

        Args:
            document_primary_case_name: The primary case name of the document being analyzed.
                                       Used to filter out contamination where citations incorrectly
                                       extract the document's own case name.
        """
        self._setup_patterns()
        logger.info("UnifiedCaseExtractionMaster initialized - all duplicates deprecated")
        self.citation_metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.document_primary_case_name = document_primary_case_name
        if document_primary_case_name:
            logger.warning(f"[CONTAMINATION-FILTER] Document primary case: '{document_primary_case_name}'")

    def _get_canonical_metadata(self, citation: Optional[str]) -> Dict[str, Any]:
        metadata = get_canonical_metadata(citation, self.citation_metadata_cache)
        if metadata:
            return metadata

        fetched = fetch_canonical_metadata_on_demand(citation) if citation else {}
        if fetched:
            self._update_canonical_cache(
                citation,
                canonical_name=fetched.get("canonical_name"),
                canonical_date=fetched.get("canonical_date"),
            )
            return fetched

        return {}

    def _update_canonical_cache(
        self,
        citation: Optional[str],
        canonical_name: Optional[str] = None,
        canonical_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = normalize_citation_key(citation)
        if not key:
            return {}

        existing = self.citation_metadata_cache.get(key, {}).copy()

        if canonical_name is None and canonical_date is None:
            return existing

        if canonical_name is not None:
            existing["canonical_name"] = canonical_name
        if canonical_date is not None:
            existing["canonical_date"] = canonical_date
        if existing:
            self.citation_metadata_cache[key] = existing
        return existing

    def _apply_canonical_preferences(
        self,
        citation: Optional[str],
        extracted_name: Optional[str],
        extracted_year: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        canonical_meta = self._get_canonical_metadata(citation) if citation else {}
        preferred_name = prefer_canonical_name(extracted_name, canonical_meta, self._is_valid_case_name)
        preferred_year = prefer_canonical_year(extracted_year, canonical_meta)
        return preferred_name or extracted_name, preferred_year or extracted_year, canonical_meta

    def _is_valid_case_name(self, case_name: Optional[str]) -> bool:
        if not case_name:
            return False
        cleaned = case_name.strip()
        if len(cleaned) < 5:
            return False
        # Accept special case types (In re, Ex parte, In the matter) or adversarial cases (v.)
        lower = cleaned.lower()
        if lower.startswith("in re ") or lower.startswith("ex parte ") or lower.startswith("in the matter"):
            return True
        return " v. " in cleaned

    def _extract_case_name_backward_from_v(self, text: str, v_position: int, debug: bool = False) -> Optional[str]:
        """
        DEC 2025 FIX: Improved backward extraction from 'v.' position.

        Works backwards from 'v.' including:
        1. Every capitalized word
        2. Lowercase legal stopwords (of, the, in, re, etc.)
        3. Legal abbreviations with periods (Inc., Dep't, Cmty., etc.)

        Stops at:
        - Sentence boundaries (. followed by space and uppercase, or newline)
        - Citation patterns (numbers followed by reporter abbreviations)
        - Common non-case-name patterns (court names, page numbers, etc.)

        Args:
            text: Full document text
            v_position: Position of 'v.' in the text
            debug: Enable debug logging

        Returns:
            Extracted case name with both plaintiff and defendant, or None
        """
        if v_position <= 0 or v_position >= len(text):
            return None

        # Legal stopwords that can appear in case names (lowercase)
        legal_stopwords = {
            "of",
            "the",
            "in",
            "re",
            "ex",
            "and",
            "for",
            "by",
            "at",
            "on",
            "to",
            "de",
            "la",
            "du",
            "von",
            "van",
            "der",
            "del",
            "al",
            "parte",
            "matter",
            "an",
            "a",
            "as",
            "or",
            "nor",
            "but",
            "yet",
            "so",
            "with",
            "from",
        }

        # Legal abbreviations (case-insensitive matching)
        # These are words that look lowercase but are actually abbreviations
        legal_abbreviations = {
            "inc",
            "llc",
            "llp",
            "corp",
            "co",
            "ltd",
            "pc",
            "lp",
            "na",
            "plc",
            "dep't",
            "dept",
            "cmty",
            "comm'n",
            "commn",
            "ass'n",
            "assn",
            "gov't",
            "govt",
            "cty",
            "ct",
            "app",
            "assocs",
            "bros",
            "ins",
            "mfg",
            "mkt",
            "prod",
            "servs",
            "sys",
            "int'l",
            "intl",
            "nat'l",
            "natl",
            "elec",
            "eng'g",
            "engg",
            "indus",
            "cnty",
            "twp",
            "univ",
            "hosp",
            "med",
            "ctr",
            "grp",
            "mgmt",
            "dev",
            "prop",
            "props",
            "hum",
            "res",
            "tech",
            "fin",
            "svcs",
            "admin",
            "ops",
            "commr",
            "comr",
            "supt",
            "u.s",
            "n.a",
            "p.c",
            "l.p",
            "l.l.c",
            "d.b.a",
            "dba",
        }

        # Get text before 'v.' (up to 300 chars for context)
        start_pos = max(0, v_position - 300)
        text_before_v = text[start_pos:v_position]

        if debug:
            logger.warning(f"[BACKWARD-V] Text before v.: '{text_before_v[-100:]}'")

        # Now work backwards from the end of text_before_v, word by word
        words = []
        current_word = []
        i = len(text_before_v) - 1

        # Skip trailing whitespace
        while i >= 0 and text_before_v[i] in " \t\n\r":
            i -= 1

        boundary_hit = False
        while i >= 0 and not boundary_hit:
            char = text_before_v[i]

            if char in " \t\n\r":
                # End of word - process it
                if current_word:
                    word = "".join(reversed(current_word))
                    word_lower = word.lower().rstrip(".,;:")
                    word_clean = word.rstrip(".,;:")

                    # Check if this word should be included
                    should_include = False

                    # 1. Capitalized words (proper nouns)
                    if word_clean and word_clean[0].isupper():
                        should_include = True

                    # 2. Legal stopwords
                    elif word_lower in legal_stopwords:
                        should_include = True

                    # 3. Legal abbreviations
                    elif word_lower.rstrip(".") in legal_abbreviations:
                        should_include = True

                    # 4. Words ending in common legal suffixes
                    elif word_lower.endswith(("'s", "'n", "'t", "'d")):
                        should_include = True

                    if should_include:
                        words.insert(0, word)
                        current_word = []
                    else:
                        # This word doesn't belong - check if it's a boundary
                        # Non-included lowercase word that's not a stopword = boundary
                        if debug:
                            logger.warning(f"[BACKWARD-V] Hit boundary at word: '{word}'")
                        boundary_hit = True
                        break

                # Skip whitespace
                while i >= 0 and text_before_v[i] in " \t\n\r":
                    i -= 1
                continue

            # Check for sentence boundary: period followed by what we've collected
            # (looking backwards, so period comes after the capital letter)
            if char == "." and current_word:
                # Check if this is an abbreviation period or sentence end
                current_word_str = "".join(reversed(current_word))

                # Look at what comes before the period
                j = i - 1
                while j >= 0 and text_before_v[j] in " \t":
                    j -= 1

                # If there's a lowercase letter before the period after space, it's likely sentence end
                if j >= 0:
                    prev_char = text_before_v[j]
                    # If previous char is lowercase and current word starts with capital after period
                    # This is likely: "sentence. Word" - a sentence boundary
                    if prev_char.islower() and current_word_str and current_word_str[0].isupper():
                        # Check if this looks like an abbreviation (single letter, common abbrev)
                        if len(current_word_str) > 2:  # Not a single-letter abbreviation
                            if debug:
                                logger.warning(f"[BACKWARD-V] Sentence boundary before '{current_word_str}'")
                            boundary_hit = True
                            words.insert(0, current_word_str)
                            break

                # Include the period in the word (for abbreviations)
                current_word.append(char)
                i -= 1
                continue

            # Check for citation pattern: digits followed by reporter
            if char.isdigit():
                # We might be hitting a citation - check the context
                # Look backwards to see if this is part of "123 Wn.2d" or similar
                j = i
                while j >= 0 and (text_before_v[j].isdigit() or text_before_v[j] in " "):
                    j -= 1

                # If we have accumulated words and hit digits, might be citation boundary
                if words and len(words) >= 1:
                    # Check if this looks like a citation
                    test_text = text_before_v[max(0, j - 10) : i + 1]
                    if re.search(r"\d+\s+(?:Wn\.|Wash\.|P\.|F\.|U\.S\.|App\.)", test_text, re.IGNORECASE):
                        if debug:
                            logger.warning(f"[BACKWARD-V] Citation boundary at: '{test_text}'")
                        boundary_hit = True
                        break

            # Regular character - add to current word
            current_word.append(char)
            i -= 1

        # Don't forget the last word
        if current_word and not boundary_hit:
            word = "".join(reversed(current_word))
            word_lower = word.lower().rstrip(".,;:")
            word_clean = word.rstrip(".,;:")

            should_include = (
                (word_clean and word_clean[0].isupper())
                or word_lower in legal_stopwords
                or word_lower.rstrip(".") in legal_abbreviations
            )
            if should_include:
                words.insert(0, word)

        if not words:
            return None

        plaintiff = " ".join(words).strip(" ,;:")

        # Clean up any remaining artifacts
        plaintiff = re.sub(r"^[,;:\s]+", "", plaintiff)
        plaintiff = re.sub(r"[,;:\s]+$", "", plaintiff)

        if debug:
            logger.warning(f"[BACKWARD-V] Extracted plaintiff: '{plaintiff}'")

        # Now extract defendant (forward from 'v.')
        # Find where 'v.' ends
        v_end = v_position
        while v_end < len(text) and text[v_end : v_end + 2] in ["v.", "v ", "V.", "V "]:
            v_end += 2
        while v_end < len(text) and text[v_end] in " \t":
            v_end += 1

        # Get text after 'v.' (up to 150 chars)
        text_after_v = text[v_end : min(len(text), v_end + 150)]

        # Extract defendant using similar logic (but forward)
        defendant_words = []
        for word in text_after_v.split():
            word_clean = word.rstrip(".,;:()[]")
            word_lower = word_clean.lower()

            # Stop at citation (number followed by reporter)
            if word_clean and word_clean[0].isdigit():
                # Check if this looks like a citation
                if re.match(r"\d+$", word_clean):
                    # Might be start of citation - check next words
                    break

            # Stop at year in parentheses
            if re.match(r"\(\d{4}\)", word):
                break

            should_include = (
                (word_clean and word_clean[0].isupper())
                or word_lower in legal_stopwords
                or word_lower.rstrip(".") in legal_abbreviations
            )

            if should_include:
                defendant_words.append(word_clean)
            elif defendant_words:
                # Already have words, hit non-matching word
                break

        if not defendant_words:
            return None

        defendant = " ".join(defendant_words).strip(" ,;:")

        if debug:
            logger.warning(f"[BACKWARD-V] Extracted defendant: '{defendant}'")

        # Combine into full case name
        if plaintiff and defendant and len(plaintiff) >= 3 and len(defendant) >= 3:
            case_name = f"{plaintiff} v. {defendant}"
            if debug:
                logger.warning(f"[BACKWARD-V] Full case name: '{case_name}'")
            return case_name

        return None

    def _setup_patterns(self):
        """Setup the most comprehensive, battle-tested regex patterns."""

        # Unicode-aware character classes (from unified_extraction_architecture.py)
        self.apostrophe_chars = r"[\'\u2019\u2018\u201A\u201B\u2032\u2035\u201C\u201D\u201E\u201F\u2033\u2034\u2036\u2037\u2039\u203A\u00B4\u0060\u02B9\u02BB\u02BC\u02BD\u02BE\u02BF\u055A\u055B\u055C\u055D\u055E\u055F\u05F3]"
        self.ampersand_chars = r"[&\u0026\uFF06\u204A\u214B]"
        self.hyphen_chars = r"[-\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]"
        self.period_chars = r"[.\u002E\u2024\u2025\u2026\u2027]"
        self.space_chars = r"[\s\u0020\u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u200C\u200D\u200E\u200F\u2028\u2029\u202A\u202B\u202C\u202D\u202E\u202F]"

        # Comprehensive legal character class
        self.legal_chars = f"[a-zA-Z0-9{self.apostrophe_chars[1:-1]}{self.ampersand_chars[1:-1]}{self.hyphen_chars[1:-1]}{self.period_chars[1:-1]}{self.space_chars[1:-1]}]"

        # Best patterns from all implementations
        # FIX #37: Made ALL quantifiers NON-GREEDY (added ?) and reduced max lengths from 80 to 40
        # to prevent matching past the context window and capturing the NEXT case name instead of
        # the one BEFORE the citation. This was the root cause of "183 Wn.2d 649" extracting
        # "Spokane County" (116 chars AFTER) instead of "Lopez Demetrio" (40 chars BEFORE).
        self.case_name_patterns = [
            # PRIORITY 0: Complex legal names with full party descriptions (HIGHEST PRIORITY - MOVED TO TOP)
            # Matches: "Chance Gresser, individually and as parent, natural guardian, next of friendand on behalf of his daughter, C.G., and Erin Gresser, individually and asparent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center"
            # Matches: "Francis Rudnicki and Pamela Rudnicki, as parents, guardians and next friends of Alexander Rudnicki, a minor v. Bianco"
            r"([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:individually|as\s+(?:parent|guardian|next\s+friend|administrator|executor|trustee|personal\s+representative)|and\s+on\s+behalf\s+of|by\s+and\s+through)[^,]*)*)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:d/b/a|doing\s+business\s+as|a\s+(?:Delaware|California|New\s+York)\s+(?:Corporation|Corp|Inc|LLC|Ltd))[^,]*)*)",
            # PRIORITY 0A: "In re" cases with full party names (HIGH PRIORITY)
            # Matches: "In re: The PEOPLE of the State of Colorado v. Regina M. SPRINKLE"
            r"In\s+re:\s+([A-Z][A-Z\s\'&\-\.,]+)\s+[Vv]\.?\s+([A-Z][A-Z\s\'&\-\.,]+)",
            # PRIORITY 0B: Complex estate and multi-party cases
            # Matches: "ESTATE OF MELVIN JOSEPH LONG, by and through MARLA HUDSON LONG, Administratrix, v. JAMES D. FOWLER"
            # This fixes the "Long v. Fowler" false extraction issue
            r"(ESTATE\s+OF\s+[A-Z][A-Z\s\'&\-\.,]+(?:,\s+by\s+and\s+through\s+[A-Z][A-Z\s\'&\-\.,]+(?:,\s+[A-Z][a-zA-Z\s\'&\-\.,]+)?)?)\s+[Vv]\.?\s+([A-Z][A-Z\s\'&\-\.,]+)",
            r"(Estate\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]+(?:,\s+by\s+and\s+through\s+[A-Z][a-zA-Z\s\'&\-\.,]+(?:,\s+[A-Z][a-zA-Z\s\'&\-\.,]+)?)?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)",
            # PRIORITY 0C: ALL CAPS case names (common in court documents)
            # Matches: "CMTY. LEGAL SERVICES V . U.S. HHS" or "COMMUNITY LEGAL SERVICES V. UNITED STATES"
            r"([A-Z][A-Z\'\.\&\s\-,]{2,150})\s+[Vv]\.?\s+([A-Z][A-Z\'\.\&\s\-,]{2,150})",
            # PRIORITY 1: Standard citation format - match case name immediately before citation
            # Use lookbehind to ensure sentence boundary without capturing non-case-name text
            # Matches: "Spokeo, Inc. v. Robins, 578 U.S. 330" or "Raines v. Byrd, 521 U.S. 811"
            # FIXED: Made patterns GREEDY to capture full legal names with complex party descriptions
            # FIX #69: Added [Vv]\.? to handle both "v." and "V ." variations
            r"(?:(?<=\.)\s+|(?<=\?)\s+|(?<=!)\s+|^)([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)(?:,\s*\d+)",
            # PRIORITY 2: Corporate patterns with full name capture
            # FIX #68D: Removed ? to make greedy
            r"([A-Z][a-zA-Z\s\'&\-\.,]+,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)(?:\s*,)",
            # PRIORITY 3: Standard v. patterns with comma
            # FIX #68D: Removed ? to make greedy
            r"(?:In\s+re\s+)?([A-Z][a-zA-Z\'\.\&\s\-,]{2,150})\s+[Vv]\.?\s+([A-Z][a-zA-Z\'\.\&\s\-,]{2,150})(?:\s*,)",
            # PRIORITY 4: Enhanced patterns (from clustering)
            # FIX #68D: Removed ? to make greedy
            r"(?:In\s+re\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,150})\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,150})",
            # In re patterns (title case and all caps)
            r"In\s+re\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)",
            r"In\s+re\s+(?:Marriage\s+of\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)",
            r"IN\s+RE\s+([A-Z][A-Z\s\'&\-\.,]{2,40}?)",
            # State patterns (title case and all caps)
            r"State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30}?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)",
            r"([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)\s+[Vv]\.?\s+State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30}?)",
            r"STATE\s+(?:OF\s+)?([A-Z][A-Z\s]{2,30}?)\s+[Vv]\.?\s+([A-Z][A-Z\s\'&\-\.,]{2,40}?)",
            # Government patterns - made defendant pattern greedy to capture full names
            r"([A-Z][a-zA-Z\s\'&\-\.,]*?)\s+[Vv]\.?\s+(United\s+States|U\.S\.|UNITED\s+STATES)",
            r"(United\s+States|U\.S\.|UNITED\s+STATES)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)",  # Made greedy to get full defendant
        ]

        # Context detection patterns - MUST match case name format (Name v. Name)
        # FIX #37: Made quantifiers non-greedy to prevent overmatch
        # FIX #69: Added [Vv]\.? to handle both "v." and "V ." variations
        self.context_patterns = [
            # Standard format: "Case Name, Citation"
            r"([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+\s+[A-Za-z.]+\s+\d+",
            # With year: "Case Name, Citation (Year)"
            r"([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?)\s*,\s*\d+\s+[A-Za-z.]+(?:\s+\d+)?\s*\(\d{4}\)",
            # Signal words: "See Case Name, Citation"
            r"(?:In|The case of|As stated in|Citing|Following|See)\s+([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+",
            # ALL CAPS format
            r"([A-Z][A-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][A-Z\s\'&\-\.,]+?),\s*\d+\s+[A-Za-z.]+\s+\d+",
        ]

        # Year patterns
        self.year_patterns = [
            r"\((\d{4})\)",  # (2020)
            r",\s*(\d{4})",  # , 2020
            r"(\d{4})\s*\)",  # 2020)
        ]

    def extract_case_name_and_date(
        self,
        text: str,
        citation: Optional[str] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        debug: bool = False,
    ) -> MasterExtractionResult:
        """
        THE MASTER EXTRACTION FUNCTION

        This is THE ONLY function that should be used for case name extraction.
        It consolidates all the best features from duplicate functions.

        Args:
            text: Full document text
            citation: Citation text (if available)
            start_index: Start position of citation
            end_index: End position of citation
            debug: Enable debug logging

        Returns:
            MasterExtractionResult with extracted case name and date
        """
        # CRITICAL DEBUG: Log EVERY call to verify this method is being used
        logger.error(f"[DEBUG] [MASTER_EXTRACT ENTRY] citation='{citation}', start_index={start_index}")

        # FIX #33: ALWAYS log for "183 Wn.2d 649" to trace the bug
        force_debug = citation and "183" in citation and "649" in citation
        if debug or force_debug:
            logger.warning(
                f"[DEBUG] MASTER_EXTRACT: Starting unified extraction for '{citation}' at {start_index}-{end_index}"
            )
            if force_debug:
                logger.warning(f"[DEBUG] FIX #33 DEBUG: This is the problematic citation!")
                logger.warning(f"   Text at position: '{text[start_index:start_index+50] if start_index else 'N/A'}'")
                logger.warning(
                    f"   Text before (50 chars): '{text[start_index-50:start_index] if start_index and start_index >= 50 else 'N/A'}'"
                )

        # Normalize text to handle Unicode issues
        normalized_text = self._normalize_text(text)

        # USER FIX: Strategy -1 - Simple citation format (NEW - PREPROCESSING)
        # Handle case where user submits just "Case Name, Citation (Year)" without context
        # Pattern: "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
        if citation:
            simple_pattern = r"^([A-Z][a-zA-Z\s\'&\-,\.]+\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-,\.]+),\s+\d+\s+[A-Z][a-z\.]+\d*\s+\d+\s*\((\d{4})\)\s*$"
            match = re.match(simple_pattern, text.strip())
            if match:
                extracted_name = match.group(1).strip()
                extracted_year = match.group(2)
                logger.warning(
                    f"[SUCCESS] [SIMPLE-FORMAT] Extracted from standalone citation: '{extracted_name}' ({extracted_year})"
                )
                return MasterExtractionResult(
                    case_name=extracted_name,
                    year=extracted_year,
                    confidence=0.95,
                    method="simple_citation_format",
                    debug_info={"pattern": "standalone_citation"},
                    extracted_case_name=extracted_name,
                    extracted_year=extracted_year,
                )

        # FIX NOV 9: Strategy -0.5 - Special citation format handling (NEW - PRE-PROCESSING)
        # Handle patterns that commonly fail: string citations, cert. denied, WestLaw with docket, etc.
        if citation:
            if start_index is None:
                logger.error(f"[SPECIAL-FORMATS] ⚠️ Citation '{citation}' has NO start_index, trying to find it...")
                # Try to find the citation in the text
                escaped_citation = re.escape(citation)
                match = re.search(escaped_citation, text)
                if match:
                    start_index = match.start()
                    logger.error(f"[SPECIAL-FORMATS] ✅ Found '{citation}' at position {start_index}")
                else:
                    logger.error(f"[SPECIAL-FORMATS] ❌ Could not find '{citation}' in text, skipping Strategy -0.5")

            if start_index is not None:
                logger.error(f"[SPECIAL-FORMATS] ✨ CALLING Strategy -0.5 for '{citation}' at position {start_index}")
                try:
                    result = self._extract_special_citation_formats(
                        text, citation, start_index, bool(debug or force_debug)
                    )
                    logger.error(
                        f"[SPECIAL-FORMATS] 🔙 Strategy -0.5 RETURNED for '{citation}' - result type: {type(result)}"
                    )
                    if result and result.case_name and result.case_name != "N/A":
                        logger.error(f"[SUCCESS] ✅ Strategy -0.5 extracted: '{result.case_name}'")
                        return result
                    else:
                        logger.error(
                            f"[SPECIAL-FORMATS] ❌ Strategy -0.5 returned nothing for '{citation}' - result={result}"
                        )
                except Exception as e:
                    logger.error(f"[SPECIAL-FORMATS] 💥 EXCEPTION in Strategy -0.5: {e}")
                    import traceback

                    logger.error(f"[SPECIAL-FORMATS] Traceback: {traceback.format_exc()}")

        # FIX #69: Strategy 0 - Comma-anchored extraction (NEW - HIGHEST PRIORITY)
        # Use comma before citation as anchor to work backwards and find full case name
        # This fixes truncation issues like "E. Palo Alto v. U." → "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't..."
        if citation and start_index is not None:
            if force_debug:
                logger.warning(f"[DEBUG] FIX #69: Trying Strategy 0 - Comma-anchored extraction")
            result = self._extract_with_comma_anchor(text, citation, start_index, bool(debug or force_debug))
            if result and result.case_name and result.case_name != "N/A":
                # Validate extraction against canonical metadata
                self._validate_extraction(result, citation, bool(debug or force_debug))
                if force_debug:
                    logger.warning(f"[SUCCESS] FIX #69: Strategy 0 succeeded! Extracted: '{result.case_name}'")
                return result

        # Strategy 1: Position-aware extraction (best accuracy)
        if start_index is not None and end_index is not None:
            if force_debug:
                logger.warning(f"[DEBUG] FIX #33: Trying Strategy 1 - Position-aware extraction")
            # FIX #43: CRITICAL - Use ORIGINAL text, not normalized!
            # Normalization removes line breaks (\n → space), shifting ALL positions!
            # Indices are calculated from original text, so MUST use original text for slicing!
            result = self._extract_with_position(
                text, citation or "", start_index, end_index, bool(debug or force_debug)
            )
            if result and result.case_name and result.case_name != "N/A":
                # Validate extraction against canonical metadata if available
                if citation:
                    self._validate_extraction(result, citation, bool(debug or force_debug))
                if force_debug:
                    logger.warning(f"[SUCCESS] FIX #33: Strategy 1 succeeded! Extracted: '{result.case_name}'")
                    logger.warning(f"   extracted_case_name: '{result.extracted_case_name}'")
                    logger.warning(f"   canonical_name: '{result.canonical_name}'")
                return result

        # Strategy 2: Context-based extraction (fallback)
        if citation:
            # FIX #43: Use ORIGINAL text for same reason as Strategy 1
            result = self._extract_with_citation_context(text, citation, debug)
            if result and result.case_name and result.case_name != "N/A":
                # Validate extraction against canonical metadata
                self._validate_extraction(result, citation, debug)
                return result

        # Strategy 3: Pattern-based extraction (last resort)
        result = self._extract_with_patterns(normalized_text, citation, debug)
        if result and result.case_name and result.case_name != "N/A":
            return result

        # DEC 2025: Strategy 3.5 - Backward extraction from "v." position
        # This catches cases where regex patterns fail but "v." exists in context
        # Works backwards including capitalized words, legal stopwords, and abbreviations
        if start_index is not None:
            # Get broad context around citation
            context_start = max(0, start_index - 350)
            context_end = min(len(text), start_index + 150)
            broad_context = text[context_start:context_end]

            # Find "v." in the context (before the citation position)
            v_matches = list(re.finditer(r"\s+v\.\s+", broad_context, re.IGNORECASE))
            if v_matches:
                # Take the last "v." before the citation position
                relative_citation_pos = start_index - context_start
                best_v_match = None
                for m in v_matches:
                    if m.start() < relative_citation_pos:
                        best_v_match = m

                if best_v_match:
                    # Convert to absolute position and extract
                    abs_v_pos = context_start + best_v_match.start()
                    backward_case_name = self._extract_case_name_backward_from_v(text, abs_v_pos, debug)

                    if backward_case_name and len(backward_case_name) > 10:
                        logger.warning(f"[BACKWARD-V-STRATEGY] Extracted: '{backward_case_name}'")
                        # Extract year from context
                        year = self._extract_year_from_context(text[start_index : start_index + 100], debug)

                        result = MasterExtractionResult(
                            case_name=backward_case_name,
                            year=year or "Unknown",
                            confidence=0.7,
                            method="backward_v_extraction",
                            debug_info={"v_position": abs_v_pos},
                            canonical_name=None,
                            canonical_year=None,
                            extracted_case_name=backward_case_name,
                            extracted_year=year,
                        )
                        return result

        # FIX 2024-11-08: Strategy 4 - VERY aggressive fallback extraction with broader context
        # This catches citations that slip through normal extraction (headers/footers, unusual formatting)
        if start_index is not None:
            # Try with much broader context window (800 chars instead of 300)
            broad_start = max(0, start_index - 400)
            broad_end = min(len(text), start_index + 400)
            broad_context = text[broad_start:broad_end]

            # Use very simple pattern: any "X v. Y" within the broad window
            simple_pattern = r"([A-Z][A-Za-z\'\.\s&,-]{3,60}\s+v\.?\s+[A-Z][A-Za-z\'\.\s&,-]{3,60})"
            matches = re.findall(simple_pattern, broad_context)

            if matches:
                # Take the first match as the most likely case name
                candidate = matches[0].strip()
                # Quick validation
                if len(candidate) > 10 and len(candidate) < 150:
                    logger.warning(f"[AGGRESSIVE-FALLBACK] Found candidate: '{candidate}'")
                    result = MasterExtractionResult(
                        case_name=candidate,
                        year="Unknown",
                        confidence=0.5,  # Medium-low confidence for aggressive extraction
                        method="aggressive_fallback",
                        debug_info={"reason": "Broad pattern match"},
                        canonical_name=None,
                        canonical_year=None,
                        extracted_case_name=candidate,
                        extracted_year=None,
                    )
                    return result

        # No extraction succeeded - but we might have verification data!
        logger.warning(f"[WARNING] [EXTRACTION-FAILED] All strategies failed for citation: '{citation}'")

        # FIX #MISMATCH: Try to get canonical metadata as last resort
        if citation:
            canonical_metadata = self._get_canonical_metadata(citation)
            if canonical_metadata and canonical_metadata.get("canonical_name"):
                logger.warning(
                    f"[INFO] [CANONICAL-FALLBACK] Using canonical name for failed extraction: {canonical_metadata['canonical_name']}"
                )
                return MasterExtractionResult(
                    case_name=canonical_metadata["canonical_name"],
                    year=canonical_metadata.get("canonical_date", "N/A"),
                    confidence=0.8,  # High confidence since it's from canonical source
                    method="canonical_fallback",
                    debug_info={"reason": "Extraction failed, used canonical metadata"},
                    canonical_name=canonical_metadata["canonical_name"],
                    canonical_year=canonical_metadata.get("canonical_date"),
                    extracted_case_name="N/A",  # Mark that extraction failed
                    extracted_year="N/A",
                )

        # NEW: Instead of returning "N/A", try to provide a useful fallback name
        # This helps users understand what was found even if extraction failed
        fallback_name = self._generate_fallback_case_name(citation)
        fallback_year = self._extract_year_from_citation(citation)

        return MasterExtractionResult(
            case_name=fallback_name,
            year=fallback_year,
            confidence=0.3,  # Low confidence for fallback
            method="fallback_generated",
            debug_info={
                "reason": "All extraction strategies failed and no canonical metadata available",
                "fallback_generated": True,
                "original_citation": citation,
            },
            canonical_name=None,
            canonical_year=None,
            extracted_case_name=fallback_name,  # Use fallback instead of N/A
            extracted_year=fallback_year,
        )

    def _extract_special_citation_formats(
        self, text: str, citation: str, start_index: int, debug: bool
    ) -> Optional[MasterExtractionResult]:
        """
        FIX NOV 9: Handle special citation formats that commonly fail extraction.

        Patterns handled:
        1. String citations: "Name, 123 Rep 456, 789 Rep2 012"
        2. cert. denied/review granted: "123 Rep 456, cert. denied, 789 Rep2 012"
        3. WestLaw with docket: "Name, No. XX-XXXXX, 2019 WL 123456"
        4. Signal words: "accord Name, 123 Rep 456"
        5. Parenthetical citations: "(quoting Name, 123 Rep 456)"
        """
        context_before = text[max(0, start_index - 500) : start_index]
        context_after = text[start_index : min(len(text), start_index + 200)]

        # Normalize whitespace for better pattern matching
        context_clean = re.sub(r"\s+", " ", context_before)

        logger.error(f"[SPECIAL-FORMATS] 🔍 Analyzing context for '{citation}'")
        logger.error(f"[SPECIAL-FORMATS] Context (last 150 chars): ...{context_clean[-150:]}")
        logger.error(f"[SPECIAL-FORMATS] Citation starts at position: {start_index}")

        # PATTERN 1: STRING CITATIONS
        # "Erickson v. Pharmacia, LLC, 31 Wn. App. 2d 100, 110-11, 548 P.3d 226"
        # IMPROVED: Take LAST match (closest to citation) and handle company suffixes
        # FIX DEC 2025 v4: Only accept matches in last 150 chars to avoid grabbing wrong case
        # FIX DEC 2025 v5: Skip Pattern 1 if there's a case name ("v.") in last 60 chars
        # This indicates the immediate pre-citation context has a case name that comma anchor can handle better
        last_60 = context_clean[-60:] if len(context_clean) >= 60 else context_clean
        has_immediate_case_name = bool(re.search(r"\s+v\.\s+", last_60, re.IGNORECASE))
        if has_immediate_case_name:
            logger.error(f"[SPECIAL-FORMATS] Pattern 1 SKIP: Found 'v.' in last 60 chars - deferring to comma anchor")

        string_pattern = r"([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+\s+[A-Za-z.\s]+\d+"
        matches = list(re.finditer(string_pattern, context_clean)) if not has_immediate_case_name else []
        if matches:
            # Take LAST match (closest to our citation)
            match = matches[-1]
            # FIX DEC 2025 v4: PROXIMITY CHECK - match must end within last 150 chars of context
            # This prevents grabbing case names from earlier citations in a long context
            match_end_distance = len(context_clean) - match.end()
            if match_end_distance > 150:
                logger.error(f"[SPECIAL-FORMATS] Pattern 1 SKIP: match too far ({match_end_distance} chars from end)")
            else:
                case_name = match.group(1).strip()
                logger.error(f"[SPECIAL-FORMATS] Pattern 1 raw match (last of {len(matches)}): '{case_name}'")

                # IMPROVED: Two-step extraction - first try to isolate just the case name
                case_name_match = re.search(
                    r"([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE
                )
                if not case_name_match:
                    case_name_match = re.search(r"(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)

                if case_name_match:
                    case_name = case_name_match.group(1).strip()
                    case_name = re.sub(r"[,\s]+$", "", case_name)  # Clean trailing punctuation
                    logger.error(f"[SPECIAL-FORMATS] ✅ STRING CITATION (refined): '{case_name}'")
                    year = self._extract_year_from_context(context_after, debug)
                    return MasterExtractionResult(
                        case_name=case_name,
                        year=year or "N/A",
                        confidence=0.85,
                        method="string_citation",
                        debug_info={"pattern": "multiple_reporters"},
                        extracted_case_name=case_name,
                        extracted_year=year,
                    )

                # FALLBACK: If refinement failed but we have "v." or "in re", use raw match
                elif "v." in case_name.lower() or "in re" in case_name.lower():
                    logger.error(f"[SPECIAL-FORMATS] ⚠️  STRING CITATION (unrefined): '{case_name}'")
                    year = self._extract_year_from_context(context_after, debug)
                    return MasterExtractionResult(
                        case_name=case_name,
                        year=year or "N/A",
                        confidence=0.7,  # Lower confidence for unrefined extraction
                        method="string_citation_unrefined",
                        debug_info={"pattern": "multiple_reporters_fallback"},
                        extracted_case_name=case_name,
                        extracted_year=year,
                    )

        # PATTERN 2: CERT. DENIED / REVIEW GRANTED
        # "796 P.2d 421 (1990), cert. denied, 498 U.S. 941"
        # Need to look BEFORE "cert. denied" for the primary case
        if re.search(r"(?:cert\.|certiorari)\s+denied|review\s+granted", context_clean, re.IGNORECASE):
            logger.error(f"[SPECIAL-FORMATS] Pattern 2: Found cert. denied/review granted pattern")
            # Look further back for the primary case name
            broader_context = text[max(0, start_index - 800) : start_index]
            broader_clean = re.sub(r"\s+", " ", broader_context)

            # Find last "v." pattern before cert. denied
            v_patterns = re.findall(r"([A-Z][^,;\n]{10,100}\s+v\.\s+[^,;\n]{10,100})", broader_clean)
            if v_patterns:
                case_name = v_patterns[-1].strip()
                case_name = self._clean_case_name(case_name)
                logger.error(f"[SPECIAL-FORMATS] ✅ CERT. DENIED: '{case_name}'")
                year = self._extract_year_from_context(broader_context[-300:], debug)
                return MasterExtractionResult(
                    case_name=case_name,
                    year=year or "N/A",
                    confidence=0.8,
                    method="cert_denied",
                    debug_info={"pattern": "cert_denied_review_granted"},
                    extracted_case_name=case_name,
                    extracted_year=year,
                )

        # PATTERN 3: WESTLAW WITH DOCKET NUMBER
        # "Nazar v. Harbor Freight Tools USA Inc., No. 2:18-CV-00348-SMJ, 2019 WL 2066127"
        # IMPROVED: Take LAST match and handle company suffixes
        docket_pattern = r"([A-Z][^,]{10,150}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*No\.?\s+[\w:/-]+"
        matches = list(re.finditer(docket_pattern, context_clean, re.IGNORECASE))
        if matches:
            match = matches[-1]
            case_name = match.group(1).strip()
            logger.error(f"[SPECIAL-FORMATS] Pattern 3 raw match (last of {len(matches)}): '{case_name}'")

            # IMPROVED: Two-step extraction
            case_name_match = re.search(
                r"([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE
            )
            if not case_name_match:
                case_name_match = re.search(r"(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)

            if case_name_match:
                case_name = case_name_match.group(1).strip()
                case_name = re.sub(r"[,\s]+$", "", case_name)
                logger.error(f"[SPECIAL-FORMATS] ✅ WESTLAW WITH DOCKET (refined): '{case_name}'")
                year = self._extract_year_from_context(context_after, debug)
                return MasterExtractionResult(
                    case_name=case_name,
                    year=year or "N/A",
                    confidence=0.9,
                    method="westlaw_docket",
                    debug_info={"pattern": "westlaw_with_docket"},
                    extracted_case_name=case_name,
                    extracted_year=year,
                )

            # FALLBACK: Use raw match if it contains "v." or "in re"
            elif "v." in case_name.lower() or "in re" in case_name.lower():
                logger.error(f"[SPECIAL-FORMATS] ⚠️  WESTLAW WITH DOCKET (unrefined): '{case_name}'")
                year = self._extract_year_from_context(context_after, debug)
                return MasterExtractionResult(
                    case_name=case_name,
                    year=year or "N/A",
                    confidence=0.75,
                    method="westlaw_docket_unrefined",
                    debug_info={"pattern": "westlaw_docket_fallback"},
                    extracted_case_name=case_name,
                    extracted_year=year,
                )

        # PATTERN 4: SIGNAL WORDS
        # "accord Goad v. Celotex Corp., 831 F.2d 508"
        # IMPROVED: Take LAST match and handle company suffixes
        # CRITICAL FIX: Skip if there's an immediate case name (v. in last 60 chars) - defer to comma anchor
        if not has_immediate_case_name:
            signal_words = ["accord", "see", "see also", "compare", "citing", "but see", "cf.", "e.g.", "e.g"]
            for signal in signal_words:
                signal_pattern = rf"\b{re.escape(signal)}\b\s+([A-Z][^,]{{10,150}}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+\s+[A-Za-z.\s]+\d+"
                matches = list(re.finditer(signal_pattern, context_clean, re.IGNORECASE))
                if matches:
                    match = matches[-1]
                    # CRITICAL FIX: Check if the match is close enough to the citation
                    # If signal word match is >100 chars from the citation, skip it
                    match_end_distance = len(context_clean) - match.end()
                    if match_end_distance > 100:
                        logger.error(
                            f"[SPECIAL-FORMATS] Pattern 4 SKIP: signal '{signal}' match too far ({match_end_distance} chars from citation)"
                        )
                        continue
                    case_name = match.group(1).strip()
                    logger.error(
                        f"[SPECIAL-FORMATS] Pattern 4 (signal '{signal}') raw match (last of {len(matches)}): '{case_name}'"
                    )

                    # IMPROVED: Two-step extraction
                    case_name_match = re.search(
                        r"([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE
                    )
                    if not case_name_match:
                        case_name_match = re.search(r"(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)

                    if case_name_match:
                        case_name = case_name_match.group(1).strip()
                        case_name = re.sub(r"[,\s]+$", "", case_name)
                        logger.error(f"[SPECIAL-FORMATS] ✅ SIGNAL WORD '{signal}' (refined): '{case_name}'")
                        year = self._extract_year_from_context(context_after, debug)
                        return MasterExtractionResult(
                            case_name=case_name,
                            year=year or "N/A",
                            confidence=0.85,
                            method="signal_word",
                            debug_info={"pattern": f"signal_{signal}", "signal_word": signal},
                            extracted_case_name=case_name,
                            extracted_year=year,
                        )

                    # FALLBACK: Use raw match if it contains "v." or "in re"
                    elif "v." in case_name.lower() or "in re" in case_name.lower():
                        logger.error(f"[SPECIAL-FORMATS] ⚠️  SIGNAL WORD '{signal}' (unrefined): '{case_name}'")
                        year = self._extract_year_from_context(context_after, debug)
                        return MasterExtractionResult(
                            case_name=case_name,
                            year=year or "N/A",
                            confidence=0.7,
                            method="signal_word_unrefined",
                            debug_info={"pattern": f"signal_{signal}_fallback", "signal_word": signal},
                            extracted_case_name=case_name,
                            extracted_year=year,
                        )

        # PATTERN 5: PARENTHETICAL CITATIONS
        # "(quoting In re Marriage of Williams, 115 Wn.2d 202)"
        # Look inside parentheses
        if "(" in context_clean[-100:] and ")" not in context_clean[-100:]:
            paren_pattern = r"\(\s*(?:quoting|citing|see|accord)\s+([A-Z][^,]{{10,120}}?),\s*\d+\s+[A-Za-z.\s]+\d+\s*$"
            match = re.search(paren_pattern, context_clean, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                case_name = self._clean_case_name(case_name)
                if "v." in case_name.lower() or "in re" in case_name.lower():
                    logger.error(f"[SPECIAL-FORMATS] ✅ PARENTHETICAL: '{case_name}'")
                    year = self._extract_year_from_context(context_after, debug)
                    return MasterExtractionResult(
                        case_name=case_name,
                        year=year or "N/A",
                        confidence=0.8,
                        method="parenthetical",
                        debug_info={"pattern": "parenthetical_citation"},
                        extracted_case_name=case_name,
                        extracted_year=year,
                    )

        logger.error(f"[SPECIAL-FORMATS] ❌ No special patterns matched for '{citation}'")
        return None

    def _validate_extraction(self, result: MasterExtractionResult, citation: str, debug: bool) -> None:
        """
        FIX #MISMATCH: Validate extracted name against canonical metadata.

        This helps identify extraction errors by comparing what we extracted
        with what the authoritative source says. Logs warnings for significant mismatches.

        Args:
            result: The extraction result to validate
            citation: The citation being validated
            debug: Enable debug logging
        """
        if not citation or not result.case_name or result.case_name == "N/A":
            return

        # Get canonical metadata
        canonical_metadata = self._get_canonical_metadata(citation)
        if not canonical_metadata or not canonical_metadata.get("canonical_name"):
            return  # No canonical data to validate against

        canonical_name = canonical_metadata["canonical_name"]
        extracted_name = result.case_name

        # Normalize for comparison
        norm_extracted = extracted_name.lower().strip().replace("  ", " ")
        norm_canonical = canonical_name.lower().strip().replace("  ", " ")

        # Check if names are similar (handle abbreviations)
        if norm_extracted == norm_canonical:
            return  # Perfect match

        # Check for common abbreviations
        abbreviations = {
            "ins": "immigration and naturalization service",
            "dep't": "department",
            "att'y": "attorney",
            "gen.": "general",
        }

        exp_extracted = norm_extracted
        exp_canonical = norm_canonical
        for abbr, full in abbreviations.items():
            exp_extracted = exp_extracted.replace(abbr, full)
            exp_canonical = exp_canonical.replace(abbr, full)

        if exp_extracted == exp_canonical:
            return  # Match after abbreviation expansion

        # Check if extracted is contained in canonical (partial extraction)
        if len(norm_extracted) > 10 and norm_canonical.find(norm_extracted) >= 0:
            logger.info(f"[INFO] [PARTIAL-MATCH] Extracted name is subset of canonical for {citation}")
            return  # Acceptable partial match

        # Check if canonical is contained in extracted (over-extraction)
        if len(norm_canonical) > 10 and norm_extracted.find(norm_canonical) >= 0:
            logger.info(f"[INFO] [OVER-EXTRACTION] Extracted name contains canonical for {citation}")
            return  # Acceptable over-extraction

        # Check last names match (common for abbreviated forms)
        extracted_parts = norm_extracted.split(" v. ")
        canonical_parts = norm_canonical.split(" v. ")
        if len(extracted_parts) == 2 and len(canonical_parts) == 2:
            ext_last = extracted_parts[0].split()[-1]
            can_last = canonical_parts[0].split()[-1]
            if ext_last == can_last:
                logger.info(f"[INFO] [LASTNAME-MATCH] Last names match for {citation}, likely abbreviation")
                return

        # Significant mismatch detected - log warning
        logger.warning(f"[WARNING] [EXTRACTION-MISMATCH] Possible extraction error for {citation}")
        logger.warning(f"   Extracted: '{extracted_name}'")
        logger.warning(f"   Canonical: '{canonical_name}'")
        logger.warning(f"   Method: {result.method}")
        logger.warning(f"   Confidence: {result.confidence}")

        # Store canonical data in result for reference
        result.canonical_name = canonical_name
        result.canonical_year = canonical_metadata.get("canonical_date")

    def _filter_header_contamination(self, context: str, debug: bool) -> str:
        """
        FIX #67: Remove document headers and metadata that contaminate extraction.

        CRITICAL FIX: Only filter lines that are PURE headers, not case discussion.
        Lines with case names (containing "v.") should NEVER be filtered.

        Filters out lines containing:
        - Court identifiers IN ALL CAPS: "SUPREME COURT" (but not "Supreme Court")
        - Filing metadata headers: "FILED", "FILE ", "CLERK'S OFFICE"
        - Dates in header format
        - Pure all-caps lines (likely headers)
        - Document numbers and case numbers in header format

        Args:
            context: Raw context text around citation
            debug: Enable debug logging

        Returns:
            Filtered context with headers removed
        """
        # ALWAYS log to confirm this is being called
        logger.error(f"[FIX #67] FILTERING CALLED! Context length: {len(context) if context else 0}")

        if not context or len(context.strip()) == 0:
            return context

        original_context = context
        lines = context.split("\n")
        filtered_lines = []

        # CRITICAL: Case name pattern - lines containing this should NEVER be filtered
        case_name_pattern = r"\bv\.\s+[A-Z]"  # " v. " followed by capital letter

        # Header patterns to exclude - ONLY for pure headers, not case discussion
        header_patterns = [
            r"^\s*[A-Z\s,\.\-]{10,}$",  # All-caps lines (at least 10 chars, only caps/spaces/punctuation)
            r"^\s*IN THE .+ COURT\s*$",  # Pure court header lines (start of line)
            r"^\s*FILED:?\s*\d",  # "FILED: 01/15/2024"
            r"^\s*CLERK['\']?S? OFFICE\s*$",  # Pure clerk line
            r"^\s*No\.\s+\d+-\d+\s*$",  # Pure case number like "No. 102976-4" (alone on line)
            r"^\s*\d{1,2}/\d{1,2}/\d{4}\s*$",  # Pure date stamps
            r"^\s*[A-Z]{3,}\s+\d{1,2},\s+\d{4}\s*$",  # "JUNE 12, 2025" (alone on line)
            # ENHANCED: Filter case caption patterns with role words
            # These are headers like "CARTER, Respondent, v. MARY E. JONES, Appellant"
            r"^[A-Z][A-Z\s&\.\-',]+\s+(?:Respondent|Appellant|Petitioner|Appellee|Plaintiff|Defendant)s?\s*,\s+v\.\s+[A-Z][A-Za-z\s\.\-',]+\s+(?:Respondent|Appellant|Petitioner|Appellee|Plaintiff|Defendant)s?,?$",
        ]

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # CRITICAL: Never filter lines containing case names (have " v. ")
            # UNLESS they're case caption headers with role words
            if re.search(case_name_pattern, line_stripped):
                # ENHANCED: Check if this is a case caption header (has role words)
                line_upper = line_stripped.upper()
                has_role_words = any(
                    role in line_upper
                    for role in ["RESPONDENT", "APPELLANT", "PETITIONER", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                )
                # Check pattern like "NAME, ROLE v. NAME, ROLE"
                caption_pattern = r"^[A-Z][A-Z\s&\.\-',]+\s+(?:RESPONDENT|APPELLANT|PETITIONER|APPELLEE|PLAINTIFF|DEFENDANT)S?\s*,\s+V\.\s+[A-Z][A-Z\s&\.\-',]+\s+(?:RESPONDENT|APPELLANT|PETITIONER|APPELLEE|PLAINTIFF|DEFENDANT)S?,?$"
                is_caption_header = has_role_words and re.search(caption_pattern, line_upper)
                
                if not is_caption_header:
                    # Regular case discussion line - keep it
                    filtered_lines.append(line)
                    if debug:
                        logger.warning(f"[FIX #67] KEPT case name line: '{line_stripped[:80]}'")
                    continue
                else:
                    # This is a case caption header - filter it out
                    if debug:
                        logger.warning(f"[FIX #67] FILTERING case caption header: '{line_stripped[:80]}'")
                    continue

            # Check if line matches any header pattern
            is_header = False
            for pattern in header_patterns:
                if re.search(pattern, line_stripped):
                    is_header = True
                    if debug:
                        logger.warning(f"[FIX #67] Filtering header line: '{line_stripped[:80]}'")
                    break

            # Also filter very short lines (< 8 chars) that are likely headers (lowered from 10)
            if not is_header and len(line_stripped) < 8:
                is_header = True
                if debug:
                    logger.warning(f"[FIX #67] Filtering short line: '{line_stripped}'")

            if not is_header:
                filtered_lines.append(line)

        filtered_context = "\n".join(filtered_lines)

        if debug and filtered_context != original_context:
            logger.warning(f"[FIX #67] Context filtering:")
            logger.warning(f"  Original length: {len(original_context)} chars")
            logger.warning(f"  Filtered length: {len(filtered_context)} chars")
            logger.warning(f"  Removed: {len(original_context) - len(filtered_context)} chars")

        return filtered_context

    def _normalize_whitespace_for_extraction(self, context: str, debug: bool) -> str:
        """
        FIX #68: Normalize whitespace and PDF artifacts to handle PDF line breaks.

        PDF text extraction often inserts line breaks (\n) in the middle of case names
        that aren't visible in the rendered PDF. It also includes Unicode artifacts
        like � (U+FFFD replacement character) for smart quotes.

        Example issues:
            1. Line breaks: "E. Palo Alto v. U.S. Dep't\nof Health" → truncates at \n
            2. Unicode artifacts: "Dep�t" (should be "Dep't") → breaks regex patterns

        This method:
        1. Replaces all newlines with spaces
        2. Replaces common PDF Unicode artifacts (�) with apostrophes
        3. Normalizes various quote characters to standard quotes
        4. Collapses multiple spaces into single spaces
        5. Preserves punctuation and case

        Args:
            context: Context text (after header filtering)
            debug: Enable debug logging

        Returns:
            Context with normalized whitespace and characters
        """
        if not context or len(context.strip()) == 0:
            return context

        original_context = context

        # FIX #9: Enhanced line break handling for citations split across lines
        # Handles: "17 F.\n4th 901" → "17 F. 4th 901"
        # Replace newlines with spaces
        # This allows case names that span multiple lines to be captured as a single string
        normalized = context.replace("\n", " ")

        # Replace tabs with spaces
        normalized = normalized.replace("\t", " ")

        # FIX #9b: Collapse multiple spaces that result from line break removal
        # "F.  4th" → "F. 4th" (ensures proper citation format)
        normalized = re.sub(r"\s{2,}", " ", normalized)

        # FIX #68B: Replace common PDF Unicode artifacts
        # � (U+FFFD) is the Unicode replacement character used when PDF can't encode properly
        # These often appear in place of apostrophes or other special characters
        normalized = normalized.replace("\ufffd", "'")  # Unicode replacement character → apostrophe
        normalized = normalized.replace("�", "'")  # Also handle as direct character

        # Normalize various quote characters to standard ASCII quotes
        normalized = normalized.replace("\u2018", "'")  # Left single quote
        normalized = normalized.replace("\u2019", "'")  # Right single quote (smart apostrophe)
        normalized = normalized.replace("\u201c", '"')  # Left double quote
        normalized = normalized.replace("\u201d", '"')  # Right double quote
        normalized = normalized.replace("\u00b4", "'")  # Acute accent (often used as apostrophe)
        normalized = normalized.replace("\u0060", "'")  # Grave accent (often used as apostrophe)

        # Collapse multiple spaces into single spaces
        # Use regex to handle any sequence of whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Trim leading/trailing whitespace
        normalized = normalized.strip()

        if debug and normalized != original_context:
            logger.warning(f"[FIX #68] Whitespace/character normalization:")
            logger.warning(f"  Original: '{original_context[:100]}...'")
            logger.warning(f"  Normalized: '{normalized[:100]}...'")
            logger.warning(f"  Removed {original_context.count(chr(10))} newlines")
            if "�" in original_context or "\ufffd" in original_context:
                logger.warning(f"  Fixed Unicode replacement characters")

        return normalized

    def _extract_with_comma_anchor(
        self, text: str, citation: str, start_index: int, debug: bool
    ) -> Optional[MasterExtractionResult]:
        """
        FIX #69: Extract case name using comma before citation as anchor.

        Most inline citations follow format: "Case Name, Citation"
        Example: "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897"

        This method fixes the pattern start matching problem where regex incorrectly starts at "E. Palo Alto"
        instead of "Cmty. Legal Servs. in E. Palo Alto" because it sees ". E" as a sentence boundary.

        Strategy:
        1. Find comma immediately before citation (within 10 chars)
        2. Work backwards from comma to find case name
        3. Case name ends at comma, starts after sentence boundary or previous citation

        Args:
            text: Full document text (original, not normalized)
            citation: Citation string (e.g., "780 F. Supp. 3d 897")
            start_index: Position of citation in text
            debug: Enable debug logging

        Returns:
            MasterExtractionResult if extraction succeeds, None otherwise
        """
        # FIX #69 DEBUG: ALWAYS log entry to verify method is called
        logger.error(f"[FIX #69 ENTRY] Citation: '{citation}', Start: {start_index}, Text len: {len(text)}")
        print(f"[PHASE6-ENTRY] Comma anchor called for: {citation} at pos {start_index}", flush=True)

        # Step 1: Find comma before citation (within 100 chars, allowing for whitespace and semicolons)
        # PHASE 6 FIX: Increased from 10 to 100 to handle:
        #   - Pinpoint citations like ", 157"
        #   - Semicolon-separated citation series (semicolon can be 40+ chars before citation)
        pre_citation_text = text[max(0, start_index - 100) : start_index]

        # CRITICAL FIX: Detect previous citations in pre_citation_text and truncate after them
        # This prevents extracting case names from earlier citations
        citation_pattern = r"\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.|F\.(?:2d|3d|4th)?|Wn\.(?:2d)?|P\.(?:2d|3d)?)\s+\d+"
        prev_citations = list(re.finditer(citation_pattern, pre_citation_text))
        if prev_citations:
            last_prev_cit = prev_citations[-1]
            # Truncate pre_citation_text to start after the last previous citation
            truncate_pos = last_prev_cit.end()
            # Look for closing paren and comma after the citation
            after_cit = pre_citation_text[truncate_pos : truncate_pos + 20]
            paren_match = re.search(r"\(\d{4}\)\s*,?\s*", after_cit)
            if paren_match:
                truncate_pos += paren_match.end()
            pre_citation_text = pre_citation_text[truncate_pos:].lstrip()
            print(
                f"[PHASE6-PREV-CIT] Found previous citation, truncated pre_citation_text to: '{pre_citation_text}'",
                flush=True,
            )

        # FIX DEC 2025 v3: Normalize newlines in pre-citation text
        # PDF extraction often produces "Case Name,\n179 Wn.2d" with newlines
        # This breaks comma detection and pattern matching
        pre_citation_text = re.sub(r"\s+", " ", pre_citation_text)

        # FIX #69 DEBUG: Log what we're checking for comma
        logger.error(f"[FIX #69 COMMA CHECK] Pre-citation text: '{pre_citation_text}'")
        logger.error(f"[FIX #69 COMMA CHECK] Text at citation pos: '{text[start_index:start_index+50]}'")

        if "," not in pre_citation_text:
            logger.error(f"[FIX #69 FAIL] No comma found in '{pre_citation_text}' - falling back")
            print(f"[PHASE6-FAIL] No comma in 100 chars before {citation}: '{pre_citation_text}'", flush=True)
            return None  # No comma anchor, fall back to other methods
        else:
            print(f"[PHASE6-OK] Found comma in pre-text: '{pre_citation_text}'", flush=True)

        # PHASE 6 FIX: Check for semicolons FIRST (they separate different cases)
        # If there's a semicolon in the pre-text, only search for comma AFTER the last semicolon
        # Example: "Cayuga..., 761 F.3d 218; Oneida..., 605 F.3d 149"
        #                          comma1 ↑    semicolon ↑    comma2 ↑ (we want comma2)
        if ";" in pre_citation_text:
            # Find the LAST semicolon (in case there are multiple citation groups)
            last_semicolon_offset = pre_citation_text.rfind(";")
            print(f"[PHASE6] Semicolon found in pre-text - searching for comma after it", flush=True)

            # Only search for comma AFTER the last semicolon
            text_after_semicolon = pre_citation_text[last_semicolon_offset + 1 :]
            if "," in text_after_semicolon:
                comma_offset_after_semicolon = text_after_semicolon.rfind(",")
                # Calculate absolute position
                comma_pos = start_index - (
                    len(pre_citation_text) - last_semicolon_offset - 1 - comma_offset_after_semicolon
                )
                print(f"[PHASE6] Found comma after semicolon", flush=True)
            else:
                print(f"[PHASE6] No comma after semicolon - falling back", flush=True)
                return None
        else:
            # No semicolon - just find the last comma in the pre-text
            comma_offset = pre_citation_text.rfind(",")
            comma_pos = start_index - (len(pre_citation_text) - comma_offset)

        # FIX #69 DEBUG: Always log comma position
        logger.error(f"[FIX #69 SUCCESS] Found comma at position {comma_pos} (citation at {start_index})")

        # Step 2: Detect subsequent history and expand context if needed
        # Subsequent history indicators: "affirmed by", "reversed by", "vacated by", etc.
        subsequent_history_phrases = [
            r"judgment\s+vacated\s+(?:and\s+opinion\s+)?(?:repudiated\s+)?by",
            r"(?:aff['\u2019]?d|affirmed)(?:\s+(?:in\s+part|by))?",
            r"(?:rev['\u2019]?d|reversed)(?:\s+(?:in\s+part|by))?",
            r"(?:vacated|remanded)(?:\s+(?:and\s+remanded|by))?",
            r"overruled\s+by",
            r"superseded\s+by",
            r"modified\s+by",
            r"cert\.\s+(?:denied|granted)(?:\s+by)?",
        ]

        # Check for subsequent history in the 200 chars before the citation
        check_window = text[max(0, comma_pos - 200) : comma_pos]
        has_subsequent_history = False

        for phrase_pattern in subsequent_history_phrases:
            if re.search(phrase_pattern, check_window, re.IGNORECASE):
                has_subsequent_history = True
                logger.error(f"[FIX #7 SUBSEQUENT] Detected subsequent history: '{phrase_pattern}'")
                break

        # USER FIX: Work backwards from citation with expanding window
        # Start with reasonable window (100 chars), expand if no case name found
        # This is the FIRST attempt - the fallback section handles expansion
        # Standard: 100 chars (start reasonable), Subsequent history: 150 chars
        context_window = 150 if has_subsequent_history else 100
        search_start = max(0, comma_pos - context_window)
        potential_case_name = text[search_start:comma_pos]

        # FIX DEC 2025 v3: Normalize newlines in context (PDF extraction artifact)
        potential_case_name = re.sub(r"\s+", " ", potential_case_name)

        # FIX #69 DEBUG: Always log context
        logger.error(f"[FIX #69 CONTEXT] Length: {len(potential_case_name)} chars (window: {context_window})")
        logger.error(f"[FIX #69 CONTEXT] Last 100: '{potential_case_name[-100:]}'")

        # USER FIX: Handle "vacated and remanded" pattern
        # When Supreme Court citations follow "vacated and remanded", extract case name from BEFORE vacatur
        vacatur_patterns = [
            r"vacated\s+and\s+remanded",
            r"vacated",
            r"aff\'d",
            r"affirmed",
            r"reversed",
            r"rev\'d",
            r"remanded",
        ]

        if debug:
            logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Checking for vacatur patterns before citation '{citation}'")

        for vacatur_pattern in vacatur_patterns:
            vacatur_match = re.search(vacatur_pattern, potential_case_name, re.IGNORECASE)
            if debug:
                logger.warning(
                    f"🔍 VACATUR_COMMA_ANCHOR: Pattern '{vacatur_pattern}' -> {'FOUND' if vacatur_match else 'NOT FOUND'}"
                )

            if vacatur_match:
                # USER FIX: Check if there's a semicolon between vacatur and citation
                # Semicolons separate different cases - don't apply vacatur across this boundary
                text_after_vacatur = potential_case_name[vacatur_match.end() :]
                if ";" in text_after_vacatur:
                    if debug:
                        logger.warning(
                            f"🔍 VACATUR_COMMA_ANCHOR: SEMICOLON found between vacatur and citation - SKIPPING vacatur logic"
                        )
                    continue  # Skip this vacatur pattern - it's for a different case

                # Found vacatur - extract case name BEFORE it
                text_before_vacatur = potential_case_name[: vacatur_match.start()]

                # Look for case name pattern: "Name v. Name, ### F.3d"
                case_name_pattern = r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*),\s+\d+\s+F\."
                case_matches = list(re.finditer(case_name_pattern, text_before_vacatur))

                if debug:
                    logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Found {len(case_matches)} matches before vacatur")
                    if case_matches:
                        for idx, match in enumerate(case_matches):
                            logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Match {idx+1}: '{match.group(0)}'")

                if case_matches:
                    # Take LAST match (closest to vacatur)
                    last_match = case_matches[-1]
                    plaintiff = last_match.group(1).strip()
                    defendant = last_match.group(2).strip()

                    # Clean case names
                    from src.utils.text_normalizer import clean_extracted_case_name

                    plaintiff = clean_extracted_case_name(plaintiff)
                    defendant = clean_extracted_case_name(defendant)
                    vacatur_case_name = f"{plaintiff} v. {defendant}"

                    if debug:
                        logger.warning(f"✅ VACATUR_COMMA_ANCHOR: Detected '{vacatur_pattern}'")
                        logger.warning(f"✅ VACATUR_COMMA_ANCHOR: Extracted '{vacatur_case_name}'")

                    # Validate
                    if len(plaintiff) >= 3 and len(defendant) >= 3 and len(vacatur_case_name) > 10:
                        # USER FIX: For Supreme Court citations, look for year AFTER the current citation
                        # Example: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
                        # The year (2011) is at the END of all parallel citations

                        # Check if this is a Supreme Court citation (U.S., S.Ct., L.Ed.)
                        is_supreme_court = (
                            any(x in citation for x in ["U.S.", "S. Ct.", "L. Ed."]) if citation else False
                        )

                        year = None

                        if is_supreme_court:
                            # For Supreme Court citations, look for year AFTER current citation
                            # This handles parallel citations like "562 U.S. 42, 131 S. Ct. 704 (2011)"
                            after_citation_text = text[start_index : start_index + 200]
                            year = self._extract_year_from_context(after_citation_text, debug)

                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")

                        # Fallback: Extract from Federal reporter citation
                        if not year:
                            fed_match_end_pos = last_match.end()
                            year_search_text = text_before_vacatur[fed_match_end_pos : fed_match_end_pos + 50]
                            year = self._extract_year_from_context(year_search_text, debug)

                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found year '{year}' from Federal citation")

                        if debug:
                            logger.warning(f"🔍 VACATUR_YEAR: Final extracted year '{year}' for '{vacatur_case_name}'")

                        logger.error(f"[VACATUR_SUCCESS] Returning: '{vacatur_case_name}' ({year}) for '{citation}'")
                        return MasterExtractionResult(
                            case_name=vacatur_case_name,
                            year=year or "Unknown",
                            confidence=0.98,
                            method="vacatur_comma_anchor",
                            debug_info={"vacatur_pattern": vacatur_pattern, "year": year},
                            extracted_case_name=vacatur_case_name,
                            extracted_year=year,
                        )

                if debug:
                    logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Found '{vacatur_pattern}' but no case name match")
                break  # Only check first matching vacatur pattern

        # Step 3: Normalize whitespace and Unicode artifacts (Fix #68)
        potential_case_name = self._normalize_whitespace_for_extraction(potential_case_name, debug)
        logger.error(f"[FIX #69 NORMALIZED] Length: {len(potential_case_name)} chars")

        # FIX #11/#13: Clean case/docket numbers from context BEFORE pattern matching
        # This prevents header contamination like "No. 103430 -0 15" from breaking patterns
        # NOTE: Don't add digits to patterns - that would capture page numbers!
        context_cleaned = potential_case_name

        # FIX #13: More aggressive case number removal
        # Pattern: "No. 103430-0 15 v." where the case number has internal spaces/breaks
        # Strategy: Remove ANY sequence of "No." + [digits/hyphens/spaces] that ends before " v."
        # This handles: "Inc. No. 103430-0 15 v. Marston" → "Inc. v. Marston"
        context_cleaned = re.sub(r"\s+No\.\s+[\d\-\s]+(?=\s+v\.)", " ", context_cleaned, flags=re.IGNORECASE)

        # Remove case numbers after "v." (from page headers)
        context_cleaned = re.sub(r"\s+\d+\s+No\.\s+[\d\-]+\s+", " ", context_cleaned, flags=re.IGNORECASE)
        context_cleaned = re.sub(r"\s+No\.\s+[\d\-\s]+\-[\d\-\s]+\s+", " ", context_cleaned, flags=re.IGNORECASE)

        if context_cleaned != potential_case_name:
            logger.error(f"[FIX #11] Cleaned case numbers from context")
            logger.error(f"[FIX #11] Before: '{potential_case_name[-100:]}'")
            logger.error(f"[FIX #11] After:  '{context_cleaned[-100:]}'")

        # Step 4: FIX #8 - Proximity-based case name extraction
        # Find ALL candidate case names and pick the CLOSEST one to the citation

        # Define patterns for case names (not anchored to end)
        # IMPORTANT: NO DIGITS in patterns - page numbers would match!
        patterns = [
            # Pattern 0: "See [Case Name]" - HIGHEST PRIORITY
            (
                r"(?:See|see|Citing|citing|Compare|compare)\s+([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})",
                0,
                "signal_word",
            ),
            # Pattern 1: "In re" cases - ENHANCED for better coverage
            (r"(In\s+re\s+[A-Z][a-zA-Z0-9\s\'&\-\.,]{5,})", 1, "in_re"),
            # Pattern 1b: FALLBACK "In re" cases - more permissive
            (r"(In\s+re\s+[A-Z][a-zA-Z\s]{3,}(?:\s+[A-Z][a-zA-Z\s]*)*)", 1, "in_re_fallback"),
            # Pattern 2: "Ex parte" cases
            (r"(Ex\s+parte\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})", 1, "ex_parte"),
            # Pattern 2a: Case names at end of sentence or clause - MORE PRECISE
            # Matches: "...cited in Smith v. Johnson" where case name is at end
            (
                r"\b([A-Z][a-zA-Z\s\'&\-\.,]{5,40}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,40})(?=[,.;]|\s+(?:and|or|which|that|who|where|when|in|on|at|by|for|to|of)\b|$)",
                2,
                "end_clause",
            ),
            # Pattern 3: Standard case names - ENHANCED for better precision
            # OLD: r"([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})" - too broad
            # NEW: Added word boundaries and excluded common words to prevent false matches
            (
                r"\b([A-Z][a-zA-Z\s\'&\-\.,]{5,40}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,40})(?=\s|,|$)",
                3,
                "standard",
            ),
            # Pattern 4: FIX #12 - Short-form citations (single party name at END)
            # Matches: "... that [Endnote 18] Marston" where full case appears earlier
            # Only matches if at very end of context (last 20 chars) to avoid false positives
            # Accepts single capitalized word of 4+ chars (Marston, Smith, etc.)
            (r"([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]+)*)$", 10, "short_form"),
        ]

        # Find all candidate case names with their positions
        # FIX #11: Use cleaned context for pattern matching AND position calculations
        candidates = []
        for pattern, priority, pattern_type in patterns:
            for match in re.finditer(pattern, context_cleaned, re.IGNORECASE):
                case_name = match.group(1).strip()
                # FIX #11b: Use cleaned context length for distance calculation
                distance_from_end = len(context_cleaned) - match.end()

                # FIX #8: Check if this crosses a section header boundary
                # FIX #11b: Use cleaned context for boundary check
                # PHASE 6 FIX: Add semicolon as boundary - semicolons separate different cases in legal citations
                # Example: "See Cayuga...; Oneida...; Hamaatsa..." - each case is separated by semicolon
                text_after_match = context_cleaned[match.end() :]
                has_semicolon = ";" in text_after_match[:200]
                has_section_header = bool(re.search(r"\n\s*[A-Z][A-Z\s]{3,}\n", text_after_match[:200]))

                # FIX DEC 2025: Check for INTERVENING CITATIONS between this case name and the target citation
                # If another citation appears between a candidate case name and the target, that candidate
                # is for a DIFFERENT case and should be heavily penalized.
                # Example: "Shavlik v. Dawson Place, 11 Wn. App. 2d 250...Manufactured Housing v. State, 142 Wn.2d 347"
                #          "Shavlik" has intervening "11 Wn. App. 2d 250", so should NOT be selected for "142 Wn.2d 347"
                # Pattern matches common citation formats: "123 Wn.2d", "456 P.3d", "789 F.3d", etc.
                # FIX DEC 2025 v2: EXCLUDE the target citation itself from this check!
                # Otherwise we incorrectly penalize "Sargent v. Seattle, 179 Wn.2d 376" when extracting for "179 Wn.2d 376"
                intervening_citation_pattern = r"\d+\s+(?:Wn\.?\s*(?:2d|App\.?\s*2d)?|P\.?\s*[23]d|F\.?\s*(?:2d|3d|4th|Supp\.?)|U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.)"
                # Find all citation matches in text after case name
                intervening_matches = re.findall(intervening_citation_pattern, text_after_match[:150], re.IGNORECASE)
                # Filter out matches that are part of the target citation
                has_intervening_citation = False
                for interv_match in intervening_matches:
                    # Check if this match is NOT part of the target citation
                    if interv_match.strip() not in citation:
                        has_intervening_citation = True
                        break

                crosses_boundary = has_semicolon or has_section_header or has_intervening_citation

                # PHASE 6 DEBUG
                if has_semicolon:
                    logger.error(f"[PHASE6] SEMICOLON detected after '{case_name[:30]}' - applying boundary penalty")
                if has_intervening_citation:
                    logger.error(
                        f"[FIX DEC 2025] INTERVENING CITATION detected after '{case_name[:30]}' - applying boundary penalty"
                    )

                candidates.append(
                    {
                        "name": case_name,
                        "distance": distance_from_end,
                        "priority": priority,
                        "pattern_type": pattern_type,
                        "position": match.start(),
                        "crosses_boundary": crosses_boundary,
                    }
                )

        # FIX #8 DEBUG: Log all candidates
        if candidates:
            logger.error(f"[FIX #8] Found {len(candidates)} candidate case names")
            for idx, cand in enumerate(candidates):
                logger.error(
                    f"  Candidate {idx+1}: '{cand['name'][:50]}' (distance: {cand['distance']}, priority: {cand['priority']}, boundary: {cand['crosses_boundary']})"
                )

        # FIX #8: Score and sort candidates
        # Lower score = better match
        # FIX DEC 2025: Heavily penalize distance to prefer CLOSEST case name
        for cand in candidates:
            # Distance penalty: exponential growth to strongly prefer closest match
            # A case name 50 chars away scores much better than one 150 chars away
            distance_penalty = cand["distance"] * 5  # Multiply distance by 5 for stronger penalty

            score = (
                cand["priority"] * 100  # Pattern priority (0-2) x100 (reduced from x1000)
                + distance_penalty  # Distance from citation (heavily weighted)
                + (10000 if cand["crosses_boundary"] else 0)  # Heavy penalty for crossing boundaries
            )
            cand["score"] = score

        # Sort by score (ascending - lower is better)
        candidates.sort(key=lambda x: x["score"])

        # Pick the best candidate
        best_match = None
        if candidates:
            best_match = candidates[0]
            logger.error(f"[FIX #8 SELECTED] Best match: '{best_match['name'][:50]}' (score: {best_match['score']})")

        if best_match:
            # Step 5: Extract and clean the best match
            case_name = best_match["name"]

            # FIX #8 DEBUG: Log the selected case name
            logger.error(f"[FIX #8 EXTRACTED] Raw: '{case_name[:100]}'")

            # Step 6: Clean the case name
            case_name = self._clean_case_name(case_name)
            logger.error(f"[FIX #8 CLEANED] After clean: '{case_name[:100]}'")
            
            # ENHANCED: Extract just the case name from longer sentences
            # If we got something like "This was later cited in Smith v. Johnson",
            # extract just "Smith v. Johnson"
            if len(case_name) > 30 and " v. " in case_name:
                # Check if this looks like a sentence with signal words
                signal_words = ["see", "citing", "cited", "referenced", "following", "compare", "accord", "quoting", "holding", "stating", "noting", "observing", "finding", "concluding", "ruling", "precedent", "decision", "established", "as", "in", "the", "court", "ruled"]
                lower_case = case_name.lower()
                
                # If signal words are present, try to extract just the case name
                if any(word in lower_case for word in signal_words):
                    # Find all case names in the text and take the last one
                    # Use a more precise pattern that doesn't match the whole sentence
                    case_name_matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", case_name)
                    if case_name_matches:
                        # Take the last (most recent) case name found
                        extracted_case = case_name_matches[-1].strip()
                        # Double check that this looks like a proper case name
                        if " v. " in extracted_case and len(extracted_case) < 60:
                            logger.error(f"[FIX #8 SENTENCE CLEAN] Extracted '{extracted_case}' from '{case_name}'")
                            case_name = extracted_case

            # Step 7: Remove common citation introducers and signal phrases
            introducer_patterns = [
                r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                r"^See\s+also\s+",  # "See also"
                r"^See\s+generally\s+",  # "See generally"
                r"^But\s+see\s+",  # "But see"
                r"^(?:See|Citing|Quoting|Following|E\.g\.,)\s+",  # "quoting Kidwell..." → "Kidwell..."
                r"^(?:see|citing|quoting|following|e\.g\.,)\s+",  # lowercase versions
                r"^Cf\.?\s+",  # "Cf."
                r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
            ]

            original_name = case_name
            for intro_pattern in introducer_patterns:
                case_name = re.sub(intro_pattern, "", case_name, flags=re.IGNORECASE)

            if case_name != original_name:
                logger.error(f"[FIX #8 INTRODUCER] Removed introducer: '{original_name[:50]}' -> '{case_name[:50]}'")

            # Step 8: Validate it looks like a case name
            if not self._looks_like_case_name(case_name, debug):
                logger.error(f"[FIX #8 VALIDATION FAIL] Doesn't look like case name: '{case_name[:100]}'")

                # CRITICAL FALLBACK: Try "In re" specific extraction if validation failed
                if debug:
                    logger.error(f"[FIX #8 IN-RE FALLBACK] Attempting 'In re' fallback extraction...")

                in_re_fallback = self._extract_in_re_fallback(text, citation, start_index, debug)
                if in_re_fallback:
                    logger.error(f"[FIX #8 IN-RE FALLBACK] SUCCESS: Found '{in_re_fallback.case_name}'")
                    return in_re_fallback

                return None  # No valid match found

            logger.error(f"[FIX #8 VALIDATION OK] Passed validation!")

            # Step 9: Extract year from context after citation
            year_context = text[start_index : start_index + 100]
            year = self._extract_year_from_context(year_context, debug)

            logger.error(f"[FIX #8 FINAL] Case name: '{case_name}' ({len(case_name)} chars), Year: {year}")

            # Step 10: Apply canonical preferences if available
            preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                citation,
                case_name,
                year,
            )
            canonical_year_value = extract_year_value(
                canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
            )

            print(f"[PHASE6-RETURN] Comma anchor returning: '{preferred_name or case_name}'", flush=True)
            return MasterExtractionResult(
                case_name=preferred_name or "N/A",
                year=preferred_year or "N/A",
                confidence=0.9,  # High confidence - proximity-based selection
                method="comma_anchored_proximity",
                context=f"...{potential_case_name[-100:]}",
                debug_info={
                    "comma_position": comma_pos,
                    "case_name_length": len(case_name),
                    "pattern_type": best_match["pattern_type"],
                    "distance": best_match["distance"],
                    "score": best_match["score"],
                    "canonical": canonical_meta,
                },
                canonical_name=canonical_meta.get("canonical_name"),
                canonical_year=canonical_year_value,
                extracted_case_name=case_name,
                extracted_year=year,
            )

        # FIX #8 DEBUG: Log when no candidates found
        logger.error(f"[FIX #8 NO MATCH] No candidate case names found in {context_window} char window")
        logger.error(f"[FIX #8 NO MATCH] Context was: '{potential_case_name[-200:]}'")

        # USER FIX: EXPANDING WINDOW FALLBACK
        # If tight window found nothing, progressively expand: 40 → 80 → 120 → 200
        expansion_sizes = [80, 120, 200] if context_window < 80 else [200]
        for expand_size in expansion_sizes:
            if context_window >= expand_size:
                continue
            logger.error(f"[EXPANDING-WINDOW] Expanding from {context_window} to {expand_size} chars")
            expanded_start = max(0, comma_pos - expand_size)
            expanded_context = text[expanded_start:comma_pos]
            expanded_context = self._normalize_whitespace_for_extraction(expanded_context, debug)

            # Try finding case names in expanded context
            for pattern, priority, pattern_type in patterns:
                for match in re.finditer(pattern, expanded_context, re.IGNORECASE):
                    case_name = match.group(1).strip()
                    case_name = self._clean_case_name(case_name)

                    if self._looks_like_case_name(case_name, debug):
                        logger.error(f"[FIX #8 FALLBACK SUCCESS] Found in expanded window: '{case_name}'")
                        year = self._extract_year_from_context(text[start_index : start_index + 100], debug)
                        return MasterExtractionResult(
                            case_name=case_name,
                            year=year or "N/A",
                            confidence=0.7,  # Lower confidence for expanded window
                            method="comma_anchored_expanded",
                            debug_info={"expanded_window": True},
                            extracted_case_name=case_name,
                            extracted_year=year,
                        )

        return None

    def _looks_like_case_name(self, text: str, debug: bool) -> bool:
        """
        FIX #69: Validate that extracted text looks like a real case name.

        Checks:
        1. Contains " v. " (plaintiff v. defendant) OR starts with "In re" (USER FIX)
        2. Starts with capital letter
        3. Has reasonable length (10-200 chars)
        4. Doesn't contain obvious contamination
        5. Has proper party name structure

        Args:
            text: Potential case name to validate
            debug: Enable debug logging

        Returns:
            True if text looks like a case name, False otherwise
        """
        # FIX #69 DEBUG: Always log validation attempts
        logger.error(f"[FIX #69 VALIDATE] Checking: '{text[:100] if text else 'None'}'")
        print(f"[PHASE6-VALIDATION-START] Checking: '{text}'", flush=True)

        # USER FIX: Allow special case types in addition to " v. " cases
        # Support: "In re", "In the matter of", "Matter of", "Ex parte", "Estate of"
        text_lower = text.lower() if text else ""
        has_v_pattern = " v. " in text_lower
        is_special_case = (
            text_lower.startswith("in re ")
            or text_lower.startswith("in the matter of ")
            or text_lower.startswith("matter of ")
            or text_lower.startswith("ex parte ")
            or text_lower.startswith("estate of ")
        )

        if not text or (not has_v_pattern and not is_special_case):
            logger.error(f"[FIX #69 VALIDATE] FAIL: No ' v. ' or special case pattern in text")
            print(f"[PHASE6-VALIDATION-FAIL] No v. or special case pattern", flush=True)
            return False

        if len(text) < 10:
            logger.error(f"[FIX #69 VALIDATE] FAIL: Too short ({len(text)} chars)")
            return False

        if len(text) > 200:
            logger.error(f"[FIX #69 VALIDATE] FAIL: Too long ({len(text)} chars)")
            return False

        # Check if starts with capital letter
        if not text[0].isupper():
            logger.error(f"[FIX #69 VALIDATE] FAIL: Doesn't start with capital")
            return False

        # USER FIX: Only validate plaintiff/defendant structure for " v. " cases
        # For special cases, just validate they have content after the prefix
        if has_v_pattern:
            # Split into plaintiff and defendant
            v_lower = " v. "
            if v_lower not in text.lower():
                return False

            # Find "v." case-insensitively
            v_pos = text.lower().find(v_lower)
            plaintiff = text[:v_pos].strip()
            defendant = text[v_pos + len(v_lower) :].strip()

            # Both parts should have at least one word
            if len(plaintiff.split()) < 1 or len(defendant.split()) < 1:
                logger.error(f"[FIX #69 VALIDATE] FAIL: Plaintiff '{plaintiff}' or defendant '{defendant}' too short")
                return False
        elif is_special_case:
            # For special cases, validate content after prefix
            # Find which prefix it is and check content after it
            prefixes = {"in re ": 6, "in the matter of ": 17, "matter of ": 10, "ex parte ": 9, "estate of ": 10}

            for prefix, length in prefixes.items():
                if text_lower.startswith(prefix):
                    after_prefix = text[length:].strip()
                    if len(after_prefix) < 5:  # At least a few chars after prefix
                        logger.error(f"[FIX #69 VALIDATE] FAIL: '{prefix.strip()}' case too short after prefix")
                        return False
                    break

        # Check for obvious contamination
        # FIX: Be more specific - only reject if these appear at the start or as standalone phrases
        # Don't reject if they're part of "As established in" or "The court established"
        contamination_indicators = [
            "held that",
            "the court held that", 
            "the court has held",
            "the court argues",
            "the court found",
            "the court determined",
            "the court concluded",
            "the court reasoned",
            "this court",
            "in recent times",
            "in the present case",
            "for the purposes of",
            "as a matter of law",
        ]

        # text_lower already defined above
        for indicator in contamination_indicators:
            if indicator in text_lower:
                logger.error(f"[FIX #69 VALIDATE] FAIL: Contains contamination '{indicator}'")
                return False

        # FIX: Check if extracted name matches document's primary case name (CONTAMINATION)
        # CRITICAL: Skip contamination check if document_primary_case_name is too long (>50 chars)
        # This indicates it was incorrectly extracted and includes citation text
        doc_primary = self.document_primary_case_name
        if doc_primary and len(doc_primary) > 50:
            logger.warning(f"[CONTAMINATION-FILTER] Skipping - primary case name too long ({len(doc_primary)} chars)")
            doc_primary = None
        if doc_primary:
            logger.error(f"[CONTAMINATION-FILTER] Checking '{text[:80]}' against primary '{doc_primary[:80]}'")
            print(f"[PHASE6-CONTAMINATION-CHECK] Primary case: '{doc_primary}'", flush=True)
            contamination_result = self._is_document_case_contamination(text, True)  # Force debug
            if contamination_result:
                logger.error(f"[CONTAMINATION-FILTER] ✅ REJECTED: Matches document primary case")
                logger.error(f"[CONTAMINATION-FILTER]    Rejected text: '{text[:100]}'")
                print(
                    f"[PHASE6-VALIDATION-FAIL] Contamination: matches primary case '{self.document_primary_case_name}'",
                    flush=True,
                )
                return False
            else:
                logger.error(f"[CONTAMINATION-FILTER] ⚠️  Passed (no match): '{text[:80]}'")
        else:
            logger.error(f"[CONTAMINATION-FILTER] ⚠️  SKIPPED: No document primary case name set!")

        logger.error(f"[FIX #69 VALIDATE] SUCCESS: All checks passed!")
        print(f"[PHASE6-VALIDATION-PASS] All checks passed!", flush=True)
        return True

    def _extract_in_re_fallback(
        self, text: str, citation: str, start_index: int, debug: bool
    ) -> Optional[MasterExtractionResult]:
        """
        CRITICAL FALLBACK: Special extraction for "In re" cases that might be missed by main patterns.

        This method is called when the main extraction fails but we suspect this might be an "In re" case.
        It uses more permissive patterns specifically designed for "In re" citations.

        Args:
            text: Full document text
            citation: Citation string
            start_index: Position of citation in text
            debug: Enable debug logging

        Returns:
            MasterExtractionResult if "In re" case found, None otherwise
        """
        if debug:
            logger.error(f"[IN-RE-FALLBACK] Looking for 'In re' case before '{citation}' at position {start_index}")

        # Get text before citation (look back up to 200 chars)
        pre_citation_start = max(0, start_index - 200)
        pre_citation_text = text[pre_citation_start:start_index]

        if debug:
            logger.error(f"[IN-RE-FALLBACK] Pre-citation text: '{pre_citation_text}'")

        # More permissive "In re" patterns for fallback
        in_re_patterns = [
            # Standard "In re" pattern
            r"(In\s+re\s+[A-Z][a-zA-Z0-9\s\'&\-\.,]{5,})",
            # More permissive - allows shorter names
            r"(In\s+re\s+[A-Z][a-zA-Z\s]{3,})",
            # Very permissive - just "In re" followed by capitalized words
            r"(In\s+re\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
        ]

        for pattern in in_re_patterns:
            matches = list(re.finditer(pattern, pre_citation_text, re.IGNORECASE))
            if debug:
                logger.error(f"[IN-RE-FALLBACK] Pattern '{pattern}' found {len(matches)} matches")

            for match in matches:
                case_name = match.group(1).strip()

                # Validate this is a reasonable case name
                if len(case_name) >= 10 and case_name != "N/A":  # Minimum reasonable length
                    # Extract year from citation
                    year_match = re.search(r"\((19|20)\d{2}\)", citation)
                    year = year_match.group(0).strip("()") if year_match else "N/A"

                    if debug:
                        logger.error(f"[IN-RE-FALLBACK] SUCCESS: Found '{case_name}' with year {year}")

                    return MasterExtractionResult(
                        case_name=case_name,
                        year=year,
                        confidence=0.7,  # Lower confidence for fallback
                        method="in_re_fallback",
                        context=pre_citation_text[-100:],
                        debug_info={"pattern": pattern, "fallback_used": True},
                    )

        if debug:
            logger.error(f"[IN-RE-FALLBACK] No 'In re' case found")

        return None

    def _is_document_case_contamination(self, extracted_name: str, debug: bool) -> bool:
        """
        FIX: Detect if extracted case name is contaminated with document's primary case name.

        Contamination occurs when the extraction picks up the current document's case name
        instead of the cited case name. This happens because the document's case name
        appears frequently throughout the text near citations.

        Examples of contamination:
            - Document: "Gopher Media LLC v. Melone"
            - Citation: 890 F.3d 828
            - Extracted (WRONG): "MELONE California state court..."
            - Extracted (WRONG): "GOPHER MEDIA LLC v. MELONE Pacific Pictures Corp"

        Args:
            extracted_name: The case name that was extracted
            debug: Enable debug logging

        Returns:
            True if contaminated (should be rejected), False if clean
        """
        if not self.document_primary_case_name or not extracted_name:
            return False

        # Normalize both for comparison (case-insensitive, ignore punctuation)
        def normalize_for_comparison(name):
            # Remove common case name punctuation and spacing variations
            normalized = name.lower()
            normalized = re.sub(r"[,\.\s]+", " ", normalized)
            normalized = normalized.strip()
            return normalized

        extracted_normalized = normalize_for_comparison(extracted_name)
        primary_normalized = normalize_for_comparison(self.document_primary_case_name)

        # Strategy 1: Check if primary case name is CONTAINED in extracted name
        # Example: "GOPHER MEDIA LLC v. MELONE Pacific Pictures" contains "gopher media llc v melone"
        if primary_normalized in extracted_normalized:
            if debug:
                logger.warning(f"[CONTAMINATION-FILTER] Containment match:")
                logger.warning(f"  Extracted: '{extracted_name}'")
                logger.warning(f"  Primary: '{self.document_primary_case_name}'")
            return True

        # Strategy 2: Check if extracted name contains primary case's distinctive parts
        # Example: "MELONE Railroad Co." contains "melone" from "Gopher Media v. Melone"
        primary_parts = primary_normalized.split(" v ")
        if len(primary_parts) == 2:
            plaintiff = primary_parts[0].strip()
            defendant = primary_parts[1].strip()

            # If both plaintiff AND defendant appear in extracted name, it's contamination
            # Single match could be coincidence (e.g., "United States" appears often)
            if plaintiff in extracted_normalized and defendant in extracted_normalized:
                if debug:
                    logger.warning(f"[CONTAMINATION-FILTER] Both parties match:")
                    logger.warning(f"  Extracted: '{extracted_name}'")
                    logger.warning(f"  Primary plaintiff: '{plaintiff}', defendant: '{defendant}'")
                return True

            # FIX: Also check for distinctive words from PLAINTIFF
            # PHASE 6 FIX: Added common organizational/tribal words to prevent false matches
            # (e.g., "Cayuga Indian Nation" vs "Oneida Indian Nation" should not match on "indian nation")
            common_parties = [
                "united states",
                "state",
                "county",
                "city",
                "government",
                "people",
                "indian",
                "nation",
                "tribe",
                "tribal",
                "band",
                "company",
                "corporation",
                "incorporated",
                "limited",
                "association",
                "society",
            ]
            plaintiff_words = [word for word in plaintiff.split() if len(word) > 5]  # Very distinctive words
            for plaint_word in plaintiff_words:
                if plaint_word not in common_parties and plaint_word in extracted_normalized:
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] Plaintiff word match:")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Matched word: '{plaint_word}' from plaintiff '{plaintiff}'")
                    return True

            # If defendant is distinctive (>8 chars, not common) and appears, likely contamination
            # Common defendants like "United States" don't count
            # PHASE 6 FIX: Use same extended list as plaintiff check
            common_parties_def = [
                "united states",
                "state",
                "county",
                "city",
                "government",
                "indian",
                "nation",
                "tribe",
                "tribal",
                "band",
            ]

            # FIX: Check for ANY distinctive word from defendant, not just full name
            # "MELONE Railroad" should match defendant "andrew melone" via "melone"
            defendant_words = [word for word in defendant.split() if len(word) > 4]  # Significant words only
            for def_word in defendant_words:
                if def_word not in common_parties_def and def_word in extracted_normalized:
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] Defendant word match:")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Matched word: '{def_word}' from defendant '{defendant}'")
                    return True

            # Also check full defendant name (original logic)
            if len(defendant) > 8 and defendant not in common_parties_def and defendant in extracted_normalized:
                if debug:
                    logger.warning(f"[CONTAMINATION-FILTER] Full defendant match:")
                    logger.warning(f"  Extracted: '{extracted_name}'")
                    logger.warning(f"  Primary defendant: '{defendant}'")
                return True

        # Strategy 3: Check similarity ratio (fuzzy matching)
        # If names are >80% similar, likely contamination
        # Only check if both names have similar length (within 50%)
        len_ratio = min(len(extracted_normalized), len(primary_normalized)) / max(
            len(extracted_normalized), len(primary_normalized)
        )
        if len_ratio > 0.5:  # Similar length
            # Calculate simple similarity (word overlap)
            extracted_words = set(extracted_normalized.split())
            primary_words = set(primary_normalized.split())

            if len(primary_words) > 0:
                overlap = len(extracted_words & primary_words)
                similarity = overlap / len(primary_words)

                if similarity > 0.8:  # >80% of primary case words appear in extracted
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] High similarity ({similarity:.2%}):")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Primary: '{self.document_primary_case_name}'")
                    return True

        return False

    def _extract_with_position(
        self, text: str, citation: str, start_index: int, end_index: int, debug: bool
    ) -> Optional[MasterExtractionResult]:
        """Position-aware extraction with optimized context window."""
        # USER FIX 2024-10-21: Increase to 300 chars for vacatur pattern detection
        # 150 chars wasn't enough to reach both "vacated and remanded" AND the case name before it
        # Example: "Oneida v. Madison, 605 F.3d 149...vacated and remanded, 562 U.S. 42" needs ~200+ chars
        # CRITICAL FIX: Reduce context window to prevent citation association bug
        # 300 chars was too large and included other case discussions
        # 150 chars is sufficient for immediate case name context while preventing cross-contamination
        context_start = max(0, start_index - 150)  # FIXED: Reduced from 300 to 150 chars
        # FIX #38: ONLY look BACKWARD! Context must end at START of citation, not END!
        # Fix #32 used end_index which allowed 15 chars of forward context (citation length),
        # causing extraction of "Spokane County" (after citation) instead of "Lopez Demetrio" (before).
        context_end = start_index  # FIX #38: Context ends at citation START, not END!

        # FIX #42: CRITICAL - Log ACTUAL values used to create context
        if debug:
            logger.error(f"🔍 FIX #42: Creating context with:")
            logger.error(f"   start_index = {start_index}")
            logger.error(f"   end_index = {end_index}")
            logger.error(f"   context_start = {context_start} (start_index - 150)")
            logger.error(f"   context_end = {context_end} (should == start_index)")
            logger.error(f"   Slicing: text[{context_start}:{context_end}]")

        context = text[context_start:context_end]

        # CRITICAL FIX: Detect previous citations in context and truncate after them
        # This prevents extracting case names from earlier citations
        # Example: "Smith v. Jones, 500 U.S. 123 (1991)...Johnson v. Texas, 509 U.S. 350"
        # For 509 U.S. 350, we only want context AFTER "500 U.S. 123" ends
        citation_pattern = r"\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.|F\.(?:2d|3d|4th)?|Wn\.(?:2d)?|P\.(?:2d|3d)?)\s+\d+"
        prev_citations = list(re.finditer(citation_pattern, context))
        if prev_citations:
            # Find the last previous citation that ends before our target
            last_prev_cit = prev_citations[-1]
            # Truncate context to start after the last previous citation
            # Add some buffer to include year parenthetical: "(1991),"
            truncate_pos = last_prev_cit.end()
            # Look for closing paren and comma after the citation
            after_cit = context[truncate_pos : truncate_pos + 20]
            paren_match = re.search(r"\(\d{4}\)\s*,?\s*", after_cit)
            if paren_match:
                truncate_pos += paren_match.end()
            old_context = context
            context = context[truncate_pos:].lstrip()
            context_start = context_start + truncate_pos + (len(old_context) - truncate_pos - len(context))
            if debug:
                logger.warning(
                    f"[PREV-CIT-BOUNDARY] Found prev citation at {last_prev_cit.start()}-{last_prev_cit.end()}"
                )
                logger.warning(f"[PREV-CIT-BOUNDARY] Truncated context from '{old_context[-60:]}' to '{context}'")

        # TEMPORARILY DISABLED: Boundary detection was cutting off case names
        # Let's test with just reduced context windows first
        # debug_boundary = debug
        # if debug_boundary:
        #     logger.error(f"[BOUNDARY-DEBUG] Original context: '{context}'")
        #
        # # Look for natural sentence boundaries within the context
        # # Find the last period, newline, or double newline that's reasonably close to citation
        # boundary_patterns = [
        #     r'\. +[A-Z]',  # Period + space + capital (new sentence)
        #     r'\.\n',      # Period + newline
        #     r'\n\n',      # Double newline (paragraph break)
        #     r'\.  +',     # Period + multiple spaces
        # ]
        #
        # best_boundary_pos = -1
        # for pattern in boundary_patterns:
        #     matches = list(re.finditer(pattern, context))
        #     if matches:
        #         # Use the last boundary that's at least 30 characters from the end
        #         # This ensures we don't cut off the immediate case name context
        #         # Increased from 20 to 30 to avoid cutting off case names
        #         for match in matches:
        #             boundary_pos = match.end()
        #             if boundary_pos < len(context) - 30:  # Leave at least 30 chars before citation
        #                 # CRITICAL FIX: Don't cut off in the middle of a word
        #                 # Make sure we're not truncating a case name
        #                 if boundary_pos > 0 and boundary_pos < len(context):
        #                     # Check if we're cutting off a word (next char is not space)
        #                     next_char = context[boundary_pos] if boundary_pos < len(context) else ''
        #                     if next_char.isalpha():  # We're cutting off a word
        #                         continue  # Skip this boundary
        #         best_boundary_pos = max(best_boundary_pos, boundary_pos)
        #
        # # If we found a good boundary, truncate context to start after it
        # if best_boundary_pos > 0:
        #     old_context = context
        #     context = context[best_boundary_pos:]
        #     if debug_boundary:
        #         logger.error(f"[BOUNDARY-DEBUG] Truncated at boundary position {best_boundary_pos}")
        #         logger.error(f"[BOUNDARY-DEBUG] New context: '{context}'")

        # FIX #67: Filter out document headers and metadata
        # Headers often contain text like "SUPREME COURT CLERK", "FILED", etc. that contaminate extraction
        context = self._filter_header_contamination(context, debug)

        # FIX #68: Normalize whitespace to handle PDF line breaks
        # PDF extraction adds \n in the middle of case names, causing severe truncation
        # Example: "E. Palo Alto v. U.S. Dep't\nof Health" → "E. Palo Alto v. U.S. Dep't of Health"
        context = self._normalize_whitespace_for_extraction(context, debug)

        # PHASE 6 FIX: Check for semicolons in context (they separate different cases)
        # If there's a semicolon, only use text AFTER the last semicolon
        # Example: "Cayuga..., 761 F.3d 218; Oneida..., 605 F.3d 149"
        #          We want "Oneida" (after semicolon), not "Cayuga" (before)
        if ";" in context:
            last_semicolon_pos = context.rfind(";")
            print(
                f"[PHASE6-POSITION] Semicolon found at position {last_semicolon_pos} in context - using text after it",
                flush=True,
            )
            old_context = context
            context = context[last_semicolon_pos + 1 :]  # Only use text AFTER last semicolon
            # Strip leading/trailing whitespace and commas to help patterns match
            context = context.strip().rstrip(",").strip()
            print(f"[PHASE6-POSITION] Old context: '{old_context[-80:]}'", flush=True)
            print(f"[PHASE6-POSITION] New context (trimmed): '{context}'", flush=True)

            # IMPORTANT: After trimming, context_start is no longer accurate!
            # The trimmed context ends at start_index and has length len(context)
            # So it starts at: start_index - len(context)
            context_start = start_index - len(context)
            print(
                f"[PHASE6-POSITION] Adjusted context_start from {max(0, start_index - 300)} to {context_start}",
                flush=True,
            )

        # FIX #40: CRITICAL ASSERTION - Context must NOT include the citation itself!
        # This catches any bugs where context extends past start_index
        citation_snippet = citation[: min(10, len(citation))]  # First 10 chars of citation
        if citation_snippet in context:
            logger.error(f"🚨 CRITICAL BUG: Context includes citation '{citation_snippet}'!")
            logger.error(f"   Context window: [{context_start}:{context_end}]")
            logger.error(f"   Last 50 chars of context: '{context[-50:]}'")
            # Force context to end before citation
            context = text[context_start:start_index]

        if debug:
            logger.warning(f"🔍 POSITION_EXTRACT: Context ({len(context)} chars): '{context[:100]}...'")
            logger.warning(f"   Context window: [{context_start}:{context_end}]")
            logger.warning(f"   Full context: '{context}'")
            logger.warning(f"   Text AFTER citation (next 150 chars): '{text[end_index:end_index+150]}'")

        # USER FIX: Handle "vacated and remanded" pattern
        # When Supreme Court citations follow appellate decisions with "vacated and remanded",
        # extract the case name from IMMEDIATELY BEFORE the vacatur phrase, not from earlier in the paragraph
        vacatur_patterns = [
            r"vacated\s+and\s+remanded",
            r"vacated",
            r"aff\'d",
            r"affirmed",
            r"reversed",
            r"rev\'d",
            r"remanded",
        ]

        if debug:
            logger.warning(f"🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '{citation}'")
            logger.warning(f"🔍 VACATUR_DEBUG: Search context ({len(context)} chars): '{context[-200:]}'")

        for vacatur_pattern in vacatur_patterns:
            vacatur_match = re.search(vacatur_pattern, context, re.IGNORECASE)
            if debug:
                logger.warning(
                    f"🔍 VACATUR_DEBUG: Pattern '{vacatur_pattern}' -> {'FOUND' if vacatur_match else 'NOT FOUND'}"
                )

            if vacatur_match:
                # USER FIX: Check if there's a semicolon between vacatur and citation
                # Semicolons separate different cases - don't apply vacatur across this boundary
                text_after_vacatur = context[vacatur_match.end() :]
                if ";" in text_after_vacatur:
                    if debug:
                        logger.warning(
                            f"🔍 VACATUR_DEBUG: SEMICOLON found between vacatur and citation - SKIPPING vacatur logic"
                        )
                    continue  # Skip this vacatur pattern - it's for a different case

                # Found vacatur language - now find the case name BEFORE it
                vacatur_pos_in_context = vacatur_match.start()
                text_before_vacatur = context[:vacatur_pos_in_context]

                # Look for case name pattern immediately before vacatur
                # Pattern: "Plaintiff Name v. Defendant Name, 123 F.3d 149" (or F.2d, F., etc.)
                # Handles multi-word names like "Oneida Indian Nation v. Madison County"
                case_name_pattern = r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*),\s+\d+\s+F\."
                case_matches = list(re.finditer(case_name_pattern, text_before_vacatur))

                if debug:
                    logger.warning(f"🔍 VACATUR_DEBUG: Found {len(case_matches)} case name matches before vacatur")
                    if case_matches:
                        for idx, match in enumerate(case_matches):
                            logger.warning(f"🔍 VACATUR_DEBUG: Match {idx+1}: '{match.group(0)}'")
                    logger.warning(
                        f"🔍 VACATUR_DEBUG: Text before vacatur ({len(text_before_vacatur)} chars): '{text_before_vacatur[-200:]}'"
                    )

                if case_matches:
                    # Take the LAST match (closest to vacatur phrase)
                    last_match = case_matches[-1]
                    plaintiff = last_match.group(1).strip()
                    defendant = last_match.group(2).strip()

                    # Clean up case names
                    from src.utils.text_normalizer import clean_extracted_case_name

                    plaintiff = clean_extracted_case_name(plaintiff)
                    defendant = clean_extracted_case_name(defendant)
                    vacatur_case_name = f"{plaintiff} v. {defendant}"

                    if debug:
                        logger.warning(f"✅ VACATUR_DETECTED: Found '{vacatur_pattern}' before citation")
                        logger.warning(f"✅ VACATUR_CASE: Extracted '{vacatur_case_name}' from text before vacatur")

                    # Validate the case name
                    if len(plaintiff) >= 3 and len(defendant) >= 3 and len(vacatur_case_name) > 10:
                        # USER FIX: For Supreme Court citations, look for year AFTER the current citation
                        # Example: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
                        # The year (2011) is at the END of all parallel citations

                        # Check if this is a Supreme Court citation (U.S., S.Ct., L.Ed.)
                        is_supreme_court = (
                            any(x in citation for x in ["U.S.", "S. Ct.", "L. Ed."]) if citation else False
                        )

                        year = None

                        if is_supreme_court:
                            # For Supreme Court citations, look for year AFTER current citation
                            # This handles parallel citations like "562 U.S. 42, 131 S. Ct. 704 (2011)"
                            after_citation_text = text[start_index : start_index + 200]
                            year = self._extract_year_from_context(after_citation_text, debug)

                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")

                        # Fallback: Extract from Federal reporter citation
                        if not year:
                            fed_match_end_pos = last_match.end()
                            year_search_text = text_before_vacatur[fed_match_end_pos : fed_match_end_pos + 50]
                            year = self._extract_year_from_context(year_search_text, debug)

                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found year '{year}' from Federal citation")

                        if debug:
                            logger.warning(f"🔍 VACATUR_YEAR: Final extracted year '{year}' for '{vacatur_case_name}'")

                        return MasterExtractionResult(
                            case_name=vacatur_case_name,
                            year=year or "Unknown",
                            confidence=0.98,
                            method="vacatur_pattern",
                            debug_info={
                                "vacatur_pattern": vacatur_pattern,
                                "case_name": vacatur_case_name,
                                "year": year,
                            },
                            extracted_case_name=vacatur_case_name,
                            extracted_year=year,
                        )

                if debug:
                    logger.warning(
                        f"🔍 VACATUR_SKIP: Found '{vacatur_pattern}' but couldn't extract case name before it"
                    )
                break  # Only check first matching vacatur pattern

        # Try all patterns on the focused context
        print(f"[PHASE6-PATTERN] Starting pattern matching on context: '{context[:60]}'", flush=True)
        for i, pattern in enumerate(self.case_name_patterns):
            # FIX #41: CRITICAL - Log EXACTLY what's passed to regex.search
            if debug:
                logger.warning(f"🔍 FIX #41: About to search pattern {i}")
                logger.warning(f"   Context type: {type(context)}, length: {len(context)}")
                logger.warning(f"   Last 50 chars of context: {repr(context[-50:])}")
                if "Spokane" in context:
                    logger.error(f"🚨 FIX #41: 'Spokane' IS in context before regex!")
                else:
                    logger.warning(f"✅ FIX #41: 'Spokane' NOT in context before regex")

            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                print(f"[PHASE6-PATTERN] Pattern {i} MATCHED! Extracting...", flush=True)
                if debug:
                    logger.warning(f"✅ Pattern {i} matched: {pattern[:60]}...")
                    logger.warning(f"   Groups: {match.groups()}")
                    logger.warning(f"   Match position in context: {match.start()}-{match.end()}")
                    logger.warning(f"   Match text: '{match.group(0)}'")
                case_name = self._build_case_name_from_match(match, pattern, debug)

                # FIX 2024-11-08: Position-based validation to prevent extracting names from nearby citations
                # Check if the extracted name is from a different citation (too far away)
                if start_index is not None and end_index is not None:
                    # Calculate where in the context the match was found
                    # FIX DEC 2025: Use actual context length, not hardcoded 300
                    # Context length varies (150 chars for position method, different for comma-anchor)
                    context_start_in_text = start_index - len(context)
                    match_pos_in_text = context_start_in_text + match.start()

                    # Distance from citation position
                    distance_from_citation_start = abs(match_pos_in_text - start_index)
                    distance_from_citation_end = abs(match_pos_in_text - end_index)
                    min_distance = min(distance_from_citation_start, distance_from_citation_end)

                    # If match is more than 100 chars away from citation, it's likely from a nearby citation
                    if min_distance > 100:
                        if debug:
                            logger.warning(
                                f"🚫 Position validation failed: match is {min_distance} chars from citation"
                            )
                            logger.warning(f"   Likely extracted from nearby citation, not this one")
                        continue  # Skip this match and try the next pattern

                # CRITICAL FIX: Validate the extraction to prevent false extractions
                if not self._validate_case_name_extraction(case_name, context, debug):
                    if debug:
                        logger.warning(f"🚫 Skipping invalid extraction: '{case_name}'")
                    continue  # Skip this match and try the next pattern

                if debug:
                    logger.warning(f"   Built case name: '{case_name}'")
                    # FIX #40B: Track if "Spokane" appears at this stage
                    if "Spokane" in case_name:
                        logger.error(f"🚨 BUG: 'Spokane' in BUILT case_name!")

                # USER FIX 2024-10-16: Extract year from AFTER citation first, fallback to context
                # This prevents picking up years from previous citations
                year_context_after = text[end_index : end_index + 100]
                year = self._extract_year_from_context(year_context_after, debug)
                if not year:
                    # Fallback to context before citation
                    year = self._extract_year_from_context(context, debug)

                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    if debug:
                        logger.warning(f"   Cleaned case name: '{cleaned_name}'")
                        # FIX #40B: Track if "Spokane" appears at this stage
                        if "Spokane" in cleaned_name:
                            logger.error(f"🚨 BUG: 'Spokane' in CLEANED case_name!")

                    # USER FIX 2024-10-16: Add proximity validation
                    # Reject if extracted name is >100 chars away from citation
                    match_pos_in_original = context_start + match.start()
                    distance_from_citation = start_index - match_pos_in_original

                    # PHASE 6 DEBUG
                    print(
                        f"[PHASE6-PROXIMITY] match.start()={match.start()}, context_start={context_start}, match_pos={match_pos_in_original}, start_index={start_index}, distance={distance_from_citation}",
                        flush=True,
                    )

                    # CRITICAL FIX: Adjust proximity filter for smaller context windows
                    # With 150-200 char context windows, 100 chars is too restrictive
                    # Allow up to 150 chars to capture case names that are reasonably close
                    if distance_from_citation > 150:  # Increased from 100 to 150 chars
                        print(
                            f"[PHASE6-REJECT-PROXIMITY] Rejected: distance {distance_from_citation} > 150", flush=True
                        )
                        if debug:
                            logger.warning(
                                f"   ❌ REJECTED: Too far from citation ({distance_from_citation} chars away)"
                            )
                        continue  # Try next pattern

                    # P3 FIX: CRITICAL - Validate to filter contamination BEFORE accepting extraction
                    if not self._looks_like_case_name(cleaned_name, debug):
                        print(
                            f"[PHASE6-REJECT-VALIDATION] Rejected: name validation failed for '{cleaned_name}'",
                            flush=True,
                        )
                        if debug:
                            logger.warning(
                                f"   ❌ REJECTED by validation (contamination or invalid): '{cleaned_name[:100]}'"
                            )
                        continue  # Try next pattern

                    print(f"[PHASE6-ACCEPT] Passed all validation! Returning: '{cleaned_name}'", flush=True)

                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    if debug:
                        # FIX #40B: Track if "Spokane" appears at this stage
                        if "Spokane" in str(preferred_name):
                            logger.error(f"🚨 BUG: 'Spokane' in PREFERRED case_name!")
                    if debug:
                        logger.warning(f"   After canonical preferences:")
                        logger.warning(f"      preferred_name: '{preferred_name}'")
                        logger.warning(f"      canonical_meta: {canonical_meta}")
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    if debug:
                        logger.warning(f"   Creating result with:")
                        logger.warning(f"      case_name (display): '{preferred_name or 'N/A'}'")
                        logger.warning(f"      extracted_case_name: '{cleaned_name}'")
                        logger.warning(f"      canonical_name: '{canonical_meta.get('canonical_name')}'")
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.9 - (i * 0.1),  # Higher confidence for earlier patterns
                        method=f"position_pattern_{i}",
                        start_index=start_index,
                        end_index=end_index,
                        context=context[:100] + "...",
                        debug_info={
                            "pattern": pattern,
                            "raw_match": match.groups(),
                            "canonical": canonical_meta,
                        },
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )

        print(
            f"[PHASE6-PATTERN] NO patterns matched context: '{context[:60]}' - returning None (will fallback)",
            flush=True,
        )
        return None

    def _extract_with_citation_context(self, text: str, citation: str, debug: bool) -> Optional[MasterExtractionResult]:
        """Context-based extraction around citation."""
        # Find citation in text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return None

        # CRITICAL FIX: Reduce context window to prevent citation association bug
        # 400 chars was too large and included other case discussions
        # 200 chars is sufficient for immediate case name context while preventing cross-contamination
        context_start = max(0, citation_pos - 200)  # FIXED: Reduced from 400 to 200 chars
        # FIX #38: Context must end at citation START, not END!
        # Using citation_pos + len(citation) includes the citation itself and text after it,
        # causing forward contamination. Context should end where citation BEGINS.
        context_end = citation_pos  # FIX #38: Context ends at citation START!
        context = text[context_start:context_end]

        # FIX #67: Filter out document headers and metadata
        context = self._filter_header_contamination(context, debug)

        # FIX #68: Normalize whitespace to handle PDF line breaks
        context = self._normalize_whitespace_for_extraction(context, debug)

        # Try context patterns
        for pattern in self.context_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()

                # USER FIX 2024-10-16: Extract year from AFTER citation first
                year_context_after = text[citation_pos : citation_pos + 100] if citation_pos >= 0 else ""
                year = self._extract_year_from_context(year_context_after, debug)
                if not year:
                    # Fallback to context before citation
                    year = self._extract_year_from_context(context, debug)

                if len(case_name) > 3:
                    cleaned_name = self._clean_case_name(case_name)

                    # CRITICAL FIX: Add contamination validation that was missing!
                    # This prevents document header contamination (like "R.PENDLETON SUPREME COURT CLERK...")
                    if not self._validate_case_name_extraction(cleaned_name, context, debug):
                        if debug:
                            logger.warning(f"🚫 [CITATION-CONTEXT] Contamination detected, rejecting: '{cleaned_name}'")
                        continue  # Skip this match and try next pattern

                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.7,
                        method="citation_context",
                        context=context[:100] + "...",
                        debug_info={
                            "pattern": pattern,
                            "citation_pos": citation_pos,
                            "canonical": canonical_meta,
                        },
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )

        return None

    def _extract_with_patterns(
        self, text: str, citation: Optional[str], debug: bool
    ) -> Optional[MasterExtractionResult]:
        """Pattern-based extraction as last resort."""
        # Use broader context but still reasonable
        sample_text = text[:2000]  # First 2000 chars

        # FIX #67: Filter out document headers and metadata
        sample_text = self._filter_header_contamination(sample_text, debug)

        # FIX #68: Normalize whitespace to handle PDF line breaks
        sample_text = self._normalize_whitespace_for_extraction(sample_text, debug)

        for pattern in self.case_name_patterns:
            match = re.search(pattern, sample_text, re.IGNORECASE)
            if match:
                case_name = self._build_case_name_from_match(match, pattern, debug)

                # CRITICAL FIX: Validate the extraction to prevent false extractions
                if not self._validate_case_name_extraction(case_name, sample_text, debug):
                    if debug:
                        logger.warning(f"🚫 Skipping invalid extraction: '{case_name}'")
                    continue  # Skip this match and try the next pattern

                year = self._extract_year_from_context(sample_text[:500], debug)

                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.5,
                        method="pattern_fallback",
                        context=sample_text[:100] + "...",
                        debug_info={"pattern": pattern, "canonical": canonical_meta},
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )

        return None

    def _generate_fallback_case_name(self, citation: Optional[str]) -> str:
        """
        Generate a meaningful fallback case name when extraction fails.

        Instead of returning "N/A", this provides useful information about
        what the system found, helping users understand the verification status.

        Args:
            citation: The citation text

        Returns:
            A descriptive case name indicating what was found
        """
        if not citation:
            return "Unknown Citation"

        # Try to extract useful information from the citation
        # Extract court type from citation
        if "U.S." in citation:
            return "U.S. Supreme Court Case"
        elif "F.3d" in citation or "F.2d" in citation:
            return "Federal Appeals Case"
        elif "F. Supp." in citation:
            return "Federal District Case"
        elif "Wn.2d" in citation or "Wn. App." in citation:
            return "Washington State Case"
        elif "P.3d" in citation or "P.2d" in citation:
            return "Pacific Reporter Case"
        elif "S. Ct." in citation:
            return "U.S. Supreme Court Case"
        elif "L. Ed." in citation:
            return "U.S. Supreme Court Case"
        else:
            # Generic fallback with citation info
            citation_parts = citation.split()
            if len(citation_parts) >= 2:
                return f"Case ({citation_parts[0]} {citation_parts[1]})"
            else:
                return f"Legal Citation ({citation[:20]}...)"

    def _extract_year_from_citation(self, citation: Optional[str]) -> str:
        """
        Extract year from citation text.

        Args:
            citation: The citation text

        Returns:
            Year string or "N/A"
        """
        if not citation:
            return "N/A"

        # Look for year in parentheses
        year_match = re.search(r"\((19|20)\d{2}\)", citation)
        if year_match:
            return year_match.group(1)

        return "N/A"

    def _validate_case_name_extraction(self, case_name: str, context: str, debug: bool) -> bool:
        """
        Validate that the extracted case name is not a false extraction from a complex case name.

        This prevents issues like extracting "Long v. Fowler" from
        "ESTATE OF MELVIN JOSEPH LONG, by and through MARLA HUDSON LONG, Administratrix, v. JAMES D. FOWLER"

        Args:
            case_name: The extracted case name to validate
            context: The context where the case name was extracted
            debug: Enable debug logging

        Returns:
            True if the extraction is valid, False if it's a false extraction
        """
        if not case_name or case_name == "N/A":
            return True  # Don't validate empty names

        # Check for false extractions from complex case names
        case_name.lower()
        context_lower = context.lower()

        # Pattern 1: Check if we extracted a simple "Last v. Last" from a complex estate case
        # Example: "Long v. Fowler" from "ESTATE OF MELVIN JOSEPH LONG...v. JAMES D. FOWLER"
        if re.match(r"^[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+$", case_name):
            # Check if context contains "ESTATE OF" or "Estate of" with the same last names
            estate_pattern = (
                r"estate\s+of\s+[^,]+"
                + re.escape(case_name.split(" v. ")[0].split()[-1])
                + r"[^,]*v\.\s+[^,]*"
                + re.escape(case_name.split(" v. ")[1].split()[-1])
            )
            if re.search(estate_pattern, context_lower):
                if debug:
                    logger.warning(
                        f"🚫 FALSE EXTRACTION DETECTED: '{case_name}' is a simplified extraction from complex estate case"
                    )
                return False

        # Pattern 2: Check for other complex case patterns that might be simplified incorrectly
        # Look for patterns like "by and through", "Administratrix", "Executor", etc.
        complex_indicators = [
            r"by\s+and\s+through",
            r"administratrix",
            r"executor",
            r"personal\s+representative",
            r"trustee",
            r"guardian",
        ]

        for indicator in complex_indicators:
            if re.search(indicator, context_lower):
                # If context has complex indicators but case name is simple, it might be false
                if len(case_name.split()) <= 4 and " v. " in case_name:
                    if debug:
                        logger.warning(
                            f"🚫 POTENTIAL FALSE EXTRACTION: '{case_name}' from complex case context with '{indicator}'"
                        )
                    return False

        return True

    def _build_case_name_from_match(self, match, pattern: str, debug: bool) -> str:
        """Build case name from regex match groups."""
        groups = match.groups()

        if len(groups) == 1:
            # Single group (In re cases)
            return groups[0].strip()
        elif len(groups) >= 2:
            # Two groups (plaintiff v. defendant)
            plaintiff = groups[0].strip()
            defendant = groups[1].strip()
            return f"{plaintiff} v. {defendant}"

        return match.group(0).strip()

    def _extract_year_from_context(self, context: str, debug: bool) -> Optional[str]:
        """Extract year from context using comprehensive patterns.

        USER FIX 2024-12-24: Find the CLOSEST year to the start of context and
        stop at citation boundaries like 'aff'd', ';', etc.

        Example: For "47 Conn. Supp. 113, 119, 778 A.2d 1038 (Conn. Super. Ct. 2000), aff'd, 63 Conn. App. 695, 778 A.2d 1006 (2001)"
        Should return 2000 (closest), not 2001 (further away)
        """
        if not context:
            return None

        # USER FIX: Truncate context at citation boundaries BEFORE searching for years
        # This prevents picking up years from subsequent citations like "aff'd, ... (2001)"
        boundary_patterns = [
            r",\s*aff\'?d\b",  # ", aff'd" or ", affd"
            r",\s*rev\'?d\b",  # ", rev'd" or ", revd"
            r",\s*cert\.\s*denied",  # ", cert. denied"
            r",\s*overruled\b",  # ", overruled"
            r",\s*superseded\b",  # ", superseded"
            r";\s*see\s+also\b",  # "; see also"
            r";\s*accord\b",  # "; accord"
            r"\.\s+[A-Z]",  # Sentence boundary (". " followed by capital)
        ]

        truncated_context = context
        earliest_boundary = len(context)

        for boundary_pattern in boundary_patterns:
            match = re.search(boundary_pattern, context, re.IGNORECASE)
            if match and match.start() < earliest_boundary:
                earliest_boundary = match.start()
                if debug:
                    logger.debug(f"[YEAR-EXTRACT] Found boundary '{match.group()}' at position {match.start()}")

        # Truncate context at the earliest boundary (but include some space for the year parenthetical)
        if earliest_boundary < len(context):
            # Look for the last closing paren before the boundary (to include the year)
            last_paren = context.rfind(")", 0, earliest_boundary + 1)
            if last_paren > 0:
                truncated_context = context[: last_paren + 1]
            else:
                truncated_context = context[:earliest_boundary]
            if debug:
                logger.debug(f"[YEAR-EXTRACT] Truncated context at boundary: '{truncated_context[:80]}...'")

        # USER FIX: Find ALL year matches and pick the CLOSEST to position 0 (start of citation)
        # Enhanced patterns to match years in various parenthetical formats
        enhanced_year_patterns = [
            r"\([^)]*?(\d{4})[^)]*?\)",  # Year anywhere in parentheses: (Conn. Super. Ct. 2000)
            r"\((\d{4})\)",  # Simple year in parens: (2020)
            r",\s*(\d{4})",  # Year after comma: , 2020
            r"(\d{4})\s*\)",  # Year at end of parens: 2020)
        ]

        best_year = None
        best_distance = float("inf")

        for pattern in enhanced_year_patterns:
            for match in re.finditer(pattern, truncated_context):
                year = match.group(1)
                if 1800 <= int(year) <= 2030:  # Reasonable year range
                    distance = match.start()

                    # CRITICAL FIX: Filter out years from document headers
                    year_start = match.start()
                    year_end = match.end()
                    context_start = max(0, year_start - 30)
                    context_end = min(len(truncated_context), year_end + 30)
                    year_context = truncated_context[context_start:context_end]

                    # Check if year appears in header-like patterns
                    header_patterns = [
                        r"[A-Z]{3,}\s+\d{1,2},\s*\d{4}",  # "JUNE 12, 2025"
                        r"FILED[:\s]+\d{4}",  # "FILED: 2025"
                        r"CLERK.*\d{4}",  # "CLERK'S OFFICE...2025"
                        r"SUPREME COURT.*\d{4}",  # "SUPREME COURT...2025"
                    ]

                    is_header_year = False
                    for header_pattern in header_patterns:
                        if re.search(header_pattern, year_context, re.IGNORECASE):
                            is_header_year = True
                            if debug:
                                logger.debug(f"[YEAR-EXTRACT] Rejected year {year} - appears in header pattern")
                            break

                    # Also check if the context is all-caps (likely a header)
                    if not is_header_year and year_context.strip().isupper() and len(year_context.strip()) > 15:
                        is_header_year = True
                        if debug:
                            logger.debug(f"[YEAR-EXTRACT] Rejected year {year} - context is all-caps header")

                    if not is_header_year and distance < best_distance:
                        best_year = year
                        best_distance = distance
                        if debug:
                            logger.debug(f"[YEAR-EXTRACT] Found year {year} at distance {distance}")

        if debug and best_year:
            logger.debug(f"[YEAR-EXTRACT] Returning closest year: {best_year}")

        return best_year

    def _clean_case_name(self, case_name: str, context: Optional[str] = None) -> str:
        """
        Clean and normalize case name using best practices from all implementations.

        Args:
            case_name: The extracted case name to clean
            context: Optional broader text context for finding full corporate names
        """
        if not case_name:
            return "N/A"

        # CRITICAL FIX: Remove sentence fragments BEFORE normalizing whitespace
        # Look for patterns like "scheme as a whole. Ass'n of..." and keep only "Ass'n of..."
        cleaned = case_name.strip()
        
        # ENHANCED: Remove case caption role patterns that cause contamination
        # Patterns like "CARTER, Respondent, v. MARY E. JONES, Appellant" should be cleaned
        # to "CARTER v. MARY E. JONES"
        role_pattern = r"\s*,\s*(?:Respondent|Appellant|Petitioner|Appellee|Plaintiff|Defendant)s?\b"
        cleaned = re.sub(role_pattern, "", cleaned, flags=re.IGNORECASE)
        # Also handle role words before party names
        role_prefix_pattern = r"^(?:Respondent|Appellant|Petitioner|Appellee|Plaintiff|Defendant)s?\s*,\s*"
        cleaned = re.sub(role_prefix_pattern, "", cleaned, flags=re.IGNORECASE)
        # Clean up any double commas left behind
        cleaned = re.sub(r"\s*,\s*,\s*", ", ", cleaned)
        cleaned = re.sub(r"^\s*,\s*|\s*,\s*$", "", cleaned)

        # FIX #68C: Match full case name, not just minimum
        # OLD: r'\.\s+([A-Z].+?\s+v\.\s+.+?)$' used NON-GREEDY .+? which truncated names
        # NEW: Use greedy .+ to capture complete case names
        # Match: sentence-ending period followed by spaces/newline, then case name with "v."
        # Look for the last occurrence of ". " followed by capital letter and a "v." pattern
        case_name_match = re.search(r"\.\s+([A-Z].+\s+v\.\s+.+)$", cleaned)
        if case_name_match:
            potential_name = case_name_match.group(1).strip()
            # Verify it looks like a case name (has "v." and starts with capital)
            if " v. " in potential_name:
                cleaned = potential_name

        # NOW normalize whitespace after we've extracted the case name
        cleaned = re.sub(r"\s+", " ", cleaned)

        # DEBUG: Log for contamination issue
        if "Batzel" in cleaned or "doctrine" in cleaned.lower():
            logger.error(f"[CONTAMINATION-DEBUG] Before cleaning: '{cleaned}'")

        # Remove common prefixes that indicate contamination
        # USER FIX: Protect special case type prefixes from removal
        # CRITICAL: Remove signal words first, before other cleaning
        contamination_prefixes = [
            # Signal words FIRST - these introduce citations but aren't part of the case name
            # FIX 2024-11-08: Added "also", "We review", "The court", "Under" to fix 1031351.pdf contamination
            r"^(?:See|see|See also|see also|also|Also|Citing|citing|Compare|compare|But see|but see|Cf\.|cf\.|quoting|Quoting|accord|Accord|We review|we review|The court|the court|Under|under)\s+",
            r"^(?:The case of|As stated in|Following)\s+",
            # FIX 2024-11-08: Add de novo review language that contaminates case names
            r"^(?:choice of law questions?|questions? of law|de novo|issues? of law|issues? of)\s+",
            # FIX 2024-11-09: Add reporter prefix pattern for citations like "prod.liab.rep. (Cch) P 13,403"
            r"^[a-z][a-z.]*\s*\([^)]+\)\s*[A-Z]?\s*[\d,]+\s+",  # Lowercase reporter prefix with parentheses and numbers
            # Phase 4 USER FIX: Additional contamination phrases
            r"^(?:The parties are|The parties were)\s+",
            # CRITICAL FIX: Be more specific about court phrases to avoid rejecting valid case names
            # FIX 2024-11-08: Simplified - just remove these prefixes, allow case names that follow
            r"^(?:The court in|The court held|The court decided|The court stated|We review|we review)\s+",
            r"^(?:The defendant|The plaintiff)\s+(?!.*\s+v\.\s+)",
            r"^(?:If in|As in)\s+",
            # CRITICAL FIX: Filter generic appellant/defendant contamination
            # Pattern: "Appellants, v. JAMES S. SHAW and DOE SHAW, and their marital community"
            # This appears to be header/footer text contaminating multiple citations
            r"^(?:Appellants,?\s*|Appellant,?\s*|Petitioners,?\s*|Petitioner,?\s*|Respondents,?\s*|Respondent,?\s*)",
            r"^(?:Defendants?,?\s*|Plaintiffs?,?\s*|JAMES\s+S\.\s*SHAW|DOE\s+SHAW)\s+",
            # Phase 4 USER FIX v2: Remove connecting phrases after signal words are removed
            r"^(?:this|that|such|the)\s+(?:precedent|case|decision|holding|rule|standard|doctrine),?\s+in\s+",
            r"^(?:precedent|case|decision|holding|rule|standard|doctrine),?\s+in\s+",
            r"^(?:court held that|established|the defendant)\s*[.\s]*",
            r"^(?:of\s+law)[\s\.]*",
            # CRITICAL FIX: Filter procedural text contamination
            # Pattern: "III Brant v. Shaw Following a hearing" → should be "III Brant v. Shaw"
            r"(?:\s+(?:Following|After|During|Before|In)\s+(?:a\s+)?(?:hearing|trial|proceeding|appeal|argument|motion|conference|review))\s*$",
            # Only remove "In " if NOT part of case type prefixes
            # Protect: "In re", "In the matter of"
            r"^In\s+(?!re\s|the\s+matter\s)",
            # Only remove "Matter " if NOT "Matter of"
            r"^Matter\s+(?!of\s)",
            # Only remove "Estate " if NOT "Estate of"
            r"^Estate\s+(?!of\s)",
            # Only remove "Ex " if NOT "Ex parte"
            r"^Ex\s+(?!parte\s)",
        ]

        # FIX #9: Remove case/docket numbers that appear due to page breaks
        # CRITICAL: Handle spaces within case numbers from line breaks: "No. 103430 -0 15"

        # Pattern 1: Before "v." - Standard case numbers
        cleaned = re.sub(r"\s+No\.\s+[\d\-]+\s+\d+(?=\s+v\.)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+No\.\s+[\d\-]+(?=\s+v\.)", "", cleaned, flags=re.IGNORECASE)

        # Pattern 1b: Complex case numbers with hyphens (continuous or with spaces)
        # "No. 103430-0-15" OR "No. 103430 -0 15" → remove before "v."
        cleaned = re.sub(r"\s+No\.\s+[\d\-\s]+\-[\d\-\s]+(?=\s+v\.)", "", cleaned, flags=re.IGNORECASE)

        # Pattern 1c: Case numbers with spaces from line breaks: "No. 103430 -0 15"
        # This specifically targets the problematic pattern with internal spaces
        cleaned = re.sub(r"\s+No\.\s+\d+\s+-\d+\s+\d+(?=\s+v\.)", "", cleaned, flags=re.IGNORECASE)

        # Pattern 2: After "v." - Page number contamination
        # "Inc. v. Band 6 No. 103430-0 Tribe" → "Inc. v. Band Tribe"
        cleaned = re.sub(r"\s+\d+\s+No\.\s+[\d\-]+\s+", " ", cleaned, flags=re.IGNORECASE)

        # Pattern 2b: Complex case numbers after "v." (with or without spaces)
        cleaned = re.sub(r"\s+No\.\s+[\d\-\s]+\-[\d\-\s]+\s+", " ", cleaned, flags=re.IGNORECASE)

        # Pattern 3: Standalone page numbers between words (page breaks)
        # "Band 6 Potawatomi" → "Band Potawatomi" (only if surrounded by capitals)
        cleaned = re.sub(r"([A-Z][a-z]+)\s+\d{1,2}\s+([A-Z][a-z]+)", r"\1 \2", cleaned)

        # USER FIX 2024-10-21: Strip whitespace before applying patterns
        # Ensures ^ anchor works correctly even if there's leading whitespace
        cleaned = cleaned.strip()

        for prefix in contamination_prefixes:
            before = cleaned
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE).strip()
            if before != cleaned:
                logger.error(f"[CLEAN_DEBUG] Removed prefix: '{before}' → '{cleaned}'")

        # NEW: Remove descriptive legal phrases and status words that contaminate case names
        # Strategy: If we detect contamination words, try to extract just the case name portion

        # First, remove common procedural introducers at the start
        # NOTE: Signal words are now handled in contamination_prefixes above
        procedural_prefixes = [
            r"^(?:under|applying|following|relying on)\s+",
        ]
        for pattern in procedural_prefixes:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # If there's a "v." pattern, look for contamination words before it
        if " v. " in cleaned:
            # Check for contamination keywords
            contamination_words = [
                "doctrine",
                "rule",
                "test",
                "standard",
                "principle",
                "holding",
                "overruling",
                "superseding",
                "superseded",
                "overruled",
                "reversed",
                "affirming",
                "affirmed",
                "modifying",
                "modified",
            ]

            has_contamination = any(word in cleaned.lower() for word in contamination_words)

            if has_contamination:
                # Extract just the case name: find the pattern "PartyName v. PartyName"
                # Look for the last occurrence of a capital letter followed by party names and "v."
                case_match = re.search(
                    r"\b([A-Z][\w\'\.\-]+(?:\s+(?:of|&|and|v\.)\s+[\w\'\.\-]+)*(?:\s+[A-Z][\w\'\.\-]+)*)\s+v\.\s+([A-Z][\w\'\.\-,\s&]+(?:Inc\.|Corp\.|LLC|Ltd\.|Co\.|Company|[A-Z][\w\'\.\-]+)*)(?:\s|$)",
                    cleaned,
                )
                if case_match:
                    plaintiff = case_match.group(1).strip()
                    defendant = case_match.group(2).strip()

                    # Verify plaintiff doesn't start with a contamination word
                    first_word = plaintiff.split()[0].lower() if plaintiff.split() else ""
                    if first_word not in contamination_words:
                        cleaned = f"{plaintiff} v. {defendant}"
                        # Remove trailing punctuation that might have been captured
                        cleaned = re.sub(r"\s*[,;\.]+$", "", cleaned)

        # USER FIX 2024-10-16: Remove citation patterns that got included
        # Example: "Inc. v. Stillaguamish Tribe of Indians, 31 Wn. App. 2d 343, 359-62"
        # Should be: "Inc. v. Stillaguamish Tribe of Indians"

        # USER FIX 2024-10-16 PM: Remove state reporter citations like "2017-NM-007"
        # Pattern: ", YYYY-STATE-NUMBER" where STATE is 2-letter code
        cleaned = re.sub(r",\s*\d{4}-[A-Z]{2}-\d+", "", cleaned)

        # Remove anything that looks like: ", [volume] [reporter] [page]"
        cleaned = re.sub(r",\s*\d+\s+[A-Z][a-z]*\.?\s*(?:App\.)?\s*\d*d?\s*\d+.*$", "", cleaned)
        # Also remove pin cites like ", 359-62"
        cleaned = re.sub(r",\s*\d+-\d+.*$", "", cleaned)
        # Remove standalone citations at end: "245 F.3d 889" or "31 Wn. App. 2d 343"
        cleaned = re.sub(r"\s+\d+\s+[A-Z][a-z]*\.?\s*(?:App\.)?\s*\d*d?\s*\d+.*$", "", cleaned)

        # Remove trailing punctuation except periods in abbreviations
        cleaned = re.sub(r"[,;:]+$", "", cleaned)

        # USER FIX 2024-10-16: Fix corporate name truncation
        # If name starts with corporate suffix (Inc., LLC, etc.), it's truncated
        # Example: "Inc. v. Stillaguamish" should be "Flying T Ranch, Inc. v. Stillaguamish"
        corporate_suffixes = [
            r"^Inc\.?\s+v\.",
            r"^LLC\.?\s+v\.",
            r"^Corp\.?\s+v\.",
            r"^Ltd\.?\s+v\.",
            r"^Co\.?\s+v\.",
            r"^L\.P\.?\s+v\.",
        ]

        is_truncated = any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in corporate_suffixes)

        if is_truncated:
            # USER FIX 2024-10-16 PM: Search context first, then case_name
            # Try to find the full corporate name in context (if provided), then original case_name
            search_text = context if context else case_name
            # Look for pattern: [Company Name], Inc. v. [Defendant]
            corp_name_match = re.search(
                r"([A-Z][A-Za-z\s&\'\.\-]+(?:,\s*)?(?:Inc|LLC|Corp|Ltd|Co|L\.P\.)\.?)\s+v\.", search_text, re.IGNORECASE
            )
            if corp_name_match:
                # Found the full corporate name, use it
                full_corp_name = corp_name_match.group(1).strip()
                # Replace truncated start with full name
                cleaned = re.sub(
                    r"^(?:Inc|LLC|Corp|Ltd|Co|L\.P\.)\.?\s+", full_corp_name + " ", cleaned, flags=re.IGNORECASE
                )

        # FIX DEC 2025: Repair missing first party (names starting with "v.")
        # Example: "v. Parmelee" should be "DeLong v. Parmelee"
        if cleaned.strip().startswith("v.") or cleaned.strip().startswith("V."):
            if context:
                # Extract defendant name from the truncated string
                defendant_match = re.match(r"^v\.\s+(.+)$", cleaned.strip(), re.IGNORECASE)
                if defendant_match:
                    defendant = defendant_match.group(1).strip()
                    # Search context for full case name ending with this defendant
                    # Pattern: [Plaintiff] v. [Defendant]
                    full_case_match = re.search(
                        r"([A-Z][A-Za-z\s&\'\.\-,]+)\s+v\.\s+" + re.escape(defendant[:20]), context, re.IGNORECASE
                    )
                    if full_case_match:
                        plaintiff = full_case_match.group(1).strip()
                        # Clean plaintiff of any leading garbage
                        plaintiff = re.sub(r"^(?:See|Citing|In|The)\s+", "", plaintiff, flags=re.IGNORECASE).strip()
                        if plaintiff and len(plaintiff) > 2:
                            cleaned = f"{plaintiff} v. {defendant}"
                            logger.error(
                                f"[TRUNCATION-REPAIR] Repaired missing plaintiff: 'v. {defendant}' -> '{cleaned}'"
                            )

        # FIX DEC 2025: Repair partial first party truncation
        # Example: "Motor Co v. City" should be "Ford Motor Co. v. City"
        # Detect: short word + "Co" or "Co." at start, missing company name
        partial_truncation_match = re.match(
            r"^([A-Z][a-z]+)\s+(Co\.?|Corp\.?|Inc\.?)\s+v\.\s+(.+)$", cleaned, re.IGNORECASE
        )
        if partial_truncation_match and context:
            short_name = partial_truncation_match.group(1)  # e.g., "Motor"
            suffix = partial_truncation_match.group(2)  # e.g., "Co"
            defendant = partial_truncation_match.group(3)  # e.g., "City of Seattle"

            # Search context for full company name ending with this pattern
            # Look for: [Full Name] Motor Co. v.
            full_company_pattern = (
                rf"([A-Z][A-Za-z\s&\'\.\-,]+\s+{re.escape(short_name)}\s+{re.escape(suffix)}\.?)\s+v\."
            )
            full_company_match = re.search(full_company_pattern, context, re.IGNORECASE)
            if full_company_match:
                full_plaintiff = full_company_match.group(1).strip()
                cleaned = f"{full_plaintiff} v. {defendant}"
                logger.error(
                    f"[TRUNCATION-REPAIR] Repaired partial truncation: '{short_name} {suffix}' -> '{full_plaintiff}'"
                )

        # Fix common corporate abbreviation issues
        cleaned = re.sub(r"\bInc\b(?!\.)(?!\s+v\.)", "Inc.", cleaned)
        cleaned = re.sub(r"\bCorp\b(?!\.)(?!\s+v\.)", "Corp.", cleaned)
        cleaned = re.sub(r"\bLLC\b(?!\.)(?!\s+v\.)", "LLC", cleaned)
        cleaned = re.sub(r"\bLtd\b(?!\.)(?!\s+v\.)", "Ltd.", cleaned)

        # FIX DEC 2025: Expand severely abbreviated names if context is available
        # Example: "Cmtys Wash v. State" -> "Manufactured Housing Communities of Washington v. State"
        if context and " v. " in cleaned:
            # Check if name looks severely abbreviated (very short first party)
            v_pos = cleaned.find(" v. ")
            if v_pos > 0:
                first_party = cleaned[:v_pos].strip()
                second_party = cleaned[v_pos + 4 :].strip()

                # If first party is very short (likely abbreviated), try to find full name in context
                if len(first_party) < 20 and not any(
                    word in first_party.lower() for word in ["state", "united states", "city of", "county of"]
                ):
                    # Search context for a longer case name with similar second party
                    full_name_pattern = rf"([A-Z][A-Za-z\s&\'\.\-,]+{{20,}})\s+v\.\s+{re.escape(second_party[:15])}"
                    full_name_match = re.search(full_name_pattern, context, re.IGNORECASE)
                    if full_name_match:
                        full_first_party = full_name_match.group(1).strip()
                        # Clean leading garbage
                        full_first_party = re.sub(
                            r"^(?:See|Citing|In|The)\s+", "", full_first_party, flags=re.IGNORECASE
                        ).strip()
                        if len(full_first_party) > len(first_party) + 5:
                            old_cleaned = cleaned
                            cleaned = f"{full_first_party} v. {second_party}"
                            logger.error(f"[ABBREVIATION-EXPAND] Expanded '{old_cleaned}' -> '{cleaned}'")

        # If we've removed everything, return original
        if not cleaned.strip():
            return case_name.strip()

        # Check if this looks like a document header
        if self._is_document_header(cleaned):
            logger.error(f"[CLEAN_DEBUG] REJECTED as header: '{cleaned}'")
            return "N/A"

        logger.error(f"[CLEAN_DEBUG] FINAL cleaned: '{cleaned}'")
        return cleaned.strip()

    def _is_document_header(self, text: str) -> bool:
        """Check if text looks like a document header rather than a case name."""
        if not text:
            return True

        # Document header patterns
        # CRITICAL: These should NOT match valid case names (containing " v. ")
        header_patterns = [
            r"^IN THE\s+(?!.*\s+v\.\s+)",  # "IN THE..." but not "IN THE MATTER OF X v. Y"
            r"^CASE NO\.\s*",
            r"^NO\.\s*\d+",
            r"^FILED:\s*",
            r"^DATE:\s*",
            r"^COURT:\s*",
            r"^DISTRICT:\s*",
            r"^CIRCUIT:\s*",
            r"^APPEAL:\s*",
            r"^APPELLATE:\s*",
            r"^SUPREME:\s*",
            r"^STATE OF\s+(?!.*\s+v\.\s+)",  # "STATE OF..." but not case name
            # CRITICAL FIX: Don't reject "United States v. X" as header!
            # Only reject standalone "UNITED STATES" or "UNITED STATES" followed by punctuation
            r"^UNITED STATES\s*[,;:\.]?\s*$",  # Standalone only
            r"^PLAINTIFFS,?\s*$",
            r"^DEFENDANTS\.?\s*$",
            r"^PLAINTIFFS-APPELLEES,?\s*$",
            r"^DEFENDANT-APPELLANT\.?\s*$",
            r"^THOMSON REUTERS",
            r"^WEST PUBLISHING",
            r"^ROSS INTELLIGENCE",
            r"^ENTERPRISE CENTRE",
            r"^CORPORATION,?\s*$",
            r"^GMBH\s*$",
            r"^INC\.?\s*$",
            r"^LLC\s*$",
            r"^LTD\.?\s*$",
            r"^CO\.?\s*$",
        ]

        for pattern in header_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Check for very long text that's likely a document header
        if len(text) > 100:
            return True

        # Check for text that's mostly uppercase (document headers)
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            return True

        # Check for text with too many commas (document headers)
        if text.count(",") > 3:
            return True

        return False

    def _normalize_text(self, text: str) -> str:
        """Normalize text to handle Unicode and encoding issues."""
        if not text:
            return ""

        # Handle common Unicode issues
        text = text.replace("\u2019", "'")  # Smart apostrophe
        text = text.replace("\u201c", '"').replace("\u201d", '"')  # Smart quotes
        text = text.replace("\u2013", "-").replace("\u2014", "-")  # En/em dashes
        text = text.replace("\u00a0", " ")  # Non-breaking space

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        return text


# Global singleton instance
_master_extractor = None


def get_master_extractor() -> UnifiedCaseExtractionMaster:
    """Get the singleton master extractor instance."""
    global _master_extractor
    if _master_extractor is None:
        _master_extractor = UnifiedCaseExtractionMaster()
    return _master_extractor


def extract_case_name_and_date_unified_master(
    text: str,
    citation: Optional[str] = None,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    debug: bool = False,
    canonical_name: Optional[str] = None,
    canonical_date: Optional[str] = None,
    document_primary_case_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    THE SINGLE, UNIFIED EXTRACTION FUNCTION

    This function replaces ALL 120+ duplicate extraction functions.
    Use this instead of:
    - extract_case_name_and_date_master()
    - extract_case_name_and_year_unified()
    - _extract_case_name_enhanced()
    - All other duplicate functions

    Args:
        document_primary_case_name: The primary case name of the document being analyzed.
                                   Used to filter out contamination.

    Returns:
        Dictionary with case_name, year, confidence, method, and debug_info
    """
    extractor = get_master_extractor()

    # CRITICAL FIX: ALWAYS set document primary case name (even if None) to ensure consistency
    # across singleton extractor instance. Otherwise, old value persists across calls.
    extractor.document_primary_case_name = document_primary_case_name
    if document_primary_case_name:
        logger.warning(f"[CONTAMINATION-FILTER] Set document primary case: '{document_primary_case_name[:80]}'")

    if citation:
        extractor._update_canonical_cache(
            citation,
            canonical_name=canonical_name,
            canonical_date=canonical_date,
        )
        cached_meta = extractor._get_canonical_metadata(citation)
        if cached_meta.get("canonical_name") and cached_meta.get("canonical_date"):
            # CRITICAL FIX: When returning cached canonical data, keep extracted fields separate
            return {
                "case_name": cached_meta["canonical_name"],
                "year": cached_meta["canonical_date"],
                "date": cached_meta["canonical_date"],
                "confidence": 1.0,
                "method": "canonical_metadata_cache",
                "start_index": start_index,
                "end_index": end_index,
                "context": text[:100] + "...",
                "debug_info": {"canonical_source": "cache"},
                "canonical_name": cached_meta["canonical_name"],
                "canonical_year": cached_meta["canonical_date"],
                "extracted_case_name": "N/A",  # No extraction performed when using cache
                "extracted_year": "N/A",  # No extraction performed when using cache
            }

    result = extractor.extract_case_name_and_date(text, citation, start_index, end_index, debug)

    if citation:
        extractor._update_canonical_cache(
            citation,
            canonical_name=result.canonical_name,
            canonical_date=result.canonical_year,
        )

    # CRITICAL FIX: extracted_case_name must ONLY contain text from document, NEVER canonical data
    return {
        "case_name": result.case_name,
        "year": result.year,
        "date": result.year,
        "confidence": result.confidence,
        "method": result.method,
        "start_index": result.start_index,
        "end_index": result.end_index,
        "context": result.context,
        "debug_info": result.debug_info or {},
        "canonical_name": result.canonical_name,
        "canonical_year": result.canonical_year,
        "extracted_case_name": result.extracted_case_name or "N/A",  # NEVER use canonical
        "extracted_year": result.extracted_year or "N/A",  # NEVER use canonical
    }
