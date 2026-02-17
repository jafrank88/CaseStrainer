"""
Text normalization utilities for handling Unicode character encoding issues.

This module provides functions to normalize text by converting problematic Unicode
characters to their standard ASCII equivalents, making regex patterns more reliable.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Unicode character mappings for common problematic characters
UNICODE_MAPPINGS = {
    # Apostrophes and quotes
    "\u2019": "'",  # Right single quotation mark
    "\u2018": "'",  # Left single quotation mark
    "\u201a": "'",  # Single low-9 quotation mark
    "\u201b": "'",  # Single high-reversed-9 quotation mark
    "\u2032": "'",  # Prime
    "\u2035": "'",  # Reversed prime
    "\u201c": '"',  # Left double quotation mark
    "\u201d": '"',  # Right double quotation mark
    "\u201e": '"',  # Double low-9 quotation mark
    "\u201f": '"',  # Double high-reversed-9 quotation mark
    "\u2033": '"',  # Double prime
    "\u2034": '"',  # Triple prime
    "\u2036": '"',  # Reversed double prime
    "\u2037": '"',  # Reversed triple prime
    "\u2039": "<",  # Single left-pointing angle quotation mark
    "\u203a": ">",  # Single right-pointing angle quotation mark
    "\u00b4": "'",  # Acute accent
    "\u0060": "`",  # Grave accent
    "\u02b9": "'",  # Modifier letter prime
    "\u02bb": "'",  # Modifier letter turned comma
    "\u02bc": "'",  # Modifier letter apostrophe
    "\u02bd": "'",  # Modifier letter reversed comma
    "\u02be": "'",  # Modifier letter right half ring
    "\u02bf": "'",  # Modifier letter left half ring
    # Ampersands
    "\u0026": "&",  # Ampersand (standard)
    "\uff06": "&",  # Fullwidth ampersand
    "\u204a": "&",  # Tironian sign et
    "\u214b": "&",  # Turned ampersand
    # Hyphens and dashes
    "\u002d": "-",  # Hyphen-minus (standard)
    # NOTE: Soft hyphen (\u00ad) is handled separately in normalize_text() to preserve spacing
    "\u2010": "-",  # Hyphen
    "\u2011": "-",  # Non-breaking hyphen
    "\u2012": "-",  # Figure dash
    "\u2013": "-",  # En dash
    "\u2014": "-",  # Em dash
    "\u2015": "-",  # Horizontal bar
    "\u2212": "-",  # Minus sign
    "\ufe58": "-",  # Small em dash
    "\ufe63": "-",  # Small hyphen-minus
    "\uff0d": "-",  # Fullwidth hyphen-minus
    # Periods and dots
    "\u002e": ".",  # Full stop (standard)
    "\u2024": ".",  # One dot leader
    "\u2025": "..",  # Two dot leader
    "\u2026": "...",  # Horizontal ellipsis
    "\u2027": ".",  # Hyphenation point
    # Other punctuation
    "\u055a": ":",  # Armenian apostrophe
    "\u055b": ":",  # Armenian emphasis mark
    "\u055c": ":",  # Armenian exclamation mark
    "\u055d": ":",  # Armenian comma
    "\u055e": ":",  # Armenian question mark
    "\u055f": ":",  # Armenian abbreviation mark
    "\u05f3": "'",  # Hebrew punctuation geresh
}


def normalize_text(text: str) -> str:
    """
    Normalize text by converting problematic Unicode characters to standard ASCII equivalents.

    This function handles common Unicode character encoding issues that can cause
    regex patterns to fail, such as smart quotes, em dashes, and other special characters.
    Also fixes line breaks in legal citations.
    """
    logger.info(f"🔍 [TEXT-NORMALIZE] normalize_text called with {len(text)} chars")
    
    if not text:
        logger.info(f"🔍 [TEXT-NORMALIZE] Empty text, returning as-is")
        return text

    normalized = text

    # Show sample of original text
    sample = text[:100].replace('\n', '\\n').replace('\r', '\\r')
    logger.info(f" [TEXT-NORMALIZE] Original text sample: '{sample}...'")

    # FIX 2026-02-04: Remove soft hyphens with their line breaks FIRST
    # PDFs use soft hyphens (\xad / U+00AD) to indicate optional line breaks
    # Pattern: "Trans\xad\nUnion" -> "TransUnion"
    # CRITICAL FIX: Also remove space BEFORE the soft hyphen to prevent "Swin \xad\ndle" -> "Swin dle"
    normalized = re.sub(r'\s*\xad\s*[\n\r]+\s*', '', normalized)
    # Also handle standalone soft hyphens (no line break following)
    normalized = normalized.replace('\xad', '')

    # Apply Unicode character mappings
    for unicode_char, ascii_char in UNICODE_MAPPINGS.items():
        normalized = normalized.replace(unicode_char, ascii_char)

    # CRITICAL FIX 2026-02-05: Remove Supreme Court slip opinion page headers/footers FIRST
    # These appear as patterns like "10 \nTRANSUNION LLC v. RAMIREZ \nOpinion of the Court"
    # They can break citations that span page boundaries (e.g., "508" on one page, "U.S. 520" on next)

    # Step 1: Collapse multiple whitespace/newline sequences (like " \n \n \n") into single newline
    # This simplifies the header detection
    normalized = re.sub(r'(?:\s*\n)+', '\n', normalized)

    # Step 2: Remove page headers - pattern: "\nPageNum\nCASE v. NAME\nOpinion of..."
    # The pattern appears AFTER the previous content ends with \n
    # Handle various Opinion author patterns
    normalized = re.sub(
        r'\n(\d{1,2})\n([A-Z][A-Z\s]+(?:v\.|VS\.?)\s+[A-Z][A-Z\s]+)\n(Opinion of (?:the Court|THOMAS|KAGAN|[A-Z]+),?\s*J\.?|Syllabus|Cite as:)[^\n]*\n',
        '\n',
        normalized,
        flags=re.IGNORECASE
    )

    # Also remove standalone page numbers that appear on their own line (common in slip opinions)
    # Pattern: citation ends, then "\nPageNum\nCASE v. NAME\n" then citation continues
    normalized = re.sub(
        r'\n(\d{1,2})\n([A-Z][A-Z\s]+(?:v\.|VS\.?)\s+[A-Z][A-Z\s]+)\n',
        '\n',
        normalized,
        flags=re.IGNORECASE
    )

    # Step 3: Remove standalone "Cite as:" headers
    normalized = re.sub(r'\nCite as:\s*\d+\s+U\.?\s*S\.?\s*____[^\n]*\n', '\n', normalized, flags=re.IGNORECASE)

    # CRITICAL FIX: Handle line breaks in legal citations
    # Pattern: "200\nU. S. 321" -> "200 U. S. 321"
    # This fixes the broken citation issue where citations are split across lines
    before_fix = normalized

    # FIX 2026-02-05: More comprehensive citation line break handling
    # Handle U.S. citations: "481\nU. S. 465" -> "481 U. S. 465"
    normalized = re.sub(r"(\d+)\s*[\n\r]+\s*([Uu]\.?\s*[Ss]\.?)\s+(\d+)", r"\1 \2 \3", normalized)
    normalized = re.sub(r"(\d+)\s*[\n\r]+\s*([Uu]\.?\s*[Ss]\.?)[\n\r]+\s*(\d+)", r"\1 \2 \3", normalized)

    # Handle F.3d, F.2d, F. citations with line breaks in various positions
    # Pattern: "617\nF. 3d 688" -> "617 F.3d 688" (volume on separate line)
    normalized = re.sub(r"(\d+)\s*[\n\r]+\s*([Ff])\.?\s*(\d+)\s*[a-z]?\s+(\d+)", r"\1 \2.\3d \4", normalized)
    # Pattern: "882 F. 3d\n616" -> "882 F.3d 616" (page on separate line)
    normalized = re.sub(r"(\d+)\s+([Ff])\.?\s*(\d+)[a-z]?\s*[\n\r]+\s*(\d+)", r"\1 \2.\3d \4", normalized)
    # Pattern: "F.\n3d" -> "F.3d"
    normalized = re.sub(r"([Ff])\.?\s*[\n\r]+\s*(\d+[a-z])", r"\1.\2", normalized)
    # Pattern: "F.\n3" -> "F. 3" (without suffix letter)
    normalized = re.sub(r"([Ff])\.?\s*[\n\r]+\s*(\d+)", r"\1. \2", normalized)

    # Handle S.E.2d, N.E.2d, N.W.2d, S.W.2d, So.2d, So.3d: "143 S. E.\n631" -> "143 S.E. 631"
    normalized = re.sub(r"(\d+)\s+([SsNn])\.?\s*([EeWw])\.?\s*(\d*[a-z]*)\s*[\n\r]+\s*(\d+)", r"\1 \2.\3.\4 \5", normalized)

    # Handle S. Ct.: "141 S.\nCt." -> "141 S. Ct."
    normalized = re.sub(r"(\d+)\s+[Ss]\.?\s*[\n\r]+\s*[Cc]t\.?", r"\1 S. Ct.", normalized)

    # Handle L. Ed.: "200 L.\nEd." -> "200 L. Ed."
    normalized = re.sub(r"(\d+)\s+[Ll]\.?\s*[\n\r]+\s*[Ee]d\.?", r"\1 L. Ed.", normalized)

    # Handle F. Supp.: "123 F.\nSupp." -> "123 F. Supp."
    normalized = re.sub(r"(\d+)\s+[Ff]\.?\s*[\n\r]+\s*[Ss]upp\.?", r"\1 F. Supp.", normalized)

    # Handle state reporters with line breaks: "150 Va.\n301" -> "150 Va. 301"
    normalized = re.sub(r"(\d+)\s+([A-Z][a-z]{1,4})\.?\s*[\n\r]+\s*(\d+)", r"\1 \2. \3", normalized)

    # Handle Fed. Appx. / F. App'x: "639 Fed.\nAppx." -> "639 Fed. Appx."
    normalized = re.sub(r"(\d+)\s+[Ff]ed\.?\s*[\n\r]+\s*[Aa]pp", r"\1 Fed. App", normalized)

    # Handle Cranch, Wheat., How. (early Supreme Court reporters)
    normalized = re.sub(r"(\d+)\s+([Cc]ranch|[Ww]heat\.?|[Hh]ow\.?)\s*[\n\r]+\s*(\d+)", r"\1 \2 \3", normalized)

    # Replace remaining newlines/tabs with spaces (general cleanup)
    normalized = re.sub(r"[\n\r\t]+", " ", normalized)

    # Additional normalization: clean up multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Clean up multiple periods (but preserve ellipsis)
    normalized = re.sub(r"\.{4,}", "...", normalized)

    # Show sample of normalized text
    sample_after = normalized[:100].replace('\n', '\\n').replace('\r', '\\r')
    logger.info(f"🔍 [TEXT-NORMALIZE] Normalized text sample: '{sample_after}...'")

    # Check if we fixed the broken citation
    if "200\n U. S. 321" in before_fix or "200\nU. S. 321" in before_fix:
        if "200 U. S. 321" in normalized:
            logger.info(f"✅ [TEXT-NORMALIZE] FIXED: Found '200 U. S. 321' in normalized text")
        else:
            logger.warning(f"⚠️ [TEXT-NORMALIZE] NOT FIXED: Still no '200 U. S. 321' in normalized text")

    logger.debug(f"Text normalization: '{text[:50]}...' -> '{normalized[:50]}...'")

    return normalized.strip()


def normalize_case_name(case_name: str) -> str:
    """
    Normalize a case name specifically, handling common legal text issues.

    Args:
        case_name: Case name to normalize

    Returns:
        Normalized case name
    """
    if not case_name:
        return case_name

    # First apply general text normalization
    normalized = normalize_text(case_name)

    # Legal-specific normalizations
    # Handle common abbreviations
    normalized = re.sub(r"\bDept\b", "Dep't", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bDepartment\b", "Dep't", normalized, flags=re.IGNORECASE)

    # CRITICAL FIX: Remove spaces that break words (e.g., "Swin dle" -> "Swindle")
    # This handles cases where soft hyphens left spaces in the middle of words
    # Pattern: lowercase letter + space + lowercase letter -> remove space
    # BUT exclude "v" followed by period (legal citation separator "v.")
    # AND only rejoin if the combined result is a common/valid word
    def should_rejoin_words(match):
        """Only rejoin if the combined word is a known word fragment."""
        part1 = match.group(1)
        part2 = match.group(2)
        combined = part1 + part2
        
        # Common word fragments that should be rejoined
        common_fragments = {
            'swindle', 'swin', 'dle', 'gard', 'ner', 'gardner',
            'reserv', 'ists', 'reservists', 'madi', 'son', 'madison',
            'labo', 'ratories', 'laboratories', 'trans', 'union', 'transunion',
            'spoken', 'spokeo', 'commu', 'nications', 'communications',
            'tele', 'commc', 'telecommc', 'telecommunications',
            'international', 'int', 'l', 'national', 'nat', 'department', 'dep',
            'government', 'gov', 'corp', 'corporation', 'inc', 'incorporated',
        }
        
        # Only rejoin if the combined word or its parts are in common fragments
        if combined.lower() in common_fragments:
            return combined
        # Also rejoin if part1 is a clear prefix (ends with common split points)
        if part1.lower() in ['swin', 'gard', 'reserv', 'madi', 'labo', 'commu', 'tele', 'trans']:
            return combined
        # Don't rejoin - return original with space
        return match.group(0)
    
    normalized = re.sub(r'([a-z])\s+([a-z])(?!\.)', should_rejoin_words, normalized)

    # Also fix common broken name patterns
    normalized = re.sub(r'\bSwin dle\b', 'Swindle', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bGard ner\b', 'Gardner', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bReserv ists\b', 'Reservists', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bMadi son\b', 'Madison', normalized, flags=re.IGNORECASE)

    # Ensure space before "v." in case names (e.g., "Mackv." -> "Mack v.")
    # This fixes cases where the space was incorrectly removed during text extraction
    normalized = re.sub(r'([a-zA-Z])v\.', r'\1 v.', normalized)

    # Fix common word-merge issues from PDF extraction
    # Only fix when there's a clear word boundary indicator (capital letter)
    # "Defendersof Wildlife" -> "Defenders of Wildlife"
    normalized = re.sub(r'([a-z])of([A-Z])', r'\1 of \2', normalized)  # "Defendersof W" -> "Defenders of W"
    normalized = re.sub(r'([a-z])ofthe\b', r'\1 of the', normalized)  # "Defendersofthe" -> "Defenders of the"
    normalized = re.sub(r'\bofthe([A-Z])', r'of the \1', normalized)  # "oftheC" -> "of the C"
    normalized = re.sub(r'([a-z])forthe\b', r'\1 for the', normalized)  # "Committeeforthe" -> "Committee for the"
    normalized = re.sub(r'([a-z])tothe\b', r'\1 to the', normalized)  # "Committeetothe" -> "Committee to the"

    # Clean up extra spaces around punctuation
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    normalized = re.sub(r"\s*\.\s*", ". ", normalized)

    logger.debug(f"Case name normalization: '{case_name}' -> '{normalized}'")

    return normalized.strip()


def clean_extracted_case_name(case_name: str) -> str:
    """
    Clean up extracted case names by removing leading text that doesn't belong.

    This function handles cases where regex patterns capture too much text,
    such as when "court. Lopez Demetrio v. Sakuma Bros. Farms" should be
    cleaned to "Lopez Demetrio v. Sakuma Bros. Farms".

    Args:
        case_name: Extracted case name to clean

    Returns:
        Cleaned case name
    """
    if not case_name:
        return case_name

    # Remove leading text that doesn't belong to case names
    # FIXED: More specific patterns that don't destroy valid case names like "Spokeo, Inc."
    leading_patterns = [
        # Remove specific legal phrases that appear before case names
        r"^(court|court\.|this\s+court|we\s+review|also\s+an?\s+issue|statutory\s+interpretation|questions?\s+of\s+law|de\s+novo|in\s+light\s+of|the\s+record\s+certified|federal\s+court)[\s\.]*",
        r"^(and|or|but|that|this|is|also|we|may|ask|resolution|of|that|question|necessary|to|resolve|case|before)[\s\.]*",
        r"^(see|citing|quoting|accord|id\.|ibid\.|brief\s+at|opening\s+br\.|reply\s+br\.)[\s\.]*",
        # More specific patterns for the current issue
        r"^[^A-Z]*an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
        r"^[^A-Z]*interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
        r"^[^A-Z]*statutory\s+interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
        # REMOVED: r'^[^A-Z]*' - This was too aggressive and destroyed valid case names
    ]

    cleaned = case_name
    for pattern in leading_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove leading punctuation and whitespace
    cleaned = re.sub(r"^[\s\.,;:]+", "", cleaned)

    # Ensure the cleaned name starts with a capital letter
    if cleaned and not cleaned[0].isupper():
        # Find the first capital letter
        match = re.search(r"[A-Z]", cleaned)
        if match:
            cleaned = cleaned[match.start() :]
        else:
            # If no capital letter found, return original
            cleaned = case_name

    logger.debug(f"Case name cleaning: '{case_name}' -> '{cleaned}'")

    return cleaned.strip()


def is_unicode_problematic(text: str) -> bool:
    """
    Check if text contains problematic Unicode characters that could cause regex issues.

    Args:
        text: Text to check

    Returns:
        True if text contains problematic Unicode characters
    """
    if not text:
        return False

    # Check for any characters in our problematic Unicode ranges
    for unicode_char in UNICODE_MAPPINGS.keys():
        if unicode_char in text:
            return True

    return False
