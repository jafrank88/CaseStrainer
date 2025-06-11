import re


def normalize_us_citation(citation_text):
    """Normalize U.S. citation format, handling extra spaces and ensuring U.S. format."""
    # Handle U.S. Reports citations with extra spaces, ensuring U.S. format
    us_match = re.match(r"(\d+)\s+U\.?\s*\.?\s*S\.?\s*\.?\s*(\d+)", citation_text)
    if us_match:
        volume, page = us_match.groups()
        # Always use U.S. format
        return f"{volume} U.S. {page}"
    return citation_text


# Test cases
test_citations = [
    "487 U. S. 879",
    "487 U.S. 879",
    "487 U.  S.  879",
    "487 U.S. 879",
    "487 U . S . 879",  # Added test case with spaces around dots
    "487 U.  S.  879",  # Added test case with extra spaces
]

print("Testing citation normalization:")
for citation in test_citations:
    normalized = normalize_us_citation(citation)
    print(f"Original: {citation}")
    print(f"Normalized: {normalized}")
    print()
