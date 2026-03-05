"""
UNIFIED Case Name Extractor - Single source of truth for ALL extractions.

This module replaces all scattered extraction logic with ONE method that
ALWAYS uses strict context isolation to prevent case name bleeding.

CRITICAL PRINCIPLE:
- EVERY citation extraction MUST go through extract_case_name_with_strict_isolation()
- NO other extraction methods should be used
- This ensures 100% consistency and zero case name bleeding
"""

import logging
import re
from typing import Optional, List, Any
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_adaptive_context_for_citation,
    extract_case_name_from_strict_context,
    is_citation_or_part_of_citation,
)

logger = logging.getLogger(__name__)


def extract_case_name_with_strict_isolation(
    text: str,
    citation_text: str,
    citation_start: int,
    citation_end: int,
    all_citations: Optional[List[Any]] = None,
    document_primary_case_name: Optional[str] = None,
) -> Optional[str]:
    """
    THE ONLY case name extraction function that should be used.

    This function uses strict context isolation to prevent case name bleeding
    between nearby citations.

    Args:
        text: Full document text
        citation_text: The citation string (e.g., "506 U.S. 139")
        citation_start: Start position of citation in text
        citation_end: End position of citation in text
        all_citations: Optional list of all citations for better boundary detection
        document_primary_case_name: Optional document primary case name for contamination filtering

    Returns:
        Extracted case name or None

    Example:
        >>> extract_case_name_with_strict_isolation(
        ...     text="See Will v. Hallock, 546 U.S. 345 (2006) (quoting P.R. Aqueduct v. Metcalf, 506 U.S. 139)",
        ...     citation_text="506 U.S. 139",
        ...     citation_start=80,
        ...     citation_end=92
        ... )
        'P.R. Aqueduct v. Metcalf'  # Correctly isolates, not "Will v. Hallock"
    """
    try:
        # USER FIX 2026-01-27: Enhanced logging for problematic citations
        # FIX 2026-02-01: Added "524 u.s." for semicolon-separated citation debugging
        # FIX 2026-01-30: Added "199 f.3d 263" for But see / federal reporter extraction
        is_problematic_citation = any(
            pattern in citation_text.lower()
            for pattern in ["554 u.s. 724", "418 u.s. 323", "397 u.s. 150", "590 u.s. ___", "wl 6070490", "524 u.s.", "491 u.s.", "199 f.3d 263", "523 u.s. 83"]
        )
        
        logger.info(
            f"[UNIFIED-EXTRACT] Starting strict extraction for {citation_text} at pos {citation_start}-{citation_end}"
        )
        
        if is_problematic_citation:
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] PROBLEMATIC CITATION: {citation_text} at pos {citation_start}-{citation_end}"
            )
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Text before citation: '{text[max(0, citation_start-100):citation_start]}'"
            )
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Text after citation: '{text[citation_end:citation_end+100]}'"
            )

        # Get all citation positions for proper boundary detection
        all_positions = find_all_citation_positions(text)
        logger.debug(f"[UNIFIED-EXTRACT] Found {len(all_positions)} total citation positions in document")
        
        if is_problematic_citation:
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Found {len(all_positions)} citation positions"
            )
            nearby_positions = [
                pos for pos in all_positions
                if abs(pos["start"] - citation_start) < 200
            ]
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Found {len(nearby_positions)} citations within 200 chars"
            )

        # Get adaptive context (starts small and expands until case name found)
        # USER FIX: Reduced from 300 to 100 chars to prevent cascading contamination
        # The expanding window (25->50->75->100) handles legitimate distant names
        adaptive_context = get_adaptive_context_for_citation(
            text, citation_start, citation_end, all_positions, max_lookback=100
        )
        
        if is_problematic_citation:
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Initial adaptive_context ({len(adaptive_context)} chars)"
            )

        # Defensive trim: semicolons separate different cases. Use ONLY text after last semicolon so we get
        # "Davis v. Federal Election Comm'n" not "Meese v. Keene" for "554 U.S. 724" in series.
        if adaptive_context and ";" in adaptive_context:
            last_semicolon = adaptive_context.rfind(";")
            after_semicolon = adaptive_context[last_semicolon + 1 :].strip()
            if len(after_semicolon) >= 5:  # Any meaningful text after semicolon
                if is_problematic_citation:
                    logger.debug(
                        f"[UNIFIED-EXTRACT-TRACE] Found semicolon at position {last_semicolon}, trimming context"
                    )
                logger.debug(
                    f"[UNIFIED-EXTRACT] Trimming context at semicolon for {citation_text} (kept {len(after_semicolon)} chars)"
                )
                adaptive_context = after_semicolon

        # If context contains an INTERVENING citation (a different citation before our target),
        # use only text after the rightmost such citation so we get "Davis v. FEC" not "Meese v. Keene".
        # Do NOT trim when the only match IS the target citation - then the case name is to the left.
        if adaptive_context and citation_text:
            def _norm_cite(t: str) -> str:
                t = re.sub(r"\s+", " ", t.lower()).strip()
                t = re.sub(r"u\.\s*s\.?", "u.s.", t, flags=re.IGNORECASE)
                t = re.sub(r"f\.\s*3d", "f.3d", t, flags=re.IGNORECASE)
                t = re.sub(r"f\.\s*2d", "f.2d", t, flags=re.IGNORECASE)
                t = re.sub(r"f\.\s*4th", "f.4th", t, flags=re.IGNORECASE)
                return re.sub(r"\s+", " ", t).strip()

            norm_target = _norm_cite(citation_text)
            base_target = norm_target.split(",")[0].strip() if "," in norm_target else norm_target

            # Build pattern that matches either U.S. or federal reporters (F.2d/F.3d/F.4th) so we find target in context
            is_us = bool(re.match(r"^\d+\s+u\.?\s*s\.?\s*\d+", norm_target))
            is_federal_reporter = bool(re.match(r"^\d+\s+f\.?\s*(?:2d|3d|4th)?\s+\d+", norm_target))

            pattern = None
            if is_us:
                pattern = re.compile(
                    r"\d+\s+U\.?\s*S\.?\s+\d+(?:\s*,\s*\d+)?",
                    re.IGNORECASE,
                )
            elif is_federal_reporter:
                pattern = re.compile(
                    r"\d+\s+F\.?\s*(?:2d|3d|4th)\s+\d+(?:\s*,\s*\d+)?",
                    re.IGNORECASE,
                )

            last_match = None
            if pattern:
                for m in pattern.finditer(adaptive_context):
                    last_match = m
            if last_match:
                matched_citation = adaptive_context[last_match.start() : last_match.end()]
                norm_matched = _norm_cite(matched_citation)
                base_matched = norm_matched.split(",")[0].strip() if "," in norm_matched else norm_matched
                is_target_citation = (
                    norm_matched == norm_target
                    or norm_matched.startswith(norm_target + ",")
                    or norm_matched.startswith(norm_target + " ")
                    or (base_matched == base_target and base_target)
                )
                if not is_target_citation:
                    after_citation = adaptive_context[last_match.end() :].strip()
                    after_citation = re.sub(r"^[;,]\s*", "", after_citation).strip()
                    if len(after_citation) >= 5:
                        if is_problematic_citation:
                            logger.debug(
                                f"[UNIFIED-EXTRACT-TRACE] Trimming at intervening citation"
                            )
                        logger.info(
                            f"[UNIFIED-EXTRACT] Trimming at intervening citation for {citation_text} "
                            f"(kept {len(after_citation)} chars after citation)"
                        )
                        adaptive_context = after_citation
                    else:
                        adaptive_context = ""
                    logger.debug(
                        f"[UNIFIED-EXTRACT] Intervening citation with no case name after; cleared context for {citation_text}"
                    )
                else:
                    # Last match IS the target citation. Use ONLY text immediately before it.
                    before_target = adaptive_context[: last_match.start()].strip()
                    before_target = re.sub(r",\s*$", "", before_target).strip()
                    if len(before_target) >= 5:
                        adaptive_context = before_target
                        logger.debug(
                            f"[UNIFIED-EXTRACT] Using only text before target citation for {citation_text} ({len(adaptive_context)} chars)"
                        )

        logger.debug(f"[UNIFIED-EXTRACT] Adaptive context for {citation_text}: {len(adaptive_context)} chars")

        # Extract case name from adaptive context
        if is_problematic_citation:
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] Calling extract_case_name_from_strict_context"
            )
        
        case_name = extract_case_name_from_strict_context(adaptive_context, citation_text)

        # Strip trailing ", YYYY" (citation year) so "Thole v. U. S. Bank N. A, 2020" -> "Thole v. U. S. Bank N. A"
        if case_name and re.search(r",\s*(19|20)\d{2}\s*\.?\s*$", case_name):
            case_name = re.sub(r",\s*(19|20)\d{2}\s*\.?\s*$", "", case_name).strip().rstrip(",").strip()
            logger.debug(f"[UNIFIED-EXTRACT] Stripped trailing year from case name for {citation_text}")

        # Reject at extraction layer if result is citation/fragment/statute (after year strip)
        if case_name and is_citation_or_part_of_citation(case_name, citation_text):
            logger.debug(
                f"[UNIFIED-EXTRACT-REJECT] {citation_text} -> '{case_name}' REJECTED (citation/fragment/statute)"
            )
            case_name = None

        # USER FIX 2026-01-27: Remove signal phrases immediately after extraction
        if case_name:
            original_case_name = case_name
            signal_phrase_patterns = [
                r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                r"^See\s+also\s+",  # "See also"
                r"^See\s+generally\s+",  # "See generally"
                r"^But\s+see\s+",  # "But see"
                r"^Cf\.?\s+",  # "Cf."
                r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
            ]
            for pattern in signal_phrase_patterns:
                case_name = re.sub(pattern, "", case_name, flags=re.IGNORECASE).strip()
            
            if case_name != original_case_name:
                logger.debug(
                    f"[UNIFIED-EXTRACT-SIGNAL] Removed signal phrase: '{original_case_name}' -> '{case_name}' for {citation_text}"
                )
        
        if is_problematic_citation:
            logger.debug(
                f"[UNIFIED-EXTRACT-TRACE] extract_case_name_from_strict_context returned: '{case_name}'"
            )

        # NOTE: Removed strict boundary validation that was causing performance issues
        # The extraction already uses isolated context, so additional validation was redundant
        # and was rejecting valid extractions, causing retries and slowdowns

        # FINAL SAFETY CHECK: Reject header patterns before returning
        # This ensures no header slips through even if previous checks missed it
        if case_name:
            case_name_upper = case_name.upper()
            has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
            has_role_word = any(
                role in case_name_upper
                for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
            )
            has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

            # Reject if it's clearly a header (ET AL + role word, or role word + NO)
            if (has_et_al and has_role_word) or (has_role_word and has_no):
                logger.warning(
                    f"[UNIFIED-EXTRACT-FINAL-REJECT] {citation_text} -> '{case_name}' REJECTED (header pattern detected)"
                )
                case_name = None

            # Context-bleeding: reject all-caps match when defendant ends with justice surname (header/attribution)
            # e.g. "TRANSUNION LLC v. RAMIREZ THOMAS" from "THOMAS, J., dissenting" should not attach to "426 U.S. 26"
            if case_name and case_name.isupper() and (" v. " in case_name or " v " in case_name):
                parts = re.split(r"\s+v\.?\s+", case_name, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    defendant = re.sub(r",\s*(?:Inc\.|Corp\.|LLC|Ltd\.).*$", "", parts[1].strip(), flags=re.IGNORECASE).strip()
                    last_word = defendant.split()[-1] if defendant.split() else ""
                    justice_surnames = {
                        "THOMAS", "ALITO", "ROBERTS", "KAVANAUGH", "BARRETT", "GORSUCH", "SOTOMAYOR", "KAGAN",
                        "JACKSON", "KENNEDY", "SCALIA", "GINSBURG", "BREYER", "O'CONNOR", "REHNQUIST", "STEVENS",
                    }
                    if last_word in justice_surnames:
                        logger.warning(
                            f"[UNIFIED-EXTRACT-FINAL-REJECT] {citation_text} -> '{case_name}' REJECTED (all-caps + justice surname defendant)"
                        )
                        case_name = None

        # Apply contamination filtering if document primary case name is provided
        if case_name and document_primary_case_name:
            if _is_document_case_contamination(case_name, document_primary_case_name):
                logger.debug(
                    f"[UNIFIED-EXTRACT-CONTAMINATION] {citation_text} -> '{case_name}' REJECTED (matches primary)"
                )
                return None
            else:
                logger.info(
                    f"[UNIFIED-EXTRACT-CONTAMINATION] {citation_text} -> '{case_name}' PASSED (no contamination)"
                )

        # CRITICAL FIX: Validate extracted case name before returning
        # This prevents contaminated names like "WPLA claim. Call v. Heard" from being returned
        if case_name:
            from src.extraction.validation import is_valid_case_name

            if not is_valid_case_name(case_name):
                if is_problematic_citation:
                    logger.debug(
                        f"[UNIFIED-EXTRACT-TRACE] REJECTED by is_valid_case_name: '{case_name}'"
                    )
                logger.debug(
                    f"[UNIFIED-EXTRACT-REJECT] {citation_text} -> '{case_name}' REJECTED by validator"
                )
                return None
            
            if is_problematic_citation:
                logger.debug(
                    f"[UNIFIED-EXTRACT-TRACE] FINAL RESULT for {citation_text}: '{case_name}'"
                )
            logger.debug(f"[UNIFIED-EXTRACT-SUCCESS] {citation_text} -> '{case_name}'")
            return case_name
        else:
            if is_problematic_citation:
                logger.debug(
                    f"[UNIFIED-EXTRACT-TRACE] FINAL RESULT: No case name found for {citation_text}"
                )
            logger.debug(f"[UNIFIED-EXTRACT-FAIL] No case name found for {citation_text}")
            return None

    except Exception as e:
        logger.error(f"[UNIFIED-EXTRACT-ERROR] Failed to extract for {citation_text}: {e}")
        return None


def apply_unified_extraction_to_all_citations(text: str, citations: List[Any], force_reextract: bool = False) -> None:
    """
    Apply unified extraction to ALL citations in the list.

    This ensures every citation uses strict context isolation,
    regardless of how it was originally found.

    Args:
        text: Full document text
        citations: List of citation objects
        force_reextract: If True, re-extract even if case name exists
    """
    logger.info(f"[UNIFIED-EXTRACT-ALL] Applying unified extraction to {len(citations)} citations")

    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    for citation in citations:
        # Get citation details
        if hasattr(citation, "citation"):
            cit_text = citation.citation
            start = getattr(citation, "start_index", None)
            end = getattr(citation, "end_index", None)
            existing_name = getattr(citation, "extracted_case_name", None)
        elif isinstance(citation, dict):
            cit_text = citation.get("citation")
            start = citation.get("start_index")
            end = citation.get("end_index")
            existing_name = citation.get("extracted_case_name")
        else:
            logger.warning(f"[UNIFIED-EXTRACT-ALL] Unknown citation type: {type(citation)}")
            continue

        # Skip if no position info
        if start is None or end is None:
            logger.debug(f"[UNIFIED-EXTRACT-ALL] Skipping {cit_text} - no position info")
            skipped_count += 1
            continue

        # Skip if already has good extraction (unless forcing)
        if not force_reextract and existing_name and existing_name != "N/A" and len(existing_name) > 10:
            logger.debug(f"[UNIFIED-EXTRACT-ALL] Skipping {cit_text} - already has: {existing_name}")
            skipped_count += 1
            continue

        # Extract using unified method
        case_name = extract_case_name_with_strict_isolation(text, cit_text, start, end, citations)

        if case_name:
            # Set the extracted case name
            if hasattr(citation, "extracted_case_name"):
                citation.extracted_case_name = case_name
            elif isinstance(citation, dict):
                citation["extracted_case_name"] = case_name

            extracted_count += 1
            logger.info(f"[UNIFIED-EXTRACT-ALL] Set {cit_text} -> '{case_name}'")
        else:
            # Set to N/A if extraction failed
            if hasattr(citation, "extracted_case_name"):
                citation.extracted_case_name = "N/A"
            elif isinstance(citation, dict):
                citation["extracted_case_name"] = "N/A"

            failed_count += 1
            logger.warning(f"[UNIFIED-EXTRACT-ALL] Failed to extract for {cit_text}")

    logger.info(
        f"[UNIFIED-EXTRACT-ALL] Complete: "
        f"{extracted_count} extracted, {skipped_count} skipped, {failed_count} failed"
    )


def _is_document_case_contamination(
    extracted_name: str, document_primary_case_name: str, similarity_threshold: float = 0.95
) -> bool:
    """
    Detect if extracted case name is contaminated with document's primary case name.

    Args:
        extracted_name: The case name that was extracted
        document_primary_case_name: The document's primary case name

    Returns:
        True if contaminated (should be rejected), False if clean
    """
    if not document_primary_case_name or not extracted_name:
        return False

    # CRITICAL FIX: First check for header patterns in extracted name
    # This catches cases where the header format is extracted even if normalization doesn't match

    # SIMPLE CHECK FIRST: If name contains both "ET AL" and a role word, or role word and NO, it's a header
    extracted_upper = extracted_name.upper()
    has_et_al = "ET AL" in extracted_upper or "ETAL" in extracted_upper.replace(" ", "")
    has_role_word = any(
        role in extracted_upper
        for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
    )
    has_no = "NO." in extracted_upper or " NO " in extracted_upper or extracted_upper.endswith(" NO")

    # CRITICAL FIX: Check for "Opinion of the Court" contamination
    # This happens when citation context includes header text like "Opinion of the Court CASE v. NAME"
    if "OPINION OF THE COURT" in extracted_upper:
        logger.warning(f"[CONTAMINATION-FILTER] REJECTED 'Opinion of the Court' header: '{extracted_name}'")
        return True

    # ENHANCED: If the case name contains "ET AL" WITH a role word, it's almost certainly a header
    # BUT: "ET AL" alone can be legitimate (e.g., "Smith et al. v. Jones")
    # Only reject if it's clearly a header pattern (ET AL + role word, or role word + NO)
    if has_et_al and has_role_word:
        logger.warning(f"[CONTAMINATION-FILTER] REJECTED header (ET AL + role word): '{extracted_name}'")
        return True

    # If it has a role word and NO, it's almost certainly a header
    if has_role_word and has_no:
        logger.warning(
            f"[CONTAMINATION-FILTER] REJECTED header (role word + NO): '{extracted_name}' (has_role_word={has_role_word}, has_no={has_no})"
        )
        return True

    # If it has ET AL and a role word, it's almost certainly a header
    if has_et_al and has_role_word:
        logger.warning(
            f"[CONTAMINATION-FILTER] REJECTED header (ET AL + role word): '{extracted_name}' (has_et_al={has_et_al}, has_role_word={has_role_word})"
        )
        return True

    # THEN: Check detailed patterns
    header_patterns = [
        # Pattern 1: "ET AL., Petitioners" anywhere in the name
        r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b",  # "ET AL., Petitioners"
        # Pattern 2: "Respondent. NO" or "Petitioners, NO" (with or without number)
        r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b",  # "Respondent. NO" or "Petitioners, NO"
        # Pattern 3: "ET AL., Petitioners, v. ... Respondent. NO" pattern (full header format)
        r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b",  # "ET AL., Petitioners, v. ... Respondent. NO"
        # Pattern 4: ENHANCED - Catch "ET AL., Petitioners, v. ... Respondent. NO" with any spacing
        r"ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO",  # "ET AL., Petitioners, v. ... Respondent. NO"
        # Pattern 5: Case names that END with "Respondent. NO" or similar
        r"\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*$",  # Ends with "Respondent. NO" or "Petitioners, NO"
        # Pattern 6: FIX 2026-02-04 - Supreme Court header with Justice name appended
        # Pattern: "CASE v. NAME JUSTICE_NAME" like "TRANSUNION LLC v. RAMIREZ THOMAS J"
        # Justice names: Roberts, Thomas, Alito, Sotomayor, Kagan, Gorsuch, Kavanaugh, Barrett, Jackson
        r"\bv\.\s+[A-Z][A-Za-z]+\s+(?:ROBERTS|THOMAS|ALITO|SOTOMAYOR|KAGAN|GORSUCH|KAVANAUGH|BARRETT|JACKSON)\s*,?\s*(?:C\.?\s*J\.?|J\.?)?\s*$",
        # Pattern 7: Any case name ending with "JUSTICE_LASTNAME J" or "JUSTICE_LASTNAME, J."
        r"\s+(?:ROBERTS|THOMAS|ALITO|SOTOMAYOR|KAGAN|GORSUCH|KAVANAUGH|BARRETT|JACKSON|BREYER|GINSBURG|SCALIA|KENNEDY|SOUTER|STEVENS|O['']?CONNOR|REHNQUIST)\s*,?\s*(?:C\.?\s*J\.?|J\.?)?\s*$",
    ]
    for pattern in header_patterns:
        if re.search(pattern, extracted_name, re.IGNORECASE):
            logger.warning(
                f"[CONTAMINATION-FILTER] REJECTED header pattern in extracted name: '{extracted_name}' (matched pattern: {pattern})"
            )
            return True

    # Normalize both for comparison (case-insensitive, ignore punctuation, handle abbreviations)
    def normalize_for_comparison(name):
        normalized = name.lower()
        # Remove role words and docket numbers for comparison
        normalized = re.sub(r"\bet\s+al\.?\b", "", normalized)
        normalized = re.sub(r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?)\b", "", normalized)
        normalized = re.sub(r"\bno\.?\s*\d+", "", normalized)

        # Normalize common abbreviations to full forms for better comparison
        # This handles cases where one system uses "Inc." and another uses "Incorporated"
        abbreviation_map = {
            r"\binc\.?\b": "incorporated",
            r"\bcorp\.?\b": "corporation",
            r"\bco\.?\b": "company",
            r"\bllc\.?\b": "limited liability company",
            r"\bltd\.?\b": "limited",
            r"\blp\.?\b": "limited partnership",
            r"\bassoc\.?\b": "association",
            r"\bauto\.?\b": "automobile",
            r"\bins\.?\b": "insurance",
            r"\bmfg\.?\b": "manufacturing",
            r"\bmgmt\.?\b": "management",
        }
        for abbrev, full_form in abbreviation_map.items():
            normalized = re.sub(abbrev, full_form, normalized)

        normalized = re.sub(r"[,\.\s]+", " ", normalized)
        normalized = normalized.strip()
        return normalized

    extracted_normalized = normalize_for_comparison(extracted_name)
    primary_normalized = normalize_for_comparison(document_primary_case_name)

    # CRITICAL: Use similarity scoring instead of simple containment checks
    # Different systems can have different case names for the same case (abbreviations vs full names)
    # We should only reject if similarity is VERY high (>= 0.95), indicating it's likely the same case

    def calculate_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two normalized case names."""
        if not name1 or not name2:
            return 0.0

        # Exact match
        if name1 == name2:
            return 1.0

        # Check if one contains the other (but require high overlap)
        if name1 in name2:
            # Calculate overlap ratio
            overlap_ratio = len(name1) / len(name2) if len(name2) > 0 else 0.0
            return overlap_ratio
        elif name2 in name1:
            overlap_ratio = len(name2) / len(name1) if len(name1) > 0 else 0.0
            return overlap_ratio

        # Word-based similarity (Jaccard similarity)
        words1 = set(name1.split())
        words2 = set(name2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        word_similarity = intersection / union

        # Sequence similarity (handles abbreviations better)
        from difflib import SequenceMatcher

        seq_similarity = SequenceMatcher(None, name1, name2).ratio()

        # Combined similarity (weighted average)
        # Word similarity is more important for case names
        combined = 0.6 * word_similarity + 0.4 * seq_similarity

        return combined

    similarity = calculate_similarity(extracted_normalized, primary_normalized)

    # Strategy 1: Exact match after normalization (definitely contamination)
    if extracted_normalized == primary_normalized:
        logger.warning(
            f"[CONTAMINATION-FILTER] Exact match: '{extracted_name}' == '{document_primary_case_name}' (similarity: {similarity:.2f})"
        )
        return True

    # Strategy 2: Very high similarity (>= 0.95) - likely the same case
    # This catches cases like "Erickson v. Pharmacia LLC" vs "Erickson v. Pharmacia, LLC"
    if similarity >= 0.95:
        logger.warning(
            f"[CONTAMINATION-FILTER] Very high similarity: '{extracted_name}' ~= '{document_primary_case_name}' (similarity: {similarity:.2f})"
        )
        return True

    # Strategy 3: Check if BOTH parties match AND similarity is high (>= 0.85)
    # This handles cases where both plaintiff and defendant match, but formatting differs
    primary_parts = primary_normalized.split(" v ")
    if len(primary_parts) == 2:
        plaintiff = primary_parts[0].strip()
        defendant = primary_parts[1].strip()

        if plaintiff and defendant:
            # Check if both parties appear in extracted name
            plaintiff_match = plaintiff in extracted_normalized
            defendant_match = defendant in extracted_normalized

            # Only reject if BOTH parties match AND overall similarity is high
            # This prevents false positives from cases that just share a common party name
            if plaintiff_match and defendant_match and similarity >= 0.85:
                logger.warning(
                    f"[CONTAMINATION-FILTER] Both parties match with high similarity: '{extracted_name}' ~= '{document_primary_case_name}' (similarity: {similarity:.2f})"
                )
                return True

    # Strategy 4: If similarity is moderate (0.7-0.95), check if it's likely contamination
    # by checking if extracted name contains the full primary name structure
    if 0.7 <= similarity < 0.95:
        # Check if primary name is contained in extracted name (but require high similarity)
        if primary_normalized in extracted_normalized:
            # Additional check: make sure it's not just a partial match
            # If extracted name is much longer, it might be a different case
            length_ratio = len(extracted_normalized) / len(primary_normalized) if len(primary_normalized) > 0 else 1.0
            if length_ratio <= 1.5:  # Extracted name shouldn't be much longer
                logger.warning(
                    f"[CONTAMINATION-FILTER] Containment with high similarity: '{extracted_name}' contains '{document_primary_case_name}' (similarity: {similarity:.2f})"
                )
                return True

    # If similarity is low (< 0.7), it's likely a different case, even if they share some words
    # Don't reject - different systems can have different case names for the same case
    logger.debug(
        f"[CONTAMINATION-FILTER] Similarity too low to reject: '{extracted_name}' vs '{document_primary_case_name}' (similarity: {similarity:.2f})"
    )
    return False


__all__ = [
    "extract_case_name_with_strict_isolation",
    "apply_unified_extraction_to_all_citations",
]
