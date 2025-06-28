import re
from typing import List

def normalize_citation(citation: str) -> str:
    """
    Normalize a legal citation for best compatibility with external APIs.
    Handles Washington, federal, regional, and international reporters, plus general cleanup.
    """
    if not citation or not isinstance(citation, str):
        return ""

    # Replace multiple spaces with a single space and trim
    normalized = re.sub(r"\s+", " ", citation.strip())

    # Washington-specific normalization
    normalized = re.sub(r"Wn\.\s*App\.", "Wash. App.", normalized)
    normalized = re.sub(r"Wn\.\s*2d", "Wash. 2d", normalized)
    normalized = re.sub(r"Wn\.\s*3d", "Wash. 3d", normalized)
    normalized = re.sub(r"Wn\.", "Wash.", normalized)

    # Standardize regional/state reporters
    normalized = re.sub(r"Cal\.\s*App\.", "Cal. App.", normalized)
    normalized = re.sub(r"Cal\.\s*Rptr\.", "Cal. Rptr.", normalized)
    normalized = re.sub(r"N\.Y\.\s*App\.", "N.Y. App.", normalized)
    normalized = re.sub(r"Tex\.\s*App\.", "Tex. App.", normalized)
    normalized = re.sub(r"Fla\.\s*App\.", "Fla. App.", normalized)
    normalized = re.sub(r"Ill\.\s*App\.", "Ill. App.", normalized)
    normalized = re.sub(r"Ohio\s*App\.", "Ohio App.", normalized)
    normalized = re.sub(r"Mich\.\s*App\.", "Mich. App.", normalized)
    normalized = re.sub(r"Pa\.\s*Super\.", "Pa. Super.", normalized)
    normalized = re.sub(r"Mass\.\s*App\.", "Mass. App.", normalized)

    # International reporters
    normalized = re.sub(r"UKSC", "UKSC", normalized)
    normalized = re.sub(r"EWCA\s+Civ", "EWCA Civ", normalized)
    normalized = re.sub(r"EWHC", "EWHC", normalized)
    normalized = re.sub(r"SCC", "SCC", normalized)
    normalized = re.sub(r"FCA", "FCA", normalized)
    normalized = re.sub(r"FC", "FC", normalized)
    normalized = re.sub(r"HCA", "HCA", normalized)

    # General cleanup
    normalized = re.sub(r"[\u2013\u2014]", "-", normalized)  # em/en dashes
    normalized = re.sub(r"[\u2018\u2019]", "'", normalized)  # smart single quotes
    normalized = re.sub(r"[\u201C\u201D]", '"', normalized)  # smart double quotes
    normalized = re.sub(r"[\u00A0]", " ", normalized)  # non-breaking spaces
    normalized = re.sub(r"\s*,\s*", ", ", normalized)  # commas
    normalized = re.sub(r"\s+v\.?\s+", " v. ", normalized)  # v.
    normalized = re.sub(r"\s+&\.?\s+", " & ", normalized)  # &
    normalized = re.sub(r"\s+vs\.?\s+", " v. ", normalized)  # vs.
    normalized = re.sub(r"\s+versus\s+", " v. ", normalized)  # versus
    normalized = re.sub(r"\(\s*", "(", normalized)  # space after (
    normalized = re.sub(r"\s*\)", ")", normalized)  # space before )
    normalized = re.sub(r"\[\s*", "[", normalized)  # space after [
    normalized = re.sub(r"\s*\]", "]", normalized)  # space before ]
    normalized = re.sub(r"\.\s*\.", "..", normalized)  # double periods
    normalized = re.sub(r"\.\s*\.\s*\.", "...", normalized)  # triple periods

    return normalized


def generate_citation_variants(citation: str) -> List[str]:
    """
    Generate all plausible variants of a citation for fallback/parallel search.
    Includes Washington-specific, normalized, and expanded forms.
    """
    variants = set()
    if not citation or not isinstance(citation, str):
        return []

    # Start with the original and normalized forms
    normalized = normalize_citation(citation)
    variants.add(citation)
    variants.add(normalized)

    # Washington-specific patterns
    washington_patterns = [
        # Standard Washington patterns (Wn. -> Wash.)
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn \2 \3'),
        # Washington App patterns (Wn. App. -> Wash. App.)
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. App. \2 \3'),
        # Washington 2d patterns (Wn. 2d -> Wash. 2d)
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wash. 2d \2 \3'),
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Washington 2d \2 \3'),
        # Handle cases where Wn. is already in the citation
        (r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
    ]
    for original, replacement in washington_patterns:
        variant = re.sub(original, replacement, citation, flags=re.IGNORECASE)
        if variant != citation:
            variants.add(variant)
        variant = re.sub(original, replacement, normalized, flags=re.IGNORECASE)
        if variant != normalized:
            variants.add(variant)

    # Add specific Washington variants for better search
    if 'Wn.' in citation or 'Wn ' in citation:
        wash_variant = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
        variants.add(wash_variant)
        wash_full_variant = citation.replace('Wn.', 'Washington ').replace('Wn ', 'Washington ')
        variants.add(wash_full_variant)

    return list(variants) 