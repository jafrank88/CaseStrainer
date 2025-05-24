import re


def washington_state_to_bluebook(citation: str) -> str:
    """
    Converts Washington state court citation format to Bluebook format.
    Handles both Supreme Court (Wn.2d) and Court of Appeals (Wn. App.)
    """
    # Supreme Court: Wn.2d -> Wash. 2d
    citation = re.sub(r"Wn\.2d", "Wash. 2d", citation)
    # Court of Appeals: Wn. App. -> Wash. App.
    citation = re.sub(r"Wn\. App\.", "Wash. App.", citation)

    # Add court in parenthetical if not present
    # Extract year from parenthetical if present
    match = re.search(r"\((\d{4})\)", citation)
    year = match.group(1) if match else None
    # Determine court type
    if "Wash. App." in citation:
        parenthetical = f"(Wash. Ct. App."
    elif "Wash. 2d" in citation:
        parenthetical = f"(Wash."
    else:
        parenthetical = None

    # Replace parenthetical with Bluebook style
    if parenthetical and year:
        citation = re.sub(r"\(\d{4}\)", f"{parenthetical} {year})", citation)
    elif parenthetical:
        citation = citation.rstrip(")") + f" {parenthetical})"

    return citation


def normalize_illinois_oklahoma(citation: str) -> str:
    """
    For Illinois and Oklahoma, remove paragraph markers (¶ 12, ¶ 15, etc) for deduplication.
    """
    # Remove paragraph markers (¶ 12, ¶ 15, etc)
    citation = re.sub(r",?\s*¶+\s*\d+", "", citation)
    return citation


def normalize_washington_synonyms(citation: str) -> str:
    """
    Normalize Washington synonyms for deduplication (Wn.2d <-> Wash. 2d, Wn. App. <-> Wash. App.)
    """
    citation = citation.replace("Wn.2d", "Wash. 2d")
    citation = citation.replace("Wn. App.", "Wash. App.")
    return citation


def normalize_for_deduplication(citation: str, state: str) -> str:
    """
    Normalize a citation string for deduplication, handling state-specific quirks.
    """
    state = state.lower()
    if state == "washington":
        return normalize_washington_synonyms(citation)
    elif state in ("illinois", "oklahoma"):
        return normalize_illinois_oklahoma(citation)
    else:
        return citation


# Example test cases
if __name__ == "__main__":
    print("=== Washington Normalization ===")
    wa_examples = [
        "Smith v. Jones, 123 Wn.2d 456 (2015)",
        "Smith v. Jones, 123 Wash. 2d 456 (Wash. 2015)",
        "Smith v. Jones, 45 Wn. App. 678 (2014)",
        "Smith v. Jones, 45 Wash. App. 678 (Wash. Ct. App. 2014)",
    ]
    for ex in wa_examples:
        print("Original:   ", ex)
        print("Normalized: ", normalize_for_deduplication(ex, "washington"))
        print()

    print("=== Illinois/Oklahoma Normalization ===")
    ill_ok_examples = [
        "People v. Smith, 2014 IL 123456, ¶ 15",
        "People v. Smith, 2014 IL 123456",
        "Smith v. State, 2014 OK CR 15, ¶ 12",
        "Smith v. State, 2014 OK CR 15",
    ]
    for ex in ill_ok_examples:
        print("Original:   ", ex)
        print("Normalized: ", normalize_for_deduplication(ex, "illinois"))
        print()
