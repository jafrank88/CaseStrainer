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
    s = fix_f3d_volume_comma_glitch(s)
    # Strip PDF bleed: prior line's "E.D.Mich.1985)" glued before "712 F.2d ..." (no space before year).
    _bleed = re.compile(
        r"^\s*(?:[A-Z]\.)+[A-Za-z]*\.?(?:19\d{2}|20\d{2})\)\s+(?=\d+\s+)",
        re.IGNORECASE,
    )
    while True:
        m = _bleed.match(s)
        if not m:
            break
        s = s[m.end() :].lstrip()
    # TOA / line-wrap glue: Chapman v. California is 386 U.S. 18 (1967), not 188.
    s = re.sub(r"\b386\s+U\.\s*S\.\s+188\b", "386 U.S. 18", s, flags=re.IGNORECASE)
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
        logger.debug("Suppressed exception", exc_info=True)
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

    # PDF breaks inside domains (e.g. Amazon. com)
    cleaned = fix_pdf_domain_dot_spacing(cleaned)

    # Step 2: Remove context bleed (Americancourts., Syllabusmat)
    cleaned = remove_context_bleed_from_name(cleaned)

    # Step 3: Remove citation references
    cleaned = remove_citation_references_from_name(cleaned)

    # Step 4: Fix truncation
    cleaned = fix_truncation_at_word_boundary(cleaned, context)

    # Step 5: Fix duplicate corporate suffixes (Inc., LLC, etc.)
    # Pattern: "Inc. , Inc." -> "Inc."
    # Pattern: "LLC , LLC" -> "LLC"
    suffixes = ["Inc\\.", "LLC", "Corp\\.", "Ltd\\.", "Co\\.", "L\\.P\\.", "LLP"]
    for suffix in suffixes:
        # Fix "Inc. , Inc." -> "Inc."
        cleaned = re.sub(rf"{suffix}\s*,\s*{suffix}", suffix, cleaned, flags=re.IGNORECASE)
        # Fix "Inc., Inc." -> "Inc."
        cleaned = re.sub(rf"{suffix},\s*{suffix}", suffix, cleaned, flags=re.IGNORECASE)
        # Fix "Inc. Inc." -> "Inc."
        cleaned = re.sub(rf"{suffix}\s+{suffix}", suffix, cleaned, flags=re.IGNORECASE)
    
    # Step 6: Fix spacing around commas
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)  # " , " -> ", "
    cleaned = re.sub(r",\s*,", ", ", cleaned)  # ", ," -> ", "
    
    # Step 7: Final cleanup
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Validate result
    if len(cleaned) < 3 or " v. " not in cleaned.lower():
        logger.warning(f"[EXTRACTION-CLEAN] Result may be invalid: '{cleaned}'")

    return cleaned


def fix_pdf_domain_dot_spacing(text: str) -> str:
    """
    Repair PDF line/column breaks inside domains: ``Amazon. com`` -> ``Amazon.com``.
    Runs a few passes for chained fragments (``. co . uk`` is rare in case law).
    """
    if not text:
        return text
    s = text.replace("\uff0e", ".").replace("\u3002", ".")
    for _ in range(5):
        s2 = re.sub(
            r"\b([A-Za-z][A-Za-z.'\-]*)\.\s+(com|org|net|edu|gov|io|co)\b",
            r"\1.\2",
            s,
            flags=re.IGNORECASE,
        )
        if s2 == s:
            break
        s = s2
    return s


def fix_pdf_titlecase_org_token_breaks(text: str) -> str:
    """
    Repair PDF breaks in multi-token org names before ``Org``:
    ``Public. Resource. Org`` -> ``Public.Resource.Org`` (common in Public.Resource.Org survey cites).
    Conservative: requires TitleCase.TitleCase.Org only.
    """
    if not text:
        return text
    s = text.replace("\uff0e", ".").replace("\u3002", ".")
    for _ in range(4):
        s2 = re.sub(
            r"\b([A-Z][a-z]{1,30})\.\s+([A-Z][a-z]{1,30})\.\s+(Org)\b",
            r"\1.\2.\3",
            s,
        )
        if s2 == s:
            break
        s = s2
    return s


def fix_limited_partnership_abbrev_spacing(text: str) -> str:
    """Normalize ``L. P.`` / ``l. p.`` (PDF spaces) to ``L.P.`` in party names."""
    if not text:
        return text
    return re.sub(r"\bL\.\s+P\.\b", "L.P.", text, flags=re.IGNORECASE)


def fix_f3d_volume_comma_glitch(text: str) -> str:
    """
    Repair ``756, 50 F.3d 73`` artifacts: volume and reporter split so a 1–2 digit
    fragment is glued between volume and ``F.3d``. Keeps ``12, 50 F.3d`` unchanged
    (volume 12 < 100 guard).
    """

    def repl(m: re.Match) -> str:
        v, mid, page = m.group(1), m.group(2), m.group(3)
        try:
            iv, imid = int(v), int(mid)
        except ValueError:
            return m.group(0)
        if iv >= 100 and imid < iv and imid <= 99:
            return f"{v} F.3d {page}"
        return m.group(0)

    return re.sub(
        r"\b(\d{3,4}),\s*(\d{1,2})\s+F\.3d\s+(\d+)\b",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def apply_pre_extraction_text_fixes(text: str) -> str:
    """
    Full-document fixes before eyecite/regex (PDF survey / law-review layouts).
    Safe for unseen documents: conservative patterns only.
    """
    if not text:
        return text
    s = text.replace("\uff0e", ".").replace("\u3002", ".")
    s = fix_pdf_domain_dot_spacing(s)
    s = fix_pdf_titlecase_org_token_breaks(s)
    s = fix_f3d_volume_comma_glitch(s)
    s = merge_s_ct_page_split_in_string(s)
    return s


# --- Supreme Court Reporter (S. Ct.) PDF / eyecite repair ---


def _merge_s_ct_page_fragments(vol: str, a: str, b: str) -> Optional[str]:
    """If a+b is a plausible S. Ct. page (3-4 digits, 100-9999), return merged cite body."""
    if not a.isdigit() or not b.isdigit():
        return None
    comb = a + b
    if len(comb) < 3 or len(comb) > 4:
        return None
    n = int(comb)
    if 100 <= n <= 9999:
        return f"{vol} S. Ct. {comb}"
    return None


def merge_s_ct_page_split_in_string(text: str) -> str:
    """
    Join S. Ct. page digits split across whitespace (e.g. PDF line break became space).
    Skips when the second number starts a following U.S. cite.
    """
    if not text or "S." not in text and "s." not in text:
        return text

    def repl(m: re.Match) -> str:
        merged = _merge_s_ct_page_fragments(m.group(1), m.group(2), m.group(3))
        return merged if merged else m.group(0)

    return re.sub(
        r"\b(\d{2,3})\s+S\.\s*Ct\.\s+(\d{1,3})\s+(\d{1,3})\b(?!\s+U\.\s*S\.)",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def merge_s_ct_page_split_across_newline(text: str) -> str:
    """Same as merge_s_ct_page_split_in_string but for newline between page fragments."""

    def repl(m: re.Match) -> str:
        merged = _merge_s_ct_page_fragments(m.group(1), m.group(2), m.group(3))
        return merged if merged else m.group(0)

    return re.sub(
        r"(\d{2,3})\s+[Ss]\.\s*[Cc]t\.?\s+(\d{1,3})\s*[\n\r]+\s*(\d{1,3})\b",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def strip_absorbed_prose_after_s_ct_or_led2d(citation_str: str) -> str:
    """
    Eyecite sometimes includes the next sentence or bracket citation in the S. Ct. / L. Ed. 2d span.
    Trim at the first clear prose boundary after a valid reporter+page core.
    """
    if not citation_str:
        return citation_str
    s = citation_str.strip()

    m = re.match(
        r"^(\d{2,3}\s+S\.\s*Ct\.\s+\d{2,4})\s*([\.,])\s+(As\s+stated|Whether\s+the|But\s+as|Question\s+\d|The\s+following)\b",
        s,
        re.IGNORECASE,
    )
    if m:
        return m.group(1)

    m = re.match(
        r"^(\d{2,3}\s+S\.\s*Ct\.\s+\d{2,4})\s*\[\s*",
        s,
        re.IGNORECASE,
    )
    if m and len(s) > len(m.group(1)) + 8:
        return m.group(1)

    m = re.match(
        r"^(\d+\s+L\.\s*Ed\.\s*2d\s+\d+)\s*([\.,])\s+(As\s+stated|Whether\s+the|But\s+as)\b",
        s,
        re.IGNORECASE,
    )
    if m:
        return m.group(1)

    return citation_str


def reconcile_eyecite_scotus_suffix_year(citation_str: str, lookup_text: str) -> str:
    """
    Eyecite can append ``(scotus YYYY)`` using a wrong year when the Table of Authorities
    packs many cites on one line (e.g. ``603 U.S. 369 (2024)... Melendez ... (1991)``).

    If the same volume + U.S. + page appears in the citation or lookup text with a plain
    ``(YYYY)`` parenthetical, use that year for the ``(scotus YYYY)`` suffix.
    """
    if not citation_str or "(scotus" not in citation_str.lower():
        return citation_str
    if not re.search(r"\(scotus\s+\d{4}\s*\)", citation_str, re.I):
        return citation_str
    vp = re.search(r"\b(\d+)\s+U\.\s*S\.\s+(\d+)", citation_str, re.I)
    if not vp:
        return citation_str
    v, p = vp.group(1), vp.group(2)
    hunter = re.compile(
        rf"\b{re.escape(v)}\s+U\.\s*S\.\s+{re.escape(p)}\s*\((\d{{4}})\)",
        re.I,
    )
    wrong_m = re.search(r"\(scotus\s+(\d{4})\s*\)", citation_str, re.I)
    wrong_y = wrong_m.group(1) if wrong_m else ""
    for blob in (citation_str, lookup_text or ""):
        m = hunter.search(blob)
        if not m:
            continue
        doc_y = m.group(1)
        if wrong_y and doc_y == wrong_y:
            return citation_str
        if 1900 <= int(doc_y) <= 2035:
            fixed, n = re.subn(
                r"\(scotus\s+\d{4}\s*\)",
                f"(scotus {doc_y})",
                citation_str,
                count=1,
                flags=re.I,
            )
            if n:
                return fixed
    return citation_str


def snap_s_ct_citation_to_source_window(
    citation_str: str, full_text: str, start_idx: Optional[int]
) -> str:
    """
    When eyecite truncates the page (e.g. 24 vs 2429) or absorbs prose, prefer the S. Ct. cite
    found in the source text near the span start.
    """
    if start_idx is None or start_idx < 0 or not citation_str or "S. Ct." not in citation_str:
        return strip_absorbed_prose_after_s_ct_or_led2d(citation_str)
    if not full_text:
        return strip_absorbed_prose_after_s_ct_or_led2d(citation_str)
    win_s = max(0, start_idx - 45)
    win_e = min(len(full_text), start_idx + max(120, len(citation_str) + 40))
    win = full_text[win_s:win_e]
    candidates = list(re.finditer(r"\b(\d{2,3}\s+S\.\s*Ct\.\s+\d{3,4})\b", win, re.IGNORECASE))
    cur = citation_str.strip()
    if not candidates:
        return strip_absorbed_prose_after_s_ct_or_led2d(cur)
    best = min(candidates, key=lambda m: abs(win_s + m.start() - start_idx))
    good = best.group(1)
    vm_g = re.match(r"^(\d{2,3})\s+S\.\s*Ct\.\s+(\d{3,4})\b", good, re.IGNORECASE)
    if not vm_g:
        return strip_absorbed_prose_after_s_ct_or_led2d(cur)
    vol_g, pg = vm_g.group(1), vm_g.group(2)

    # Eyecite span may be "133 S. Ct. ..." at start, or "Name, 133 S. Ct. 22" with truncated page.
    vm_c = re.match(r"^(\d{2,3})\s+S\.\s*Ct\.\s+(\d{2,4})\b", cur, re.IGNORECASE)
    if vm_c and vm_c.group(1) == vol_g:
        pc = vm_c.group(2)
        if pc == pg:
            return strip_absorbed_prose_after_s_ct_or_led2d(cur)
        if pg.startswith(pc) and len(pg) > len(pc):
            return strip_absorbed_prose_after_s_ct_or_led2d(good)

    emb = re.search(r"\b(\d{2,3})\s+S\.\s*Ct\.\s+(\d{2,4})\b", cur, re.IGNORECASE)
    if emb:
        vol_e, pc = emb.group(1), emb.group(2)
        if vol_e == vol_g and pg.startswith(pc) and len(pg) > len(pc):
            fixed = cur[: emb.start(2)] + pg + cur[emb.end(2) :]
            return strip_absorbed_prose_after_s_ct_or_led2d(fixed)

    return strip_absorbed_prose_after_s_ct_or_led2d(cur)


__all__ = [
    "normalize_bold_italic_to_plain",
    "normalize_citation_text",
    "normalize_to_ascii_display",
    "clean_markdown_contamination",
    "fix_truncation_at_word_boundary",
    "remove_context_bleed_from_name",
    "remove_citation_references_from_name",
    "clean_extracted_case_name",
    "fix_pdf_domain_dot_spacing",
    "fix_pdf_titlecase_org_token_breaks",
    "fix_limited_partnership_abbrev_spacing",
    "fix_f3d_volume_comma_glitch",
    "apply_pre_extraction_text_fixes",
    "merge_s_ct_page_split_in_string",
    "merge_s_ct_page_split_across_newline",
    "strip_absorbed_prose_after_s_ct_or_led2d",
    "snap_s_ct_citation_to_source_window",
    "reconcile_eyecite_scotus_suffix_year",
]
