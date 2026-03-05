"""
Utilities to clean contamination from extracted case names and dates.
Handles bold, italic, and bold+italic (markdown, HTML, Unicode mathematical symbols)
by normalizing to plain text for extraction and matching.
"""

import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Latin ligatures (e.g. from PDFs) -> ASCII equivalents. Apply before other mappings.
_LATIN_LIGATURES = {
    "\uFB00": "ff",   # ﬀ
    "\uFB01": "fi",   # ﬁ
    "\uFB02": "fl",   # ﬂ
    "\uFB03": "ffi",  # ﬃ
    "\uFB04": "ffl",  # ﬄ
    "\uFB05": "st",   # ﬅ
    "\uFB06": "st",   # ﬆ
}

# Unicode Mathematical Alphanumeric Symbols (U+1D400–U+1D7FF) map to ASCII.
# Ranges: Bold A-Z (1D400–1D419), Bold a-z (1D41A–1D433), Italic A-Z (1D434–1D44D),
# Italic a-z (1D44E–1D467), Bold Italic A-Z (1D468–1D481), Bold Italic a-z (1D482–1D49B),
# Script, Fraktur, double-struck, etc. We map Latin letters and digits to ASCII.
_MATH_RANGE_MIN = 0x1D400
_MATH_RANGE_MAX = 0x1D7FF
_MATH_ASCII_RANGES = [
    (0x1D400, 0x1D419, 0x41),   # Bold A-Z
    (0x1D41A, 0x1D433, 0x61),   # Bold a-z
    (0x1D434, 0x1D44D, 0x41),   # Italic A-Z
    (0x1D44E, 0x1D467, 0x61),   # Italic a-z
    (0x1D468, 0x1D481, 0x41),   # Bold Italic A-Z
    (0x1D482, 0x1D49B, 0x61),   # Bold Italic a-z
    (0x1D49C, 0x1D4B5, 0x41),   # Script A-Z
    (0x1D4B6, 0x1D4CF, 0x61),   # Script a-z
    (0x1D4D0, 0x1D4E9, 0x41),   # Bold Script A-Z
    (0x1D4EA, 0x1D503, 0x61),   # Bold Script a-z
    (0x1D504, 0x1D51D, 0x41),   # Fraktur A-Z
    (0x1D51E, 0x1D537, 0x61),   # Fraktur a-z
    (0x1D538, 0x1D551, 0x41),   # Double-struck A-Z
    (0x1D552, 0x1D56B, 0x61),   # Double-struck a-z
    (0x1D7CE, 0x1D7D7, 0x30),   # Bold digit 0-9
]


def _math_symbol_to_ascii(c: str) -> Optional[str]:
    """Map a single Unicode mathematical alphanumeric character to ASCII, or None."""
    o = ord(c)
    for lo, hi, base in _MATH_ASCII_RANGES:
        if lo <= o <= hi:
            return chr(base + (o - lo))
    return None


def normalize_citation_text(citation: str) -> str:
    """
    Normalize citation text for display: fix common abbreviations and truncation artifacts.
    - Nat' Life -> Nat'l (e.g. Am. Nat' Life Bank -> Am. Nat'l Bank)
    - Repair unbalanced parens (e.g. Haroco citation missing closing ) )
    """
    if not citation or not isinstance(citation, str):
        return citation or ""
    s = citation
    # Nat' Life / Nat' L (split apostrophe) -> Nat'l
    s = re.sub(r"\bNat'\s+Life\b", "Nat'l", s, flags=re.IGNORECASE)
    s = re.sub(r"\bNat'\s+L\b", "Nat'l", s, flags=re.IGNORECASE)
    # Repair unbalanced parens: if more ( than ), append ) to balance
    open_count = s.count("(") - s.count(")")
    if open_count > 0:
        s = s.rstrip() + ")" * open_count
    return s


def normalize_to_ascii_display(text: str) -> str:
    """
    Convert Unicode to ASCII for display and matching. Use on any user-facing string
    (case names, labels, citation text) so nothing slips through.
    - Latin ligatures (ﬀ, ﬁ, ﬂ, etc.) -> ff, fi, fl
    - Smart quotes, en/em dash, non-breaking space -> ASCII equivalents
    - Unicode mathematical alphanumeric symbols -> ASCII
    - Remaining non-ASCII (e.g. accented letters) -> ASCII via NFKD decomposition
    """
    if not text or not isinstance(text, str):
        return text or ""
    s = text
    # 1) Latin ligatures (PDF/typography)
    for u, a in _LATIN_LIGATURES.items():
        s = s.replace(u, a)
    # 2) Punctuation/quotes/dashes from text_normalizer (avoid importing full normalize_text)
    try:
        from src.utils.text_normalizer import UNICODE_MAPPINGS
        for u, a in UNICODE_MAPPINGS.items():
            s = s.replace(u, a)
    except Exception:
        pass
    # 3) Non-breaking space
    s = s.replace("\u00a0", " ")
    # 4) Bold/italic (HTML, markdown, Unicode math symbols)
    s = normalize_bold_italic_to_plain(s, collapse_whitespace=False, skip_unicode_math=False)
    # 5) Any remaining non-ASCII: NFKD decompose and keep only ASCII (é -> e, etc.)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_bold_italic_to_plain(
    text: str, collapse_whitespace: bool = True, skip_unicode_math: bool = False
) -> str:
    """
    Normalize text that may be regular, bold, italic, or bold+italic to plain ASCII-friendly text.
    - Strips HTML tags: <b>, <i>, <em>, <strong>, </b>, etc.
    - Strips markdown: *italic*, **bold**, _italic_, __bold__
    - Replaces Unicode mathematical alphanumeric symbols (e.g. mathematical italic A) with ASCII,
      unless skip_unicode_math=True (use for full-document text to avoid slow per-char loop).
    If collapse_whitespace is False, newlines are preserved (e.g. for text extractor before header removal).
    """
    if not text or not isinstance(text, str):
        return text or ""
    s = text
    # 1) Strip HTML-style tags (content preserved)
    s = re.sub(r"</?[bBiIeEmMsStTrRoOnNgG]\s*>", "", s)
    s = re.sub(r"</?span[^>]*>", "", s)
    s = re.sub(r"</?font[^>]*>", "", s)
    # 2) Markdown bold/italic: strip markers, keep content (order matters: ** before *)
    s = re.sub(r"\*\*([^\*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^\*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)
    # 3) Unicode mathematical bold/italic -> ASCII (skip if skip_unicode_math or long text with no math symbols)
    if not skip_unicode_math:
        if len(s) > 2000 and not any(
            _MATH_RANGE_MIN <= ord(c) <= _MATH_RANGE_MAX for c in s
        ):
            pass
        else:
            out = []
            for c in s:
                replacement = _math_symbol_to_ascii(c)
                if replacement is not None:
                    out.append(replacement)
                else:
                    out.append(c)
            s = "".join(out)
    if collapse_whitespace:
        s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_markdown_contamination(text: str) -> str:
    """
    Remove markdown and formatting characters that contaminate case names.
    Prefer normalize_bold_italic_to_plain() for full bold/italic normalization.
    """
    if not text:
        return text

    # Remove markdown characters at the start
    cleaned = re.sub(r"^[>\#\*\-\+]+\s*", "", text)

    # Remove markdown bold/italic markers
    cleaned = re.sub(r"\*\*([^\*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^\*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)

    # Remove extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if cleaned != text:
        logger.info(f"[MARKDOWN-CLEAN] Removed markdown: '{text}' -> '{cleaned}'")

    return cleaned


def fix_truncation_at_word_boundary(case_name: str, context: str = "") -> str:
    """
    Fix case names that are truncated mid-word.

    Args:
        case_name: Potentially truncated case name
        context: Surrounding context to find complete name

    Returns:
        Fixed case name
    """
    if not case_name:
        return case_name

    # Check if truncated (ends with incomplete word)
    if re.search(r"\b[A-Z][a-z]{1,2}\s*$", case_name):
        # Try to find complete name in context
        if context:
            # Look for the case name pattern in context
            escaped_name = re.escape(case_name[:20])  # Use first part as anchor
            pattern = escaped_name + r"[A-Za-z\s\.,\'&]{0,50}"
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                complete_name = match.group(0)
                # Find the end at a reasonable boundary
                if " v. " in complete_name:
                    # Extend to include full defendant name
                    parts = complete_name.split(" v. ")
                    if len(parts) == 2:
                        defendant = parts[1]
                        # Find end of defendant name
                        end_match = re.search(r"^[A-Za-z\s\.,\'&]+", defendant)
                        if end_match:
                            complete_name = f"{parts[0]} v. {end_match.group(0)}"

                if len(complete_name) > len(case_name):
                    logger.info(f"[TRUNCATION-FIX] Fixed truncation: '{case_name}' -> '{complete_name}'")
                    return complete_name.strip()

    return case_name


def remove_context_bleed_from_name(case_name: str) -> str:
    """
    Remove context bleed contamination from extracted case names.
    Examples: "Americancourts. Spokeo" -> "Spokeo", "X v. Y Syllabusmat" -> "X v. Y"
    """
    if not case_name:
        return case_name
    original = case_name
    # Leading: "Americancourts." / "American courts." / "Federal courts."
    case_name = re.sub(
        r"^(?:American|Federal)\s*courts?\.?\s*",
        "",
        case_name,
        flags=re.IGNORECASE,
    )
    # Trailing: "Syllabusmat", "Syllabus" (header bleed)
    case_name = re.sub(r"\s+Syllabusmat\s*$", "", case_name, flags=re.IGNORECASE)
    case_name = re.sub(r"\s+Syllabus\s*$", "", case_name, flags=re.IGNORECASE)
    case_name = re.sub(r"\s+", " ", case_name).strip()
    if case_name != original:
        logger.info(f"[CONTEXT-BLEED-CLEAN] Removed: '{original}' -> '{case_name}'")
    return case_name


def remove_citation_references_from_name(case_name: str) -> str:
    """
    Remove citation references that were incorrectly included in case names.

    Args:
        case_name: Case name that may contain citation references

    Returns:
        Cleaned case name
    """
    if not case_name:
        return case_name

    original = case_name

    # Remove citation patterns at the end
    # Matches: ", 148 Wn.2d 224, 239" or ", 159 Wn.2d 700" etc.
    patterns = [
        r",\s*\d+\s+(?:Wn\.2d|Wash\.2d|Wn\.\s*App\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$",
        r",\s*\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$",
        r",\s*\d+\s+(?:P\.2d|P\.3d|P\.)\s+\d+(?:\s*,\s*\d+)?$",
        r",\s*\d+\s+(?:F\.2d|F\.3d|F\.\s*Supp\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$",
        r",\s*\d+\s+[A-Z][A-Za-z\.]+\s+\d+(?:\s*,\s*\d+)?$",
    ]

    for pattern in patterns:
        case_name = re.sub(pattern, "", case_name, flags=re.IGNORECASE)

    # Clean up trailing commas
    case_name = re.sub(r"\s*,\s*$", "", case_name).strip()

    if case_name != original:
        logger.info(f"[CITATION-REF-CLEAN] Removed citation: '{original}' -> '{case_name}'")

    return case_name


def clean_extracted_case_name(case_name: str, context: str = "") -> str:
    """
    Comprehensive cleaning of extracted case names.

    Args:
        case_name: Extracted case name
        context: Surrounding context for fixing truncation

    Returns:
        Cleaned case name
    """
    if not case_name or case_name in ("N/A", "Unknown", "Unknown Case"):
        return case_name

    # Step 1: Normalize bold/italic (markdown, HTML, Unicode) to plain text
    cleaned = normalize_bold_italic_to_plain(case_name)
    # Step 1b: Remove any remaining markdown (leading #, >, etc.)
    cleaned = clean_markdown_contamination(cleaned)

    # Step 2: Remove context bleed (Americancourts., Syllabusmat)
    cleaned = remove_context_bleed_from_name(cleaned)

    # Step 3: Remove citation references
    cleaned = remove_citation_references_from_name(cleaned)

    # Step 4: Fix truncation
    cleaned = fix_truncation_at_word_boundary(cleaned, context)

    # Step 5: Final cleanup
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Validate result
    if len(cleaned) < 3 or " v. " not in cleaned.lower():
        logger.warning(f"[EXTRACTION-CLEAN] Result may be invalid: '{cleaned}'")

    return cleaned


__all__ = [
    "normalize_bold_italic_to_plain",
    "normalize_citation_text",
    "normalize_to_ascii_display",
    "clean_markdown_contamination",
    "fix_truncation_at_word_boundary",
    "remove_context_bleed_from_name",
    "remove_citation_references_from_name",
    "clean_extracted_case_name",
]
