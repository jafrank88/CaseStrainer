import re


def extract_case_name_from_context(context_before: str) -> str:
    """
    Attempt to extract a probable case name from the text before a citation.
    Looks for patterns like 'Smith v. Jones', 'In re Estate of ...', etc.
    Returns the case name if found, otherwise returns ''.
    """
    # Look for common case name patterns (last 100 chars)
    context = context_before[-100:]
    # Pattern: e.g., Smith v. Jones, In re Estate of Smith
    patterns = [
        r"([A-Z][A-Za-z\'\-]+\s+v\.\s+[A-Z][A-Za-z\'\-]+)",
        r"(In\s+re\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)",
        r"(Estate\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)",
        r"(Matter\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)",
        r"(Ex\s+parte\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, context))
        if matches:
            # Return the last match (closest to citation)
            return matches[-1].group(1)
    return ""
