import re

# Re-export is_valid_case_name for easy access
from src.extraction.validation import is_valid_case_name  # noqa: F401


def expand_abbreviations(case_name: str) -> str:
    """Expand common legal abbreviations that get truncated."""
    if not case_name:
        return case_name

    abbreviations = {
        r"\bCommc'?\b": "Communications",
        r"\bTelecommc'?\b": "Telecommunications",
        r"\bCorp'?\b": "Corporation",
        r"\bInt'l\b": "International",
        r"\bNat'l\b": "National",
        r"\bDep't\b": "Department",
        r"\bGov't\b": "Government",
    }

    for pattern, replacement in abbreviations.items():
        case_name = re.sub(pattern, replacement, case_name, flags=re.IGNORECASE)

    return case_name


def remove_context_phrases(case_name: str) -> str:
    """Remove legal context phrases that get extracted with case names."""
    if not case_name:
        return case_name

    context_patterns = [
        r"^The\s+(dissent|majority|plurality|concurrence),?\s+(quoting|citing|in|from)\s+",
        r"^(Quoting|Citing|See|In|As|where|when|while)\s+",
        r"^(As|Where|When|While)\s+(?:the\s+)?(?:Court|dissent|majority)\s+(?:stated|noted|held)\s+in\s+",
    ]

    for pattern in context_patterns:
        case_name = re.sub(pattern, "", case_name, flags=re.IGNORECASE)

    return case_name.strip()


def clean_extracted_case_name(case_name: str) -> str:
    """Shared cleaner for extracted case names.

    - Strips leading/trailing debris and sentence fragments
    - Preserves parties around "v." and common legal tokens (of, the, &)
    - Avoids contaminating with citation text or prose
    """
    if not case_name:
        return case_name

    name = case_name

    # Fix PDF line-break hyphenation (e.g., "Co- hens" -> "Cohens", "Vir- ginia" -> "Virginia")
    # Pattern: word fragment + hyphen/dash + whitespace(s) + lowercase continuation
    # Use \s+ to catch all whitespace types (regular space, non-breaking space \xa0, etc.)
    # Normalize unicode dashes to ASCII hyphen, then fix explicit hyphen line-wrap
    # artifacts only (e.g. "Mar- bury" -> "Marbury"). Do NOT collapse plain spaces,
    # otherwise valid names become "Doev." / "Cityof".
    name = name.replace("\u2013", "-").replace("\u2014", "-")
    name = re.sub(r"(\w)-\s+([a-z])", r"\1\2", name)

    # FIX 2026-02-04: Handle cases where PDF extraction removed the hyphen entirely
    # Pattern: "Swin dle" -> "Swindle", "Gard ner" -> "Gardner", "Labo ratories" -> "Laboratories"
    # Match: Capital letter + word fragment + space + lowercase fragment (looks like split word)
    # Be conservative to avoid joining "A dog" or "The court"
    def rejoin_split_words(match):
        """Rejoin word fragments that were split by PDF line breaks."""
        part1 = match.group(1)
        part2 = match.group(2)
        combined = part1 + part2

        # Don't rejoin common standalone words
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was',
            'one', 'our', 'out', 'has', 'his', 'how', 'its', 'may', 'new', 'now', 'old',
            'see', 'two', 'way', 'who', 'did', 'get', 'let', 'put', 'say', 'she', 'too',
            'use', 'of', 'in', 'on', 'at', 'to', 'by', 'from', 'with', 'vs', 'v'
        }
        if part1.lower() in common_words or part2.lower() in common_words:
            return match.group(0)

        # Rejoin if:
        # 1. First part is 2+ chars (not just "A" or "I")
        # 2. Second part is 2+ chars
        # 3. Combined word looks reasonable (3+ chars)
        if len(part1) >= 2 and len(part2) >= 2 and len(combined) >= 5:
            return combined

        return match.group(0)  # Keep original if not confident

    # Match patterns like "Swin dle", "Gard ner", "Labo ratories"
    # First part: capital + letters, 2-10 chars
    # Second part: lowercase letters, 2-10 chars
    name = re.sub(r'\b([A-Z][a-z]{1,9})\s+([a-z]{2,10})\b', rejoin_split_words, name)

    # Remove leading punctuation and whitespace
    name = re.sub(r"^[\s\.,;:]+", "", name)
    # Remove trailing punctuation and whitespace
    name = re.sub(r"[\s\.,;:]+$", "", name)

    # Remove obvious prose/sentence starters before a case name
    cleanup_patterns = [
        r"^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*",
        # Remove "novo" and similar legal terms at the start
        r"^(?:novo\.?\s+|de\s+novo\.?\s+)",
        # REMOVED: r'^[^A-Za-z]*' - This was destroying valid case names like "Spokeo, Inc."
        # Only remove specific punctuation at start, not letters
        r"^[\s\.,;:!?\-]*",
    ]
    for pattern in cleanup_patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    # CRITICAL FIX: Remove trailing years and dates from case names
    # Patterns like ", 2020", ", 2020-06-26", " (2020)", etc.
    # This prevents document publication years from contaminating case names
    # ENHANCED: Also remove years that appear anywhere in the name (not just trailing)
    # This handles cases where extraction patterns match "Case Name, 2020" as a single match
    trailing_year_patterns = [
        r",\s*\d{4}(?:-\d{2}-\d{2})?\s*$",  # ", 2020" or ", 2020-06-26" at end
        r"\s+\(\d{4}\)\s*$",  # " (2020)" at end
        r",\s*\d{4}\s*$",  # ", 2020" at end (more specific)
        r",\s*\d{4}(?:-\d{2}-\d{2})?\s*(?=,|$|;)",  # ", 2020" anywhere before comma/semicolon/end
        r"\s+\(\d{4}\)\s*(?=,|$|;)",  # " (2020)" anywhere before comma/semicolon/end
    ]
    for pattern in trailing_year_patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    
    # ENHANCED: Also remove standalone years (>= 2020) that appear after case names
    # This catches cases like "Davis v. Federal Election Comm'n, 2020" where year is part of extraction
    # Only remove recent years (>= 2020) to avoid removing valid case years like "2008"
    # CRITICAL: Remove years >= 2020 anywhere in the name (not just at end)
    recent_year_patterns = [
        r",\s*(20[2-9]\d|2[1-9]\d{2})\s*(?=,|$|;|\.)",  # ", 2020" before comma/semicolon/period/end
        r",\s*(20[2-9]\d|2[1-9]\d{2})\s*$",  # ", 2020" at end
        r"\s+(20[2-9]\d|2[1-9]\d{2})\s*(?=,|$|;|\.)",  # " 2020" before punctuation/end
    ]
    for pattern in recent_year_patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    
    # FINAL SAFEGUARD: If name still contains "2020" or similar, remove it aggressively
    # This handles edge cases where patterns didn't catch it (e.g., "Davis v. Federal Election Comm'n, 2020")
    if re.search(r"20[2-9]\d", name):
        # Find and remove any occurrence of "2020" or similar years
        name = re.sub(r",?\s*20[2-9]\d\s*,?\s*", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+20[2-9]\d\s*", " ", name, flags=re.IGNORECASE)
        name = re.sub(r"20[2-9]\d\s*", "", name, flags=re.IGNORECASE)
        # Clean up any double spaces or trailing commas
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r",\s*$", "", name)

    # If the core "X v. Y" is present, trim around it to avoid extra prose
    v_match = re.search(r"([A-Z][A-Za-z0-9&\.\',\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.\',\s-]+)", name)
    if v_match:
        name = f"{v_match.group(1).strip()} v. {v_match.group(2).strip()}"

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Repair commonly joined legal tokens from PDF/OCR artifacts.
    # Examples: "Hawkinsexrel." -> "Hawkins ex rel.", "Rapuanoetal." -> "Rapuano et al."
    name = re.sub(r"\b([A-Za-z]{3,})\s*exrel\.?\b", r"\1 ex rel.", name, flags=re.IGNORECASE)
    name = re.sub(r"\bexrel\.?\b", "ex rel.", name, flags=re.IGNORECASE)
    name = re.sub(r"\b([A-Za-z]{3,})\s*etal\.?\b", r"\1 et al.", name, flags=re.IGNORECASE)
    name = re.sub(r"\betal\.?\b", "et al.", name, flags=re.IGNORECASE)
    name = re.sub(r"\bet\s+al\s*\b", "et al.", name, flags=re.IGNORECASE)
    # Clean punctuation artifacts from OCR/token-join repairs, e.g. "ex rel. ."
    name = re.sub(r"\bex\s+rel\.\s*\.\s*", "ex rel. ", name, flags=re.IGNORECASE)
    name = re.sub(r"\bet\s+al\.\s*\.\s*", "et al. ", name, flags=re.IGNORECASE)
    name = re.sub(r"\.\s+\.", ".", name)
    name = re.sub(r"\s+([,.;:])", r"\1", name)

    # Expand abbreviations (Commc' -> Communications)
    name = expand_abbreviations(name)

    # Remove context phrases ("The dissent, quoting")
    name = remove_context_phrases(name)

    # IMPROVED: Contamination filtering - reject case names that contain legal procedural text
    if name and len(name) > 3:
        import logging

        logger = logging.getLogger(__name__)

        # Check for legal procedural words that indicate contamination
        legal_words = [
            "accepted",
            "certification",
            "analysis",
            "defendant",
            "argue",
            "applicants",
            "employment",
            "standing",
            "statute",
            "injury",
            "decline",
            "address",
            "scope",
            "question",
            "issue",
            "review",
            "court",
            "held",
            "ruling",
            "decision",
        ]
        word_count = sum(1 for word in legal_words if word.lower() in name.lower())

        if word_count >= 2:  # Too many legal procedural words
            logger.warning(
                f"[CONTAMINATION] Rejected case name '{name}' - contains {word_count} legal procedural words"
            )
            return "N/A"

        # Check for sentence-like structures that indicate contamination
        # Only check for clear sentence indicators, not period-space which can be in valid case names
        sentence_indicators = [" and by the ", " are that ", " who do not ", " we decline to ", " as it is beyond "]

        if any(indicator in name for indicator in sentence_indicators):
            logger.warning(f"[CONTAMINATION] Rejected case name '{name}' - contains sentence structure")
            return "N/A"

        # Check if too long (likely contaminated with legal text)
        if len(name) > 150:  # Reasonable case name length limit
            logger.warning(f"[CONTAMINATION] Rejected case name '{name}' - too long ({len(name)} chars)")
            return "N/A"

    return name
