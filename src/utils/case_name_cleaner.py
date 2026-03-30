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
        r"\bCorp\.": "Corporation",
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
        # Exclude "In" when part of "In re" (case name prefix) - preserve "In re Rosier"
        r"^(Quoting|Citing|See|In(?!\s+re\s)|As|where|when|while)\s+",
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

    # Brief TOA lines often prefix case names (e.g. "TABLE OF AUTHORITIES Federal Cases Chapman v. ...")
    name = re.sub(r"^TABLE\s+OF\s+AUTHORITIES\s+", "", name, flags=re.IGNORECASE).strip()
    name = re.sub(r"^Federal\s+Cases\s+", "", name, flags=re.IGNORECASE).strip()

    # Fix "Nat' Life" / "Nat' L" (split apostrophe) so expand_abbreviations can normalize Nat'l -> National
    name = re.sub(r"\bNat'\s+Life\b", "Nat'l Life", name, flags=re.IGNORECASE)
    name = re.sub(r"\bNat'\s+L\b", "Nat'l", name, flags=re.IGNORECASE)

    # Fix PDF/OCR accent corruption: "Garc A-Ayala" (í lost) -> "Garcia-Ayala" (ASCII for v. regex)
    name = re.sub(r"\bGarc\s+A\s*-\s*([A-Z][a-z]+)\b", r"Garcia-\1", name, flags=re.IGNORECASE)

    # "A.V." split across PDF tokenization: "A v. Ex Rel. Vanderhye" -> "A.V. ex rel. Vanderhye"
    name = re.sub(
        r"^A\s+v\.\s+Ex\s+Rel\.\s+",
        "A.V. ex rel. ",
        name,
        flags=re.IGNORECASE,
    )
    # Common publisher initialism mangled by lowercasing
    name = re.sub(r"\bA&m\b", "A&M", name, flags=re.IGNORECASE)

    # Fix PDF line-break hyphenation (e.g., "Co- hens" -> "Cohens", "Vir- ginia" -> "Virginia")
    # Pattern: word fragment + hyphen/dash + whitespace(s) + lowercase continuation
    # Use \s+ to catch all whitespace types (regular space, non-breaking space \xa0, etc.)
    # Normalize unicode dashes to ASCII hyphen, then fix explicit hyphen line-wrap
    # artifacts only (e.g. "Mar- bury" -> "Marbury"). Do NOT collapse plain spaces,
    # otherwise valid names become "Doev." / "Cityof".
    name = name.replace("\u2013", "-").replace("\u2014", "-")
    name = re.sub(r"(\w)-\s+([a-z])", r"\1\2", name)

    # Issue 6 fix: collapse expanded "Corporation." (from Corp.) back to "Corporation"
    # expand_abbreviations converts Corp. -> Corporation but leaves the "." behind
    name = re.sub(r'\bCorporation\.(?=\s|,|;|$)', 'Corporation', name)

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

    # Issue 1 fix: merge PDF/OCR-split abbreviations where "v." is part of the word, not a party separator.
    # Applies only inside the DEFENDANT (after the first real "v.") to avoid clobbering
    # legitimate "De La Cruz v. Smith" style names.
    _first_v = re.search(r'\s+v\.\s+', name)
    if _first_v:
        _before_v = name[:_first_v.end()]
        _after_v = name[_first_v.end():]
        _split_abbrev = [
            (r'\bDe\s+v\.\s+', 'Dev. '),    # Ritz-Carlton De v. Co -> Dev. Co
            (r'\bSer\s+v\.\s*', 'Serv. '), # Mobile Fleet Ser v., Inc -> Serv.
            (r'\bUni\s+v\.\s+', 'Univ. '), # La. State Uni v. Med -> Univ.
            (r'\bDi\s+v\.\s+', 'Div. '),   # Di v. Corp -> Div. Corp
            (r'\bIn\s+v\.\s+(?=[A-Z])', 'Inv. '),  # Private In v. Corp -> Inv. Corp
        ]
        for _pat, _rep in _split_abbrev:
            _after_v = re.sub(_pat, _rep, _after_v)
        name = _before_v + _after_v

    # Issue 3 fix: strip US state section-header contamination from the start of case names.
    # The "Basic Legal Citation" book (and similar) organises by state; the first case in each
    # section gets the state name prepended (e.g. "Tennessee Lawson v. Hawkins Co").
    # Safety: do NOT strip when the state name is part of a company name (e.g. "Nevada Motor Coach").
    _COMPANY_STARTERS = {
        'motor', 'coach', 'bus', 'power', 'gas', 'electric', 'energy', 'mutual',
        'bank', 'capital', 'fund', 'fire', 'central', 'western', 'eastern',
        'northern', 'southern', 'pacific', 'atlantic', 'inland', 'express',
        'national', 'general', 'first', 'second', 'standard', 'premier',
    }
    _STATE_PREFIX_RE = re.compile(
        r'^(?:Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|'
        r'Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|'
        r'Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|'
        r'Mississippi|Missouri|Montana|Nebraska|Nevada|New\s+Hampshire|'
        r'New\s+Jersey|New\s+Mexico|New\s+York|North\s+Carolina|North\s+Dakota|'
        r'Ohio|Oklahoma|Oregon|Pennsylvania|Rhode\s+Island|South\s+Carolina|'
        r'South\s+Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|'
        r'West\s+Virginia|Wisconsin|Wyoming|District\s+(?:Columbia|of\s+Columbia))\s+',
        re.IGNORECASE
    )
    _sm = _STATE_PREFIX_RE.match(name)
    if _sm:
        _remainder = name[_sm.end():]
        _next_word = _remainder.split()[0].rstrip('.,;').lower() if _remainder.split() else ''
        if _next_word not in _COMPANY_STARTERS and ' v. ' in _remainder.lower():
            name = _remainder

    # Issue 4 fix: strip leading citation fragments that contaminate case names.
    # Patterns like "Garrelts 23 N.W. NI Indus. v. ..." or "Farrar Oil Co. 1997 ND 31 12 Cont'..."
    # where citation text or a prior defendant name bleeds into the next case name.
    _FRAG_PATTERNS = [
        # Leading citation fragment: "Word 123 Abbr. 456 RealCase v. Def"
        r'^[A-Z][a-z]+\s+\d+\s+(?:[A-Z]\.?\s*){1,3}\d+\s+(?=[A-Z])',
        # Leading name + neutral citation: "Word YEAR Reporter NUM RealCase v. Def"
        r'^[A-Z][A-Za-z .]*?\s+\d{4}\s+[A-Z]{2,4}\s+\d+\s+\d+\s+(?=[A-Z][a-z])',
        # Trailing apostrophe fragment at start: "Name' RealCase v. Def"
        r"^[A-Z][a-z']+[']\s+(?=[A-Z])",
    ]
    for _fp in _FRAG_PATTERNS:
        _fm = re.match(_fp, name)
        if _fm:
            _candidate = name[_fm.end():]
            if ' v. ' in _candidate.lower():
                name = _candidate
                break

    # Remove leading punctuation and whitespace
    name = re.sub(r"^[\s\.,;:]+", "", name)
    # Remove trailing punctuation and whitespace
    name = re.sub(r"[\s\.,;:]+$", "", name)

    # Remove obvious prose/sentence starters before a case name
    # (Consolidated from case_name_cleaner + text_normalizer leading patterns)
    cleanup_patterns = [
        # Docket number prefix (e.g. "Trump No. 24-1287 Learning Resources" -> "Learning Resources")
        r"^[A-Za-z]+\s+No\.\s*\d+[-–](?:\w+[-–])?\d+\s+",
        r"^No\.\s*\d+[-–](?:\w+[-–])?\d+\s+",
        # "Dkt. No. 28)." or "(Dkt. No. 28)." or "No. 28)." prefix followed by optional page number
        r"^(?:\(?\s*)?(?:Dkt\.?\s*)?No\.?\s*\d+\s*\)\.?\s*(?:\d+\s+)?",
        # Prose before case name (e.g. "Generalis concurrently filing... in Trump v. Washington")
        r"^(?:Generalis|Parties?|Petitioner|Respondent)\s+concurrently\s+filing\s+a\s+petition\s+for\s+(?:a\s+)?writ\s+of\s+certiorari\s+in\s+",
        r"^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*",
        r"^(?:novo\.?\s+|de\s+novo\.?\s+)",
        # Court-attribution full sentences
        r"^The\s+(?:district|trial|circuit|state)\s+court\s+[^.]*\.\s*",
        r"^The\s+court\s+[^.]*\.\s*",
        # Single legal phrases (from text_normalizer) e.g. "court. Lopez" -> "Lopez"
        r"^(?:court|court\.|this\s+court|we\s+review|also\s+an?\s+issue|statutory\s+interpretation|questions?\s+of\s+law|de\s+novo|in\s+light\s+of|the\s+record\s+certified|federal\s+court)[\s\.]*",
        r"^(?:and|or|but|that|this|is|also|we\b|may|ask|resolution|of|question|necessary|to|resolve|case|before)[\s\.]*",
        r"^(?:see|citing|quoting|accord|id\.|ibid\.|brief\s+at|opening\s+br\.|reply\s+br\.)[\s\.]*",
        # Long de novo / issue-of-law phrases
        r"^[^A-Z]*an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
        r"^[^A-Z]*interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
        r"^[^A-Z]*statutory\s+interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*",
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

    # Truncated docket tail (PDF): ", No. C" with no case number before year/decision date
    name = re.sub(r",\s*No\.?\s+C\s*$", "", name, flags=re.IGNORECASE).strip()
    name = re.sub(r",\s*No\.?\s+C\s+(?=\d{4}\s*$)", ", ", name, flags=re.IGNORECASE).strip()

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
    # "Hawkinsex rel" (space between ex and rel) -> "Hawkins ex rel."
    name = re.sub(r"\b([A-Za-z]{4,})ex\s+rel\.?\b", r"\1 ex rel.", name, flags=re.IGNORECASE)
    # "Rapuanoet al" (space between et and al) -> "Rapuano et al."
    name = re.sub(r"\b([A-Za-z]*[aeiouyAEIOUY])et\s+al\.?\b", r"\1 et al.", name, flags=re.IGNORECASE)
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

    # Remove context bleed: "Americancourts. Spokeo" -> "Spokeo", "American courts. X" -> "X"
    from src.utils.extraction_cleaner import remove_context_bleed_from_name
    name = remove_context_bleed_from_name(name)

    # First-capital fallback (from text_normalizer): if still leading lowercase junk, slice from first capital
    if name and len(name) > 1 and not name[0].isupper():
        first_cap = re.search(r"[A-Z]", name)
        if first_cap:
            name = name[first_cap.start() :].strip()

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

    # Ensure all Unicode is converted to ASCII for display (ligatures, smart quotes, math symbols, accents)
    from src.utils.extraction_cleaner import normalize_to_ascii_display
    return normalize_to_ascii_display(name)
