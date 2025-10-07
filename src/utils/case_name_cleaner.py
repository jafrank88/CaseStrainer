import re


def clean_extracted_case_name(case_name: str) -> str:
    """Shared cleaner for extracted case names.

    - Strips leading/trailing debris and sentence fragments
    - Preserves parties around "v." and common legal tokens (of, the, &)
    - Avoids contaminating with citation text or prose
    """
    if not case_name:
        return case_name

    name = case_name

    # Remove leading punctuation and whitespace
    name = re.sub(r'^[\s\.,;:]+', '', name)
    # Remove trailing punctuation and whitespace
    name = re.sub(r'[\s\.,;:]+$', '', name)

    # Remove obvious prose/sentence starters before a case name
    cleanup_patterns = [
        r'^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*',
        # Remove "novo" and similar legal terms at the start
        r'^(?:novo\.?\s+|de\s+novo\.?\s+)',
        # REMOVED: r'^[^A-Za-z]*' - This was destroying valid case names like "Spokeo, Inc."
        # Only remove specific punctuation at start, not letters
        r'^[\s\.,;:!?\-]*',
    ]
    for pattern in cleanup_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # If the core "X v. Y" is present, trim around it to avoid extra prose
    v_match = re.search(r'([A-Z][A-Za-z0-9&\.\'\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.\'\s-]+)', name)
    if v_match:
        name = f"{v_match.group(1).strip()} v. {v_match.group(2).strip()}"

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    # IMPROVED: Contamination filtering - reject case names that contain legal procedural text
    if name and len(name) > 3:
        import logging
        logger = logging.getLogger(__name__)
        
        # Check for legal procedural words that indicate contamination
        legal_words = ['accepted', 'certification', 'analysis', 'defendant', 'argue', 'applicants', 
                      'employment', 'standing', 'statute', 'injury', 'decline', 'address', 'scope',
                      'question', 'issue', 'review', 'court', 'held', 'ruling', 'decision']
        word_count = sum(1 for word in legal_words if word.lower() in name.lower())
        
        if word_count >= 2:  # Too many legal procedural words
            logger.warning(f"🚫 CONTAMINATION: Rejected case name '{name}' - contains {word_count} legal procedural words")
            return "N/A"
        
        # Check for sentence-like structures that indicate contamination
        # Only check for clear sentence indicators, not period-space which can be in valid case names
        sentence_indicators = [' and by the ', ' are that ', ' who do not ', ' we decline to ', ' as it is beyond ']
        
        if any(indicator in name for indicator in sentence_indicators):
            logger.warning(f"🚫 CONTAMINATION: Rejected case name '{name}' - contains sentence structure")
            return "N/A"
        
        # Check if too long (likely contaminated with legal text)
        if len(name) > 150:  # Reasonable case name length limit
            logger.warning(f"🚫 CONTAMINATION: Rejected case name '{name}' - too long ({len(name)} chars)")
            return "N/A"

    return name


