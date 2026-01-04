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
    ]

    for pattern in additional_header_patterns:
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
    "Dep't of Ecology" → "Department of Ecology"
    "Lakeside Indus." → "Lakeside Industries"
    "Bd. of Regents" → "Board of Regents"
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
    "Rozner v. Bellevue" → "Rozner v. City of Bellevue" (if "City of Bellevue" appears in context)
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
    3. If N/A, expands window progressively (25 → 50 → 75 → 100 → max)
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
    logger.error(f"[BACKWARDS-EXTRACT] Starting backwards extraction for citation at {citation_start}")

    # USER FIX: Progressive window sizes - start small and expand only if needed
    # This ensures we get the CLOSEST case name to the citation first
    # FIX DEC 2025 v10: Increased initial windows to capture longer corporate names
    # like "Fisher Broad.–Seattle TV LLC v. City of Seattle" (56 chars)
    window_sizes = [60, 80, 100, 125, max_lookback]

    for window_size in window_sizes:
        # Get context with current window size
        context = get_strict_context_for_citation(
            text, citation_start, citation_end, all_citation_positions, window_size
        )

        logger.error(f"[BACKWARDS-EXTRACT] Window {window_size}: context='{context[-60:] if context else 'EMPTY'}'")

        # Check if this context contains a case name
        if _contains_case_name(context):
            logger.error(f"[BACKWARDS-EXTRACT] Found case name in {window_size} char window")
            return context
        else:
            logger.error(f"[BACKWARDS-EXTRACT] No case name in {window_size} char window, expanding...")

    # If no case name found in any window, return the largest context
    # The caller will handle the N/A case and use canonical fallback
    logger.error(f"[BACKWARDS-EXTRACT] No case name found after all expansions, returning max context")
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

    # Common case name patterns
    case_patterns = [
        r"\b[A-Z][a-zA-Z\'\.\&]*\s+v\.?\s+[A-Z][a-zA-Z\'\.\&]*",  # X v. Y
        r"\bIn\s+re\s+[A-Z][a-zA-Z\'\.\&]*",  # In re X
        r"\bState(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*)?\s+v\.?\s+[A-Z][a-zA-Z\'\.\&]*",  # State v. Y
        r"\bCity\s+of\s+[A-Z][a-zA-Z\'\.\&]*\s+v\.?\s+[A-Z][a-zA-Z\'\.\&]*",  # City of X v. Y
    ]

    context_lower = context.lower()

    # Skip if context looks like it's from a different citation
    skip_patterns = [
        r"\b\d+\s+[a-z\.]+\s+\d+",  # Contains another citation
        r"\bid\.?\b",  # Contains "id." or "id"
        r"\bsupra\b",  # Contains "supra"
        r"\bsee\b",  # Contains "see"
    ]

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
    closest_citation_start = None

    for pos_start, pos_end, cit_text in all_citation_positions:
        # Skip if this is the same citation or after it
        if pos_start >= citation_start:
            continue

        # Calculate distance from this citation to our target citation
        distance = citation_start - pos_end

        # Track the closest citation
        if distance < closest_citation_distance:
            closest_citation_distance = distance
            closest_citation_start = pos_start
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
    logger.error(f"[HARD-BOUNDARY] Previous citation ends at {closest_citation_end}, using as HARD boundary")
    logger.error(f"[HARD-BOUNDARY] Distance to previous citation: {closest_citation_distance} chars")

    # The boundary is the END of the closest previous citation - NO EXCEPTIONS
    if closest_citation_end > 0:
        previous_boundary = closest_citation_end
        logger.error(f"[HARD-BOUNDARY] Set boundary to {previous_boundary}")

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

    # Additional boundary trimming to prefer the nearest case segment
    # If there's a semicolon-separated series, keep only the segment AFTER the last semicolon
    # within a reasonable proximity window to the citation (prevents pulling prior cases).
    if strict_context:
        # Always keep only the segment AFTER the last semicolon to avoid pulling
        # case names from earlier clauses in multi-citation sentences.
        last_sc = strict_context.rfind(";")
        if last_sc != -1:
            strict_context = strict_context[last_sc + 1 :].strip()

        # Also trim after the last em-dash or long dash which often separates cites
        # FIX DEC 2025 v10: Don't trim if dash is part of a case name (followed by corporate suffix)
        for dash in ("—", "–", "--"):
            last_dash = strict_context.rfind(dash)
            if last_dash != -1:
                after_dash = strict_context[last_dash + 1 :].strip()[:25].lower()
                is_part_of_name = any(
                    s in after_dash for s in ["llc", "inc", "corp", "ltd", "co.", " tv ", "radio", "broadcast"]
                )
                if is_part_of_name:
                    logger.error(f"[DASH-TRIM-SKIP] Dash part of case name: '{strict_context}'")
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
    # DEBUG: Log every call to track if this function is being used
    logger.error(
        f"[DEBUG] [STRICT-CONTEXT-ISOLATOR-CALLED] extract_case_name_from_strict_context() invoked for {citation_text}"
    )
    logger.error(f"[DEBUG] [STRICT-CONTEXT-ISOLATOR-CALLED] Context: '{context}'")

    if not context or len(context) < 10:
        logger.error(
            f"[STRICT-EXTRACT-DEBUG] Context too short for {citation_text}: {len(context) if context else 0} chars"
        )
        return None

    # DEBUG: Log the context being analyzed (ENABLED FOR DEBUGGING FIX #13)
    logger.error(f"[STRICT-EXTRACT-DEBUG] Citation: {citation_text}")
    logger.error(f"[STRICT-EXTRACT-DEBUG] Context ({len(context)} chars): '{context[-200:]}'")  # Last 200 chars

    # First unescape any HTML entities (e.g., &#039;, &amp;)
    try:
        context = html.unescape(context)
    except Exception:
        pass

    # CRITICAL: Normalize Unicode characters BEFORE pattern matching
    # Convert smart quotes and apostrophes to ASCII equivalents
    context = context.replace("\u2019", "'")  # Right single quotation mark → apostrophe
    context = context.replace("\u2018", "'")  # Left single quotation mark → apostrophe
    context = context.replace("\u201c", '"')  # Left double quotation mark
    context = context.replace("\u201d", '"')  # Right double quotation mark
    context = context.replace("\u00b4", "'")  # Acute accent → apostrophe
    context = context.replace("\u0060", "'")  # Grave accent → apostrophe
    context = context.replace("\u00a0", " ")  # Non-breaking space → space
    # Normalize dashes and unusual spaces
    context = context.replace("\u2013", "-")  # En dash
    context = context.replace("\u2014", "-")  # Em dash
    context = re.sub(r"[\u2000-\u200B\u202F\u205F\u3000]", " ", context)  # other thin/figure spaces
    # CRITICAL FIX: Remove docket numbers EARLY (before whitespace normalization)
    # This prevents "Erickson v. Pharmacia, No. 103135-1" from contaminating extraction
    context = re.sub(r",?\s*No\.\s*[\d\-]+", "", context, flags=re.IGNORECASE)

    # Collapse whitespace (normalize newlines to spaces)
    context = re.sub(r"\s+", " ", context).strip()

    # CRITICAL: Remove signal words and case history notations BEFORE pattern matching
    # IMPROVED: Only remove signal words at START of context to avoid truncating case names

    # FIRST: Remove entire lines containing legal concepts that aren't case names
    # This handles "Anti-SLAPP Statute / Collateral Order Doctrine\n\nOverruling..."
    doctrine_lines_pattern = r"[^\n]*\b(doctrine|rule|test|standard|principle|holding)\b[^\n]*\n+"
    context = re.sub(doctrine_lines_pattern, "", context, flags=re.IGNORECASE)

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
        logger.debug(f"[STRICT-EXTRACT] Cleaned signal words: '{original_context[-50:]}' → '{context[-50:]}'")

    # Additional cleanup: remove any remaining isolated docket patterns that might have been missed
    context_before_clean = context
    context = re.sub(r"\s+No\.\s+[\d\-\s]+(?=\s+v\.)", " ", context, flags=re.IGNORECASE)
    if context != context_before_clean:
        logger.error(f"[FIX #13] Cleaned case numbers from context")
        logger.error(f"[FIX #13] Before: '{context_before_clean[-100:]}'")
        logger.error(f"[FIX #13] After:  '{context[-100:]}'")
    else:
        logger.error(f"[FIX #13] No case numbers found to clean in context")

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
        # PRIORITY 1: Complex legal names with full party descriptions (NEW - HIGHEST PRIORITY)
        # Matches: "Chance Gresser, individually and as parent, natural guardian, next of friendand on behalf of his daughter, C.G., and Erin Gresser, individually and asparent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center"
        # Matches: "Francis Rudnicki and Pamela Rudnicki, as parents, guardians and next friends of Alexander Rudnicki, a minor v. Bianco"
        r"([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:individually|as\s+(?:parent|guardian|next\s+friend|administrator|executor|trustee|personal\s+representative)|and\s+on\s+behalf\s+of|by\s+and\s+through)[^,]*)*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:d/b/a|doing\s+business\s+as|a\s+(?:Delaware|California|New\s+York)\s+(?:Corporation|Corp|Inc|LLC|Ltd))[^,]*)*)(?:\s*[;\(]|,\s*\d|,\s*No\.|$)",
        # PRIORITY 2: "In re" cases with full party names
        # Matches: "In re: The PEOPLE of the State of Colorado v. Regina M. SPRINKLE"
        r"In\s+re:\s+([A-Z][A-Z\s\'&\-\.,]+)\s+v\.\s+([A-Z][A-Z\s\'&\-\.,]+)(?:\s*[;\(]|,\s*\d|$)",
        # PRIORITY 3: Standard "v." pattern - ENHANCED to handle complex corporate names
        # Stop at semicolon or opening paren to prevent cross-citation contamination
        # ENHANCED: Better handling of corporate suffixes (LLC, Inc., Corp., Co., etc.)
        # and abbreviations (N., Ry., etc.) in case names
        # Pattern now explicitly allows:
        # - Single letter abbreviations followed by period (N., W., etc.)
        # - Corporate suffixes (LLC, Inc., Corp., Co., Ltd., etc.)
        # - Common legal abbreviations (Ry., Auto, Supply, etc.)
        r"([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)(?:\s*[;\(,]|,\s*\d+|,\s*No\.|$)",
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
                logger.error(
                    f"[PATTERN-DEBUG] Pattern {pattern_idx} found {len(matches)} matches in context: '{context}'"
                )
                for match in matches:
                    logger.error(f"[PATTERN-DEBUG] Match: '{match.group()}'")
            else:
                logger.error(f"[PATTERN-DEBUG] Pattern {pattern_idx} found no matches in context: '{context}'")

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
                    logger.error(f"[PATTERN-REJECT] IMMEDIATELY REJECTED header pattern in match: '{match.group(0)}'")
                    continue  # Skip this match
                filtered_matches.append(match)

            # If all matches were headers, try next pattern
            if not filtered_matches:
                logger.error(
                    f"[PATTERN-REJECT] All matches for pattern {pattern_idx} were headers, trying next pattern"
                )
                continue

            matches = filtered_matches  # Use filtered matches

            # USER FIX 2024-10-26: Take the match CLOSEST to the end of context (closest to citation)
            # Calculate distance from end of context for each match
            context_length = len(context)
            best_match = None
            best_distance = float("inf")

            for match in matches:
                # Distance from end of context = how far from the citation
                match_end = match.end()
                distance_from_end = context_length - match_end

                if distance_from_end < best_distance:
                    best_distance = distance_from_end
                    best_match = match

            if best_match is None:
                continue

            match = best_match  # Use the closest match to citation
            # USER FIX: Since we now use expanding windows that start small,
            # we can be more lenient here - the small starting window already ensures proximity
            # The distance threshold should match the context length (which is controlled by the window)
            logger.error(
                f"[DISTANCE-DEBUG] Pattern {pattern_idx}: best_distance={best_distance}, context_length={context_length}"
            )
            # Accept if the case name ends within the context (distance from end < context length)
            # This ensures we're getting case names that are actually in our bounded context
            if best_distance > context_length:
                logger.error(
                    f"[DISTANCE-DEBUG] REJECTED: Match outside context bounds ({best_distance} > {context_length})"
                )
                continue
            else:
                logger.error(f"[DISTANCE-DEBUG] ACCEPTED: Match within context bounds")

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

                logger.error(
                    f"[REPORTER-DEBUG] Pattern {pattern_idx}: target_fam='{target_fam}', between_fam='{between_fam}', between_seg='{between_seg[:50]}...'"
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
                    logger.error(f"[PARALLEL-DEBUG] Testing pattern against: '{between_clean}'")
                    if re.match(parallel_pattern, between_clean):
                        logger.error(f"[REPORTER-DEBUG] ACCEPTED: Detected parallel citation cluster pattern")
                    else:
                        logger.error(f"[PARALLEL-DEBUG] Pattern did not match")
                        # Check if the different citation is immediately after the match
                        distance_to_next_citation = len(between_seg) - len(between_seg.lstrip()[:20])
                        if distance_to_next_citation < 20:
                            logger.error(
                                f"[REPORTER-DEBUG] REJECTED: Different citation immediately follows match (not parallel cluster)"
                            )
                            continue
                        else:
                            logger.error(f"[REPORTER-DEBUG] ACCEPTED: Different citation is far enough away")
                elif between_fam == "unknown":
                    logger.error(f"[REPORTER-DEBUG] ACCEPTED: No citation detected after match (between_fam=unknown)")

            except Exception as e:
                logger.error(f"[REPORTER-DEBUG] Exception in reporter family validation: {e}")

            if pattern_idx in [1, 2, 3]:  # Patterns with 2 groups (plaintiff v. defendant)
                logger.error(f"[PATTERN-GROUP-DEBUG] Pattern {pattern_idx}: Processing 2-group pattern")
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                logger.error(f"[PATTERN-GROUP-DEBUG] Raw groups: plaintiff='{plaintiff}', defendant='{defendant}'")

                # Clean up whitespace and newlines
                plaintiff = re.sub(r"\s+", " ", plaintiff).strip(" ,;\n")
                defendant = re.sub(r"\s+", " ", defendant).strip(" ,;\n")

                # Fix corporate name punctuation: "Spokeo , Inc." → "Spokeo, Inc."
                plaintiff = re.sub(r"\s+,\s+", ", ", plaintiff)
                defendant = re.sub(r"\s+,\s+", ", ", defendant)

                # Remove trailing incomplete words (truncation artifacts)
                plaintiff = re.sub(r"\s+[a-z]{1,2}$", "", plaintiff)  # "Name v. Ca" → "Name v."
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
                            logger.error(f"[GOV-PREFIX-FIX] Restored prefix: '{plaintiff}'")
                except Exception:
                    pass

                # Trim plaintiff to text after the last sentence boundary to remove narrative prefixes
                try:
                    boundaries = []
                    for token in [". ", "; ", "—", "–"]:
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
                logger.error(
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
                logger.error(f"[STRICT-EXTRACT] REJECTED header (ET AL + role word): '{case_name}'")
                return None

            # If it has a role word and NO, it's almost certainly a header
            if has_role_word and has_no:
                logger.error(
                    f"[STRICT-EXTRACT] REJECTED header (role word + NO): '{case_name}' (has_role_word={has_role_word}, has_no={has_no})"
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
                logger.error(
                    f"[STRICT-EXTRACT] REJECTED header (multiple role words: {role_word_count}): '{case_name}'"
                )
                return None

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
            sentence_starters = [
                "at ",
                "the ",
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
                    logger.error(
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
                        logger.error(
                            f"[VALIDATION-DEBUG] REJECTED: Trailing punctuation without known abbreviation or valid structure"
                        )
                        continue  # Suspicious punctuation unless it's corporate or known abbreviation
                    else:
                        logger.error(f"[VALIDATION-DEBUG] ACCEPTED: Found known abbreviation in combined name")

            # If we reach here and there is no 'v.' and not an accepted prefix (In re, Ex parte, Estate of, Matter of), reject to avoid narrative fragments
            if " v. " not in case_name.lower():
                if not re.search(r"^(In\s+re|Ex\s+parte|Estate\s+of|Matter\s+of)\b", case_name, re.IGNORECASE):
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
                    logger.error(f"[STRICT-EXTRACT-FINAL-REJECT] REJECTED header pattern in final check: '{case_name}'")
                    logger.error(
                        f"[STRICT-EXTRACT-FINAL-REJECT]   has_et_al={has_et_al_final}, has_role={has_role_word_final}, has_no={has_no_final}"
                    )
                    logger.error(
                        f"[STRICT-EXTRACT-FINAL-REJECT]   header_pattern_match={header_pattern_match is not None}, role_no_pattern={role_no_pattern is not None}"
                    )
                    return None  # CRITICAL FIX: Return None immediately, don't try next pattern

                logger.info(
                    f"[STRICT-EXTRACT] Extracted '{case_name}' for {citation_text} " f"using pattern {pattern_idx}"
                )
                logger.error(f"[FINAL-DEBUG] RETURNING case name: '{case_name}' for {citation_text}")
                return case_name
            else:
                logger.error(
                    f"[FINAL-DEBUG] REJECTED case name too short: '{case_name}' ({len(case_name)} chars) for {citation_text}"
                )

        except Exception as e:
            logger.debug(f"[STRICT-EXTRACT] Pattern {pattern_idx} failed: {e}")

    logger.warning(f"[STRICT-EXTRACT] No case name found for {citation_text}")
    # Fallback: capture '... v. ...,' immediately before the citation (common formatting)
    try:
        recent = context[-160:]
        # Stop defendant at ', No.' or comma-before-reporter; non-greedy capture of defendant
        m = re.search(r"([A-Z][^,;()]{2,120})\s+v\.\s+([^,;()]{2,120}?)(?=,\s*(?:\d|No\b|$))\s*,?\s*$", recent)
        if m:
            plaintiff = re.sub(r"\s+", " ", m.group(1)).strip(" ,;\n")
            defendant = re.sub(r"\s+", " ", m.group(2)).strip(" ,;\n")
            # Trim narrative prefixes from plaintiff using last sentence/delimiter boundary
            try:
                boundaries = []
                for token in [". ", "; ", "—", "–"]:
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

                logger.info(f"[STRICT-EXTRACT:FALLBACK] Extracted '{fallback_name}' for {citation_text}")
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
            logger.info(f"[STRICT-ISOLATION] {citation_text} → '{case_name}'")
        else:
            logger.warning(f"[STRICT-ISOLATION] Failed to extract for {citation_text}")

    return results


__all__ = [
    "find_all_citation_positions",
    "get_strict_context_for_citation",
    "get_adaptive_context_for_citation",
    "extract_case_name_from_strict_context",
    "extract_with_strict_isolation",
]
