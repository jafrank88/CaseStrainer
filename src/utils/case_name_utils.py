"""
Case name utilities - single source of truth for clean_case_name and is_valid_case_name.

Use this module everywhere to avoid duplication. Extraction, clustering, and
verification should import from here.

  from src.utils.case_name_utils import clean_case_name, is_valid_case_name
"""

import re
from typing import Optional


def clean_case_name(name: str) -> str:
    """
    Clean and normalize a case name.

    Removes:
    - Leading/trailing whitespace
    - Extra spaces
    - Common citation prefixes (see, see also, cf., e.g., etc.)
    - Trailing punctuation
    """
    if not name:
        return ""

    name = name.strip()
    name = re.sub(r"\s+", " ", name)

    fragments_to_remove = [
        "see ",
        "see, ",
        "see also ",
        "see, e.g., ",
        "cf. ",
        "e.g., ",
        "i.e., ",
        "accord ",
        "contra ",
        "but see ",
        "compare ",
        "citing ",
        "quoted in ",
    ]
    name_lower = name.lower()
    for fragment in fragments_to_remove:
        if name_lower.startswith(fragment):
            name = name[len(fragment) :].strip()
            name_lower = name.lower()

    name = name.rstrip(",.;:")
    return name


def is_valid_case_name(name: str) -> bool:
    """
    Quick check if a string is a plausible case name.

    Returns True only if the name has minimal structure (e.g. "v." or "In re")
    and does not look like a statute, citation text, or truncated/fragment.
    """
    if not name or not name.strip():
        return False

    name = name.strip()

    # Too short to be a real case name
    if len(name) < 10:
        return False

    # Should have v. / In re / Ex parte
    has_vs = any(m in name.lower() for m in [" v.", " v ", " vs.", " vs "])
    has_in_re = name.lower().startswith("in re ")
    has_ex_parte = name.lower().startswith("ex parte ")
    if not (has_vs or has_in_re or has_ex_parte):
        return False

    # Truncation
    if name.endswith("...") or name.endswith(".."):
        return False

    # Statute-like
    statute_words = ["act", "code", "statute", "regulation", "title", "section"]
    if any(w in name.lower() for w in statute_words):
        return False

    # Citation contamination
    citation_patterns = [
        r"\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed|F\.\d*d|F\.\s*Supp)",
        r"\d+\s+(?:Wn\.|Wash\.|P\.\d*d|A\.\d*d)",
    ]
    for pattern in citation_patterns:
        if re.search(pattern, name):
            return False

    # Opinion/judge contamination
    bad = ("opinion of the court", "j., dissenting", "j., concurring", "c.j.,")
    if any(b in name.lower() for b in bad):
        return False

    return True


def clean_case_name_contamination(extracted_name: str, canonical_name: Optional[str] = None) -> str:
    """
    Centralized version of the contamination cleaner from unified_processing_pipeline.

    Args:
        extracted_name: The potentially contaminated extracted case name
        canonical_name: The verified canonical case name (optional, currently unused)

    Returns:
        Cleaned case name (or \"N/A\" when rejected)
    """
    if not extracted_name or extracted_name == "N/A":
        return extracted_name

    cleaned = extracted_name

    # Court procedural text (common in briefs) or generic narrative text
    procedural_contamination_patterns = [
        r"^(?:Wash\.|Washington|Or\.|Oregon|Cal\.|California)\s+(?:Sup\.|Supreme)\s+(?:Ct\.|Court)\s+(?:oral\s+arg\.|argument)",
        r"^(?:oral\s+arg(?:ument)?\.?|argument)\s*,?\s*",
        r"^(?:We\s+interpret|The\s+court|This\s+court|As\s+stated)",
        r"^(?:quoting|citing|following|accord|see\s+also|but\s+see)",
        # Strip leading sentence fragments that end right before a real citation
        r"^[a-z][^A-Z]*\s+([A-Z][a-zA-Z\s'&\-\.,]+\s+v\.\s+[A-Z][a-zA-Z\s'&\-\.,]+)",
    ]

    # Strip TOA header prefixes (e.g. "Cases-Continued: Page Murray v. ...")
    cleaned = re.sub(
        r'^(?:TABLE\s+OF\s+AUTHORITIES\s+)?(?:(?:I{1,3}V?|V?I{0,3})\s+)?'
        r'Cases(?:[-]Continued)?(?:\s*:\s*|\s+)(?:Page\s+)?',
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(r"^Page\s+(?=[A-Z])", "", cleaned).strip()

    # Strip docket numbers: ", No. 2", ", No. CV 25", bare ", No"
    cleaned = re.sub(
        r",\s*No\.?\s*(?:[\w\-\.]+(?:\s+[\w\-\.]+)*)?\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Strip trailing commas, numbers, junk (e.g. ", , 1337, 2020")
    cleaned = re.sub(r"(?:,\s*)+(?:\d{1,5}\s*,?\s*)*$", "", cleaned).strip()
    cleaned = cleaned.rstrip(",").strip()

    # First pass: detect if the entire name is procedural text (reject)
    for pattern in procedural_contamination_patterns[:3]:
        if re.match(pattern, cleaned, re.IGNORECASE):
            return "N/A"

    # Second pass: try to extract case name from contaminated text
    for pattern in procedural_contamination_patterns[3:]:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match and match.lastindex:
            cleaned = match.group(1).strip()
            break

    # Common signal word contamination patterns
    signal_patterns = [
        r"^(?:this\s+case\s+involves|the\s+case\s+involves|case\s+involves)\s+(.+)$",
        r"^(?:see\s+the\s+case|see\s+case|the\s+case|case)\s+(?:of\s+)?(.+)$",
        r"^(?:in\s+this\s+case|in\s+the\s+case|in\s+case),?\s+(.+)$",
        r"^(?:cf|e\.g\.|i\.e\.|see\s+also|see|compare|accord|but\s+see|but\s+cf|contra)\.?\s+(.+)$",
        r"^(?:if|when|where|while|although|though|unless|until|since|because|as)\s+(?:in\s+)?(.+)$",
    ]

    for pattern in signal_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
            break

    # Final validation: ensure it looks like a case name (has \"v.\" or is \"In re\")
    if cleaned and cleaned != "N/A":
        has_v = " v. " in cleaned or " v " in cleaned.lower()
        is_in_re = cleaned.lower().startswith("in re ") or cleaned.lower().startswith("in the matter")
        if not has_v and not is_in_re:
            if len(cleaned) < 15 or not re.search(r"[A-Z][a-z]+", cleaned):
                # Keep but caller may flag as suspicious
                return cleaned

    return cleaned


def is_document_case_contamination_post_process(
    extracted_name: str,
    document_primary_case_name: str,
    similarity_threshold: float = 0.95,
) -> bool:
    """
    Post-processing contamination check: Detect if extracted case name matches document's primary case name.

    This centralizes the logic previously embedded in UnifiedProcessingPipeline.
    """
    if not document_primary_case_name or not extracted_name or extracted_name == "N/A":
        return False

    from src.utils.unified_case_name_extractor import _is_document_case_contamination

    return _is_document_case_contamination(
        extracted_name,
        document_primary_case_name,
        similarity_threshold=similarity_threshold,
    )
