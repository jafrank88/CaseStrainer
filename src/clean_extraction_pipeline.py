"""
========================================================
DEPRECATED - DO NOT MODIFY THIS FILE
========================================================

THIS FILE IS NOT ACTIVELY USED IN PRODUCTION!

ACTIVE EXTRACTION CODE IS IN:
    src/unified_case_extraction_master.py

This file exists for fallback purposes only.
Any improvements should be made to unified_case_extraction_master.py instead.

Active call path: unified_citation_processor_v2.py:4048-4089
    -> extract_case_name_and_date_unified_master()
    -> UnifiedCaseExtractionMaster.extract_case_name_and_date()

STOP! Before modifying this file:
1. Check if unified_case_extraction_master.py already has what you need
2. If you must add a feature, add it there instead
3. This file only runs as a fallback when the master fails
"""

import warnings

warnings.warn(
    "WARNING: clean_extraction_pipeline.py is DEPRECATED. " "Active code is in src.unified_case_extraction_master",
    DeprecationWarning,
    stacklevel=2,
)

import logging
import re
from typing import List, Dict, Optional
from src.models import CitationResult
from src.utils.unified_case_name_extractor import extract_case_name_with_strict_isolation
from src.citation_patterns import CitationPatterns  # CONSOLIDATED: Import shared patterns
from src.case_name_validator import is_valid_case_name  # NEW: Validation
from src.utils.strict_context_isolator import (
    get_strict_context_for_citation,
    find_all_citation_positions,
)  # Context validation for eyecite names

logger = logging.getLogger(__name__)


def _extract_special_citation_formats(text: str, citation_text: str, start_index: int) -> Optional[str]:
    """
    FIX NOV 9: Handle special citation formats that commonly fail extraction.

    Patterns handled:
    1. String citations: "Name, 123 Rep 456, 789 Rep2 012"
    2. WestLaw with docket: "Name, No. XX-XXXXX, 2019 WL 123456"
    3. Signal words: "accord Name, 123 Rep 456"

    Args:
        text: Full document text
        citation_text: The citation string (e.g., "548 P.3d 226")
        start_index: Position of citation in text

    Returns:
        Extracted case name or None if no pattern matched
    """
    # USER FIX v2: Further reduced from 100 to 50 chars to stop cascading contamination
    # FIX JAN 2026: Increase to 150 chars to handle longer case names like "Allegiant Travel Co."
    context_before = text[max(0, start_index - 150) : start_index]
    context_clean = re.sub(r"\s+", " ", context_before)
    
    # For WestLaw citations, we need full context including the citation itself
    # because the pattern matches both case name and WL citation
    full_context = text[max(0, start_index - 150) : min(len(text), start_index + 100)]
    full_context_clean = re.sub(r"\s+", " ", full_context)

    logger.error(f"[SPECIAL-FORMATS] ✨ Trying special format extraction for '{citation_text}'")

    # PATTERN 1: STRING CITATIONS - "Name, LLC, 31 Wn. App. 2d 100, 110-11, 548 P.3d 226"
    # Match case name followed by optional company suffix, then reporter citations
    # Look for the LAST occurrence to get the name closest to this citation
    string_pattern = r"([A-Z][^,]{10,120}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+\s+[A-Za-z.\s]+\d+"
    matches = list(re.finditer(string_pattern, context_clean))
    if matches:
        # Use the last match (closest to the citation we're extracting)
        match = matches[-1]
        case_name = match.group(1).strip()

        # Extract ONLY the case name, removing any prefix text
        # Look for "v." or "In re" pattern (more flexible - not anchored to end)
        case_name_match = re.search(r"([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)
        if not case_name_match:
            case_name_match = re.search(r"(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)

        if case_name_match:
            case_name = case_name_match.group(1).strip()
            # Clean up any trailing punctuation
            case_name = re.sub(r"[,\s]+$", "", case_name)
            logger.error(f"[SPECIAL-FORMATS] ✅ STRING CITATION: '{case_name}'")
            return case_name

        # FALLBACK: If pattern doesn't match, check if we have "v." in the captured text
        if "v." in case_name.lower() or "in re" in case_name.lower():
            logger.error(f"[SPECIAL-FORMATS] ⚠️ STRING CITATION (unfiltered): '{case_name}'")
            return case_name

    # PATTERN 2: WESTLAW WITH DOCKET - "Name, Inc., No. 2:18-CV-00348-SMJ, 2019 WL 2066127"
    # Handle company suffixes anywhere in the case name (middle or end)
    # IMPORTANT: Only apply for WL citations
    if "WL" in citation_text:
        # Updated pattern: captures full case name with v. and optional company suffix anywhere
        # Uses full_context because pattern includes both case name and WL citation
        docket_pattern = r"([A-Za-z][\w\s&\-\.',]*?(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?[\w\s&\-\.',]*?v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[\w:-]+,?\s*)?\d{4}\s+WL\s+\d+"
        matches = list(re.finditer(docket_pattern, full_context_clean, re.IGNORECASE))
        if matches:
            match = matches[-1]
            case_name = match.group(1).strip()
            
            # The new pattern already captures the full case name, just clean it up
            case_name = re.sub(r"[,\s]+$", "", case_name)
            logger.error(f"[SPECIAL-FORMATS] ✅ WESTLAW WITH DOCKET: '{case_name}'")
            return case_name

    # PATTERN 3: SIGNAL WORDS - "accord Name, Corp., 831 F.2d 508"
    signal_words = ["accord", "see", "see also", "compare", "citing", "but see", "cf.", "e.g."]
    for signal in signal_words:
        # Handle company suffixes after case name
        # Look for the LAST occurrence of this signal word pattern
        signal_pattern = (
            rf"\b{signal}\b\s+([A-Z][^,]{{10,120}}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*\d+\s+[A-Za-z.\s]+\d+"
        )
        matches = list(re.finditer(signal_pattern, context_clean, re.IGNORECASE))
        if matches:
            match = matches[-1]
            case_name = match.group(1).strip()

            # Extract ONLY the case name, removing any prefix text
            case_name_match = re.search(
                r"([A-Z][\w\s&\',.-]+?\s+v\.\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE
            )
            if not case_name_match:
                case_name_match = re.search(r"(In re\s+[\w\s&\',.-]+?)(?:,|\s*$)", case_name, re.IGNORECASE)

            if case_name_match:
                case_name = case_name_match.group(1).strip()
                case_name = re.sub(r"[,\s]+$", "", case_name)
                logger.error(f"[SPECIAL-FORMATS] ✅ SIGNAL WORD '{signal}': '{case_name}'")
                return case_name

            if "v." in case_name.lower() or "in re" in case_name.lower():
                logger.error(f"[SPECIAL-FORMATS] ⚠️ SIGNAL WORD '{signal}' (unfiltered): '{case_name}'")
                return case_name

    logger.error(f"[SPECIAL-FORMATS] ❌ No special patterns matched")
    return None


def _eyecite_name_in_strict_context(text: str, citation: CitationResult) -> bool:
    """Return True if the existing extracted_case_name appears in the strict
    pre-citation context (last ~100-300 chars), indicating it belongs to this
    specific citation rather than an earlier clause/citation.

    CRITICAL FIX: Also reject names that contain signal words like "This case involves"
    """
    try:
        if not citation or not getattr(citation, "extracted_case_name", None):
            return False
        name = citation.extracted_case_name
        if not name or name == "N/A":
            return False

        # NEW: Reject names containing signal words that indicate contamination
        signal_patterns = [
            r"\b(this\s+case\s+involves|the\s+case\s+involves|case\s+involves|involves\s+the\s+case)\b",
            r"\b(see\s+the\s+case|see\s+case|the\s+case|case)\b\s+",
            r"\b(in\s+this\s+case|in\s+the\s+case|in\s+case)\b\s+",
            r"\b(cf|e\.g\.|i\.e\.|see also|see|compare|accord|but see|but cf|contra)\b\.?\s+",
            r"\b(if|when|where|while|although|though|unless|until|since|because|as)\b\s+(?:in\s+)?",
        ]

        for pattern in signal_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                logger.warning(f"[EYECITE-VALIDATION] Rejecting eyecite name with signal words: '{name}'")
                return False

        # NEW: Reject fragment extractions like "Inc v. Montgomery" - these start with company suffixes
        # A valid case name shouldn't start with just "Inc", "Corp", "LLC", etc.
        fragment_patterns = [
            r"^(Inc\.?|Corp\.?|LLC|L\.L\.C\.|Ltd\.?|Co\.?|Ass\'?n|Assoc\.?|Org\.?)\s+v\.?\s+",
            r"^(The|A|An)\s+(Inc\.?|Corp\.?|LLC)\s+v\.?\s+",
        ]
        for pattern in fragment_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                logger.warning(f"[EYECITE-VALIDATION] Rejecting fragment extraction: '{name}'")
                return False

        start = getattr(citation, "start_index", None)
        end = getattr(citation, "end_index", None)
        if start is None or end is None:
            return False
        # Obtain strictly isolated context (respects previous citation and semicolons)
        strict_context = get_strict_context_for_citation(text, start, end, None, max_lookback=100)
        if not strict_context:
            return False
        # Normalize quotes for comparison
        ctx = strict_context.replace("\u2019", "'").replace("\u2018", "'").lower()
        nm = str(name).replace("\u2019", "'").replace("\u2018", "'").lower()
        # Require that the name (or its main portion before an opening paren/comma) appears
        # near the end of the strict context (closest to the citation)
        core = nm.split("(")[0].split(",")[0].strip()
        if not core or len(core) < 5:
            core = nm
        hit = ctx.rfind(core)
        if hit == -1:
            return False
        # Ensure proximity (name should end within ~150 chars before the citation)
        distance = len(ctx) - (hit + len(core))
        if distance > 150:
            return False
        # Ensure no hard boundary between the name end and citation
        between = ctx[hit + len(core) :]
        if ";" in between:
            return False
        import re as _re

        if _re.search(r"\bsee\s+also\b", between, _re.IGNORECASE):
            return False
        return True
    except Exception:
        return False


def _is_simplified_case_name(case_name: str) -> bool:
    """
    Detect if a case name is simplified (missing full legal descriptions).

    Args:
        case_name: The case name to check

    Returns:
        True if the case name appears to be simplified
    """
    if not case_name or len(case_name) < 10:
        return False

    case_name_lower = case_name.lower()

    # Check for indicators of simplified names
    simplified_indicators = [
        # Very short names (likely simplified)
        len(case_name) < 30,
        # Missing common legal relationship terms
        not any(
            term in case_name_lower
            for term in [
                "individually",
                "as parent",
                "as guardian",
                "as next friend",
                "administrator",
                "executor",
                "trustee",
                "personal representative",
                "on behalf of",
                "by and through",
                "d/b/a",
                "doing business as",
                "corporation",
                "incorporated",
                "limited liability company",
            ]
        ),
        # Very simple "Last v. Last" pattern (likely simplified)
        len(case_name.split(" v. ")) == 2 and all(len(part.split()) <= 3 for part in case_name.split(" v. ")),
        # Missing corporate suffixes that should be present
        ("inc" in case_name_lower or "corp" in case_name_lower or "llc" in case_name_lower) and len(case_name) < 50,
    ]

    # If multiple indicators suggest simplification, consider it simplified
    return sum(simplified_indicators) >= 2


# Check if eyecite is available
try:
    from eyecite import get_citations

    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False
    logger.warning("Eyecite not available - will use regex-only extraction")


class CleanExtractionPipeline:
    """
    Clean extraction pipeline with zero case name bleeding.

    This class implements a simple, linear pipeline:
    1. Find citations (eyecite + regex)
    2. Deduplicate
    3. Extract case names using ONLY strict context isolation
    4. Extract dates
    5. Return results

    IMPORTANT: Citation patterns are now imported from citation_patterns.py
    (single source of truth). Do NOT define patterns here.
    """

    def __init__(self, document_primary_case_name: Optional[str] = None):
        # CONSOLIDATED: Use shared citation patterns instead of local definitions
        self.citation_patterns = CitationPatterns.get_compiled_patterns()
        self.document_primary_case_name = document_primary_case_name
        logger.info("[CLEAN-PIPELINE] Using shared citation patterns from citation_patterns.py")
        if document_primary_case_name:
            logger.info(f"[CLEAN-PIPELINE] Document primary case name set: '{document_primary_case_name}'")

    def _build_citation_patterns(self) -> Dict[str, re.Pattern]:
        """
        DEPRECATED: This method is kept for backwards compatibility only.
        Now returns shared patterns from citation_patterns.py
        """
        logger.warning("[CLEAN-PIPELINE] _build_citation_patterns() is deprecated - using shared patterns")
        return CitationPatterns.get_compiled_patterns()

    def _preprocess_text(self, text: str) -> str:
        """
        FIX #13: Preprocess text to remove markers that break context isolation.
        FIX #PDF: Normalize PDF line breaks that confuse eyecite citation parsing.

        This removes endnote/footnote markers that separate case names from citations.
        Example: "Acres Bonusing, Inc. v. Marston [Endnote 18], 17 F.4th 901"
        Becomes: "Acres Bonusing, Inc. v. Marston, 17 F.4th 901"

        Also normalizes PDF line breaks within citations:
        Example: "196 Wn.2d\n199" -> "196 Wn.2d 199"
        """
        if not text:
            return text

        # FIX #PDF: Normalize line breaks within citation patterns BEFORE other processing
        # This fixes PDF extraction issues where citations get split across lines
        # Pattern: "196 Wn.2d\n199" or "196 Wn.2d \n 199" -> "196 Wn.2d 199"

        # Fix line breaks between volume/reporter and page number
        # Matches: "123 Wn.2d\n456" or "123 P.3d\n789"
        text = re.sub(
            r"(\d+\s+(?:Wn\.|Wash\.|P\.|S\.\s*Ct\.|L\.\s*Ed\.|F\.|U\.S\.|A\.|N\.E\.|N\.W\.|S\.E\.|S\.W\.|So\.|Cal\.|N\.Y\.)[^\d\n]*\d*[d]?)\s*\n+\s*(\d+)",
            r"\1 \2",
            text,
            flags=re.IGNORECASE,
        )

        # Fix line breaks in "v." constructs: "Borton\nv.\nSons" -> "Borton v. Sons"
        text = re.sub(r"(\w)\s*\n+\s*(v\.?)\s*\n+\s*(\w)", r"\1 \2 \3", text)

        # Fix line breaks after commas in citation strings: ", LLC ,\n196" -> ", LLC, 196"
        text = re.sub(r",\s*\n+\s*(\d)", r", \1", text)

        # Fix line breaks between party name and citation: "Props., LLC\n, 196" -> "Props., LLC, 196"
        text = re.sub(r"(\w)\s*\n+\s*,\s*(\d)", r"\1, \2", text)

        logger.debug("[CLEAN-PIPELINE] Applied PDF line break normalization")

        # FIX #13: Remove endnote/footnote markers in square brackets
        # Patterns: [Endnote 18], [Footnote 5], [FN 3], [n.3], etc.
        removed_count = 0

        # Pattern 1: [Endnote N] with optional surrounding whitespace
        text, count = re.subn(r"\s*\[(?:Endnote|Footnote|FN|n\.?)\s*\d+\]\s*", " ", text, flags=re.IGNORECASE)
        removed_count += count

        # Pattern 2: Endnote markers without brackets (less common but possible)
        text, count = re.subn(r"\s+(?:Endnote|Footnote|FN)\s+\d+\s+", " ", text, flags=re.IGNORECASE)
        removed_count += count

        # Pattern 3: Remove standalone footnote superscripts/numbers between text
        # Be conservative - only remove if it looks like a footnote (small number between words)
        # This catches: "argument that\n\n18\n\nMarston" -> "argument that Marston"
        text = re.sub(r"(\w)\s+\d{1,3}\s+(?=[A-Z][a-z])", r"\1 ", text)

        if removed_count > 0:
            logger.info(f"[CLEAN-PIPELINE] Removed {removed_count} endnote/footnote markers")

        # Clean up any double spaces or excessive whitespace created by removals
        text = re.sub(r"\s+", " ", text)

        # Clean up double commas
        text = re.sub(r",\s*,", ",", text)

        return text

    def extract_citations(self, text: str) -> List[CitationResult]:
        """Extract citations with clean pipeline."""
        print(f"CleanExtractionPipeline.extract_citations CALLED with {len(text)} chars")
        logger.info(f"[CLEAN-PIPELINE] Starting clean extraction pipeline for {len(text)} chars")
        logger.info(f"[CLEAN-PIPELINE] EYECITE_AVAILABLE = {EYECITE_AVAILABLE}")

        # Import law review filter
        try:
            from src.citation_extractor import is_law_review_citation
        except ImportError:
            # Fallback if import fails
            def is_law_review_citation(citation: str) -> bool:
                return bool(re.search(r"\bL\.\s*Rev\.\s|\bLaw\s+Rev", citation, re.IGNORECASE))

        # FIX #13: Preprocess text to remove endnote markers
        original_length = len(text)
        text = self._preprocess_text(text)
        if len(text) != original_length:
            logger.info(
                f"[CLEAN-PIPELINE] Preprocessing: {original_length} -> {len(text)} chars (removed {original_length - len(text)} chars)"
            )

        # Step 1: Find all citations
        all_citations = self._find_all_citations(text)
        logger.info(f"[CLEAN-PIPELINE] Step 1: Found {len(all_citations)} total citations")

        # Step 2: Deduplicate
        deduplicated = self._deduplicate_citations(all_citations)
        logger.info(f"[CLEAN-PIPELINE] Step 2: {len(deduplicated)} after deduplication")

        # Step 2.5: Filter out law review citations (academic articles, not cases)
        filtered = []
        law_review_count = 0
        for citation in deduplicated:
            if is_law_review_citation(citation.citation):
                law_review_count += 1
                logger.info(f"🚫 [LAW-REVIEW-FILTER] Excluded: {citation.citation}")
            else:
                filtered.append(citation)

        if law_review_count > 0:
            logger.info(f"[CLEAN-PIPELINE] Step 2.5: Filtered out {law_review_count} law review citations")
            logger.info(f"[CLEAN-PIPELINE] {len(filtered)} case citations remaining after filtering")

        deduplicated = filtered

        # Step 3: Extract case names using ONLY strict context isolation
        self._extract_all_case_names(text, deduplicated)
        logger.info(f"[CLEAN-PIPELINE] Step 3: Case names extracted for all citations")

        # Step 4: Extract dates
        # DEBUG: Log dates BEFORE _extract_all_dates
        logger.error("=" * 80)
        logger.error("[DEBUG-BEFORE-DATE-EXTRACT] Dates BEFORE _extract_all_dates:")
        for cit in deduplicated:
            if "Hamaatsa" in str(cit.extracted_case_name):
                logger.error(f"🔴 [BEFORE-HAMAATSA] {cit.citation} → Date: {cit.extracted_date}")
        logger.error("=" * 80)

        self._extract_all_dates(text, deduplicated)
        logger.info(f"[CLEAN-PIPELINE] Step 4: Dates extracted for all citations")

        # Step 4.5: Share case names within citation groups (AFTER dates extracted)
        self._share_names_in_citation_groups(text, deduplicated)
        logger.info(f"[CLEAN-PIPELINE] Step 4.5: Shared case names within citation groups")

        # OPTIMIZATION: Verification is handled by unified_processing_pipeline.py
        # This pipeline should ONLY extract citations, not verify them
        # This eliminates duplicate verification calls and improves performance by 30-50%
        logger.info(
            f"[CLEAN-PIPELINE] Pipeline complete: {len(deduplicated)} citations extracted (verification handled by unified pipeline)"
        )
        
        # FIX JAN 2026: Mark WL and Lexis citations as unverified due to proprietary format
        proprietary_count = 0
        for cit in deduplicated:
            # Check if this is a WL or Lexis citation that is not verified
            if not cit.verified:
                # WL citations: format like "2021 WL 3622166"
                # Lexis citations: format like "2021 WL 3622166" (often marked as WL but from Lexis)
                if re.search(r"\d{4}\s+WL\s+\d+", cit.citation) or re.search(r"Lexis\s+\d+", cit.citation, re.IGNORECASE):
                    cit.verification_status = "proprietary_format"
                    cit.verification_error = "Unverified due to proprietary format"
                    proprietary_count += 1
                    logger.debug(f"[PROPRIETARY] {cit.citation}: Marked as unverified due to proprietary format")
        
        if proprietary_count > 0:
            logger.info(f"[PROPRIETARY] Marked {proprietary_count} WL/Lexis citations as unverified due to proprietary format")
        
        return deduplicated

    def _share_names_in_citation_groups(self, text: str, citations: List[CitationResult]) -> None:
        """
        Share case names within citation groups following legal citation structure.

        Legal citations typically follow this pattern:
        Case Name, Citation1, Citation2, Citation3 (Year)

        Example:
        Lac du Flambeau Band of Lake Superior Chippewa Indians v. Coughlin,
        599 U.S. 382, 143 S. Ct. 1689, 216 L. Ed. 2d 342 (2023)

        All citations between the case name and the year should share the same case name.
        """
        logger.info(f"[CITATION-GROUPS] Detecting citation groups in {len(citations)} citations")

        # Sort citations by position in text
        sorted_citations = sorted(citations, key=lambda c: c.start_index if c.start_index else 0)

        groups_found = 0
        names_shared = 0

        i = 0
        while i < len(sorted_citations):
            current = sorted_citations[i]

            # Skip if no case name extracted or position unknown
            if not current.extracted_case_name or current.extracted_case_name == "N/A" or not current.start_index:
                i += 1
                continue

            # Look for subsequent citations within 200 characters
            group = [current]
            j = i + 1
            window_year = None
            year_abs_pos = None
            try:
                # Detect the year immediately following the cluster: (YYYY)
                after_segment = text[current.end_index : current.end_index + 400] if current.end_index else ""
                m_year = re.search(r"\((\d{4})\)", after_segment)
                if m_year:
                    window_year = m_year.group(1)
                    year_abs_pos = (current.end_index or 0) + m_year.start()
            except Exception:
                pass

            while j < len(sorted_citations):
                next_cit = sorted_citations[j]

                if not next_cit.start_index:
                    break
                # If we already found the year boundary, stop once we pass it
                if year_abs_pos is not None and next_cit.start_index >= year_abs_pos:
                    break

                # Fallback proximity check if no year was detected nearby
                if year_abs_pos is None:
                    distance = next_cit.start_index - current.end_index if current.end_index else 999999
                    if distance > 200:
                        break  # Too far apart, end of group

                # Check text between citations - should be mostly commas/whitespace
                between_text = text[current.end_index : next_cit.start_index] if current.end_index else ""
                between_clean = re.sub(r"[,\s]+", "", between_text)

                # HARD BOUNDARY: Do not share across semicolons or transition phrases like 'see also'
                if ";" in between_text or re.search(r"\bsee\s+also\b", between_text, re.IGNORECASE):
                    break

                # If there's significant text between citations (not just commas), it's a new group
                if len(between_clean) > 10:
                    break

                group.append(next_cit)
                current = next_cit
                j += 1

            # If we found a group of 2+ citations, check if they should share names
            if len(group) >= 2:
                # CRITICAL FIX: ALWAYS check for year conflicts in the group
                # Citations with different years are different cases and should NOT share names
                # This was only checking when window_year is None, causing cascading name bugs
                years = set()
                for cit in group:
                    if cit.extracted_date:
                        years.add(cit.extracted_date)
                if len(years) > 1:
                    logger.info(f"[CITATION-GROUPS] Skipping group - different years detected: {years}")
                    i = j if j > i + 1 else i + 1
                    continue

                # Check 2: Names should be variations of each other (not completely different)
                # If we got very different names, they might be different cases in same string
                names_list = []
                for cit in group:
                    if cit.extracted_case_name and cit.extracted_case_name != "N/A":
                        names_list.append(cit.extracted_case_name)

                # If we have multiple different names, check if they're variations (substring/superset)
                if len(set(names_list)) > 1:
                    # Check if names are related (one is substring of another)
                    names_related = False
                    for i_name in range(len(names_list)):
                        for j_name in range(i_name + 1, len(names_list)):
                            name1 = names_list[i_name].lower()
                            name2 = names_list[j_name].lower()
                            # Check if one is a substring of the other (allowing for truncation)
                            if name1 in name2 or name2 in name1:
                                names_related = True
                                break
                        if names_related:
                            break

                    if not names_related:
                        logger.info(f"[CITATION-GROUPS] Skipping group - unrelated names: {set(names_list)}")
                        i = j if j > i + 1 else i + 1
                        continue

                groups_found += 1

                # VERBATIM POLICY: Prefer the first local 'v.' case name within the window
                # Avoid caption-like names that contain docket/role tokens
                best_name = None
                caption_tokens = ("petitioners", "respondent", "appellant", "appellee", "aka", "no")
                # Pass 1: first 'v.' name without caption tokens
                for cit in group:
                    name = cit.extracted_case_name or None
                    if (
                        name
                        and name != "N/A"
                        and "v." in name
                        and not any(tok in name.lower() for tok in caption_tokens)
                    ):
                        best_name = name
                        break
                # Pass 2: any 'v.' name
                if not best_name:
                    for cit in group:
                        name = cit.extracted_case_name or None
                        if name and name != "N/A" and "v." in name:
                            best_name = name
                            break
                # Pass 3: special case prefixes (In re, Ex parte, In the matter)
                if not best_name:
                    for cit in group:
                        name = cit.extracted_case_name or None
                        if (
                            name
                            and name != "N/A"
                            and (
                                name.lower().startswith("in re")
                                or name.lower().startswith("ex parte")
                                or name.lower().startswith("in the matter")
                            )
                        ):
                            best_name = name
                            break
                # Pass 4: scan window text for a local 'X v. Y' if still not found
                if not best_name:
                    try:
                        # Define scan bounds: from first citation end to year boundary (if found)
                        first_cit = group[0]
                        scan_start = first_cit.end_index or first_cit.start_index or 0
                        scan_end = year_abs_pos if year_abs_pos is not None else min(len(text), scan_start + 400)
                        if 0 <= scan_start < scan_end <= len(text):
                            window_seg = text[scan_start:scan_end]
                            # Look for 'X v. Y' and stop at ', No.' or comma before reporter
                            m = re.search(
                                r"([A-Z][^,;()\n]{2,120})\s+v\.\s+([^,;()\n]{2,120}?)(?=,\s*(?:\d|No\b|$))", window_seg
                            )
                            if m:
                                cand = f"{m.group(1).strip()} v. {m.group(2).strip()}"
                                # Exclude caption-like tokens per verbatim policy (no cleanup)
                                if not any(tok in cand.lower() for tok in caption_tokens):
                                    best_name = cand
                                    logger.info(
                                        f"[CITATION-GROUPS] Window scan selected local case name: '{best_name}'"
                                    )
                    except Exception:
                        pass

                # Final fallback: any non-empty name that does NOT include caption tokens
                if not best_name:
                    for cit in group:
                        name = cit.extracted_case_name or None
                        if name and name != "N/A" and not any(tok in name.lower() for tok in caption_tokens):
                            best_name = name
                            break

                if best_name:
                    # CRITICAL: Filter out header patterns before sharing names
                    # Check if best_name contains header patterns (ET AL + role word, or role word + NO)
                    best_name_upper = best_name.upper()
                    has_et_al = "ET AL" in best_name_upper or "ETAL" in best_name_upper.replace(" ", "")
                    has_role_word = any(
                        role in best_name_upper
                        for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                    )
                    has_no = "NO." in best_name_upper or " NO " in best_name_upper or best_name_upper.endswith(" NO")

                    # Skip if it's clearly a header (ET AL + role word, or role word + NO)
                    if (has_et_al and has_role_word) or (has_role_word and has_no):
                        logger.warning(
                            f"[CITATION-GROUPS] REJECTED header pattern from best_name: '{best_name}' - NOT sharing with group"
                        )
                        best_name = None

                    if best_name:
                        # Share the best name with all citations in the group
                        citations_text = ", ".join([c.citation for c in group])
                        logger.info(f"[CITATION-GROUPS] Found group: {citations_text}")
                        if window_year:
                            logger.info(f"[CITATION-GROUPS] Window year detected: {window_year}")
                        else:
                            logger.info(
                                f"[CITATION-GROUPS] Same year (fallback): {list(set([c.extracted_date for c in group if c.extracted_date]))}"
                            )
                        logger.info(f"[CITATION-GROUPS] Best name: '{best_name}'")

                        for cit in group:
                            old_name = cit.extracted_case_name
                            # PARALLEL vs SERIES CITATION FIX: Check if this citation is parallel or series
                            # Parallel citations (same case) should share names, series citations (different cases) should not
                            if cit.start_index and cit.start_index > 0:
                                look_behind = text[max(0, cit.start_index - 100):cit.start_index]
                                prev_citation_pattern = r'\d{4}\s+WL\s+\d+|\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+|\d+\s+U\.S\.\s+\d+'
                                
                                if re.search(prev_citation_pattern, look_behind):
                                    # Found a previous citation - check if it's parallel (same case) or series (different case)
                                    is_parallel = False
                                    
                                    # Check if we have eyecite metadata
                                    if hasattr(cit, 'metadata') and cit.metadata:
                                        current_plaintiff = cit.metadata.get('plaintiff')
                                        current_defendant = cit.metadata.get('defendant')
                                        
                                        # Find the previous citation
                                        for prev_cit in group:
                                            if (hasattr(prev_cit, 'end_index') and hasattr(cit, 'start_index') and
                                                prev_cit.end_index and cit.start_index and
                                                prev_cit.end_index < cit.start_index and 
                                                cit.start_index - prev_cit.end_index < 100):
                                                
                                                # Check if they have the same parties
                                                if hasattr(prev_cit, 'metadata') and prev_cit.metadata:
                                                    prev_plaintiff = prev_cit.metadata.get('plaintiff')
                                                    prev_defendant = prev_cit.metadata.get('defendant')
                                                    
                                                    if (current_plaintiff and current_defendant and 
                                                        current_plaintiff == prev_plaintiff and 
                                                        current_defendant == prev_defendant):
                                                        is_parallel = True
                                                        logger.info(f"[PARALLEL-FIX-GROUP] Sharing name for parallel citation: {cit.citation}")
                                                        break
                                                    
                                                    # Check extra field
                                                    extra = prev_cit.metadata.get('extra')
                                                    if extra and cit.citation in extra:
                                                        is_parallel = True
                                                        logger.info(f"[PARALLEL-FIX-GROUP] Sharing name for parallel citation (via extra): {cit.citation}")
                                                        break
                                        
                                        # Check for semicolon
                                        if ';' in look_behind:
                                            is_parallel = False
                                            logger.info(f"[SERIES-FIX-GROUP] Semicolon detected - not sharing name for series citation: {cit.citation}")
                                    
                                    if not is_parallel:
                                        # This is a series citation - don't share the name
                                        logger.info(f"[SERIES-FIX-GROUP] Not sharing name for series citation: {cit.citation}")
                                        if not hasattr(cit, "metadata") or cit.metadata is None:
                                            cit.metadata = {}
                                        cit.metadata["is_series_citation"] = True
                                        continue
                            
                            if old_name != best_name:
                                cit.extracted_case_name = best_name
                                names_shared += 1
                                logger.info(
                                    f"[CITATION-GROUPS] Shared '{best_name}' with {cit.citation} (was: '{old_name}')"
                                )
                        # Apply window year to ALL citations in the group when available
                        if window_year and (cit.extracted_date != window_year):
                            cit.extracted_date = window_year
                            logger.info(f"[CITATION-GROUPS] Set year {window_year} for {cit.citation}")

            # Move to next potential group
            i = j if j > i + 1 else i + 1

        logger.info(f"[CITATION-GROUPS] Found {groups_found} groups, shared names with {names_shared} citations")

    def _find_all_citations(self, text: str) -> List[CitationResult]:
        """Find all citations using eyecite and regex."""
        citations = []
        seen = set()

        # Use eyecite if available
        if EYECITE_AVAILABLE:
            try:
                eyecite_citations = self._find_with_eyecite(text)
                for cit in eyecite_citations:
                    key = (cit.citation, cit.start_index)
                    if key not in seen:
                        citations.append(cit)
                        seen.add(key)
                logger.info(f"[CLEAN-PIPELINE] Eyecite found {len(eyecite_citations)} citations")
            except Exception as e:
                logger.error(f"[CLEAN-PIPELINE] Eyecite failed: {e}")

        # Add regex citations
        regex_citations = self._find_with_regex(text)
        for cit in regex_citations:
            key = (cit.citation, cit.start_index)
            if key not in seen:
                citations.append(cit)
                seen.add(key)
        logger.info(f"[CLEAN-PIPELINE] Regex found {len(regex_citations)} citations")

        return citations

    def _clean_eyecite_case_name(self, case_name: str, text_context: str = None) -> str:
        """
        Clean contamination from eyecite-extracted case names.

        ARCHITECTURE FIX: Delegates to unified_case_extraction_master._clean_case_name()
        to avoid code duplication. This ensures all cleaning logic is in ONE place.

        Args:
            case_name: The case name to clean
            text_context: Optional broader document text to search for full corporate names
        """
        if not case_name:
            return case_name

        # OPTION 1 CONSOLIDATION: Use the master cleaner instead of duplicating logic
        from src.unified_case_extraction_master import get_master_extractor

        try:
            extractor = get_master_extractor()
            # The master cleaner handles:
            # - Citation pattern removal (", 31 Wn. App. 2d 343")
            # - Corporate name truncation repair ("Inc. v." -> "Company, Inc. v.")
            # - Status word removal ("overruling", "affirming", etc.)
            # - Contamination filtering (doctrine, rule, test words)
            # - Normalization and validation
            # USER FIX: Pass text_context to find full corporate names
            cleaned = extractor._clean_case_name(case_name, context=text_context)
            logger.debug(f"[CLEAN-DELEGATE] '{case_name[:50]}' -> '{cleaned[:50]}'")
            return cleaned
        except Exception as e:
            logger.warning(f"[CLEAN-DELEGATE] Master cleaner failed: {e}, using original")
            return case_name.strip()

    def _find_with_eyecite(self, text: str) -> List[CitationResult]:
        """Find citations using eyecite."""
        logger.info(f"[EYECITE] Starting eyecite extraction for {len(text)} chars")
        citations = []

        try:
            found = get_citations(text)
            found_list = list(found)
            logger.info(f"[EYECITE] Eyecite found {len(found_list)} raw citations")

            for idx, cit_obj in enumerate(found_list):
                # Filter out non-case citations
                cit_type = type(cit_obj).__name__

                # Skip Id. citations and law citations
                if cit_type in ["IdCitation", "FullLawCitation", "ShortCaseCitation", "SupraCitation"]:
                    continue

                # Use eyecite's built-in span information (much more reliable than text.find!)
                if hasattr(cit_obj, "span") and cit_obj.span():
                    start, end = cit_obj.span()
                    # Get actual citation text from source
                    cit_text = text[start:end]
                else:
                    # No span info - skip this citation
                    continue

                # Skip if contains statutory indicators
                if any(indicator in cit_text for indicator in ["§", "Code", "Stat.", "C.F.R."]):
                    continue

                # USER FIX: Filter out short-form citations like "Erickson, 31 Wn. App. 2d at 118"
                # These are short citations that reference a full citation that appeared earlier
                # Pattern: Case name (1-3 words), comma, volume reporter page, "at" + page
                if self._is_short_form_citation(cit_text):
                    logger.debug(f"[EYECITE] Filtered short-form citation: '{cit_text}'")
                    continue

                # Try to extract case name and date from eyecite metadata (often more accurate)
                eyecite_case_name = None
                eyecite_date = None

                # COMPARISON MODE: Allow disabling eyecite metadata via environment variable
                import os

                use_eyecite_metadata = os.environ.get("USE_EYECITE_METADATA", "true").lower() == "true"

                if use_eyecite_metadata and hasattr(cit_obj, "metadata") and cit_obj.metadata:
                    plaintiff = getattr(cit_obj.metadata, "plaintiff", None)
                    defendant = getattr(cit_obj.metadata, "defendant", None)
                    year = getattr(cit_obj.metadata, "year", None)

                    if plaintiff and defendant:
                        # Eyecite found both parties
                        eyecite_case_name = f"{plaintiff} v. {defendant}"
                        logger.info(f"[EYECITE-META] Raw from eyecite: {eyecite_case_name}")

                        # CRITICAL: Check for header patterns IMMEDIATELY before any processing
                        eyecite_name_upper = eyecite_case_name.upper()
                        has_et_al = "ET AL" in eyecite_name_upper or "ETAL" in eyecite_name_upper.replace(
                            " ", ""
                        ).replace(".", "").replace(",", "")
                        has_role_word = any(
                            role in eyecite_name_upper
                            for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                        )
                        has_no = (
                            "NO." in eyecite_name_upper
                            or " NO " in eyecite_name_upper
                            or eyecite_name_upper.endswith(" NO")
                        )
                        header_pattern_match = re.search(
                            r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            eyecite_name_upper,
                        )

                        if (has_et_al and has_role_word) or (has_role_word and has_no) or header_pattern_match:
                            logger.error(
                                f"[EYECITE-META] REJECTED header pattern from eyecite: '{eyecite_case_name}' - setting to None"
                            )
                            eyecite_case_name = None  # Reject header immediately
                        else:
                            # CRITICAL: Clean contamination from eyecite extractions
                            # USER FIX: Pass text context to find full corporate names
                            eyecite_case_name = self._clean_eyecite_case_name(eyecite_case_name, text_context=text)
                            logger.info(f"[EYECITE-META] After cleaning: {eyecite_case_name}")
                    elif plaintiff:
                        eyecite_case_name = plaintiff
                        # USER FIX: Pass text context
                        eyecite_case_name = self._clean_eyecite_case_name(eyecite_case_name, text_context=text)
                        logger.info(f"[EYECITE-META] Extracted plaintiff only: {eyecite_case_name}")
                elif not use_eyecite_metadata:
                    logger.info(f"[EYECITE-META] Skipping eyecite metadata extraction (USE_EYECITE_METADATA=false)")

                # FIX: Skip eyecite's year extraction - it's often wrong for complex citations
                # Eyecite was extracting 1976 for both citations in our test case
                # Let our custom date extraction handle this instead
                if use_eyecite_metadata and hasattr(cit_obj, "metadata") and cit_obj.metadata:
                    year = getattr(cit_obj.metadata, "year", None)
                    if year:
                        logger.info(
                            f"[EYECITE-SKIP] Eyecite found year '{year}' for {cit_text}, but will use better extraction instead"
                        )
                        # DON'T set eyecite_date - let _extract_all_dates handle it

                        # DEBUG: Track for problematic citations
                        if "388 P.3d 977" in cit_text:
                            logger.error(f"🔍 [DEBUG-388] EYECITE provided year: {year} (skipped)")

                # FIX #13 DIAGNOSTIC: Log eyecite output for problematic citation
                if "17 F.4th 901" in cit_text or "17 F. 4th 901" in cit_text:
                    logger.error(f"[FIX-13-EYECITE] 🔍 Found target citation: {cit_text}")
                    logger.error(f"[FIX-13-EYECITE]   eyecite_case_name: '{eyecite_case_name}'")
                    logger.error(f"[FIX-13-EYECITE]   eyecite_date: '{eyecite_date}'")
                    logger.error(f"[FIX-13-EYECITE]   start: {start}, end: {end}")
                    logger.error(f"[FIX-13-EYECITE]   has metadata: {hasattr(cit_obj, 'metadata')}")
                    if hasattr(cit_obj, "metadata") and cit_obj.metadata:
                        logger.error(f"[FIX-13-EYECITE]   plaintiff: {getattr(cit_obj.metadata, 'plaintiff', None)}")
                        logger.error(f"[FIX-13-EYECITE]   defendant: {getattr(cit_obj.metadata, 'defendant', None)}")

                # FIX DEC 2025: Extract case name from document context FIRST
                # Eyecite metadata often contains abbreviated names (e.g., "Cmtys" instead of "Manufactured Hous. Cmtys.")
                # The extracted_case_name should be EXACTLY as it appears in the document
                context_case_name = None
                try:
                    from src.utils.strict_context_isolator import (
                        get_strict_context_for_citation,
                        extract_case_name_from_strict_context,
                    )

                    strict_context = get_strict_context_for_citation(text, start, end, previous_citation_end=None)
                    if strict_context:
                        context_case_name = extract_case_name_from_strict_context(strict_context, cit_text)
                        if context_case_name:
                            logger.info(f"[CONTEXT-FIRST] Extracted from document: '{context_case_name}'")
                except Exception as ctx_err:
                    logger.debug(f"[CONTEXT-FIRST] Context extraction failed: {ctx_err}")

                # Prefer context extraction over eyecite metadata (context is exact document text)
                # Only use eyecite as fallback if context extraction failed
                final_case_name = context_case_name if context_case_name else eyecite_case_name

                # If both exist, prefer the longer one (more complete)
                if context_case_name and eyecite_case_name:
                    if len(context_case_name) >= len(eyecite_case_name):
                        final_case_name = context_case_name
                        logger.info(
                            f"[CONTEXT-FIRST] Using context name (longer): '{context_case_name}' over eyecite '{eyecite_case_name}'"
                        )
                    else:
                        # Eyecite is longer, but check if it's actually more complete or just different
                        # Prefer context since it's the actual document text
                        final_case_name = context_case_name
                        logger.info(
                            f"[CONTEXT-FIRST] Using context name (document text): '{context_case_name}' over eyecite '{eyecite_case_name}'"
                        )

                # CRITICAL FIX: Filter eyecite_date if it's from a "Cite as:" header
                # Eyecite extracts dates from document text which may include headers
                filtered_eyecite_date = None
                if eyecite_date:
                    # Check if this date appears in a "Cite as:" header in the broader context
                    broader_context = text[max(0, start - 200):min(len(text), end + 200)]
                    cite_as_check = re.search(
                        rf"Cite\s+as:?\s*[^\n]*{re.escape(str(eyecite_date))}[^\n]*",
                        broader_context,
                        re.IGNORECASE
                    )
                    if cite_as_check:
                        logger.warning(
                            f"[CLEAN-PIPELINE] Rejected eyecite_date {eyecite_date} for {cit_text} - appears in 'Cite as:' header"
                        )
                        filtered_eyecite_date = None
                    else:
                        # Also check volume-based heuristics
                        if " U.S. " in cit_text:
                            volume_match = re.search(r"(\d+)\s+U\.\s*S\.", cit_text)
                            if volume_match:
                                volume = int(volume_match.group(1))
                                year_int = int(eyecite_date) if str(eyecite_date).isdigit() else None
                                if year_int and 400 <= volume <= 600 and year_int >= 2015:
                                    logger.warning(
                                        f"[CLEAN-PIPELINE] Rejected eyecite_date {eyecite_date} for {cit_text} "
                                        f"(U.S. volume {volume}) - year 2015+ is likely from header"
                                    )
                                    filtered_eyecite_date = None
                                else:
                                    filtered_eyecite_date = eyecite_date
                            else:
                                filtered_eyecite_date = eyecite_date
                        elif " F.3d " in cit_text:
                            volume_match = re.search(r"(\d+)\s+F\.\s*3d", cit_text)
                            if volume_match:
                                volume = int(volume_match.group(1))
                                year_int = int(eyecite_date) if str(eyecite_date).isdigit() else None
                                if year_int and 800 <= volume <= 900 and year_int >= 2020:
                                    logger.warning(
                                        f"[CLEAN-PIPELINE] Rejected eyecite_date {eyecite_date} for {cit_text} "
                                        f"(F.3d volume {volume}) - year 2020+ is likely from header"
                                    )
                                    filtered_eyecite_date = None
                                else:
                                    filtered_eyecite_date = eyecite_date
                            else:
                                filtered_eyecite_date = eyecite_date
                        else:
                            filtered_eyecite_date = eyecite_date
                
                # Create CitationResult
                citation = CitationResult(
                    citation=cit_text,
                    start_index=start,
                    end_index=end,
                    extracted_case_name=final_case_name,  # Prefer document context over eyecite metadata
                    extracted_date=filtered_eyecite_date,  # Use filtered eyecite date (headers removed)
                    method="clean_pipeline_v1",
                    confidence=0.9,
                    metadata={
                        "detector": "eyecite",
                        "type": cit_type,
                        "eyecite_extracted": bool(eyecite_case_name),
                        "context_extracted": bool(context_case_name),
                        # Include eyecite metadata for parallel citation detection
                        "plaintiff": plaintiff,
                        "defendant": defendant,
                        "extra": getattr(cit_obj.metadata, 'extra', None) if hasattr(cit_obj, 'metadata') and cit_obj.metadata else None,
                    },
                )

                logger.info(f"[CLEAN-PIPELINE-DEBUG] Created {cit_text} with start={start}, end={end}")

                citations.append(citation)

        except Exception as e:
            logger.error(f"[CLEAN-PIPELINE] Eyecite error: {e}")

        return citations

    def _is_short_form_citation(self, citation_text: str) -> bool:
        """
        USER FIX: Detect short-form citations like "Erickson, 31 Wn. App. 2d at 118"

        Short-form citations have the pattern:
        - Case name (1-3 words, often just a single word)
        - Comma
        - Volume Reporter Page
        - "at" + page number

        These should be filtered out because they reference a full citation that appeared earlier.
        """
        import re

        # Pattern: Case name (1-3 words), comma, volume reporter page, "at" + page
        # Examples: "Erickson, 31 Wn. App. 2d at 118" or "Smith, 123 F.3d at 456"
        short_form_pattern = r"^[A-Z][A-Za-z\s\.,&\-\']{1,40},\s+\d+\s+[A-Za-z\.\s]+\d+\s+at\s+\d+"

        if re.search(short_form_pattern, citation_text, re.IGNORECASE):
            return True

        # Also check for pattern without "at" but with just volume reporter page after comma
        # This catches cases like "Erickson, 31 Wn. App. 2d 100" (short form without "at")
        short_form_pattern2 = r"^[A-Z][A-Za-z\s\.,&\-\']{1,40},\s+\d+\s+[A-Za-z\.\s]+\d+\s+\d+$"

        if re.search(short_form_pattern2, citation_text, re.IGNORECASE):
            # Additional check: if the case name is very short (1-2 words) and citation is short,
            # it's likely a short-form citation
            parts = citation_text.split(",", 1)
            if len(parts) == 2:
                case_name_part = parts[0].strip()
                citation_part = parts[1].strip()
                # If case name is 1-2 words and citation part is just volume reporter page (no year),
                # it's likely a short-form citation
                case_name_words = len(case_name_part.split())
                if case_name_words <= 2 and not re.search(r"\(\d{4}\)", citation_part):
                    return True

        return False

    def _find_with_regex(self, text: str) -> List[CitationResult]:
        """Find citations using regex patterns."""
        citations = []

        for pattern_name, pattern in self.citation_patterns.items():
            for match in pattern.finditer(text):
                cit_text = match.group(0)
                start = match.start()
                end = match.end()

                # USER FIX: Filter out short-form citations like "Erickson, 31 Wn. App. 2d at 118"
                if self._is_short_form_citation(cit_text):
                    logger.debug(f"[REGEX] Filtered short-form citation: '{cit_text}'")
                    continue

                citation = CitationResult(
                    citation=cit_text,
                    start_index=start,
                    end_index=end,
                    extracted_case_name=None,  # Will be filled by strict isolation
                    extracted_date=None,  # Will be filled later
                    method="clean_pipeline_v1",
                    confidence=0.8,
                    metadata={"detector": "regex", "pattern": pattern_name},
                )

                citations.append(citation)

        return citations

    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations based on text and position."""
        seen = {}
        deduplicated = []

        for cit in citations:
            # Normalize citation text for comparison
            normalized = re.sub(r"\s+", " ", cit.citation.strip())

            # Create key based on citation and approximate position
            key = (normalized, cit.start_index // 10)  # Bucket positions by 10s

            if key not in seen:
                seen[key] = cit
                deduplicated.append(cit)
            else:
                # Keep the one with better position info
                existing = seen[key]
                if cit.start_index and not existing.start_index:
                    seen[key] = cit
                    deduplicated.remove(existing)
                    deduplicated.append(cit)

        return deduplicated

    def _extract_all_case_names(self, text: str, citations: List[CitationResult]) -> None:
        """
        Extract case names for citations that don't already have them.

        Eyecite provides case names for many citations. We only need to extract
        for citations where eyecite didn't find a case name.
        """
        logger.info(f"[CLEAN-PIPELINE] Extracting case names for {len(citations)} citations")

        success_count = 0
        fail_count = 0
        skipped_count = 0
        processed_citations = []  # Track citations as we process them

        for citation in citations:
            try:
                # FIX #13 DEBUG: Log ONLY target citation to reduce noise
                is_target = "17 F.4th 901" in citation.citation or "17 F. 4th 901" in citation.citation
                if is_target:
                    logger.error(f"[FIX-13-TRACE] 🎯 Processing TARGET citation: {citation.citation}")
                    logger.error(f"[FIX-13-TRACE]   Initial extracted_case_name: '{citation.extracted_case_name}'")
                    logger.error(f"[FIX-13-TRACE]   Has name: {bool(citation.extracted_case_name)}")
                    logger.error(f"[FIX-13-TRACE]   Is N/A: {citation.extracted_case_name == 'N/A'}")
                    logger.error(f"[FIX-13-TRACE]   Type: {type(citation.extracted_case_name)}")

                # Skip if eyecite already provided a good case name
                # NEW: Also validate eyecite-provided names and check for simplified extractions
                logger.error(f"🔥🔥🔥 [CLEAN-PIPELINE-DEBUG] Processing citation: {citation.citation}")
                logger.error(
                    f"🔥🔥🔥 [CLEAN-PIPELINE-DEBUG] Initial extracted_case_name: '{citation.extracted_case_name}'"
                )

                if citation.extracted_case_name and citation.extracted_case_name != "N/A":
                    # CRITICAL: Check for header patterns FIRST before any other validation
                    extracted_name_upper = citation.extracted_case_name.upper()
                    has_et_al = "ET AL" in extracted_name_upper or "ETAL" in extracted_name_upper.replace(" ", "")
                    has_role_word = any(
                        role in extracted_name_upper
                        for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                    )
                    has_no = (
                        "NO." in extracted_name_upper
                        or " NO " in extracted_name_upper
                        or extracted_name_upper.endswith(" NO")
                    )

                    is_header = (has_et_al and has_role_word) or (has_role_word and has_no)

                    if is_header:
                        logger.error(
                            f"[CLEAN-PIPELINE] REJECTED eyecite header pattern: '{citation.extracted_case_name}' - forcing re-extraction"
                        )
                        citation.extracted_case_name = None  # Force re-extraction
                        # Continue to extraction below (don't skip)
                    else:
                        is_valid = is_valid_case_name(citation.extracted_case_name)
                        is_simplified = _is_simplified_case_name(citation.extracted_case_name)
                        in_context = _eyecite_name_in_strict_context(text, citation)

                        logger.error(
                            f"🔥🔥🔥 [CLEAN-PIPELINE-DEBUG] Validation: valid={is_valid}, simplified={is_simplified}, in_context={in_context}"
                        )

                        # Accept eyecite name ONLY if it is valid, not simplified,
                        # AND appears in the strict context near this citation.
                        if is_valid and not is_simplified and in_context:
                            skipped_count += 1
                            success_count += 1  # Count as success since we have a name
                            logger.error(f"🔥🔥🔥 [CLEAN-PIPELINE-DEBUG] ✅ SKIPPING - using eyecite name")
                            logger.debug(
                                f"[CLEAN-PIPELINE] Keeping eyecite name for {citation.citation}: '{citation.extracted_case_name}'"
                            )
                            continue
                        else:
                            # Eyecite gave us junk or simplified name - need to re-extract
                            logger.error(
                                f"🔥🔥🔥 [CLEAN-PIPELINE-DEBUG] ❌ INVALID EYECITE NAME - will re-extract with strict isolator"
                            )
                            if is_simplified:
                                logger.warning(
                                    f"[CLEAN-PIPELINE] Eyecite name is simplified for {citation.citation}: '{citation.extracted_case_name}' - re-extracting for full name"
                                )
                            else:
                                logger.warning(
                                    f"[CLEAN-PIPELINE] Eyecite name invalid or out-of-context for {citation.citation}: '{citation.extracted_case_name}' - re-extracting"
                                )
                            citation.extracted_case_name = None  # Force re-extraction
                else:
                    if is_target:
                        logger.error(f"[FIX-13-TRACE]   ⚠️  No valid initial name - will extract")

                # FIX NOV 9: Try special format extraction BEFORE strict isolation
                case_name = None
                
                # PARALLEL vs SERIES CITATION FIX: Check if this is NOT the first citation
                # If it's not the first, determine if it's a parallel citation (same case) or series citation (different case)
                if citation.start_index and citation.start_index > 0:
                    # Look backwards to see if there's another citation within 100 characters
                    look_behind = text[max(0, citation.start_index - 100):citation.start_index]
                    prev_citation_pattern = r'\d{4}\s+WL\s+\d+|\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+|\d+\s+U\.S\.\s+\d+'
                    
                    # Only treat as series/parallel if there are clear indicators
                    # 1. Semicolon indicates different cases (series)
                    # 2. Comma-separated citations without periods between them (parallel/series)
                    # 3. Citations within the same sentence without case names
                    
                    is_series_or_parallel = False
                    
                    # Check for semicolon (clear series indicator)
                    if ';' in look_behind:
                        is_series_or_parallel = True
                        logger.info(f"[SERIES-DEBUG] Semicolon detected for {citation.citation}")
                    
                    # Check if citations are comma-separated without periods (likely parallel/series)
                    elif re.search(prev_citation_pattern, look_behind):
                        # Check if there's no period between the citations
                        last_period = look_behind.rfind('.')
                        last_citation = re.search(prev_citation_pattern, look_behind)
                        if last_citation and (last_period < 0 or last_period < last_citation.start()):
                            is_series_or_parallel = True
                            logger.info(f"[SERIES-DEBUG] Comma-separated citations without period for {citation.citation}")
                    
                    # Check if multiple citations appear in the same sentence without individual case names
                    elif re.search(prev_citation_pattern, look_behind):
                        # Look at the full context
                        full_context = text[max(0, citation.start_index - 200):citation.start_index + 50]
                        # Count citations in this segment
                        citation_count = len(re.findall(prev_citation_pattern, full_context))
                        # If multiple citations but no "v." patterns between them, likely series/parallel
                        v_patterns = len(re.findall(r'\s+v\.\s+', full_context))
                        if citation_count > 1 and v_patterns < citation_count:
                            is_series_or_parallel = True
                            logger.info(f"[SERIES-DEBUG] Multiple citations without case names for {citation.citation}")
                    
                    if is_series_or_parallel:
                        logger.info(f"[PARALLEL-DEBUG] Found previous citation pattern for {citation.citation}")
                        # Found a previous citation - check if it's the same case (parallel) or different (series)
                        is_parallel = False
                        
                        # Check if we have eyecite metadata to determine parallel vs series
                        if hasattr(citation, 'metadata') and citation.metadata:
                            current_plaintiff = citation.metadata.get('plaintiff')
                            current_defendant = citation.metadata.get('defendant')
                            logger.info(f"[PARALLEL-DEBUG] Current citation parties: {current_plaintiff} v. {current_defendant}")
                            
                            # Find the previous citation in our processed citations list
                            for prev_cit in citations:
                                if (hasattr(prev_cit, 'end_index') and hasattr(citation, 'start_index') and
                                    prev_cit.end_index and citation.start_index and
                                    prev_cit.end_index < citation.start_index and 
                                    citation.start_index - prev_cit.end_index < 100):
                                    
                                    logger.info(f"[PARALLEL-DEBUG] Checking previous citation: {prev_cit.citation}")
                                    
                                    # Check if both citations have the same parties (parallel citation)
                                    if hasattr(prev_cit, 'metadata') and prev_cit.metadata:
                                        prev_plaintiff = prev_cit.metadata.get('plaintiff')
                                        prev_defendant = prev_cit.metadata.get('defendant')
                                        logger.info(f"[PARALLEL-DEBUG] Previous citation parties: {prev_plaintiff} v. {prev_defendant}")
                                        
                                        # Same plaintiff and defendant means it's a parallel citation
                                        if (current_plaintiff and current_defendant and 
                                            current_plaintiff == prev_plaintiff and 
                                            current_defendant == prev_defendant):
                                            is_parallel = True
                                            logger.info(f"[PARALLEL-FIX] Detected parallel citation: {citation.citation} (same case as {prev_cit.citation})")
                                            # Use the same case name as the previous citation
                                            citation.extracted_case_name = prev_cit.extracted_case_name
                                            if not hasattr(citation, "metadata") or citation.metadata is None:
                                                citation.metadata = {}
                                            citation.metadata["is_parallel_citation"] = True
                                            success_count += 1
                                            break
                                    
                                    # Also check if previous citation's extra field contains this citation
                                    if hasattr(prev_cit, 'metadata') and prev_cit.metadata:
                                        extra = prev_cit.metadata.get('extra')
                                        if extra and citation.citation in extra:
                                            is_parallel = True
                                            logger.info(f"[PARALLEL-FIX] Detected parallel citation via extra field: {citation.citation}")
                                            citation.extracted_case_name = prev_cit.extracted_case_name
                                            if not hasattr(citation, "metadata") or citation.metadata is None:
                                                citation.metadata = {}
                                            citation.metadata["is_parallel_citation"] = True
                                            success_count += 1
                                            break
                                    
                                    # Also check if current citation's extra field contains the previous citation
                                    # (for cases where eyecite puts parallel info in the second citation)
                                    if hasattr(citation, 'metadata') and citation.metadata:
                                        extra = citation.metadata.get('extra')
                                        if extra and prev_cit.citation in extra:
                                            is_parallel = True
                                            logger.info(f"[PARALLEL-FIX] Detected parallel citation via current extra field: {citation.citation}")
                                            citation.extracted_case_name = prev_cit.extracted_case_name
                                            if not hasattr(citation, "metadata") or citation.metadata is None:
                                                citation.metadata = {}
                                            citation.metadata["is_parallel_citation"] = True
                                            success_count += 1
                                            break
                            
                            # Check for semicolon which indicates different cases
                            if ';' in look_behind:
                                is_parallel = False
                                logger.info(f"[SERIES-FIX] Semicolon detected - treating as series citation: {citation.citation}")
                        
                        if not is_parallel:
                            # This is a series citation (different case)
                            # Skip case name extraction entirely
                            logger.info(f"[SERIES-FIX-CLEAN] Skipping case name extraction for series citation: {citation.citation}")
                            citation.extracted_case_name = "N/A"
                            # Mark this as a series citation so Eyecite fallback doesn't override it
                            if not hasattr(citation, "metadata") or citation.metadata is None:
                                citation.metadata = {}
                            citation.metadata["is_series_citation"] = True
                            success_count += 1
                            continue

                # CRITICAL DEBUG: Check if start_index is None
                if citation.start_index is None:
                    logger.error(
                        f"[CRITICAL-BUG] Citation '{citation.citation}' has start_index=None - CANNOT run special format extraction!"
                    )
                else:
                    case_name = _extract_special_citation_formats(text, citation.citation, citation.start_index)
                    if case_name:
                        logger.error(f"[SPECIAL-FORMATS] 🎉 Special format extraction SUCCESS: '{case_name}'")

                # Use strict context isolation if special formats didn't find anything
                # CRITICAL: Pass full citation list so isolator can identify boundaries
                if not case_name:
                    if is_target:
                        logger.error(f"[FIX-13-TRACE]   🔍 Calling strict_context_isolator...")

                    # FIX DEC 2025 v12/v13: Find ACTUAL citation position BEFORE strict isolation
                    # eyecite often reports positions 200-300+ chars off from actual PDF text positions
                    # v13: Find the occurrence CLOSEST to eyecite's position (handles repeated citations)
                    import re as _re_pos12

                    actual_start = citation.start_index
                    actual_end = citation.end_index
                    try:
                        # FIX v14: More flexible pattern - handle all whitespace variants
                        cit_text = citation.citation
                        # Normalize citation text: collapse whitespace and make flexible
                        cit_pattern = _re_pos12.escape(cit_text)
                        # Replace escaped spaces with \s+ to match any whitespace
                        cit_pattern = cit_pattern.replace(r"\ ", r"\s+")
                        # Also handle cases where there might be no space (e.g., "Wn.2d" vs "Wn. 2d")
                        cit_pattern = cit_pattern.replace(r"\.", r"\.\s*")

                        # v13/v14: Find ALL occurrences and pick the closest one to eyecite position
                        all_matches = list(_re_pos12.finditer(cit_pattern, text))
                        logger.error(
                            f"[FIX-v14] Pattern '{cit_pattern[:30]}...' found {len(all_matches)} matches for {cit_text}"
                        )
                        if all_matches:
                            # Find match closest to eyecite's reported position
                            best_match = min(all_matches, key=lambda m: abs(m.start() - citation.start_index))
                            actual_start = best_match.start()
                            actual_end = best_match.end()
                            if actual_start != citation.start_index:
                                logger.error(
                                    f"[FIX-v14] Position correction: eyecite={citation.start_index}, actual={actual_start}, diff={actual_start - citation.start_index}"
                                )
                    except Exception as pos_err:
                        logger.warning(f"[FIX-v14] Position lookup failed: {pos_err}")

                    case_name = extract_case_name_with_strict_isolation(
                        text=text,
                        citation_text=citation.citation,
                        citation_start=actual_start,  # FIX v12: Use corrected position
                        citation_end=actual_end,  # FIX v12: Use corrected position
                        all_citations=citations,  # Pass full list for proper boundary detection
                        document_primary_case_name=getattr(
                            self, "document_primary_case_name", None
                        ),  # Pass contamination filter
                    )
                if is_target:
                    logger.error(f"[FIX-13-TRACE]   📝 Strict isolation returned: '{case_name}'")

                # DEBUG: Track extraction path for problematic citations
                if "388 P.3d 977" in citation.citation:
                    logger.error(f"🔍 [DEBUG-388] Strict isolation result: '{case_name}'")
                    logger.error(f"🔍 [DEBUG-388] Is valid: {is_valid_case_name(case_name) if case_name else False}")

                # FIX DEC 2025 v7: Always log strict isolation result for debugging N/A issues
                logger.error(
                    f"[STRICT-ISO-DEBUG] {citation.citation}: strict_iso='{case_name}', valid={is_valid_case_name(case_name) if case_name else False}"
                )

                # USER FIX 2024-10-16: Add fallback to master extractor when strict isolation fails
                if not case_name or not is_valid_case_name(case_name):
                    # Strict isolation failed - try master extractor as fallback
                    try:
                        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
                        import re as _re_pos

                        logger.error(
                            f"[CLEAN-PIPELINE-FALLBACK] Strict isolation failed for {citation.citation}, trying master extractor"
                        )

                        # FIX DEC 2025 v8: Find ACTUAL citation position in text
                        # eyecite often reports positions 200-300 chars off from actual PDF text positions
                        # This causes master extractor to look in wrong location for case name
                        actual_start = citation.start_index
                        actual_end = citation.end_index
                        try:
                            # Escape citation for regex and allow flexible whitespace
                            cit_pattern = _re_pos.escape(citation.citation).replace(r"\ ", r"\s+")
                            cit_match = _re_pos.search(cit_pattern, text)
                            if cit_match:
                                actual_start = cit_match.start()
                                actual_end = cit_match.end()
                                if actual_start != citation.start_index:
                                    logger.error(
                                        f"[FIX-v8] Position correction: eyecite={citation.start_index}, actual={actual_start}, diff={actual_start - citation.start_index}"
                                    )
                        except Exception as pos_err:
                            logger.warning(f"[FIX-v8] Position lookup failed: {pos_err}")

                        master_result = extract_case_name_and_date_unified_master(
                            text=text,
                            citation=citation.citation,
                            start_index=actual_start,
                            end_index=actual_end,
                            debug=False,
                        )

                        # USER FIX: Master returns dict, not object!
                        extracted_name = None
                        extracted_year = None
                        if master_result:
                            if isinstance(master_result, dict):
                                extracted_name = master_result.get("case_name")
                                extracted_year = master_result.get("year")
                            else:
                                extracted_name = getattr(master_result, "case_name", None)
                                extracted_year = getattr(master_result, "year", None)

                        # FIX DEC 2025 v7: Log master extractor result
                        logger.error(
                            f"[MASTER-FALLBACK-DEBUG] {citation.citation}: master_name='{extracted_name}', master_year='{extracted_year}'"
                        )

                        # SAFETY: Only accept master name if it is near this citation and in the same clause
                        def _accept_master_name(
                            doc_text: str, cit_start: int, name: str, target_citation_text: str
                        ) -> bool:
                            try:
                                if not doc_text or not name or cit_start is None:
                                    return False
                                # USER FIX v2: Further reduced from 150 to 80 chars to stop cascading contamination
                                search_window_start = max(0, cit_start - 80)
                                window = doc_text[search_window_start:cit_start]
                                # FIX DEC 2025 v6: Normalize whitespace for PDF text with newlines
                                import re as _re_norm

                                window_normalized = _re_norm.sub(r"\s+", " ", window).lower()
                                name_normalized = _re_norm.sub(r"\s+", " ", str(name)).lower()
                                pos = window_normalized.rfind(name_normalized)
                                if pos == -1:
                                    return False
                                abs_end = search_window_start + pos + len(name)
                                # Reject if there is a semicolon or 'see also' between name end and citation
                                between = doc_text[abs_end:cit_start]
                                if ";" in between:
                                    return False
                                import re as _re

                                if _re.search(r"\bsee\s+also\b", between, _re.IGNORECASE):
                                    return False

                                # Reporter-family guard: if text between contains a reporter token
                                # that belongs to a DIFFERENT family than the target citation, reject.
                                def _detect_family(s: str) -> str:
                                    s2 = s.lower()
                                    for token, fam in (
                                        ("f. 4th", "f4th"),
                                        ("f.4th", "f4th"),
                                        ("f. 3d", "f3d"),
                                        ("f.3d", "f3d"),
                                        ("f. 2d", "f2d"),
                                        ("f.2d", "f2d"),
                                        ("u.s.", "us"),
                                        ("s. ct.", "sct"),
                                        ("l. ed. 2d", "led2d"),
                                        ("a. 3d", "a3d"),
                                        ("a.3d", "a3d"),
                                        ("a. 2d", "a2d"),
                                        ("a.2d", "a2d"),
                                        ("a.", "a"),
                                        ("p. 3d", "p3d"),
                                        ("p.3d", "p3d"),
                                        ("p. 2d", "p2d"),
                                        ("p.2d", "p2d"),
                                        ("p.", "p"),
                                    ):
                                        if token in s2:
                                            return fam
                                    return ""

                                target_fam = _detect_family(str(target_citation_text or ""))
                                between_fam = _detect_family(between)
                                if between_fam and target_fam and between_fam != target_fam:
                                    return False
                                # Require close proximity
                                if (cit_start - abs_end) > 150:
                                    return False
                                return True
                            except Exception:
                                return False

                        if (
                            extracted_name
                            and extracted_name != "N/A"
                            and _accept_master_name(text, actual_start, extracted_name, citation.citation)
                        ):
                            case_name = extracted_name
                            logger.error(
                                f"[CLEAN-PIPELINE-FALLBACK] Master extractor accepted (nearby, same clause): '{case_name}'"
                            )
                        else:
                            logger.error(
                                f"[CLEAN-PIPELINE-FALLBACK] Master extractor name rejected due to distance/boundary: '{extracted_name}'"
                            )

                            # USER FIX 2024-10-16: Also use the year from master extractor
                            # Master extractor has the fixed year extraction (looks forward first)
                            if extracted_year and extracted_year != "N/A":
                                citation.extracted_date = extracted_year

                                # DEBUG: Track for problematic citations
                                if "388 P.3d 977" in citation.citation:
                                    logger.error(f"🔍 [DEBUG-388] Master extractor gave year: {extracted_year}")
                                    logger.error(f"🔍 [DEBUG-388] Set citation.extracted_date = {extracted_year}")
                    except Exception as fallback_error:
                        logger.warning(f"[CLEAN-PIPELINE-FALLBACK] Master extractor also failed: {fallback_error}")

                # NEW: Validate extracted case name
                if case_name and is_valid_case_name(case_name):
                    # CRITICAL: Check for document primary case name contamination
                    if self.document_primary_case_name and case_name:
                        # Normalize both for comparison
                        def normalize_for_comparison(name):
                            if not name:
                                return ""
                            normalized = name.lower()
                            # Remove "et al" and role words (Petitioners, Respondents, etc.) - these are document header artifacts
                            normalized = re.sub(r"\bet\s+al\.?\b", "", normalized)
                            normalized = re.sub(
                                r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?|defendants?)\b",
                                "",
                                normalized,
                            )
                            normalized = re.sub(r"\bno\.?\s*\d+", "", normalized)  # Remove docket numbers
                            # Normalize common variations
                            normalized = re.sub(r"\bllc\b", "llc", normalized)
                            normalized = re.sub(r"\bll\.?c\.?\b", "llc", normalized)
                            normalized = re.sub(r"\binc\.?\b", "inc", normalized)
                            normalized = re.sub(r"\bcorp\.?\b", "corp", normalized)
                            normalized = re.sub(r"\bco\.?\b", "co", normalized)
                            normalized = re.sub(r"[,\.\s]+", " ", normalized)
                            normalized = normalized.strip()
                            return normalized

                        extracted_normalized = normalize_for_comparison(case_name)
                        primary_normalized = normalize_for_comparison(self.document_primary_case_name)

                        # Reject if it matches the document's primary case name (bidirectional check)
                        if (
                            extracted_normalized == primary_normalized
                            or primary_normalized in extracted_normalized
                            or extracted_normalized in primary_normalized
                        ):
                            logger.error(
                                f"[CLEAN-PIPELINE-CONTAMINATION] ❌ REJECTING contaminated name '{case_name}' for citation '{citation.citation}' (matches document primary '{self.document_primary_case_name}')"
                            )
                            citation.extracted_case_name = "N/A"
                            fail_count += 1
                            continue  # Skip to next citation
                        else:
                            logger.debug(
                                f"[CLEAN-PIPELINE-CONTAMINATION] ✓ Keeping name '{case_name}' (does not match primary '{self.document_primary_case_name}')"
                            )

                    # CRITICAL: Remove signal phrases like "See, e.g.," from the extracted name
                    # These are citation signals, not part of the case name
                    original_name = case_name
                    signal_phrase_patterns = [
                        r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                        r"^See\s+also\s+",  # "See also"
                        r"^See\s+generally\s+",  # "See generally"
                        r"^But\s+see\s+",  # "But see"
                        r"^See\s+",  # "See " (standalone signal word)
                        r"^Accord\s+",  # "Accord "
                        r"^Compare\s+",  # "Compare "
                        r"^Cf\.?\s+",  # "Cf."
                        r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                        r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
                    ]
                    for pattern in signal_phrase_patterns:
                        case_name = re.sub(pattern, "", case_name, flags=re.IGNORECASE).strip()

                    if case_name != original_name:
                        logger.debug(f"[CLEAN-PIPELINE] Removed signal phrase: '{original_name}' → '{case_name}'")

                    citation.extracted_case_name = case_name
                    success_count += 1
                    logger.debug(f"[CLEAN-PIPELINE] Extracted: {citation.citation} → '{case_name}'")
                elif case_name:
                    # Extracted something but it's not valid - log it
                    citation.extracted_case_name = "N/A"
                    fail_count += 1
                    logger.warning(f"[CLEAN-PIPELINE] Invalid name rejected for {citation.citation}: '{case_name}'")
                else:
                    # No case name found - use improved fallback
                    citation.extracted_case_name = f"Unknown Case, {citation.citation}"
                    fail_count += 1
                    logger.warning(f"[CLEAN-PIPELINE] No name found for {citation.citation}, using Unknown Case fallback")

            except Exception as e:
                if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                    citation.extracted_case_name = f"Unknown Case, {citation.citation}"
                    fail_count += 1
                logger.error(f"[CLEAN-PIPELINE] Error extracting {citation.citation}: {e}")
            
            # Add to processed citations after handling
            processed_citations.append(citation)

        logger.info(
            f"[CLEAN-PIPELINE] Extraction complete: {success_count} with names ({skipped_count} from eyecite), {fail_count} failed"
        )

        # DEBUG: Log ALL citations with their extracted dates
        logger.error("=" * 80)
        logger.error("[DEBUG-ALL-DATES] Logging ALL citations with their extracted dates:")
        logger.error("=" * 80)
        for cit in citations:
            if "Hamaatsa" in str(cit.extracted_case_name):
                logger.error(
                    f"🔴 [HAMAATSA] {cit.citation} → Name: {cit.extracted_case_name} → Date: {cit.extracted_date}"
                )
            elif cit.citation:
                logger.error(f"[ALL-DATES] {cit.citation[:30]:30} → Date: {cit.extracted_date}")

    def _extract_all_dates(self, text: str, citations: List[CitationResult]) -> None:
        """Extract dates for citations that don't already have them from eyecite or master extractor."""
        for citation in citations:
            try:
                # Skip if eyecite or master extractor already provided a date
                # USER FIX 2024-10-16: Don't overwrite dates from master extractor fallback
                # EXCEPTION: Re-extract if the date seems incorrect (e.g., 2023 for a case that should be from 1876)
                should_re_extract = False
                if citation.extracted_date and citation.extracted_date != "N/A":
                    # Check if this is a known problematic case with incorrect date
                    if "94 U.S. 469" in citation.citation and citation.extracted_date == "2023":
                        logger.error(
                            f"🔍 [DEBUG-KELLOGG] RE-EXTRACTING date - current '{citation.extracted_date}' seems incorrect for 1876 case"
                        )
                        should_re_extract = True

                    if not should_re_extract:
                        logger.debug(
                            f"[CLEAN-PIPELINE] Skipping date extraction for {citation.citation} - already has: {citation.extracted_date}"
                        )

                        # DEBUG: Track for problematic citations
                        if "388 P.3d 977" in citation.citation:
                            logger.error(
                                f"🔍 [DEBUG-388] SKIPPING _extract_all_dates - already has: {citation.extracted_date}"
                            )
                        continue

                # DEBUG: Track for problematic citations
                if "388 P.3d 977" in citation.citation:
                    logger.error(f"🔍 [DEBUG-388] RUNNING _extract_all_dates - no date set yet")

                if citation.start_index is not None and citation.end_index is not None:
                    # Search context around citation - USE SMALLER WINDOW TO PREVENT CROSS-CONTAMINATION
                    search_start = max(0, citation.start_index - 50)  # Reduced from 100
                    search_end = min(len(text), citation.end_index + 100)  # Reduced from 300
                    before_context = text[search_start : citation.start_index]
                    after_context = text[citation.end_index : search_end]
                    before_context + citation.citation + after_context

                    # DEBUG: Log search window for cross-contamination debugging
                    logger.debug(
                        f"[CLEAN-PIPELINE] Citation '{citation.citation}' search window: {search_start}-{search_end}"
                    )
                    logger.debug(f"[CLEAN-PIPELINE] Before context: '{before_context}'")
                    logger.debug(f"[CLEAN-PIPELINE] After context: '{after_context}'")

                    year_found = None

                    # Strategy 1: Look for (YYYY) immediately after citation - HIGHEST PRIORITY
                    # This is the most reliable pattern: "123 F.3d 456 (2010)"
                    immediate_after = after_context[:50]  # Only look 50 chars after citation
                    
                    # CRITICAL FIX: Remove "Cite as:" header patterns BEFORE searching for years
                    cite_as_pattern = r"Cite\s+as:?\s*[^\n]*(?:\([^)]*\d{4}[^)]*\)|____\s*\(\d{4}\)|\(\d{4}\))[^\n]*"
                    immediate_after = re.sub(cite_as_pattern, "", immediate_after, flags=re.IGNORECASE)
                    
                    year_match = re.search(r"\((\d{4})\)", immediate_after)
                    if year_match:
                        year = year_match.group(1)
                        year_int = int(year)
                        
                        # CRITICAL FIX: Check if this year is part of a "Cite as:" header in broader context
                        broader_context = text[max(0, citation.start_index - 200):min(len(text), citation.end_index + 200)]
                        cite_as_check = re.search(
                            rf"Cite\s+as:?\s*[^\n]*{re.escape(year)}[^\n]*",
                            broader_context,
                            re.IGNORECASE
                        )
                        if cite_as_check:
                            logger.warning(
                                f"[CLEAN-PIPELINE] Rejected year {year} for {citation.citation} - appears in 'Cite as:' header. "
                                f"Context: '{broader_context[max(0, cite_as_check.start()-50):cite_as_check.end()+50]}'"
                            )
                        # CRITICAL FIX: Reject years 2015+ for U.S. Reports volumes 400-600 (cases from 1970s-2000s)
                        # These are almost certainly from headers, not the actual case dates
                        elif " U.S. " in citation.citation:
                            volume_match = re.search(r"(\d+)\s+U\.\s*S\.", citation.citation)
                            if volume_match:
                                volume = int(volume_match.group(1))
                                # U.S. Reports volumes 400-600 are from 1970s-2000s
                                if 400 <= volume <= 600 and year_int >= 2015:
                                    logger.warning(
                                        f"[CLEAN-PIPELINE] Rejected year {year} for {citation.citation} (U.S. volume {volume}) - "
                                        f"year 2015+ is likely from header, not case date"
                                    )
                                elif 1800 <= year_int <= 2030:
                                    year_found = year
                                    logger.debug(f"[CLEAN-PIPELINE] Found (YYYY) immediately after: {year_found}")
                            elif 1800 <= year_int <= 2030:
                                year_found = year
                                logger.debug(f"[CLEAN-PIPELINE] Found (YYYY) immediately after: {year_found}")
                        # CRITICAL FIX: Reject years 2015+ for F.3d volumes 800-900 (cases from 2010s, but 2020+ is suspicious)
                        elif " F.3d " in citation.citation:
                            volume_match = re.search(r"(\d+)\s+F\.\s*3d", citation.citation)
                            if volume_match:
                                volume = int(volume_match.group(1))
                                # F.3d volumes 800-900 are from 2010s, but 2020+ is suspicious for older volumes
                                if 800 <= volume <= 900 and year_int >= 2020:
                                    logger.warning(
                                        f"[CLEAN-PIPELINE] Rejected year {year} for {citation.citation} (F.3d volume {volume}) - "
                                        f"year 2020+ is likely from header, not case date"
                                    )
                                elif 1800 <= year_int <= 2030:
                                    year_found = year
                                    logger.debug(f"[CLEAN-PIPELINE] Found (YYYY) immediately after: {year_found}")
                            elif 1800 <= year_int <= 2030:
                                year_found = year
                                logger.debug(f"[CLEAN-PIPELINE] Found (YYYY) immediately after: {year_found}")
                        elif 1800 <= year_int <= 2030:  # Expanded range to include 1876
                            year_found = year
                            logger.debug(f"[CLEAN-PIPELINE] Found (YYYY) immediately after: {year_found}")
                        else:
                            logger.warning(
                                f"[CLEAN-PIPELINE] Rejected year {year} for {citation.citation} - outside valid range (1800-2030)"
                            )

                    # Strategy 2: Look for year in citation itself (e.g., "123 F.3d 456, 2010")
                    if not year_found:
                        citation_year_match = re.search(r",\s*(\d{4})", citation.citation)
                        if citation_year_match:
                            year = citation_year_match.group(1)
                            if 1800 <= int(year) <= 2030:  # Expanded range
                                year_found = year
                                logger.debug(f"[CLEAN-PIPELINE] Found year in citation: {year_found}")

                    # Strategy 3: Look for standalone 4-digit year in immediate context
                    # CRITICAL FIX: Filter out years from document headers (e.g., "JUNE 12, 2025", "FILED: 2025")
                    if not year_found:
                        # Look in immediate context (within 30 chars after citation)
                        year_match = re.search(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", immediate_after[:30])
                        if year_match:
                            year = year_match.group(1)
                            year_start = year_match.start()
                            year_end = year_match.end()

                            # Extract context around the year to check if it's in a header pattern
                            context_start = max(0, year_start - 20)
                            context_end = min(len(immediate_after), year_end + 20)
                            year_context = immediate_after[context_start:context_end]

                            # Check if year appears in header-like patterns
                            header_patterns = [
                                r"Cite\s+as:?\s*[^\n]*(?:\([^)]*\d{4}[^)]*\)|____\s*\(\d{4}\)|\(\d{4}\))",  # "Cite as: 594 U. S. ____ (2021)"
                                r"[A-Z]{3,}\s+\d{1,2},\s*\d{4}",  # "JUNE 12, 2025"
                                r"FILED[:\s]+\d{4}",  # "FILED: 2025" or "FILED 2025"
                                r"^\s*[A-Z\s,\.\-]{10,}\s*\d{4}",  # All-caps text followed by year
                                r"CLERK.*\d{4}",  # "CLERK'S OFFICE...2025"
                                r"SUPREME COURT.*\d{4}",  # "SUPREME COURT...2025"
                            ]

                            is_header_year = False
                            for pattern in header_patterns:
                                if re.search(pattern, year_context, re.IGNORECASE):
                                    is_header_year = True
                                    logger.debug(
                                        f"[CLEAN-PIPELINE] Rejected year {year} - appears in header pattern: '{year_context[:50]}'"
                                    )
                                    break

                            # Also check if the context is all-caps (likely a header)
                            if not is_header_year and year_context.strip().isupper() and len(year_context.strip()) > 10:
                                is_header_year = True
                                logger.debug(
                                    f"[CLEAN-PIPELINE] Rejected year {year} - context is all-caps header: '{year_context[:50]}'"
                                )

                            if not is_header_year:
                                year_found = year
                                logger.debug(
                                    f"[CLEAN-PIPELINE] Found standalone year in immediate context: {year_found}"
                                )
                            else:
                                logger.debug(f"[CLEAN-PIPELINE] Filtered out header year: {year}")

                    # Strategy 4: Extract from case name if it contains year
                    # E.g., "Smith (2010)" in the extracted case name
                    if not year_found and citation.extracted_case_name:
                        year_match = re.search(r"\((\d{4})\)", citation.extracted_case_name)
                        if year_match:
                            year = year_match.group(1)
                            if 1800 <= int(year) <= 2030:  # Expanded range
                                year_found = year
                                logger.debug(f"[CLEAN-PIPELINE] Found year in case name: {year_found}")

                    citation.extracted_date = year_found
                    
                    # DEBUG: Log for Davis and Braitberg to trace date extraction
                    if "554 U.S. 724" in citation.citation or "836 F.3d 925" in citation.citation:
                        logger.warning(
                            f"🔍 [DATE-DEBUG] Citation: {citation.citation}"
                        )
                        logger.warning(
                            f"🔍 [DATE-DEBUG] Final extracted_date: {year_found}"
                        )
                        logger.warning(
                            f"🔍 [DATE-DEBUG] Immediate after context: '{immediate_after}'"
                        )
                        logger.warning(
                            f"🔍 [DATE-DEBUG] Broader context (200 chars): '{text[max(0, citation.start_index - 200):min(len(text), citation.end_index + 200)]}'"
                        )
                    
                    if not year_found:
                        logger.debug(f"[CLEAN-PIPELINE] No year found for {citation.citation}")

                    # DEBUG: Track for problematic citations
                    if "94 U.S. 469" in citation.citation:
                        logger.error(f"🔍 [DEBUG-KELLOGG] _extract_all_dates FOUND year: {year_found}")
                        logger.error(f"🔍 [DEBUG-KELLOGG] Set citation.extracted_date = {year_found}")
                        logger.error(f"🔍 [DEBUG-KELLOGG] Context searched: '{immediate_after[:50]}'")
                else:
                    citation.extracted_date = None

            except Exception as e:
                logger.debug(f"[CLEAN-PIPELINE] Error extracting date for {citation.citation}: {e}")
                citation.extracted_date = None


def extract_citations_clean(text: str, document_primary_case_name: Optional[str] = None) -> List[CitationResult]:
    """
    Main entry point for clean citation extraction.
    
    DEPRECATED: This function is deprecated. Use extract_citations_unified from unified_case_extraction_master.py instead.
    
    This function now delegates to the unified extraction master to reduce code duplication.
    
    Args:
        text: Document text
        document_primary_case_name: Optional document primary case name for contamination filtering
        
    Returns:
        List of CitationResult objects with extracted_case_name set using strict context isolation
    """
    import warnings
    warnings.warn(
        "extract_citations_clean is deprecated. Use extract_citations_unified from unified_case_extraction_master.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    print(f"extract_citations_clean CALLED with {len(text)} chars [DEPRECATED]")
    
    # Use the new unified function
    from src.unified_case_extraction_master import extract_citations_unified
    
    citations = extract_citations_unified(text, document_primary_case_name)
    
    # Add proprietary format marking for WL citations
    import re
    proprietary_count = 0
    for cit in citations:
        if not cit.verified:
            if re.search(r"\d{4}\s+WL\s+\d+", cit.citation) or re.search(r"Lexis\s+\d+", cit.citation, re.IGNORECASE):
                cit.verification_status = "proprietary_format"
                cit.verification_error = "Unverified due to proprietary format"
                proprietary_count += 1
    
    if proprietary_count > 0:
        logger.info(f"[PROPRIETARY] Marked {proprietary_count} WL/Lexis citations as unverified due to proprietary format")
    
    # Validate position data preservation
    missing_position_count = 0
    for i, cit in enumerate(citations):
        if cit.start_index is None or cit.end_index is None:
            missing_position_count += 1
            logger.warning(f"[CLEAN-PIPELINE] Missing position data for citation {i+1}: {cit.citation}")
    
    if missing_position_count > 0:
        logger.error(
            f"[CLEAN-PIPELINE] {missing_position_count} citations missing position data - parallel verification may fail"
        )
    else:
        logger.info(f"[CLEAN-PIPELINE] All {len(citations)} citations have valid position data")
    
    print(f"extract_citations_clean returning {len(citations)} citations (position data: {len(citations) - missing_position_count}/{len(citations)} valid) [DEPRECATED]")
    return citations


__all__ = ["CleanExtractionPipeline", "extract_citations_clean"]
