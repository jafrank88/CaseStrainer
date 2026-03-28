"""
Strict Context Isolator - Prevents case name bleeding between citations.

CRITICAL PROBLEM SOLVED:
When multiple citations appear close together like:
"P.R. Aqueduct v. Met, 506 U.S. 139 ... Will v. Hallock, 546 U.S. 345"

The extractor was picking up "Will v. Hallock" for "506 U.S. 139" instead of
"P.R. Aqueduct v. Met" because it wasn't properly isolating the context.

SOLUTION:
This module provides strict context boundaries by:
1. Finding ALL citations in the document
2. For each citation, isolating ONLY the text immediately before it
3. Stopping at the nearest previous citation boundary
4. Extracting case name ONLY from that isolated context
"""

import re
import html
import logging
from typing import List, Tuple, Optional, Dict, Any
from src.citation_patterns import CitationPatterns  # CONSOLIDATED: Import shared patterns

logger = logging.getLogger(__name__)


def _filter_headers_and_footnotes_from_context(context: str) -> str:
    """
    Filter out document headers, footers, and footnotes from context to allow case names
    split across headers/footnotes to be found.

    This handles cases like:
    "Singh
    4 Federal courts...
    Erickson v. Pharmacia, No. 103135-1
    24
    v. Edwards Lifesciences Corp., 151 Wn. App. 137"

    Where "Singh v. Edwards Lifesciences Corp." is split by a header and footnote.

    Also handles footers that appear at the bottom of pages, which often contain:
    - Repeated case names (e.g., "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO")
    - Page numbers
    - Docket numbers

    Args:
        context: Context text that may contain headers/footers/footnotes

    Returns:
        Context with headers, footers, and footnotes removed
    """
    if not context:
        return context

    # CRITICAL FIX: Remove header patterns from the entire context BEFORE line-by-line processing
    # This catches headers that span multiple lines or are embedded in text
    # ENHANCED: More aggressive pattern removal to catch all header variations
    header_patterns_to_remove = [
        # CRITICAL: Remove "Cite as:" headers that contain dates (can contaminate date extraction)
        # Pattern: "Cite as: 594 U. S. ____ (2021)" or "Cite as: 594 U.S. ____ (2021)"
        r"Cite\s+as:?\s*[^\n]*(?:\([^)]*\d{4}[^)]*\)|____\s*\(\d{4}\)|\(\d{4}\))[^\n]*",
        # Pattern: "Cite as:" with citation format (even without explicit date, still a header)
        r"Cite\s+as:?\s*[^\n]*(?:U\.?\s*S\.|F\.|P\.|S\.\s*Ct\.|L\.\s*Ed\.)[^\n]*",
        # Pattern: "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO" (exact match)
        r"ERICKSON\s+ET\s+AL\.?\s*,?\s*Petitioners?[^,]*v\.\s+PHARMACIA[^,]*Respondent\.?\s*NO\.?",
        # Pattern: "ET AL., Petitioners, v. ... Respondent. NO" (full header format)
        r"[A-Z\s]*ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+[^,]+(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?",
        # Pattern: "ET AL., Petitioners" anywhere (simpler pattern)
        r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b[^,]*v\.\s+[^,]+(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?",
        # Pattern: Case name with "Respondent. NO" or "Petitioners, NO"
        r"[A-Z][A-Z\s]{15,}v\.\s+[A-Z][A-Z\s]{10,}(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?",
        # Pattern: Any text containing "ET AL" followed by role word (catch-all for headers)
        r"[^,]*ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)[^,]*",
    ]

    for pattern in header_patterns_to_remove:
        context = re.sub(pattern, "", context, flags=re.IGNORECASE | re.DOTALL)

    # ENHANCED: Additional aggressive header removal patterns
    additional_header_patterns = [
        # Pattern for headers with "ET AL" and role word anywhere (more flexible)
        r"[^.]*ET\s+AL\.?\s*[^.]*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)[^.]*",
        # Pattern: Role word followed by "NO" (common header format)
        r"[^.]*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*\d*[^.]*",
        # Pattern: Document caption with federal docket (e.g. "Ill. Union Ins. Co. No. C10-5943 RJB Milgard Mfg., Inc. v. Ill")
        # Prevents context bleed when WL citation appears under a different case's caption.
        # EXCEPTION: Do NOT remove if match contains WL or reporter citation - real citation line
        r"[^.]*(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+[^.]*",
    ]
    _citation_in_context = re.compile(
        r"\d{4}\s+WL\s+\d+|\d+\s+(?:F\.?3d|F\.?2d|U\.S\.|P\.?3d|N\.E\.2d|S\.E\.2d|S\.W\.2d|Wn\.2d|Cal\.)\s+\d+",
        re.IGNORECASE,
    )

    for i, pattern in enumerate(additional_header_patterns):
        # Third pattern (index 2): docket caption - only remove if match has no WL/reporter citation
        if i == 2:
            # Docket caption pattern: only remove if match does NOT contain a citation
            def _replacer(m):
                if _citation_in_context.search(m.group(0)):
                    return m.group(0)  # Keep - real citation line
                return ""

            context = re.sub(pattern, _replacer, context, flags=re.IGNORECASE | re.DOTALL)
        else:
            context = re.sub(pattern, "", context, flags=re.IGNORECASE | re.DOTALL)

    lines = context.split("\n")
    filtered_lines = []

    for line in lines:
        line_stripped = line.strip()

        # Skip lines that are clearly document headers
        # Pattern: "Case Name v. Defendant, No. 12345-1" (with docket number)
        if re.search(r"\bNo\.?\s*\d+[-\.]\d+", line_stripped, re.IGNORECASE):
            # Check if it's a header format (all caps or has role words)
            if (line_stripped.isupper() and len(line_stripped) > 20) or re.search(
                r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b", line_stripped, re.IGNORECASE
            ):
                logger.debug(f"[HEADER-FILTER] Filtering header line: '{line_stripped[:50]}...'")
                continue

        # Skip lines containing header patterns
        if re.search(
            r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",
            line_stripped,
            re.IGNORECASE,
        ):
            logger.debug(f"[HEADER-FILTER] Filtering line with ET AL pattern: '{line_stripped[:50]}...'")
            continue

        if re.search(
            r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\b",
            line_stripped,
            re.IGNORECASE,
        ):
            logger.debug(f"[HEADER-FILTER] Filtering line with Respondent. NO pattern: '{line_stripped[:50]}...'")
            continue

        # Skip lines with federal docket caption (e.g. "Ill. Union Ins. Co. No. C10-5943 RJB Milgard Mfg., Inc. v. Ill")
        # Prevents context bleed when citation appears under a different case's caption.
        # EXCEPTION: Do NOT filter if line contains a WL or reporter citation - those are real citation
        # lines (e.g. "Milgard Mfg., Inc. v. Ill. Union Ins. Co., No. C10-5943 RJB, 2011 WL 3298912, at *3")
        # not document headers.
        if re.search(
            r"(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+",
            line_stripped,
            re.IGNORECASE,
        ):
            has_citation_in_line = bool(
                re.search(r"\d{4}\s+WL\s+\d+", line_stripped)  # 2011 WL 3298912
                or re.search(
                    r"\d+\s+(?:F\.?3d|F\.?2d|U\.S\.|P\.?3d|N\.E\.2d|S\.E\.2d|S\.W\.2d|Wn\.2d|Cal\.)\s+\d+",
                    line_stripped,
                    re.IGNORECASE,
                )
            )
            if not has_citation_in_line:
                logger.debug(f"[HEADER-FILTER] Filtering docket caption line: '{line_stripped[:60]}...'")
                continue

        # Skip lines that are clearly footnotes (standalone numbers or short numeric lines)
        # Pattern: "24" or "4" (standalone numbers, often footnotes)
        if re.match(r"^\d{1,3}$", line_stripped):
            # Only skip if it's a short line (likely a footnote marker)
            if len(line_stripped) <= 3:
                logger.debug(f"[FOOTNOTE-FILTER] Filtering footnote line: '{line_stripped}'")
                continue

        # CRITICAL: Filter document footers (often appear at end of context or end of lines)
        # Footers typically contain:
        # - Case names repeated (same patterns as headers)
        # - Page numbers (e.g., "Page 24" or just "24")
        # - Docket numbers
        # - Often in all caps or have similar formatting to headers

        # Check if line looks like a footer (case name with role words, often at end)
        # Pattern: Case name ending with role word and NO (common footer format)
        if re.search(
            r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*$",
            line_stripped,
            re.IGNORECASE,
        ):
            # If it's all caps or has header patterns, it's likely a footer
            if line_stripped.isupper() or re.search(r"ET\s+AL", line_stripped, re.IGNORECASE):
                logger.debug(f"[FOOTER-FILTER] Filtering footer line: '{line_stripped[:50]}...'")
                continue

        # Pattern: Footer with page number (e.g., "Case Name v. Defendant - Page 24" or "Case Name - 24")
        if re.search(r"[Pp]age\s+\d+", line_stripped) or re.search(r"^\d+\s*$", line_stripped):
            # If line also contains case name patterns or is very short, likely a footer
            if len(line_stripped) < 50 or re.search(r"\bv\.\s+", line_stripped, re.IGNORECASE):
                # Check if it has header patterns (role words, ET AL, etc.)
                if re.search(
                    r"ET\s+AL|(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO",
                    line_stripped,
                    re.IGNORECASE,
                ):
                    logger.debug(f"[FOOTER-FILTER] Filtering footer with page number: '{line_stripped[:50]}...'")
                    continue

        # Pattern: All-caps lines at end of context that look like footers
        # (Footers are often the last few lines and are all caps)
        if line_stripped.isupper() and len(line_stripped) > 15:
            # Check if it contains header/footer patterns
            if re.search(
                r"ET\s+AL|(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO|No\.\s*\d+",
                line_stripped,
                re.IGNORECASE,
            ):
                # If it's near the end of context (last 3 lines), likely a footer
                line_index = len(filtered_lines)
                total_lines = len(lines)
                if line_index >= total_lines - 3:
                    logger.debug(
                        f"[FOOTER-FILTER] Filtering all-caps footer line (near end): '{line_stripped[:50]}...'"
                    )
                    continue

        # Keep the line
        filtered_lines.append(line)

    filtered_context = "\n".join(filtered_lines)

    # Normalize whitespace (replace newlines with spaces to reconnect split case names)
    filtered_context = re.sub(r"\s+", " ", filtered_context).strip()

    return filtered_context


def _expand_abbreviations(case_name: str) -> str:
    """
    Expand common legal abbreviations to improve accuracy.

    Examples:
    "Dep't of Ecology" -> "Department of Ecology"
    "Lakeside Indus." -> "Lakeside Industries"
    "Bd. of Regents" -> "Board of Regents"
    """
    # Common abbreviation mappings
    abbreviations = {
        "Dep't": "Department",
        "Dept": "Department",
        "Indus.": "Industries",
        "Indus": "Industries",
        "Co": "Company",
        "Corp": "Corporation",
        "Ltd": "Limited",
        "Bd.": "Board",
        "Bd": "Board",
        "Colls": "Colleges",
        "Dev": "Development",
        "Corr": "Corrections",
        "Ass'n": "Association",
        "Comm": "Commission",
        "Div": "Division",
        "Dist": "District",
        "Mfrs": "Manufacturers",
        "Natl": "National",
        "Am": "American",
        "Fed": "Federal",
        "Intl": "International",
        "Univ": "University",
        "Sch": "School",
        "Hosp": "Hospital",
        "Med": "Medical",
        "Elec": "Electric",
        "Tel": "Telephone",
        "Gas": "Gas",
        "Power": "Power",
        "Water": "Water",
        "Sewer": "Sewer",
        "Util": "Utilities",
    }

    # Apply abbreviations (case-sensitive)
    for abbrev, full in abbreviations.items():
        if "." in abbrev:
            # For abbreviations with periods, don't use word boundaries
            # as periods break word boundaries
            pattern = r"(?<!\w)" + re.escape(abbrev) + r"(?!\w)"
            case_name = re.sub(pattern, full, case_name)
        else:
            # For regular abbreviations, use word boundaries
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            case_name = re.sub(pattern, full, case_name)

    return case_name


def _add_missing_words(case_name: str, context: str) -> str:
    """
    Add missing common words based on context analysis.

    Examples:
    "Rozner v. Bellevue" -> "Rozner v. City of Bellevue" (if "City of Bellevue" appears in context)
    """
    # Check for missing "City of" before city names
    cities = [
        "Bellevue",
        "Seattle",
        "Spokane",
        "Tacoma",
        "Vancouver",
        "Portland",
        "Snohomish",
        "King",
        "Pierce",
        "Thurston",
    ]

    for city in cities:
        # Check if case name has city but missing "City of"
        if city in case_name and "City of" not in case_name:
            # More flexible context checking - look for "City of" + city in broader context
            broader_context = context[-500:]  # Increase context window
            if f"City of {city}" in broader_context:
                # Add "City of" before the city name (only in defendant part)
                if f"v. {city}" in case_name:
                    case_name = case_name.replace(f"v. {city}", f"v. City of {city}")
                    logger.debug(f"[ACCURACY] Added missing 'City of' for {city}")
                elif case_name.endswith(f" {city}"):
                    case_name = case_name.replace(f" {city}", f" City of {city}")
                    logger.debug(f"[ACCURACY] Added missing 'City of' for {city}")

    # Check for missing "County" after county names
    counties = ["Snohomish", "King", "Pierce", "Thurston", "Jefferson", "Kitsap"]

    for county in counties:
        if county in case_name and "County" not in case_name:
            broader_context = context[-500:]
            if f"{county} County" in broader_context:
                # Add "County" after the county name
                if f"v. {county}" in case_name:
                    case_name = case_name.replace(f"v. {county}", f"v. {county} County")
                    logger.debug(f"[ACCURACY] Added missing 'County' for {county}")
                elif case_name.endswith(f" {county}"):
                    case_name = case_name.replace(f" {county}", f" {county} County")
                    logger.debug(f"[ACCURACY] Added missing 'County' for {county}")

    return case_name


def _fix_formatting_issues(case_name: str) -> str:
    """
    Fix common formatting issues in case names.
    """
    # Fix spacing around "v."
    case_name = re.sub(r"\s+v\.\s+", " v. ", case_name)

    # Fix multiple spaces
    case_name = re.sub(r"\s+", " ", case_name).strip()

    # Fix punctuation spacing
    case_name = re.sub(r"\s*,\s*", ", ", case_name)
    case_name = re.sub(r"\s*&\s*", " & ", case_name)

    # Ensure proper LLC formatting
    case_name = re.sub(r"\bLLC\b", "LLC", case_name)

    # Ensure proper Inc formatting
    case_name = re.sub(r"\bInc\b", "Inc.", case_name)

    return case_name


def find_all_citation_positions(text: str) -> List[Tuple[int, int, str]]:
    """
    Find all citation positions in the text.

    IMPORTANT: Now uses shared citation patterns from citation_patterns.py

    Returns:
        List of (start_pos, end_pos, citation_text) tuples
    """
    citations = []

    # CONSOLIDATED: Use shared patterns instead of local definitions
    compiled_patterns = CitationPatterns.get_compiled_patterns()

    # Use subset of patterns relevant for boundary detection
    boundary_patterns = [
        compiled_patterns["us_supreme"],
        compiled_patterns["s_ct"],
        compiled_patterns["l_ed_2d"],
        compiled_patterns["f_2d"],
        compiled_patterns["f_3d"],
        compiled_patterns["f_4th"],
        compiled_patterns["f_supp_2d"],
        # Atlantic reporters (NJ, PA, etc.)
        compiled_patterns["a_general"],
        compiled_patterns["a_2d"],
        compiled_patterns["a_3d"],
        compiled_patterns["p_2d"],
        compiled_patterns["p_3d"],
        compiled_patterns["wn_2d"],
        compiled_patterns["wash_2d"],
        compiled_patterns["wn_app"],
        compiled_patterns["cal_2d"],
        compiled_patterns["cal_3d"],
        compiled_patterns["cal_4th"],
        # State reporters - Virginia (e.g. "259 Va. 568") and Tennessee (e.g. "10 Tenn. 581")
        # Needed so "Larimore v. Blaylock, 259 Va. 568; but see Swindle v. State, 10 Tenn. 581" gets correct boundary
        compiled_patterns["va_general"],
        compiled_patterns["va_2d"],
        compiled_patterns["va_3d"],
        compiled_patterns["tn_general"],
        compiled_patterns["tn_app_general"],
        # Neutral citations
        compiled_patterns["neutral_nm"],
        compiled_patterns["neutral_nd"],
        compiled_patterns["neutral_ok"],
        compiled_patterns["neutral_sd"],
        compiled_patterns["neutral_ut"],
        compiled_patterns["neutral_wi"],
        compiled_patterns["neutral_wy"],
        compiled_patterns["neutral_mt"],
    ]

    for pattern in boundary_patterns:
        for match in pattern.finditer(text):
            citations.append((match.start(), match.end(), match.group(0)))

    # Sort by position
    citations.sort(key=lambda x: x[0])

    # Deduplicate overlapping citations
    deduped = []
    last_end = -1
    for start, end, cit_text in citations:
        if start >= last_end:
            deduped.append((start, end, cit_text))
            last_end = end

    logger.debug(f"[STRICT-CONTEXT] Found {len(deduped)} citation positions")
    return deduped


def get_adaptive_context_for_citation(
    text: str,
    citation_start: int,
    citation_end: int,
    all_citation_positions: List[Tuple[int, int, str]],
    max_lookback: int = 150,  # USER FIX: Allow larger max but start small
) -> str:
    """
    USER FIX: Work BACKWARDS from citation start with EXPANDING window.

    This function:
    1. Starts with a TINY window (25 chars) immediately before citation
    2. Looks for case name that ENDS near the citation start
    3. If N/A, expands window progressively (25 -> 50 -> 75 -> 100 -> max)
    4. Always prefers the case name CLOSEST to the citation

    Args:
        text: Full document text
        citation_start: Start position of the target citation
        citation_end: End position of the target citation
        all_citation_positions: List of all citation positions in the document
        max_lookback: Maximum characters to look back from the citation

    Returns:
        Adaptive context string containing a case name
    """
    logger.debug(f"[BACKWARDS-EXTRACT] Starting backwards extraction for citation at {citation_start}")
    
    # SERIES CITATION FIX: Check if this is NOT the first citation in a series
    # If it's not the first, don't extract case name to prevent incorrect association
    # But only for clear series citations, not all nearby citations
    #
    # CRITICAL FIX 2026-01-29: Don't return empty if there's a case name AFTER the semicolon!
    # Example: "; but see Swindle v. State, 10 Tenn. 581" - should extract "Swindle v. State"
    if citation_start and citation_start > 0:
        # Look backwards to see if there's another citation within 100 characters
        look_behind = text[max(0, citation_start - 100):citation_start]
        prev_citation_pattern = r'\d{4}\s+WL\s+\d+|\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+|\d+\s+U\.?\s*S\.?\s+\d+'

        # Only treat as series if there are clear indicators
        is_series_citation = False

        # Check for semicolon (clear series indicator)
        if ';' in look_behind:
            # CRITICAL FIX: Check if there's a case name ("v.") AFTER the last semicolon
            # If so, this citation HAS its own case name and we should extract it
            last_semicolon_pos = look_behind.rfind(';')
            text_after_semicolon = look_behind[last_semicolon_pos + 1:]

            # Check for "v." pattern (indicates a case name) after the semicolon
            if re.search(r'\bv\.\s', text_after_semicolon, re.IGNORECASE):
                # There's a case name after the semicolon - DON'T skip extraction
                logger.info(f"[SERIES-DEBUG] Semicolon detected but case name found after it: '{text_after_semicolon.strip()[:50]}...'")
                is_series_citation = False
            else:
                # No case name after semicolon - this is truly a series citation
                is_series_citation = True
                logger.info(f"[SERIES-DEBUG] Semicolon detected, no case name after - treating as series citation")

        # Check if citations are comma-separated without periods between them
        elif re.search(prev_citation_pattern, look_behind):
            # Check if there's no period between the citations
            last_period = look_behind.rfind('.')
            last_citation = re.search(prev_citation_pattern, look_behind)
            if last_citation and (last_period < 0 or last_period < last_citation.start()):
                # ALSO check for "v." pattern - if present, don't treat as series
                if re.search(r'\bv\.\s', look_behind[last_citation.end():], re.IGNORECASE):
                    logger.info(f"[SERIES-DEBUG] Comma-separated but case name found after citation")
                    is_series_citation = False
                else:
                    is_series_citation = True
                    logger.info(f"[SERIES-DEBUG] Comma-separated citations without period - treating as series")

        if is_series_citation and re.search(prev_citation_pattern, look_behind):
            # This is NOT the first citation in a series
            # Return empty context to prevent case name extraction
            logger.debug(f"[SERIES-FIX-ISOLATOR] Skipping case name extraction for non-first citation at position {citation_start}")
            return ""

    # USER FIX: Progressive window sizes - start small and expand only if needed
    # This ensures we get the CLOSEST case name to the citation first
    # FIX DEC 2025 v10: Increased initial windows to capture longer corporate names
    # like "Fisher Broad.-Seattle TV LLC v. City of Seattle" (56 chars)
    # FIX JAN 2026: Further increased to handle very long case names like
    # "New York Civil Liberties Union v. New York City Transit Authority" (77 chars)
    window_sizes = [100, 150, 200, 250, max_lookback]

    for window_size in window_sizes:
        # Get context with current window size
        context = get_strict_context_for_citation(
            text, citation_start, citation_end, all_citation_positions, window_size
        )

        logger.debug(f"[BACKWARDS-EXTRACT] Window {window_size}: context='{context[-60:] if context else 'EMPTY'}'")

        # Check if this context contains a case name
        if _contains_case_name(context):
            logger.debug(f"[BACKWARDS-EXTRACT] Found case name in {window_size} char window")
            return context
        else:
            logger.debug(f"[BACKWARDS-EXTRACT] No case name in {window_size} char window, expanding...")

    # If no case name found in any window, return the largest context
    # The caller will handle the N/A case and use canonical fallback
    logger.debug(f"[BACKWARDS-EXTRACT] No case name found after all expansions, returning max context")
    return get_strict_context_for_citation(text, citation_start, citation_end, all_citation_positions, max_lookback)


def _contains_case_name(context: str) -> bool:
    """
    Check if context contains a valid case name pattern.

    Args:
        context: Text context to check

    Returns:
        True if context contains a case name pattern
    """
    if not context or len(context.strip()) < 10:
        return False

    # Common case name patterns (allow spaces in party names for "X v. Y")
    case_patterns = [
        r"\b[A-Z][a-zA-Z\'\.\&\-\s]*\s+v\.?\s+[A-Z][a-zA-Z\'\.\&\-\s]*",  # X v. Y (e.g. Association of Data Processing... v. Camp)
        r"\bIn\s+re\s+[A-Z][a-zA-Z\'\.\&]*",  # In re X
        r"\bState(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*)?\s+v\.?\s+[A-Z][a-zA-Z\'\.\&]*",  # State v. Y
        r"\bCity\s+of\s+[A-Z][a-zA-Z\'\.\&]*\s+v\.?\s+[A-Z][a-zA-Z\'\.\&]*",  # City of X v. Y
    ]

    context_lower = context.lower()

    # Skip if context looks like it's from a different citation (id./supra only for "see")
    # Do NOT skip just because "see" appears: "See Association of Data Processing... v. Camp"
    # is a valid case name and must be recognized so we use the right window.
    skip_patterns = [
        r"\b\d+\s+[a-z\.]+\s+\d+",  # Contains another citation
        r"\bsee\s+id\.?",  # "see id." or "see id"
        r"\bsee\s+supra\b",  # "see supra"
        r"\bsupra\b",  # "supra" without case name
    ]
    if re.search(r"\bid\.?\b", context_lower) and not re.search(r"\b[A-Z][a-zA-Z\'\.\&\-\s]*\s+v\.?\s+[A-Z]", context):
        # "id." with no "X v. Y" pattern -> skip
        logger.debug("[ADAPTIVE-CONTEXT] Skipping context with id. and no case name")
        return False

    for skip_pattern in skip_patterns:
        if re.search(skip_pattern, context_lower):
            logger.debug(f"[ADAPTIVE-CONTEXT] Skipping context with skip pattern: {skip_pattern}")
            return False

    # Check for case name patterns
    for pattern in case_patterns:
        if re.search(pattern, context):
            logger.debug(f"[ADAPTIVE-CONTEXT] Found case pattern: {pattern}")
            return True

    return False


def get_context_before_citation_in_text(
    text: str,
    citation_text: str,
    lookback: int = 120,
) -> Optional[str]:
    """
    Find the citation string in the document and return text immediately before it.
    Use when position-based context may be wrong (e.g. PDF/eyecite offset errors).
    Example: 'Simon v. Eastern Ky. Welfare Rights Organization, 426 U. S. 26' ->
    we find '426 U. S. 26' in text and return text before it for extraction.
    """
    if not text or not citation_text or len(citation_text.strip()) < 5:
        return None
    normalized = re.sub(r"\s+", " ", citation_text.strip()).strip()
    # For "VOL U.S. PAGE" / "VOL U. S. PAGE" use a flexible pattern that allows space in "U. S."
    us_match = re.match(r"^(\d+)\s+U\.?\s*S\.?\s*(\d+)(?:\s*,?\s*\d+)*\s*$", normalized, re.IGNORECASE)
    if us_match:
        vol, page = us_match.group(1), us_match.group(2)
        # Match "426 U.S. 26" or "426 U. S. 26" or "426 U. S. 26, 41"
        pattern_str = r"(?<!\d)" + re.escape(vol) + r"\s+U\.?\s*S\.?\s*" + re.escape(page) + r"(?:\s*,\s*\d+)*(?!\d)"
    else:
        # For "VOL F.3d PAGE" / "VOL F. 3d PAGE" (federal reporters) use flexible pattern
        fed_match = re.match(r"^(\d+)\s+F\.?\s*(2d|3d|4th)\s+(\d+)(?:\s*,?\s*\d+)*\s*$", normalized, re.IGNORECASE)
        if fed_match:
            vol, series, page = fed_match.group(1), fed_match.group(2), fed_match.group(3)
            # Match "199 F.3d 263" or "199 F. 3d 263" or "199 F.3d 263, 267"
            pattern_str = (
                r"(?<!\d)" + re.escape(vol) + r"\s+F\.?\s*" + re.escape(series) + r"\s+"
                + re.escape(page) + r"(?:\s*,\s*\d+)*(?!\d)"
            )
        else:
            escaped = re.escape(normalized)
            escaped = re.sub(r"\\\\\.", r".?", escaped)
            escaped = re.sub(r"\\\\ ", r"\\s+", escaped)
            pattern_str = r"(?<!\d)" + escaped + r"(?!\d)"
    try:
        pattern = re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        return None
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    # Prefer match that has " v. " in the lookback before it (case name immediately before citation)
    best = None
    best_has_v = False
    for m in matches:
        start = max(0, m.start() - lookback)
        before = text[start : m.start()].strip()
        has_v = " v. " in before or " v " in before
        if best is None or (has_v and not best_has_v) or (has_v == best_has_v and m.start() > (best.start() if best else 0)):
            best = m
            best_has_v = has_v
    if best is None:
        best = matches[-1]
    start = max(0, best.start() - lookback)
    context = text[start : best.start()].strip()
    if ";" in context:
        context = context[context.rfind(";") + 1 :].strip()
    return context if len(context) >= 10 else None


def get_strict_context_for_citation(
    text: str,
    citation_start: int,
    citation_end: int,
    all_citation_positions: List[Tuple[int, int, str]],
    max_lookback: int = 150,  # USER FIX: Allow larger max, the adaptive function controls actual window
) -> str:
    """
    Get strictly isolated context for a citation, stopping at previous citation boundaries.

    CRITICAL: This function prevents case name bleeding between citations.

    Args:
        text: Full document text
        citation_start: Start position of the target citation
        citation_end: End position of the target citation
        all_citation_positions: List of all citation positions in the document
        max_lookback: Maximum characters to look back from the citation

    Returns:
        Strictly isolated context string
    """
    logger.debug(f"[STRICT-CONTEXT] Getting context for citation at {citation_start}-{citation_end}")

    # CRITICAL FIX: Find the closest citation boundary before this citation
    # This prevents case name bleeding from nearby citations
    previous_boundary = 0
    closest_citation_end = 0  # Track where the closest previous citation ends

    # Special handling for citations that are part of the same case cluster
    # If the previous citation is very close (within 50 chars), it might be a parallel citation
    # for the same case, so we should look further back to find the actual case name
    closest_citation_distance = float("inf")

    for pos_start, pos_end, cit_text in all_citation_positions:
        # Skip if this is the same citation or after it
        if pos_start >= citation_start:
            continue

        # Calculate distance from this citation to our target citation
        distance = citation_start - pos_end

        # Track the closest citation
        if distance < closest_citation_distance:
            closest_citation_distance = distance
            closest_citation_end = pos_end

        # This is a previous citation - use its END position as boundary (not start)
        # This ensures we don't include any text from the previous citation
        if pos_end > previous_boundary:
            previous_boundary = pos_end  # Use END position, not start

    # USER FIX: HARD BOUNDARY - NEVER cross previous citation's END position
    # The previous code tried to "extend" beyond for parallel citations, but this
    # caused cascading contamination where each citation grabbed the previous one's case name
    #
    # Simple rule: previous_boundary = closest_citation_end (HARD STOP)
    # If no previous citation, use 0
    #
    # This may result in more N/A extractions, but the canonical fallback handles those
    logger.debug(f"[HARD-BOUNDARY] Previous citation ends at {closest_citation_end}, using as HARD boundary")
    logger.debug(f"[HARD-BOUNDARY] Distance to previous citation: {closest_citation_distance} chars")

    # The boundary is the END of the closest previous citation - NO EXCEPTIONS
    if closest_citation_end > 0:
        previous_boundary = closest_citation_end
        logger.debug(f"[HARD-BOUNDARY] Set boundary to {previous_boundary}")
        
        # CRITICAL FIX: Check if there's a semicolon after the previous citation
        # If so, the semicolon is a stronger boundary than the citation end
        # Example: "Case1, 497 U.S. 1; Case2, 418 U.S. 323"
        # For "418 U.S. 323", we should stop at the semicolon, not at "497 U.S. 1"
        if closest_citation_end < len(text):
            text_after_prev_citation = text[closest_citation_end:citation_start]
            semicolon_pos = text_after_prev_citation.find(";")
            if semicolon_pos != -1:
                # Found semicolon - use it as the boundary instead
                semicolon_absolute_pos = closest_citation_end + semicolon_pos + 1  # +1 to skip the semicolon
                logger.debug(
                    f"[SEMICOLON-BOUNDARY] Found semicolon at {semicolon_absolute_pos} "
                    f"(after previous citation at {closest_citation_end}), using as boundary"
                )
                previous_boundary = semicolon_absolute_pos

    # Calculate context start (don't go further back than max_lookback from the citation)
    context_start = max(previous_boundary, citation_start - max_lookback)

    # Check for parenthetical boundaries - CRITICAL for handling nested citations
    search_start = max(0, citation_start - max_lookback)
    text_before = text[search_start:citation_start]

    # Find the last opening parenthesis that doesn't have a matching closing parenthesis
    paren_boundary = context_start  # Default to citation boundary
    last_open_paren = text_before.rfind("(")

    if last_open_paren >= 0:
        # Found a paren - check if citation is inside it
        actual_pos = search_start + last_open_paren
        # Make sure there's no closing paren between the opening paren and our citation
        text_between = text[actual_pos:citation_start]
        if ")" not in text_between:
            # Citation is inside parenthetical - use opening paren as boundary
            paren_boundary = actual_pos + 1  # +1 to skip the '(' itself
            logger.debug(f"[PAREN-DEBUG] Citation inside parenthetical! Boundary at pos {actual_pos}")
            logger.debug(f"[PAREN-DEBUG] Text after paren: '{text[paren_boundary:citation_start][-50:]}'")
        else:
            logger.debug(f"[PAREN-DEBUG] Found '(' but has ')' between - not in parenthetical")
    else:
        logger.debug(f"[PAREN-DEBUG] No '(' found in text_before")

    # Determine strict context boundaries
    # CRITICAL: Use the STRICTEST boundary to prevent case name bleeding
    context_start = max(
        previous_boundary,  # Stop at previous citation END boundary (most important)
        paren_boundary,  # Stop at parenthetical boundary
        citation_start - max_lookback,  # Don't go too far back
    )
    context_start = max(0, context_start)

    # Extract ONLY the text before this citation
    strict_context = text[context_start:citation_start].strip()

    # NOTE: Removed citation pattern detection that was causing performance issues
    # The boundary detection already prevents including citation text, so this check was redundant

    # CRITICAL FIX: Filter out document headers, footers, and footnotes that split case names
    # Headers like "Erickson v. Pharmacia, No. 103135-1", footers with repeated case names,
    # and footnotes like "24" should be removed from context so case names split across them can be found
    strict_context = _filter_headers_and_footnotes_from_context(strict_context)

    # CRITICAL FIX: Additional boundary trimming to prefer the nearest case segment
    # If there's a semicolon-separated series, keep only the segment AFTER the last semicolon
    # within a reasonable proximity window to the citation (prevents pulling prior cases).
    # SEMICOLON IS A STRONGER BOUNDARY THAN CITATION END - always respect it!
    if strict_context:
        # Always keep only the segment AFTER the last semicolon to avoid pulling
        # case names from earlier clauses in multi-citation sentences.
        # Example: "Milkovich v. X, 497 U.S. 1; Gertz v. Y, 418 U.S. 323"
        # For "418 U.S. 323", we MUST only look at text after the semicolon
        last_sc = strict_context.rfind(";")
        if last_sc != -1:
            text_after_semicolon = strict_context[last_sc + 1 :].strip()
            # Only use semicolon boundary if there's actual text after it (not just whitespace)
            if text_after_semicolon:
                logger.debug(
                    f"[SEMICOLON-BOUNDARY] Found semicolon at position {last_sc}, "
                    f"trimming context to: '{text_after_semicolon[:100]}...'"
                )
                strict_context = text_after_semicolon

        # CRITICAL FIX: Also trim after signal phrases that indicate different cases
        # "but see", "; see also", etc. introduce different cases and should be boundaries
        # Example: "Larimore v. Blaylock, 259 Va. 568; but see Swindle v. State, 10 Tenn. 581"
        # For "10 Tenn. 581", we should only look at text after "but see"
        # BUT: Only trim if there's still meaningful context left (at least 20 chars)
        signal_phrase_patterns = [
            r";\s*but\s+see\b",  # "; but see" - introduces contrasting case
            r",\s*but\s+see\b",  # ", but see" - introduces contrasting case
            r"\bbut\s+see\b",  # "but see" anywhere (fallback)
        ]
        for pattern in signal_phrase_patterns:
            match = re.search(pattern, strict_context, re.IGNORECASE)
            if match:
                text_after_signal = strict_context[match.end() :].strip()
                # Only trim if there's enough context left (at least 20 chars)
                # This prevents removing ALL context when signal phrase appears early
                if text_after_signal and len(text_after_signal) >= 20:
                    logger.debug(
                        f"[SIGNAL-BOUNDARY] Found '{match.group(0)}' at position {match.start()}, "
                        f"trimming context to: '{text_after_signal[:100]}...' "
                        f"(kept {len(text_after_signal)} chars)"
                    )
                    strict_context = text_after_signal
                    break  # Use first signal phrase found
                else:
                    # Not enough context left - keep original context but log warning
                    logger.debug(
                        f"[SIGNAL-BOUNDARY-SKIP] Found '{match.group(0)}' but not enough context left "
                        f"({len(text_after_signal) if text_after_signal else 0} chars), keeping full context"
                    )
        
        # Also trim after the last em-dash or long dash which often separates cites
        # FIX DEC 2025 v10: Don't trim if dash is part of a case name (followed by corporate suffix)
        for dash in ("\u2014", "\u2013", "--"):
            last_dash = strict_context.rfind(dash)
            if last_dash != -1:
                after_dash = strict_context[last_dash + 1 :].strip()[:25].lower()
                is_part_of_name = any(
                    s in after_dash for s in ["llc", "inc", "corp", "ltd", "co.", " tv ", "radio", "broadcast"]
                )
                if is_part_of_name:
                    logger.debug(f"[DASH-TRIM-SKIP] Dash part of case name: '{strict_context}'")
                else:
                    strict_context = strict_context[last_dash + 1 :].strip()

        # For parenthetical citations, trim after the last comma within reasonable distance
        # to get the closest case name, but don't over-truncate for comma-separated citations
        if "(" in strict_context and "," in strict_context:
            # Special handling: if we're in a parenthetical with multiple citations,
            # we need a larger context window to capture the actual case name
            # Look for the pattern "Case Name v. Defendant, citation"
            case_pattern = strict_context.rfind(" v. ")
            if case_pattern != -1:
                # Found "v." - this is likely a proper case name, keep it
                # Find the start of the case name (look backwards for beginning)
                case_start = case_pattern
                # Look backwards to find the start of the case name
                # FIX DEC 2025: Don't stop at periods that are part of corporate suffixes
                # like "Co.", "Inc.", "Corp.", "Ltd.", "L.P.", "L.L.C.", etc.
                corporate_suffixes = ["co.", "inc.", "corp.", "ltd.", "l.p.", "l.l.c.", "llc.", "n.a.", "p.c.", "p.a."]
                while case_start > 0:
                    prev_char = strict_context[case_start - 1]
                    if prev_char in [";", "("]:
                        break
                    if prev_char == ".":
                        # Check if this period is part of a corporate suffix
                        # Look at the 5 chars before this period
                        suffix_check_start = max(0, case_start - 5)
                        suffix_text = strict_context[suffix_check_start:case_start].lower()
                        is_corporate_suffix = any(suffix_text.endswith(s[:-1]) for s in corporate_suffixes)
                        if not is_corporate_suffix:
                            break
                    case_start -= 1
                strict_context = strict_context[case_start:].strip()
            else:
                # No "v." found - use comma trimming as fallback
                commas = [i for i, c in enumerate(strict_context) if c == ","]
                if commas:
                    # Get the last comma that's within 100 chars of the end
                    last_comma = commas[-1]
                    if len(strict_context) - last_comma <= 100:
                        strict_context = strict_context[last_comma + 1 :].strip()

    logger.debug(f"[STRICT-CONTEXT] Final context: '{strict_context}'")
    return strict_context


def _is_prose_not_case_name(name: str) -> bool:
    """True if name is sentence/quote prose (e.g. \"X's failure to demonstrate actual knowledge\"), not a case name."""
    if not name or len(name) < 10:
        return False
    s = name.strip()
    # Any apostrophe-like + "s failure to" (Cockrum's failure to demonstrate actual knowledge)
    if re.search(r"[\'\u2018\u2019\u0027]s\s+failure\s+to\s+", s, re.IGNORECASE):
        return True
    # Standalone phrase without requiring apostrophe (PDF may alter the character)
    if re.search(r"\bfailure\s+to\s+(?:demonstrate|show|establish|prove)\s+(?:actual\s+)?knowledge\b", s, re.IGNORECASE):
        return True
    return False


def _is_citation_fragment_not_case_name(name: str) -> bool:
    """
    Return True if the string looks like a citation fragment (e.g. "(10 Tenn.), 1831")
    rather than a case name like "Swindle v. State". Such fragments must be rejected.
    """
    if not name or len(name) < 8:
        return False
    s = name.strip()
    # Prose/sentence misidentified as case name (e.g. "Cockrum's failure to demonstrate actual knowledge")
    if _is_prose_not_case_name(s):
        return True
    # Reporter abbreviations that indicate citation fragment (not case name)
    reporter_abbrev = r"(?:Tenn\.|Va\.|U\.\s*S\.|F\.|P\.|S\.\s*Ct\.|Wn\.|Ill\.|Ohio|Cal\.|N\.\s*Y\.|Mass\.|Tex\.)"
    # Parenthetical citation fragment: "(10 Tenn.), 1831", "(10 Tenn.)", "(259 Va.) 2010"
    if s.startswith("("):
        if re.search(r"[),]\s*\d{4}\s*$", s) and re.search(reporter_abbrev, s, re.IGNORECASE):
            return True
        # Entire string is parenthetical reporter ref + year: "(10 Tenn.), 1831"
        if re.search(r"\(\s*\d+\s*" + reporter_abbrev + r".*\d{4}\s*$", s, re.IGNORECASE):
            return True
        # Parenthetical reporter ref without year (e.g. "(10 Tenn.)" after year strip): still a fragment
        if re.search(r"\(\s*\d+\s*" + reporter_abbrev, s, re.IGNORECASE):
            return True
    # Starts with digit + reporter (e.g. "10 Tenn. 581" mistaken as name)
    if re.match(r"^\d+\s+(?:Tenn\.|Va\.|U\.\s*S\.|F\.|P\.|Wn\.)", s, re.IGNORECASE):
        return True
    return False


def _is_statute_name_not_case_name(name: str) -> bool:
    """
    Return True if the string looks like a statute/title name (e.g. "Administrative Procedure Act, 1970")
    rather than a case name. Such strings must be rejected.
    """
    if not name or len(name) < 6:
        return False
    s = name.strip()
    low = s.lower()
    # Strip trailing ", YYYY" or ", YYYY." so "Administrative Procedure Act, 1970" -> "Administrative Procedure Act"
    base = re.sub(r",\s*(19|20)\d{2}\s*\.?\s*$", "", low).strip()
    statute_endings = (" act", " code", " statute", " regulation", " rule")
    if base.endswith(statute_endings):
        return True
    # Known statute patterns (even with "v." in them, e.g. "Administrative Procedure v. Act, 1970")
    statute_patterns = [
        r"\badministrative procedure\b.*\bact\b",
        r"\bfreedom of information\b.*\bact\b",
        r"\bcivil rights\b.*\bact\b",
        r"\bunited states code\b",
    ]
    for pat in statute_patterns:
        if re.search(pat, low):
            return True
    return False


def _is_citation_or_part_of_citation(extracted_name: str, citation_text: str) -> bool:
    """
    Return True if the extracted string is the citation itself or part of it.
    Such strings must be rejected at extraction time so the case name is never
    the citation or a citation fragment.

    Checks:
    - Exact match (normalized)
    - Citation fragment patterns (e.g. "(10 Tenn.), 1831")
    - Statute names (e.g. "Administrative Procedure Act, 1970")
    - Extracted name contains the citation (e.g. "Unknown Case, 506 U.S. 139")
    - Extracted name is contained in citation (e.g. "506 U.S. 139" when citation is "506 U.S. 139 (2006)")
    """
    if not extracted_name or not citation_text:
        return False
    name = extracted_name.strip()
    cite = citation_text.strip()
    if not name or not cite:
        return False
    # Reject statute names (e.g. "Administrative Procedure Act, 1970")
    if _is_statute_name_not_case_name(name):
        return True
    # Already reject citation fragments (parenthetical + year, digit + reporter)
    if _is_citation_fragment_not_case_name(name):
        return True
    # Normalize for comparison: lowercase, collapse spaces
    norm_name = re.sub(r"\s+", " ", name.lower()).strip()
    norm_cite = re.sub(r"\s+", " ", cite.lower()).strip()
    if norm_name == norm_cite:
        return True
    # Extracted name contains the full citation (e.g. "Something, 506 U.S. 139" or "506 U.S. 139")
    if norm_cite in norm_name:
        return True
    # Extracted name is a significant substring of citation (e.g. "506 U.S. 139" vs "506 U.S. 139 (2006)")
    if norm_name in norm_cite and len(norm_name) >= 8:
        # Only treat as citation-part if the substring looks like a citation (digits, reporter abbrev)
        if re.search(r"\d+\s*(?:u\.\s*s\.|f\.|f\.\d|p\.|wn\.|tenn\.|va\.|ill\.|ohio)", norm_name, re.IGNORECASE):
            return True
    return False


def extract_case_name_from_strict_context(context: str, citation_text: str) -> Optional[str]:
    """
    Extract case name from strictly isolated context.

    This function ONLY looks at the provided context and won't bleed to other citations.

    Args:
        context: Strictly isolated context (text immediately before citation)
        citation_text: The citation text (for logging)

    Returns:
        Extracted case name or None
    """
    logger.debug(
        f"[STRICT-CONTEXT-ISOLATOR] extract_case_name_from_strict_context() invoked for {citation_text}"
    )

    if not context or len(context) < 10:
        logger.debug(
            f"[STRICT-EXTRACT] Context too short for {citation_text}: {len(context) if context else 0} chars"
        )
        return None

    logger.debug(f"[STRICT-EXTRACT] Citation: {citation_text}, context ({len(context)} chars)")

    # First unescape any HTML entities (e.g., &#039;, &amp;)
    try:
        context = html.unescape(context)
    except Exception:
        pass

    # CRITICAL: Normalize Unicode characters BEFORE pattern matching
    # Convert smart quotes and apostrophes to ASCII equivalents
    context = context.replace("\u2019", "'")  # Right single quotation mark -> apostrophe
    context = context.replace("\u2018", "'")  # Left single quotation mark -> apostrophe
    context = context.replace("\u201c", '"')  # Left double quotation mark
    context = context.replace("\u201d", '"')  # Right double quotation mark
    context = context.replace("\u00b4", "'")  # Acute accent -> apostrophe
    context = context.replace("\u0060", "'")  # Grave accent -> apostrophe
    context = context.replace("\u00a0", " ")  # Non-breaking space -> space
    # Normalize dashes and unusual spaces
    context = context.replace("\u2013", "-")  # En dash
    context = context.replace("\u2014", "-")  # Em dash
    context = re.sub(r"[\u2000-\u200B\u202F\u205F\u3000]", " ", context)  # other thin/figure spaces
    # CRITICAL FIX: Remove docket numbers EARLY (before whitespace normalization)
    # This prevents "Erickson v. Pharmacia, No. 103135-1" from contaminating extraction
    context = re.sub(r",?\s*No\.\s*[\d\-]+", "", context, flags=re.IGNORECASE)

    # Collapse whitespace (normalize newlines to spaces)
    context = re.sub(r"\s+", " ", context).strip()

    # CRITICAL: Strip citation fragment from END of context BEFORE pattern matching
    # e.g. "...Swindle v. State, (10 Tenn.), 1831" -> "...Swindle v. State" so we match the case name, not the fragment
    fragment_at_end = re.compile(
        r",\s*\(\d+\s*(?:Tenn\.|Va\.|U\.\s*S\.|F\.|P\.|Wn\.|Ill\.|Ohio)\b[^)]*\),\s*\d{4}\s*$",
        re.IGNORECASE,
    )
    if context and fragment_at_end.search(context):
        context = fragment_at_end.sub("", context).strip().rstrip(",").strip()
        logger.debug(
            f"[STRICT-EXTRACT] Stripped citation fragment from end of context for {citation_text} (before pattern matching)"
        )

    # CRITICAL: Strip leading "Under the X Act. See" / "X Act. See" so the case name is first
    # e.g. "Under the Administrative Procedure Act. See Association of Data Processing... v. Camp"
    # -> "Association of Data Processing... v. Camp" so we match the case, not the statute
    statute_see_prefix = re.compile(
        r"^(?:Under\s+(?:the\s+)?(?:Administrative\s+Procedure\s+Act|.*?\s+Act)\.?\s*\.?\s*)?"
        r"(?:See\s+(?:also\s+)?(?:e\.g\.\s*,?\s*)?)\s*",
        re.IGNORECASE,
    )
    if context and statute_see_prefix.match(context):
        context = statute_see_prefix.sub("", context).strip()
        logger.debug(
            f"[STRICT-EXTRACT] Stripped leading statute/See prefix from context for {citation_text}"
        )

    # CRITICAL: Remove signal words and case history notations BEFORE pattern matching
    # IMPROVED: Only remove signal words at START of context to avoid truncating case names

    # FIRST: Remove entire lines containing legal concepts that aren't case names
    # This handles "Anti-SLAPP Statute / Collateral Order Doctrine\n\nOverruling..."
    doctrine_lines_pattern = r"[^\n]*\b(doctrine|rule|test|standard|principle|holding)\b[^\n]*\n+"
    context = re.sub(doctrine_lines_pattern, "", context, flags=re.IGNORECASE)

    # CRITICAL FIX (context-bleeding): Judge attribution = header/attribution, not case for THIS citation.
    # Example: "... TRANSUNION LLC v. RAMIREZ THOMAS, J., dissenting ... Simon v. Eastern Ky., 426 U.S. 26"
    # We must DROP the segment containing ", J., dissenting" and use only text AFTER it, so we extract
    # "Simon v. Eastern Ky." not "TRANSUNION LLC v. RAMIREZ THOMAS".
    judge_attribution_patterns = [
        r",\s*[A-Z]+\s*,\s*J\.\s*,\s*(?:dissenting|concurring)(?:\s+in\s+(?:part|judgment))?",
        r",\s*Justice\s+[A-Z]+\s*,\s*(?:dissenting|concurring)",
        r"\b[A-Z]+\s*,\s*J\.\s*,\s*(?:dissenting|concurring)",
    ]
    for pattern in judge_attribution_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            # Use text AFTER the marker so we don't keep "X v. Y" that belongs to the attribution
            context_after_judge = context[match.end() :].strip()
            if len(context_after_judge) >= 15:
                context = context_after_judge
                logger.debug(
                    f"[JUDGE-DROP] Dropped segment containing judge attribution '{match.group(0)}'; "
                    f"using {len(context)} chars after it to avoid header bleed"
                )
                break
            else:
                logger.debug(
                    f"[JUDGE-DROP-SKIP] Judge marker found but too little text after ({len(context_after_judge)} chars)"
                )
    
    # CRITICAL FIX: Remove header text like "Opinion of the Court" that contaminates case names
    # Examples: "Opinion of the Court Sprint Communications Co. v. APCC Services"
    # Should extract "Sprint Communications Co. v. APCC Services" not "Opinion of the Court Sprint..."
    # USER FIX 2026-01-27: Enhanced to catch more variations and be more aggressive
    # USER FIX 2026-02: Add context-bleed patterns - "Americancourts.", "Syllabusmat"
    header_text_patterns = [
        r"^Opinion\s+of\s+the\s+Court\s+",  # "Opinion of the Court" at start
        r"^Opinion\s+of\s+the\s+",  # "Opinion of the" at start
        r"\bOpinion\s+of\s+the\s+Court\s+",  # "Opinion of the Court" anywhere
        r"\bOpinion\s+of\s+the\s+Court\b",  # "Opinion of the Court" (no trailing space needed)
        r"Opinion\s+of\s+the\s+Court\s+TransUnion",  # Specific pattern for TransUnion case
        # Context bleed: "Americancourts. Spokeo" -> "Spokeo" (prose before case name)
        r"^(?:American|Federal)\s*courts?\.?\s*",
        r"\b(?:American|Federal)\s*courts?\.?\s+",
        # Context bleed: "Syllabusmat" / "Syllabus" header concatenated with case name
        r"^Syllabus\s*",  # "Syllabus" at start (header)
        r"\bSyllabus\s+",  # "Syllabus " anywhere (header word)
        r"Syllabusmat\b",  # "Syllabusmat" = Syllabus + mat (contamination)
    ]
    for pattern in header_text_patterns:
        context = re.sub(pattern, "", context, flags=re.IGNORECASE)
    
    # USER FIX 2026-01-27: Also remove "Opinion of the Court" from the middle of case names
    # This handles cases where it wasn't caught by the above patterns
    context = re.sub(r"Opinion\s+of\s+the\s+Court\s+", " ", context, flags=re.IGNORECASE)
    context = re.sub(r"\s+", " ", context).strip()  # Clean up extra spaces
    
    # CRITICAL FIX: Remove legal analysis phrases that contaminate case names
    # Examples: "Frye rulings de novo", "WPLA claim", "ER 702", "We review choice of law", etc.
    legal_analysis_patterns = [
        r"^(?:Frye|Daubert|Kumho)\s+(?:rulings?|hearings?|standards?|tests?)\s+(?:de\s+novo|review|analysis)\.?\s*",
        r"^(?:WPLA|WCPA|RCW|ER|FRCP|FRCivP)\s+(?:claim|rule|statute|evidence)\.?\s*",
        r"^We\s+(?:review|hold|conclude|determine|find|affirm|reverse|remand)\s+",
        r"^(?:The\s+)?(?:court|trial\s+court|appellate\s+court)\s+(?:held|found|ruled|determined)\.?\s*",
        r"^(?:Under|Pursuant\s+to|According\s+to|In\s+accordance\s+with)\s+",
        r"^Choice\s+of\s+law\s+(?:questions?|issues?)\s+",
        r"^Washington\s+Legislature\s+intended\.?\s*",
        # ENHANCED: More patterns to catch variations
        r"\bWPLA\s+claim\.?\s*",  # "WPLA claim" anywhere (not just at start)
        r"\bWashington\s+Legislature\s+intended\.?\s*",  # "Washington Legislature intended" anywhere
        r"^ER\s+\d+\.?\s*",  # "ER 702" at start
        r"\bER\s+\d+\.?\s+",  # "ER 702" anywhere (with space after)
    ]

    for pattern in legal_analysis_patterns:
        context = re.sub(pattern, "", context, flags=re.IGNORECASE)

    # THEN: Remove signal words ONLY at start of context (improved to not truncate case names)
    signal_patterns_start_only = [
        # Signal phrases at START of context only
        r"^\s*see,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," at start
        r"^\s*see\s+also\s+",  # "See also" at start
        r"^\s*see\s+generally\s+",  # "See generally" at start
        r"^\s*but\s+see\s+",  # "But see" at start
        r"^\s*but\s+cf\.?\s+",  # "But cf." at start
        r"^\s*(cf|e\.g\.|i\.e\.|see|compare|accord|contra)\.?\s+",  # Signal words at start
    ]

    # Signal patterns that can appear anywhere (more conservative)
    signal_patterns_anywhere = [
        # Case history notations
        r"\b(overruling|overruled by|superseding|superseded by|abrogated by|disapproved of on other grounds by|disapproved of by|modified by|limited by|questioned by|criticized by|distinguished by|affirmed by|affirming|reversed by|reversing|vacated by|remanded by|amended by)\b\s+",
        # Procedural phrases
        r"\b(quoting|citing|discussing|relying on|based on|following|applying|interpreting)\b\s+",
        # Parenthetical case history
        r"\([^)]{0,150}?(overruled|superseded|abrogated|disapproved|modified|affirmed|reversed)[^)]{0,150}?\)\s*",
    ]

    original_context = context

    # Apply start-only patterns first
    for signal_pattern in signal_patterns_start_only:
        context = re.sub(signal_pattern, "", context, flags=re.IGNORECASE)

    # Apply anywhere patterns
    for signal_pattern in signal_patterns_anywhere:
        context = re.sub(signal_pattern, "", context, flags=re.IGNORECASE)

    if context != original_context:
        logger.debug(f"[STRICT-EXTRACT] Cleaned signal words: '{original_context[-50:]}' -> '{context[-50:]}'")

    # Additional cleanup: remove any remaining isolated docket patterns that might have been missed
    context_before_clean = context
    context = re.sub(r"\s+No\.\s+[\d\-\s]+(?=\s+v\.)", " ", context, flags=re.IGNORECASE)
    if context != context_before_clean:
        logger.debug(f"[STRICT-EXTRACT] Cleaned case numbers from context")
    else:
        logger.debug(f"[STRICT-EXTRACT] No case numbers found to clean in context")

    # Look for paragraph/sentence boundaries but be less aggressive
    # Only split if we have very long context (>150 chars) to avoid losing too much
    if len(context) > 150:
        sentences = re.split(r"[.!]\s+(?=[A-Z])", context)
        if len(sentences) > 1:
            # Take the last 2 sentences to preserve more context
            context = " ".join(sentences[-2:]).strip()
            logger.debug(f"[STRICT-EXTRACT] Reduced context to last 2 sentences")

    # Patterns to extract case names (IMPROVED - GREEDY patterns for full legal names)
    patterns = [
        # PRIORITY 0: Ship/admiralty cases - "The Pizarro" or "The Venus, Rae, Master"
        # Early Supreme Court cases (Wheat., Cranch, etc.) often involve ships without "v."
        # HIGHEST PRIORITY to prevent matching partial names or wrong cases
        # Pattern matches "The [Name]" or "The [Name], [Master]" at end of context (before citation)
        r"(The\s+[A-Z][a-zA-Z]+(?:\s*,\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)?)(?:\s*,?\s*$)",
        # PRIORITY 1: Complex legal names with full party descriptions (NEW - HIGHEST PRIORITY)
        # Matches: "Chance Gresser, individually and as parent, natural guardian, next of friendand on behalf of his daughter, C.G., and Erin Gresser, individually and asparent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center"
        # Matches: "Francis Rudnicki and Pamela Rudnicki, as parents, guardians and next friends of Alexander Rudnicki, a minor v. Bianco"
        r"([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:individually|as\s+(?:parent|guardian|next\s+friend|administrator|executor|trustee|personal\s+representative)|and\s+on\s+behalf\s+of|by\s+and\s+through)[^,]*)*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:d/b/a|doing\s+business\s+as|a\s+(?:Delaware|California|New\s+York)\s+(?:Corporation|Corp|Inc|LLC|Ltd))[^,]*)*)(?:\s*[;\(]|,\s*\d|,\s*No\.|$)",
        # PRIORITY 2: "In re" cases with full party names
        # Matches: "In re: The PEOPLE of the State of Colorado v. Regina M. SPRINKLE"
        r"In\s+re:\s+([A-Z][A-Z\s\'&\-\.,]+)\s+v\.\s+([A-Z][A-Z\s\'&\-\.,]+)(?:\s*[;\(]|,\s*\d|$)",
        # PRIORITY 3: Standard "v." pattern - ENHANCED to handle complex corporate names
        # Stop at semicolon or opening paren to prevent cross-citation contamination
        # ENHANCED: Allow optional ", Inc." / ", Corp." etc. so "Association... Organizations, Inc. v. Camp" matches
        # - Single letter abbreviations followed by period (N., W., etc.)
        # - Corporate suffixes (LLC, Inc., Corp., Co., Ltd., etc.)
        # FIX JAN 2026: Improved pattern to better handle signal words and docket numbers
        r"([A-Z][a-zA-Z\'\.\&\-\s]*(?:,\s*(?:Inc\.|Corp\.|Co\.|LLC|Ltd\.))?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\-\s]*(?:,\s*(?:Inc\.|Corp\.|Co\.|LLC|Ltd\.))?)(?=\s*,\s*(?:No\.|\d+)|\s*[;\(,]|$)",
        # PRIORITY 4: In re/Matter of/Estate of patterns
        r"(?:In\s+re|Matter\s+of|Estate\s+of)\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,200})(?:\s*[,;\(]|$)",
        # PRIORITY 5: Ex parte pattern
        r"Ex\s+parte\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,200})(?:\s*[,;\(]|$)",
    ]

    for pattern_idx, pattern in enumerate(patterns, 1):
        try:
            # Look for matches - find ALL matches
            matches = list(re.finditer(pattern, context, re.IGNORECASE))
            if matches:
                logger.debug(
                    f"[PATTERN-DEBUG] Pattern {pattern_idx} found {len(matches)} matches"
                )
            else:
                logger.debug(f"[PATTERN-DEBUG] Pattern {pattern_idx} found no matches")

            if not matches:
                continue

            # IMMEDIATE HEADER FILTERING: Remove header matches before processing
            filtered_matches = []
            for match in matches:
                match_text = match.group(0).upper()
                has_et_al_match = "ET AL" in match_text or "ETAL" in match_text.replace(" ", "").replace(
                    ".", ""
                ).replace(",", "")
                has_role_word_match = any(
                    re.search(role, match_text)
                    for role in [r"PETITIONER", r"RESPONDENT", r"APPELLANT", r"APPELLEE", r"PLAINTIFF", r"DEFENDANT"]
                )
                has_no_match = (
                    "NO." in match_text
                    or " NO " in match_text
                    or match_text.endswith(" NO")
                    or re.search(r"\bNO\.?\s*\d+", match_text)
                )
                header_pattern_match = re.search(
                    r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)", match_text
                )

                if (
                    (has_et_al_match and has_role_word_match)
                    or (has_role_word_match and has_no_match)
                    or header_pattern_match
                ):
                    logger.debug(f"[PATTERN-REJECT] Rejected header pattern in match: '{match.group(0)}'")
                    continue  # Skip this match
                filtered_matches.append(match)

            # If all matches were headers, try next pattern
            if not filtered_matches:
                logger.debug(
                    f"[PATTERN-REJECT] All matches for pattern {pattern_idx} were headers, trying next pattern"
                )
                continue

            matches = filtered_matches  # Use filtered matches

            # CRITICAL FIX: Prioritize matches with "v." over statute names and reject judge attribution
            # Statute names like "Administrative Procedure Act" should be rejected
            # Judge attribution like "THOMAS, J., dissenting" should be rejected
            # in favor of actual case names like "Association v. Camp"
            matches_with_v = []
            matches_without_v = []
            
            for match in matches:
                match_text = match.group(0)
                match_lower = match_text.lower()
                
                # CRITICAL FIX: Reject judge attribution text early
                # Examples: "TRANSUNION LLC v. RAMIREZ THOMAS, J., dissenting"
                # Judge markers should stop extraction, not be included
                judge_markers = [
                    r"\bJ\.,\s*(dissenting|concurring|concurring in part|concurring in judgment)",
                    r"\bJustice\s+\w+,\s*(dissenting|concurring)",
                    r",\s*dissenting$",
                    r",\s*concurring$",
                    r"\bC\.J\.,",  # Chief Justice
                    r"\bJ\.J\.,",  # Justices (plural)
                ]
                for marker in judge_markers:
                    if re.search(marker, match_text, re.IGNORECASE):
                        logger.debug(
                            f"[JUDGE-REJECT] Rejecting match with judge attribution '{match_text}' "
                            f"(contains judge marker: {marker})"
                        )
                        # If match contains judge attribution, try to extract just the case name part
                        # Stop at the judge marker
                        case_name_part = re.split(
                            r",\s*(?:THOMAS|JUSTICE|J\.|C\.J\.|J\.J\.).*?(?:dissenting|concurring)",
                            match_text,
                            flags=re.IGNORECASE
                        )[0].strip()
                        # Only use the cleaned part if it still has "v." and is valid
                        if " v. " in case_name_part and len(case_name_part) > 5:
                            # Create a new match with just the case name part
                            logger.debug(
                                f"[JUDGE-CLEAN] Extracted case name '{case_name_part}' "
                                f"from '{match_text}' (removed judge attribution)"
                            )
                            # We'll process this as a match with "v." below
                            match_text = case_name_part
                        else:
                            # Can't salvage, skip this match entirely
                            continue
                
                # USER FIX 2026-01-27: Check for intervening citations between match and target citation
                # If there's a citation between this match and the target, this match belongs to that citation
                # Example: "Meese v. Keene, 481 U.S. 465; Davis v. Federal Election Comm'n, 554 U.S. 724"
                #          For "554 U.S. 724", "Meese v. Keene" has intervening "481 U.S. 465", so reject it
                match_end_pos = match.end()
                text_after_match = context[match_end_pos:]
                
                # USER FIX 2026-01-27: Also check for semicolons - they separate different cases
                # If there's a semicolon between the match and target citation, this match is for a different case
                if ";" in text_after_match[:100]:  # Check first 100 chars after match
                    logger.debug(
                        f"[SEMICOLON-BOUNDARY] Found semicolon between '{match_text}' and target '{citation_text}' - rejecting match"
                    )
                    continue  # Skip this match - semicolon indicates different case
                
                # Check for citation patterns in text after match (before target citation)
                # Enhanced pattern to catch U.S. citations: "481 U.S. 465", "554 U.S. 724", etc.
                citation_pattern = r"\d+\s+(?:U\.?\s*S\.?|S\.\s*Ct\.|L\.\s*Ed\.|F\.(?:2d|3d|4th|Supp\.?)?|Wn\.(?:2d|App\.?\s*2d)?|P\.(?:2d|3d)?)\s+\d+"
                intervening_citations = re.findall(citation_pattern, text_after_match[:200], re.IGNORECASE)
                
                # Check if any intervening citation is NOT the target citation
                citation_norm = re.sub(r"\s+", " ", citation_text.strip().lower())
                has_intervening_citation = False
                for interv_cit in intervening_citations:
                    interv_norm = re.sub(r"\s+", " ", interv_cit.strip().lower())
                    if interv_norm != citation_norm:
                        has_intervening_citation = True
                        logger.debug(
                            f"[INTERVENING-CIT] Found intervening citation '{interv_cit}' "
                            f"between '{match_text}' and target '{citation_text}'"
                        )
                        break
                
                if has_intervening_citation:
                    continue  # Skip this match - it belongs to a different citation
                
                # Check if this is a statute name (ends with Act/Code/Statute, no "v.")
                # Also check with trailing ", YYYY" stripped so "Administrative Procedure Act, 1970" is rejected
                if " v. " not in match_lower and " v " not in match_lower:
                    match_base = re.sub(r",\s*(19|20)\d{2}\s*\.?\s*$", "", match_lower).strip()
                    statute_endings = [" act", " code", " statute", " regulation", " rule"]
                    if any(match_base.endswith(ending) for ending in statute_endings):
                        logger.debug(
                            f"[STATUTE-REJECT] Rejecting statute name '{match_text}' "
                            f"(ends with Act/Code/etc., no 'v.')"
                        )
                        continue  # Skip statute names
                
                # Categorize by whether it has "v."
                if " v. " in match_text or " v " in match_text:
                    matches_with_v.append(match)
                else:
                    matches_without_v.append(match)
            
            # Prioritize matches with "v." - these are actual case names
            if matches_with_v:
                matches = matches_with_v
                logger.debug(f"[PRIORITY] Found {len(matches)} matches with 'v.', prioritizing over {len(matches_without_v)} without")
            elif matches_without_v:
                matches = matches_without_v
                logger.debug(f"[FALLBACK] No matches with 'v.', using {len(matches)} matches without")
            else:
                # All matches were rejected (statutes, etc.)
                continue
            
            # USER FIX 2024-10-26: Take the match CLOSEST to the end of context (closest to citation)
            # Calculate distance from end of context for each match
            context_length = len(context)
            best_match = None
            best_distance = float("inf")

            for match in matches:
                # USER FIX 2026-01-27: Validate each match before considering it as best
                match_text_check = match.group(0)
                match_lower_check = match_text_check.lower()
                
                # Reject if it contains "Opinion of the Court"
                if "opinion of the court" in match_lower_check:
                    logger.debug(f"[BEST-MATCH-REJECT] Rejecting match with 'Opinion of the Court': '{match_text_check}'")
                    continue
                
                # Reject if it's a statute (even with "v."); strip trailing ", YYYY" first
                match_base_check = re.sub(r",\s*(19|20)\d{2}\s*\.?\s*$", "", match_lower_check).strip()
                if match_base_check.endswith((" act", " code", " statute")):
                    logger.debug(f"[BEST-MATCH-REJECT] Rejecting statute: '{match_text_check}'")
                    continue
                
                # Reject if it contains judge attribution
                if re.search(r"\b(dissenting|concurring|J\.\s*,)", match_text_check, re.IGNORECASE):
                    logger.debug(f"[BEST-MATCH-REJECT] Rejecting judge attribution: '{match_text_check}'")
                    continue
                
                # Context-bleeding: reject all-caps header-style match when defendant ends with justice surname
                # e.g. "TRANSUNION LLC v. RAMIREZ THOMAS" (THOMAS, J., dissenting) should not attach to "426 U.S. 26"
                if match_text_check.isupper() and (" v. " in match_text_check or " v " in match_text_check):
                    after_v = re.split(r"\s+v\.?\s+", match_text_check, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
                    # Defendant may have ", Inc." etc.; take first part and last word
                    defendant_clean = re.sub(r",\s*(?:Inc\.|Corp\.|LLC|Ltd\.).*$", "", after_v, flags=re.IGNORECASE).strip()
                    last_word = defendant_clean.split()[-1] if defendant_clean.split() else ""
                    justice_surnames = {
                        "THOMAS", "ALITO", "ROBERTS", "KAVANAUGH", "BARRETT", "GORSUCH", "SOTOMAYOR", "KAGAN",
                        "JACKSON", "KENNEDY", "SCALIA", "GINSBURG", "BREYER", "O'CONNOR", "REHNQUIST", "STEVENS",
                    }
                    if last_word in justice_surnames:
                        logger.debug(
                            f"[BEST-MATCH-REJECT] Rejecting all-caps match with justice surname defendant: '{match_text_check}'"
                        )
                        continue
                
                # Distance from end of context = how far from the citation
                match_end = match.end()
                distance_from_end = context_length - match_end

                if distance_from_end < best_distance:
                    best_distance = distance_from_end
                    best_match = match

            if best_match is None:
                continue

            match = best_match  # Use the closest match to citation
            
            # CRITICAL FIX: Check if the extracted match contains judge attribution
            # If so, try to extract just the case name part, or reject and continue searching
            match_text = match.group(0)
            judge_markers = [
                r"\bJ\.,\s*(dissenting|concurring|concurring in part|concurring in judgment)",
                r"\bJustice\s+\w+,\s*(dissenting|concurring)",
                r",\s*dissenting$",
                r",\s*concurring$",
            ]
            has_judge_attribution = any(re.search(marker, match_text, re.IGNORECASE) for marker in judge_markers)
            
            if has_judge_attribution:
                # Try to extract just the case name part (before the judge attribution)
                # Pattern: "Case Name THOMAS, J., dissenting" -> extract "Case Name"
                cleaned_match = re.split(
                    r",?\s*(?:THOMAS|JUSTICE|J\.|C\.J\.|J\.J\.).*?(?:dissenting|concurring)",
                    match_text,
                    flags=re.IGNORECASE
                )[0].strip()
                
                # Only use cleaned match if it still has "v." and is valid
                if " v. " in cleaned_match and len(cleaned_match) > 5:
                    logger.debug(
                        f"[JUDGE-CLEAN] Extracted '{cleaned_match}' from '{match_text}' "
                        f"(removed judge attribution)"
                    )
                    # Update the match to use cleaned text
                    # We'll process this below, but first check if there's a better match
                    # (a case name closer to the citation without judge attribution)
                    # Continue to see if there are other matches without judge attribution
                    # that are closer to the citation
                    continue  # Skip this match, look for better ones
                else:
                    # Can't salvage, skip this match entirely
                    logger.debug(
                        f"[JUDGE-REJECT] Cannot salvage '{match_text}' "
                        f"(no valid case name after removing judge attribution)"
                    )
                    continue
            # USER FIX: Since we now use expanding windows that start small,
            # we can be more lenient here - the small starting window already ensures proximity
            # The distance threshold should match the context length (which is controlled by the window)
            logger.debug(
                f"[DISTANCE-DEBUG] Pattern {pattern_idx}: best_distance={best_distance}, context_length={context_length}"
            )
            # Accept if the case name ends within the context (distance from end < context length)
            if best_distance > context_length:
                logger.debug(
                    f"[DISTANCE-DEBUG] REJECTED: Match outside context bounds ({best_distance} > {context_length})"
                )
                continue
            else:
                logger.debug(f"[DISTANCE-DEBUG] ACCEPTED: Match within context bounds")

            # NEARBY FRAGMENT GUARD: If the last ~120 chars contain a recent comma
            # followed by a capitalized fragment WITHOUT 'v.', prefer that fragment
            # over an earlier 'v.' match (common in shortened references like
            # "Nat'l Ass'n of Mfrs., 105 F.4th 802").
            try:
                recent = context[-120:]
                comma_idx = recent.rfind(",")
                if comma_idx != -1:
                    fragment = recent[comma_idx + 1 :].strip()
                    # Only consider fragment if it clearly looks like a case name signal
                    has_v = " v. " in fragment.lower()
                    has_prefix = re.search(r"^(in\s+re|ex\s+parte|estate\s+of|matter\s+of)\b", fragment, re.IGNORECASE)
                    if has_v or has_prefix:
                        fragment_abs_start = len(context) - len(recent) + comma_idx + 1
                        if match.end() < fragment_abs_start:
                            frag_clean = re.sub(r"\s+", " ", fragment).strip(' ,;\n()"')
                            if len(frag_clean) >= 5 and re.search(r"[A-Za-z]{3,}", frag_clean):
                                logger.info(
                                    f"[STRICT-EXTRACT] Using nearby case-like fragment: '{frag_clean}' for {citation_text}"
                                )
                                return frag_clean
            except Exception:
                pass

            # REPORTER FAMILY GUARD: If the text between this match and the citation
            # clearly references a different reporter family than the target citation,
            # treat this match as belonging to that other citation and skip it.
            # ENHANCED: Only reject if the match is IMMEDIATELY followed by a different citation
            try:

                def _detect_family(s: str) -> str:
                    s2 = s.lower()
                    if "u.s." in s2 or "supreme court" in s2:
                        return "supreme"
                    elif "s. ct." in s2 or "supreme court reporter" in s2:
                        return "supreme"
                    elif "l. ed." in s2 or "lawyer's edition" in s2:
                        return "supreme"
                    elif "f." in s2 and ("2d" in s2 or "3d" in s2 or "4th" in s2):
                        return "federal"
                    elif "f. supp." in s2:
                        return "federal"
                    elif "p." in s2 and ("2d" in s2 or "3d" in s2):
                        return "pacific"
                    elif "p.3d" in s2:
                        return "pacific"
                    elif "so." in s2 or "south eastern" in s2 or "s.e." in s2:
                        return "southeastern"
                    elif "n.e." in s2 or "northeastern" in s2 or "n.e.2d" in s2:
                        return "northeastern"
                    elif "nw." in s2 or "northwestern" in s2 or "n.w.2d" in s2:
                        return "northwestern"
                    elif "s.w." in s2 or "southwestern" in s2 or "s.w.2d" in s2:
                        return "southwestern"
                    elif "cal." in s2:
                        return "california"
                    elif "n.y." in s2 or "new york" in s2:
                        return "newyork"
                    elif "wn." in s2 or "washington" in s2:
                        return "washington"
                    elif "wash." in s2:
                        return "washington"
                    return "unknown"  # Return string instead of None

                target_fam = _detect_family(citation_text)
                between_seg = context[match.end() :]
                between_fam = _detect_family(between_seg)

                logger.debug(
                    f"[REPORTER-DEBUG] Pattern {pattern_idx}: target_fam='{target_fam}', between_fam='{between_fam}'"
                )

                # ENHANCED: Only reject if the match is IMMEDIATELY followed by a different citation
                # AND there's no evidence this is a parallel citation cluster
                # FIX DEC 2025 v9: Only apply this guard if between_fam is a KNOWN different family
                # If between_fam is 'unknown' (empty/punctuation after match), don't reject - this is normal!
                if between_fam and between_fam != "unknown" and target_fam and between_fam != target_fam:
                    # Check if this looks like a parallel citation cluster
                    # (common pattern: case name, reporter1, page1, reporter2, page2)
                    between_clean = between_seg.strip()

                    # Look for parallel citation patterns like "120 Wn. App. 175, 188," or "140 Wn.2d 19, 32,"
                    # Handle multi-word reporter names (Wn. App., Wn.2d, etc.)
                    parallel_pattern = r"^\s*\d{1,3}\s+(?:[A-Za-z\.]+\s*)*[A-Za-z\.0-9]+\s+\d+(?:\s*,\s*\d+)?\s*,?"
                    if re.match(parallel_pattern, between_clean):
                        logger.debug(f"[REPORTER-DEBUG] ACCEPTED: Detected parallel citation cluster pattern")
                    else:
                        # Check if the different citation is immediately after the match
                        distance_to_next_citation = len(between_seg) - len(between_seg.lstrip()[:20])
                        if distance_to_next_citation < 20:
                            logger.debug(
                                f"[REPORTER-DEBUG] REJECTED: Different citation immediately follows match"
                            )
                            continue
                        else:
                            logger.debug(f"[REPORTER-DEBUG] ACCEPTED: Different citation is far enough away")
                elif between_fam == "unknown":
                    logger.debug(f"[REPORTER-DEBUG] ACCEPTED: No citation detected after match (between_fam=unknown)")

            except Exception as e:
                logger.debug(f"[REPORTER-DEBUG] Exception in reporter family validation: {e}")

            if pattern_idx in [2, 3, 4]:  # Patterns with 2 groups (plaintiff v. defendant)
                # Pattern 1 (index 0) is ship cases with 1 group
                # Patterns 2, 3, 4 (indices 1, 2, 3) have 2 groups (plaintiff v. defendant)
                logger.debug(f"[PATTERN-GROUP-DEBUG] Pattern {pattern_idx}: Processing 2-group pattern")
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                logger.debug(f"[PATTERN-GROUP-DEBUG] Raw groups: plaintiff='{plaintiff}', defendant='{defendant}'")

                # Clean up whitespace and newlines
                plaintiff = re.sub(r"\s+", " ", plaintiff).strip(" ,;\n")
                defendant = re.sub(r"\s+", " ", defendant).strip(" ,;\n")

                # Fix corporate name punctuation: "Spokeo , Inc." -> "Spokeo, Inc."
                plaintiff = re.sub(r"\s+,\s+", ", ", plaintiff)
                defendant = re.sub(r"\s+,\s+", ", ", defendant)

                # Remove trailing incomplete words (truncation artifacts)
                plaintiff = re.sub(r"\s+[a-z]{1,2}$", "", plaintiff)  # "Name v. Ca" -> "Name v."
                defendant = re.sub(r"\s+[a-z]{1,2}$", "", defendant)

                # Check for truncation at start (lowercase start indicates truncation)
                if plaintiff and plaintiff[0].islower():
                    logger.warning(f"[STRICT-EXTRACT] Detected truncated plaintiff: '{plaintiff}'")
                    # Try to extract actual case name from the truncated text
                    # Look for capitalized words that could be the actual case name
                    actual_plaintiff = None

                    # Pattern 1: Look for "in [CaseName]" pattern
                    in_match = re.search(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", plaintiff)
                    if in_match:
                        actual_plaintiff = in_match.group(1)
                        logger.info(
                            f"[STRICT-EXTRACT] Extracted actual plaintiff from 'in' pattern: '{actual_plaintiff}'"
                        )

                    # Pattern 2: Look for last capitalized word(s) before "v."
                    if not actual_plaintiff:
                        # Find all capitalized words
                        cap_words = re.findall(r"\b[A-Z][a-z]+\b", plaintiff)
                        if cap_words:
                            # Use the last capitalized word as most likely to be the case name
                            actual_plaintiff = cap_words[-1]
                            # If there are multiple capitalized words at the end, include them
                            if len(cap_words) >= 2:
                                # Check if the last two words form a better case name
                                last_two = " ".join(cap_words[-2:])
                                if len(last_two) > 5:  # Reasonable case name length
                                    actual_plaintiff = last_two
                            logger.info(
                                f"[STRICT-EXTRACT] Extracted actual plaintiff from capitalized words: '{actual_plaintiff}'"
                            )

                    # Pattern 3: Look for words before "v." that might be the case name
                    if not actual_plaintiff:
                        v_match = re.search(r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+v\.", plaintiff)
                        if v_match:
                            actual_plaintiff = v_match.group(1)
                            logger.info(
                                f"[STRICT-EXTRACT] Extracted actual plaintiff from 'v.' pattern: '{actual_plaintiff}'"
                            )

                    if actual_plaintiff and len(actual_plaintiff) > 2:
                        plaintiff = actual_plaintiff
                        logger.info(f"[STRICT-EXTRACT] Using extracted plaintiff: '{plaintiff}'")
                    else:
                        continue  # Skip this match, try other patterns

                if defendant and defendant[0].islower():
                    logger.warning(f"[STRICT-EXTRACT] Detected truncated defendant: '{defendant}'")
                    continue

                # Heuristic: restore governmental prefixes if present in recent context
                # FIX DEC 2025 v10: Only apply when plaintiff IS the location, not when it CONTAINS it
                # e.g., don't replace "Seattle TV LLC" with "City of Seattle" just because it contains "Seattle"
                try:
                    recent_ctx = context[-220:]
                    mgov = re.search(
                        r"(County|City|Township|Borough)\s+of\s+([A-Z][A-Za-z\.'\-]+)", recent_ctx, flags=re.IGNORECASE
                    )
                    if mgov:
                        loc = mgov.group(2)
                        # Only apply if plaintiff is EXACTLY the location name (not containing other words)
                        if plaintiff.lower() == loc.lower():
                            # Rebuild with normalized casing
                            gov_word = mgov.group(1).capitalize()
                            loc_word = loc[0].upper() + loc[1:]
                            plaintiff = f"{gov_word} of {loc_word}"
                            logger.debug(f"[GOV-PREFIX-FIX] Restored prefix: '{plaintiff}'")
                except Exception:
                    pass

                # Trim plaintiff to text after the last sentence boundary to remove narrative prefixes
                try:
                    boundaries = []
                    for token in [". ", "; ", "-"]:
                        idx = plaintiff.rfind(token)
                        if idx != -1:
                            boundaries.append(idx + (2 if token in [". ", "; "] else 1))
                    if boundaries:
                        cut = max(boundaries)
                        tail = plaintiff[cut:].strip()
                        if tail and re.match(r"^[A-Z]", tail):
                            plaintiff = tail
                except Exception:
                    pass

                # Strip caption/docket role tokens that are not part of party names
                try:

                    def _strip_caption_roles(s: str) -> str:
                        # VERBATIM MODE: return text unchanged (no stripping)
                        return s

                    plaintiff = _strip_caption_roles(plaintiff)
                    defendant = _strip_caption_roles(defendant)
                except Exception:
                    pass
                case_name = f"{plaintiff} v. {defendant}"
                
                # FIX JAN 2026: Clean up signal words at the start of case names
                # This handles cases like "See also, e.g., Alexander v. ..." where signal words are captured
                signal_words = ["see also", "see", "cf.", "e.g.", "accord", "compare", "but see", "quoting"]
                case_name_lower = case_name.lower()
                for signal in signal_words:
                    if case_name_lower.startswith(signal):
                        # Remove the signal word and following punctuation/spaces
                        case_name = case_name[len(signal):].strip(" ,;")
                        break

                # CRITICAL FIX: Reject document header patterns
                # These patterns indicate the extracted name is from a document header/caption, not a citation
                # IMPORTANT: Only reject if the EXTRACTED NAME contains header text (role words, docket numbers, etc.)
                # - Legitimate case names like "Erickson v. Pharmacia" should NOT be rejected
                # - Case names split across headers/footnotes (like "Singh v. Edwards Lifesciences Corp.")
                #   should be found correctly because headers/footnotes are filtered from context BEFORE extraction
                # - These patterns only check the FINAL extracted name, not the context
                header_patterns = [
                    # Pattern 1: "ET AL., Petitioners" anywhere in the name (MOST COMMON)
                    r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # "ET AL., Petitioners"
                    # Pattern 1b: "ET AL" followed by role word anywhere (more flexible)
                    r"ET\s+AL\.?\s*[^,]*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # "ET AL ... Petitioners"
                    # Pattern 2: "Petitioners, NO. 103135-1" or "Respondent. NO. 103135-1"
                    r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*\d",  # "Petitioners, NO. 103135-1" or "Respondent. NO. 103135-1"
                    # Pattern 3: "Respondent. NO" (with period, no number) - CRITICAL for catching "Respondent. NO"
                    r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\b",  # "Respondent. NO" or "Petitioners, NO"
                    # Pattern 4: "NO. 103135-1 v." pattern
                    r"\bNO\.?\s*\d+.*v\.",  # "NO. 103135-1 v." pattern
                    # Pattern 5: All caps (20+ chars) with docket number - document headers are usually all caps
                    r"^[A-Z\s]{20,}\s+NO\.?\s*\d",  # All caps (20+ chars) with docket number
                    # Pattern 6: All caps with role word and NO
                    r"^[A-Z\s]{20,}.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*NO\b",  # All caps with role word and NO
                    # Pattern 7: "ET AL., Petitioners, v. ... Respondent. NO" pattern (full header format)
                    r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b",  # "ET AL., Petitioners, v. ... Respondent. NO"
                    # Pattern 8: All-caps header format with both role words
                    r"^[A-Z][A-Z\s]{30,}.*ET\s+AL\.?\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # All caps with ET AL and role word
                    # Pattern 9: ENHANCED - Catch "ET AL., Petitioners, v. ... Respondent. NO" with any spacing
                    r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO",  # "ET AL., Petitioners, v. ... Respondent. NO"
                    # Pattern 10: ENHANCED - Catch case names that END with "Respondent. NO" or similar
                    r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*$",  # Ends with "Respondent. NO" or "Petitioners, NO"
                    # Pattern 11: CRITICAL - Catch "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO"
                    r"[A-Z]+\s+ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+[A-Z]+\s+(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?",  # "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO"
                    # Pattern 12: Federal docket caption bleed (e.g. "Ill. Union Ins. Co. No. C10-5943 RJB Milgard Mfg., Inc. v. Ill")
                    r"(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+",  # Corporate + federal docket
                ]

                # CRITICAL: Check patterns case-insensitively
                # FIRST: Simple check - if name contains both "ET AL" and a role word, it's likely a header
                case_name_upper = case_name.upper()
                has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
                has_role_word = any(
                    role in case_name_upper
                    for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                )
                has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

                # CRITICAL: Check for the exact header pattern first (most specific)
                # Pattern: "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO" or similar
                if has_et_al and has_role_word:
                    # Check if it contains both "ET AL" and multiple role words (Petitioners AND Respondent)
                    # This is the signature of a document header
                    role_word_count = sum(
                        1
                        for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                        if role in case_name_upper
                    )
                    if role_word_count >= 2:
                        logger.warning(f"[STRICT-EXTRACT] REJECTED header (ET AL + multiple role words): '{case_name}'")
                        return None
                    # Also reject if it has ET AL + role word + NO
                    if has_no:
                        logger.warning(f"[STRICT-EXTRACT] REJECTED header (ET AL + role word + NO): '{case_name}'")
                        return None
                    # Reject if it has ET AL + role word (even without NO, this is almost always a header)
                    logger.warning(f"[STRICT-EXTRACT] REJECTED header (ET AL + role word): '{case_name}'")
                    return None

                # If it has a role word and NO, it's almost certainly a header
                if has_role_word and has_no:
                    logger.warning(
                        f"[STRICT-EXTRACT] REJECTED header (role word + NO): '{case_name}' (has_role_word={has_role_word}, has_no={has_no})"
                    )
                    return None

                # THEN: Check detailed patterns
                for pattern in header_patterns:
                    if re.search(pattern, case_name, re.IGNORECASE):
                        logger.warning(
                            f"[STRICT-EXTRACT] REJECTED document header pattern: '{case_name}' (matched pattern: {pattern})"
                        )
                        return None  # CRITICAL FIX: Return None immediately, don't try next pattern
                logger.debug(
                    f"[EXTRACTION-DEBUG] Built case name: '{case_name}' from plaintiff='{plaintiff}', defendant='{defendant}'"
                )

            else:  # Single-group patterns (In re, Ex parte, fallback)
                case_name = match.group(1).strip(' ,;\n()"')
                # Clean up whitespace
                case_name = re.sub(r"\s+", " ", case_name)

            # === VALIDATION ===

            # CRITICAL FIX: Reject document header patterns (applies to all case names)
            # These patterns indicate the extracted name is from a document header/caption, not a citation
            # IMPORTANT: Only reject if the pattern contains ROLE WORDS (Petitioners, Respondents, etc.)
            # or DOCKET NUMBERS (NO. 103135-1) - legitimate case names like "Erickson v. Pharmacia"
            # should NOT be rejected even if they match the document's primary case name
            # This allows the same case to be cited multiple times (e.g., lower court and appellate opinions)
            header_patterns = [
                # Pattern 1: "ET AL., Petitioners" anywhere in the name (MOST COMMON)
                r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # "ET AL., Petitioners"
                # Pattern 1b: "ET AL" followed by role word anywhere (more flexible)
                r"ET\s+AL\.?\s*[^,]*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # "ET AL ... Petitioners"
                # Pattern 2: "Petitioners, NO. 103135-1" or "Respondent. NO. 103135-1"
                r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*\d",  # "Petitioners, NO. 103135-1" or "Respondent. NO. 103135-1"
                # Pattern 3: "Respondent. NO" (with period, no number) - CRITICAL for catching "Respondent. NO"
                r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\b",  # "Respondent. NO" or "Petitioners, NO"
                # Pattern 4: "NO. 103135-1 v." pattern
                r"\bNO\.?\s*\d+.*v\.",  # "NO. 103135-1 v." pattern
                # Pattern 5: All caps (20+ chars) with docket number - document headers are usually all caps
                r"^[A-Z\s]{20,}\s+NO\.?\s*\d",  # All caps (20+ chars) with docket number
                # Pattern 6: All caps with role word and NO
                r"^[A-Z\s]{20,}.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*NO\b",  # All caps with role word and NO
                # Pattern 7: "ET AL., Petitioners, v. ... Respondent. NO" pattern (full header format)
                r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b",  # "ET AL., Petitioners, v. ... Respondent. NO"
                # Pattern 8: All-caps header format with both role words
                r"^[A-Z][A-Z\s]{30,}.*ET\s+AL\.?\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # All caps with ET AL and role word
                # Pattern 9: ENHANCED - Catch "ET AL., Petitioners, v. ... Respondent. NO" with any spacing
                r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO",  # "ET AL., Petitioners, v. ... Respondent. NO"
                # Pattern 10: ENHANCED - Catch case names that END with "Respondent. NO" or similar
                r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*$",  # Ends with "Respondent. NO" or "Petitioners, NO"
                # Pattern 11: CRITICAL - Catch "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO"
                r"[A-Z]+\s+ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+[A-Z]+\s+(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?",  # "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO"
                # Pattern 12: Federal docket caption bleed (e.g. "Ill. Union Ins. Co. No. C10-5943 RJB Milgard Mfg., Inc. v. Ill")
                r"(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+",  # Corporate + federal docket
            ]

            # CRITICAL: Check patterns case-insensitively
            # FIRST: Simple check - if name contains "ET AL" anywhere, reject immediately (most reliable indicator)
            case_name_upper = case_name.upper()
            has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
            has_role_word = any(
                role in case_name_upper
                for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
            )
            has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

            # ULTRA-AGGRESSIVE CHECK: If the extracted name contains BOTH "ET AL" AND a role word, it's DEFINITELY a header
            # This catches "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO" and all variations
            if has_et_al and has_role_word:
                logger.debug(f"[STRICT-EXTRACT] REJECTED header (ET AL + role word): '{case_name}'")
                return None

            # If it has a role word and NO, it's almost certainly a header
            if has_role_word and has_no:
                logger.debug(
                    f"[STRICT-EXTRACT] REJECTED header (role word + NO): '{case_name}'"
                )
                return None

            # ADDITIONAL CHECK: Count role words - if there are 2+ role words, it's almost certainly a header
            # (e.g., "Petitioners" and "Respondent" both appear)
            role_word_count = sum(
                1
                for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                if role in case_name_upper
            )
            if role_word_count >= 2:
                logger.debug(
                    f"[STRICT-EXTRACT] REJECTED header (multiple role words: {role_word_count}): '{case_name}'"
                )
                return None

            # CRITICAL FIX: Reject case names that start with "Opinion of the Court" or similar header text
            # Examples: "Opinion of the Court Sprint Communications Co. v. APCC Services"
            # These are header text contamination, not actual case names
            header_text_patterns = [
                r"^Opinion\s+of\s+the\s+Court\s+",
                r"^Opinion\s+of\s+the\s+",
                r"\bOpinion\s+of\s+the\s+Court\s+",
            ]
            for pattern in header_text_patterns:
                if re.search(pattern, case_name, re.IGNORECASE):
                    logger.warning(
                        f"[STRICT-EXTRACT] REJECTED header text contamination: '{case_name}' "
                        f"(contains 'Opinion of the Court')"
                    )
                    return None  # Reject immediately
            
            # THEN: Check detailed patterns
            for pattern in header_patterns:
                if re.search(pattern, case_name, re.IGNORECASE):
                    logger.warning(
                        f"[STRICT-EXTRACT] REJECTED document header pattern: '{case_name}' (matched pattern: {pattern})"
                    )
                    return None  # CRITICAL FIX: Return None immediately, don't continue to next pattern

            # Minimum length
            if len(case_name) < 5:
                continue

            # Must contain actual letters
            if not re.search(r"[A-Za-z]{3,}", case_name):
                continue

            # Reject if it's just a legal action word
            legal_action_words = [
                "vacated",
                "affirmed",
                "reversed",
                "remanded",
                "dismissed",
                "granted",
                "denied",
                "overruled",
                "modified",
                "stayed",
                "amended",
            ]
            if case_name.lower().strip() in legal_action_words:
                continue

            # Reject common non-case-name phrases
            reject_phrases = [
                "we do not",
                "this holding",
                "the court",
                "decision in",
                "holding that",
                "pursuant to",
                "under",
                "based on",
                "principles set forth",
                "intervening decision",
                "recused",
                "at common law",
                "determining the amount",
                "within the province",
            ]
            if any(phrase in case_name.lower() for phrase in reject_phrases):
                continue

            # Reject if starts with common sentence starters
            # EXCEPTION: Ship/admiralty cases legitimately start with "The" (e.g., "The Pizarro")
            is_ship_case = case_name.startswith("The ") and not " v. " in case_name
            
            sentence_starters = [
                "at ",
                "this ",
                "that ",
                "these ",
                "those ",
                "in ",
                "for ",
                "with ",
                "without ",
                "under ",
                "over ",
                "determining ",
                "establishing ",
                "calculating ",
            ]
            # Only add "the " to reject list if it's NOT a ship case
            if not is_ship_case:
                sentence_starters.append("the ")
            
            case_lower = case_name.lower()
            if any(case_lower.startswith(starter) for starter in sentence_starters):
                # Unless it's a valid case name pattern (has "v.")
                if " v. " not in case_lower:
                    continue

            # For "v." patterns, validate both party names
            if " v. " in case_name.lower():
                parts = re.split(r"\s+v\.\s+", case_name, flags=re.IGNORECASE)
                if len(parts) != 2:
                    continue

                plaintiff_part = parts[0].strip()
                defendant_part = parts[1].strip()

                # Both parties must have meaningful length
                if len(plaintiff_part) < 2 or len(defendant_part) < 2:
                    continue

                # Check for incomplete/truncated parties
                # USER FIX 2024-10-17: Allow common abbreviations like Cmty., Ass'n, Dep't
                # ENHANCED: Allow trailing commas for valid case names (common in legal citations)
                if plaintiff_part.endswith((".", ",")) or defendant_part.endswith((".", ",")):
                    combined = plaintiff_part + defendant_part
                    logger.debug(
                        f"[VALIDATION-DEBUG] Checking trailing punctuation: '{plaintiff_part}' + '{defendant_part}' = '{combined}'"
                    )

                    # Check if this is a valid case name with reasonable structure
                    has_valid_plaintiff = len(plaintiff_part.rstrip(".,")) >= 2 and re.search(
                        r"[A-Za-z]{2,}", plaintiff_part
                    )
                    has_valid_defendant = len(defendant_part.rstrip(".,")) >= 2 and re.search(
                        r"[A-Za-z]{2,}", defendant_part
                    )

                    # Allow trailing commas if both parties are valid and not just single letters
                    if (
                        (plaintiff_part.endswith(",") or defendant_part.endswith(","))
                        and has_valid_plaintiff
                        and has_valid_defendant
                    ):
                        logger.error(f"[VALIDATION-DEBUG] ACCEPTED: Valid case name with trailing comma")
                        # Clean the trailing comma for final output
                        plaintiff = plaintiff_part.rstrip(".,")
                        defendant = defendant_part.rstrip(".,")
                    elif not re.search(r"(Inc|LLC|Corp|Co|Ltd|Cmty|Ass'n|Dep't|Dept|Bd|Dist|Comm|Div)", combined):
                        logger.debug(
                            f"[VALIDATION-DEBUG] REJECTED: Trailing punctuation without known abbreviation or valid structure"
                        )
                        continue  # Suspicious punctuation unless it's corporate or known abbreviation
                    else:
                        logger.debug(f"[VALIDATION-DEBUG] ACCEPTED: Found known abbreviation in combined name")

            # If we reach here and there is no 'v.' and not an accepted prefix (In re, Ex parte, Estate of, Matter of, The [Ship]), reject to avoid narrative fragments
            if " v. " not in case_name.lower():
                # Ship/admiralty cases start with "The" (e.g., "The Pizarro", "The Venus")
                is_ship_case_pattern = re.match(r"^The\s+[A-Z][a-zA-Z]+", case_name)
                if not re.search(r"^(In\s+re|Ex\s+parte|Estate\s+of|Matter\s+of)\b", case_name, re.IGNORECASE) and not is_ship_case_pattern:
                    logger.debug(f"[STRICT-EXTRACT] Rejecting non-case-like fragment: '{case_name}'")
                    continue

            # === FINAL CLEANUP ===

            # USER FIX 2025-11-07: Verbatim mode - do not clean or normalize case_name
            case_name = case_name

            if len(case_name) >= 5:
                # FINAL SAFETY CHECK: Reject header patterns one more time before returning
                # This is a last-ditch check to ensure no header slips through
                case_name_upper_final = case_name.upper()

                # ENHANCED: More comprehensive header detection
                # Check for "ET AL" (with or without punctuation)
                has_et_al_final = (
                    "ET AL" in case_name_upper_final
                    or "ETAL" in case_name_upper_final.replace(" ", "").replace(".", "").replace(",", "")
                    or re.search(r"ET\s+AL\.?", case_name_upper_final)
                )

                # Check for role words (including plurals)
                role_patterns = [r"PETITIONER", r"RESPONDENT", r"APPELLANT", r"APPELLEE", r"PLAINTIFF", r"DEFENDANT"]
                has_role_word_final = any(re.search(role, case_name_upper_final) for role in role_patterns)

                # Check for "NO" or "NO." (docket number indicator)
                has_no_final = (
                    "NO." in case_name_upper_final
                    or " NO " in case_name_upper_final
                    or case_name_upper_final.endswith(" NO")
                    or re.search(r"\bNO\.?\s*\d+", case_name_upper_final)  # "NO 12345" or "NO. 12345"
                )

                # ENHANCED: Also check for specific header patterns
                # Pattern: "ET AL., Petitioners, v. ... Respondent. NO"
                header_pattern_match = re.search(
                    r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                    case_name_upper_final,
                )

                # Pattern: Case name ending with role word and NO
                role_no_pattern = re.search(
                    r"(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT).*NO\.?", case_name_upper_final
                )

                # Reject if it's clearly a header
                is_header = (
                    (has_et_al_final and has_role_word_final)
                    or (has_role_word_final and has_no_final)
                    or header_pattern_match is not None
                    or role_no_pattern is not None
                )

                if is_header:
                    logger.debug(f"[STRICT-EXTRACT-FINAL-REJECT] REJECTED header pattern in final check: '{case_name}'")
                    return None  # CRITICAL FIX: Return None immediately, don't try next pattern

                # USER FIX 2026-01-27: Final validation - reject statutes, dissenting opinions, and header text
                case_name_lower = case_name.lower()
                
                # CRITICAL: Reject "Opinion of the Court" contamination
                if "opinion of the court" in case_name_lower:
                    logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED 'Opinion of the Court' contamination: '{case_name}'")
                    continue
                
                # Reject statute names (even if they somehow contain "v.")
                # CRITICAL FIX 2026-01-29: Use a flag to properly skip to next match
                should_skip_match = False

                if " v. " not in case_name_lower:
                    statute_endings = [" act", " code", " statute", " regulation", " rule"]
                    if any(case_name_lower.endswith(ending) for ending in statute_endings):
                        logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED statute name: '{case_name}'")
                        should_skip_match = True

                    if not should_skip_match:
                        # Check for common statute patterns
                        statute_patterns = [
                            r"\b(administrative procedure|freedom of information|civil rights|voting rights|fair housing)\s+act\b",
                            r"\bunited states code\b",
                            r"\bfederal\s+code\s+of\s+regulations\b",
                        ]
                        for pattern in statute_patterns:
                            if re.search(pattern, case_name_lower):
                                logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED statute pattern: '{case_name}'")
                                should_skip_match = True
                                break  # Exit the inner loop
                else:
                    # Even if it has "v.", check if it's a statute name incorrectly matched
                    # Example: "Administrative Procedure Act" might match as "Administrative Procedure v. Act"
                    statute_patterns_in_name = [
                        r"administrative procedure",
                        r"freedom of information",
                    ]
                    for pattern in statute_patterns_in_name:
                        if re.search(pattern, case_name_lower) and ("act" in case_name_lower or "code" in case_name_lower):
                            logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED statute (even with 'v.'): '{case_name}'")
                            should_skip_match = True
                            break  # Exit the inner loop

                    # Also check if the name ends with "Act" or "Code" even with "v."
                    if not should_skip_match and case_name_lower.endswith((" act", " code", " statute")):
                        logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED statute ending: '{case_name}'")
                        should_skip_match = True

                if should_skip_match:
                    continue  # Skip to next match

                # Reject judge attribution/dissenting opinions
                judge_markers = [
                    r"\bJ\.,\s*(dissenting|concurring|concurring in part|concurring in judgment)",
                    r"\bJustice\s+\w+,\s*(dissenting|concurring)",
                    r",\s*dissenting$",
                    r",\s*concurring$",
                    r"\bdissenting\b",  # Anywhere in the name
                    r"\bconcurring\b",  # Anywhere in the name
                    r",\s*J\.\s*,",  # "THOMAS, J.," pattern
                ]
                for marker in judge_markers:
                    if re.search(marker, case_name, re.IGNORECASE):
                        logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED judge attribution: '{case_name}' (marker: {marker})")
                        should_skip_match = True
                        break  # Exit the inner loop

                if should_skip_match:
                    continue  # Skip to next match
                
                # USER FIX 2026-01-27: Final cleanup - remove any remaining "Opinion of the Court" text
                # This is a last-ditch check in case it wasn't caught earlier
                case_name_cleaned = re.sub(r"\s*Opinion\s+of\s+the\s+Court\s+", " ", case_name, flags=re.IGNORECASE)
                case_name_cleaned = re.sub(r"\s+", " ", case_name_cleaned).strip()
                
                # If cleaning removed significant content, use cleaned version
                if case_name_cleaned != case_name and len(case_name_cleaned) >= 5:
                    logger.warning(f"[STRICT-EXTRACT-CLEANUP] Cleaned 'Opinion of the Court' from '{case_name}' -> '{case_name_cleaned}'")
                    case_name = case_name_cleaned
                
                # Final check - reject if it still contains "Opinion of the Court"
                if "opinion of the court" in case_name.lower():
                    logger.warning(f"[STRICT-EXTRACT-FINAL] REJECTED - still contains 'Opinion of the Court': '{case_name}'")
                    continue
                
                logger.info(
                    f"[STRICT-EXTRACT] Extracted '{case_name}' for {citation_text} " f"using pattern {pattern_idx}"
                )
                # Reject if extracted name is the citation or part of it (not a case name)
                if _is_citation_or_part_of_citation(case_name, citation_text):
                    logger.warning(
                        f"[STRICT-EXTRACT] REJECTED (citation or part of citation): '{case_name}' for {citation_text}"
                    )
                    continue
                logger.debug(f"[FINAL-DEBUG] RETURNING case name: '{case_name}' for {citation_text}")
                return case_name
            else:
                logger.debug(
                    f"[FINAL-DEBUG] REJECTED case name too short: '{case_name}' ({len(case_name)} chars) for {citation_text}"
                )

        except Exception as e:
            logger.debug(f"[STRICT-EXTRACT] Pattern {pattern_idx} failed: {e}")

    logger.debug(f"[STRICT-EXTRACT] No case name found for {citation_text}")
    # CRITICAL FIX 2026-01-29: If context ends with citation fragment like ", (10 Tenn.), 1831",
    # strip it and use the remaining context for fallback so we get "Swindle v. State".
    fragment_at_end = re.compile(
        r",\s*\(\d+\s*(?:Tenn\.|Va\.|U\.\s*S\.|F\.|P\.|Wn\.|Ill\.|Ohio)\b[^)]*\),\s*\d{4}\s*$",
        re.IGNORECASE,
    )
    if context and fragment_at_end.search(context):
        context = fragment_at_end.sub("", context).strip().rstrip(",").strip()
        logger.info(
            f"[STRICT-EXTRACT-FRAGMENT-STRIP] Stripped citation fragment from context for {citation_text}, "
            f"trying fallback on remaining context"
        )
    # Fallback: capture '... v. ...,' immediately before the citation (common formatting)
    # FIX 2026-01-29: Allow comma + "(" (parenthetical citation) so "Swindle v. State, (10 Tenn.), 1831" matches
    try:
        recent = context[-160:]
        # Stop defendant at ', No.' or comma-before-reporter or comma-before-parenthetical or end; non-greedy capture
        m = re.search(
            r"([A-Z][^,;()]{2,120})\s+v\.\s+([^,;()]{2,120}?)(?=,\s*(?:\d|No\b|\(|$)|\s*$)\s*,?\s*$",
            recent,
        )
        if m:
            plaintiff = re.sub(r"\s+", " ", m.group(1)).strip(" ,;\n")
            defendant = re.sub(r"\s+", " ", m.group(2)).strip(" ,;\n")
            # Trim narrative prefixes from plaintiff using last sentence/delimiter boundary
            try:
                boundaries = []
                for token in [". ", "; ", "-"]:
                    idx = plaintiff.rfind(token)
                    if idx != -1:
                        boundaries.append(idx + (2 if token in [". ", "; "] else 1))
                if boundaries:
                    cut = max(boundaries)
                    tail = plaintiff[cut:].strip()
                    if tail and re.match(r"^[A-Z]", tail):
                        plaintiff = tail
            except Exception:
                pass
            if len(plaintiff) >= 2 and len(defendant) >= 2:
                fallback_name = f"{plaintiff} v. {defendant}"

                # Apply accuracy improvements to fallback as well
                # VERBATIM MODE: do not alter fallback_name beyond boundary trims

                # USER FIX 2026-01-27: Validate fallback name too
                fallback_lower = fallback_name.lower()

                # Reject statutes (including "X Act, 1970" by normalizing trailing year)
                if _is_statute_name_not_case_name(fallback_name):
                    logger.warning(f"[STRICT-EXTRACT-FALLBACK] REJECTED statute: '{fallback_name}'")
                    return None
                if " v. " not in fallback_lower:
                    statute_endings = [" act", " code", " statute", " regulation", " rule"]
                    if any(fallback_lower.endswith(ending) for ending in statute_endings):
                        logger.warning(f"[STRICT-EXTRACT-FALLBACK] REJECTED statute: '{fallback_name}'")
                        return None
                
                # Reject dissenting opinions
                judge_markers = [
                    r"\bJ\.,\s*(dissenting|concurring)",
                    r",\s*dissenting$",
                    r"\bdissenting\b",
                ]
                for marker in judge_markers:
                    if re.search(marker, fallback_name, re.IGNORECASE):
                        logger.warning(f"[STRICT-EXTRACT-FALLBACK] REJECTED judge attribution: '{fallback_name}'")
                        return None
                
                # Reject if fallback name is the citation or part of it
                if _is_citation_or_part_of_citation(fallback_name, citation_text):
                    logger.warning(
                        f"[STRICT-EXTRACT-FALLBACK] REJECTED (citation or part of citation): '{fallback_name}' for {citation_text}"
                    )
                    return None
                
                logger.debug(f"[STRICT-EXTRACT:FALLBACK] Extracted '{fallback_name}' for {citation_text}")
                return fallback_name
    except Exception:
        pass
    return None


def extract_with_strict_isolation(text: str, citations: List[Any], force_reextract: bool = False) -> Dict[str, str]:
    """
    Extract case names for all citations with strict context isolation.

    This prevents case name bleeding between nearby citations.

    Args:
        text: Full document text
        citations: List of citation objects (must have citation, start_index, end_index attributes)
        force_reextract: If True, re-extract even if extracted_case_name exists

    Returns:
        Dictionary mapping citation text to extracted case name
    """
    # Pre-compute all citation positions for efficient boundary detection
    all_positions = find_all_citation_positions(text)

    results = {}

    for citation in citations:
        citation_text = getattr(citation, "citation", None)
        start = getattr(citation, "start_index", None)
        end = getattr(citation, "end_index", None)

        if not citation_text or start is None or end is None:
            continue

        # Skip if already has good extraction
        existing_name = getattr(citation, "extracted_case_name", None)
        if existing_name and len(existing_name) > 10 and not force_reextract:
            results[citation_text] = existing_name
            continue

        # Get strictly isolated context
        strict_context = get_strict_context_for_citation(
            text, start, end, all_positions, max_lookback=100  # Reduced from 200 to 100
        )

        # Extract case name from isolated context
        case_name = extract_case_name_from_strict_context(strict_context, citation_text)

        if case_name:
            results[citation_text] = case_name
            # Update the citation object
            citation.extracted_case_name = case_name
            logger.info(f"[STRICT-ISOLATION] {citation_text} -> '{case_name}'")
        else:
            logger.warning(f"[STRICT-ISOLATION] Failed to extract for {citation_text}")

    return results


__all__ = [
    "find_all_citation_positions",
    "get_strict_context_for_citation",
    "get_adaptive_context_for_citation",
    "get_context_before_citation_in_text",
    "extract_case_name_from_strict_context",
    "extract_with_strict_isolation",
    "is_citation_fragment_not_case_name",
    "is_citation_or_part_of_citation",
]


def is_citation_fragment_not_case_name(name: str) -> bool:
    """Public wrapper for _is_citation_fragment_not_case_name. Use when building/displaying extracted names."""
    return _is_citation_fragment_not_case_name(name)


def is_citation_or_part_of_citation(extracted_name: str, citation_text: str) -> bool:
    """Public wrapper. Returns True if extracted_name is the citation or part of it; use at extraction to reject."""
    return _is_citation_or_part_of_citation(extracted_name, citation_text)
