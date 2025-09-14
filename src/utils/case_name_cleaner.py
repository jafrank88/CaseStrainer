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
        # FIXED: Only remove non-alpha characters at the start, not entire words
        r'^[^A-Za-z]*',
    ]
    for pattern in cleanup_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # If the core "X v. Y" is present, trim around it to avoid extra prose
    v_match = re.search(r'([A-Z][A-Za-z0-9&\.\'\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.\'\s-]+)', name)
    if v_match:
        name = f"{v_match.group(1).strip()} v. {v_match.group(2).strip()}"

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name


