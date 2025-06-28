"""
Landmark Cases Database

This module provides a database of well-known landmark cases to ensure they are properly
recognized and verified by the CaseStrainer application.
"""

# Dictionary of landmark Supreme Court cases with their citations and basic information
LANDMARK_CASES = {
    # Format: 'citation': {'name': 'Case Name', 'year': YYYY, 'court': 'Court Name', 'significance': 'Brief description'}
    # Supreme Court Reporter (U.S.) citations
    "410 U.S. 113": {
        "name": "Roe v. Wade",
        "year": 1973,
        "court": "Supreme Court of the United States",
        "significance": "Established a woman's legal right to abortion",
    },
    "347 U.S. 483": {
        "name": "Brown v. Board of Education",
        "year": 1954,
        "court": "Supreme Court of the United States",
        "significance": "Declared racial segregation in public schools unconstitutional",
    },
    "5 U.S. 137": {
        "name": "Marbury v. Madison",
        "year": 1803,
        "court": "Supreme Court of the United States",
        "significance": "Established judicial review",
    },
    "384 U.S. 436": {
        "name": "Miranda v. Arizona",
        "year": 1966,
        "court": "Supreme Court of the United States",
        "significance": "Required police to inform suspects of their rights",
    },
    "381 U.S. 479": {
        "name": "Griswold v. Connecticut",
        "year": 1965,
        "court": "Supreme Court of the United States",
        "significance": "Established right to privacy in marital relationships",
    },
    "198 U.S. 45": {
        "name": "Lochner v. New York",
        "year": 1905,
        "court": "Supreme Court of the United States",
        "significance": "Limited government regulation of labor conditions",
    },
    "17 U.S. 316": {
        "name": "McCulloch v. Maryland",
        "year": 1819,
        "court": "Supreme Court of the United States",
        "significance": "Established federal authority over states",
    },
    "376 U.S. 254": {
        "name": "New York Times Co. v. Sullivan",
        "year": 1964,
        "court": "Supreme Court of the United States",
        "significance": 'Established "actual malice" standard for defamation of public figures',
    },
    "163 U.S. 537": {
        "name": "Plessy v. Ferguson",
        "year": 1896,
        "court": "Supreme Court of the United States",
        "significance": 'Upheld "separate but equal" racial segregation',
    },
    "531 U.S. 98": {
        "name": "Bush v. Gore",
        "year": 2000,
        "court": "Supreme Court of the United States",
        "significance": "Resolved the 2000 presidential election dispute",
    },
    "558 U.S. 310": {
        "name": "Citizens United v. Federal Election Commission",
        "year": 2010,
        "court": "Supreme Court of the United States",
        "significance": "Removed restrictions on political campaign spending by organizations",
    },
    "576 U.S. 644": {
        "name": "Obergefell v. Hodges",
        "year": 2015,
        "court": "Supreme Court of the United States",
        "significance": "Legalized same-sex marriage nationwide",
    },
    # Supreme Court Reporter (S.Ct.) citations
    "93 S.Ct. 705": {
        "name": "Roe v. Wade",
        "year": 1973,
        "court": "Supreme Court of the United States",
        "significance": "Established a woman's legal right to abortion",
    },
    "74 S.Ct. 686": {
        "name": "Brown v. Board of Education",
        "year": 1954,
        "court": "Supreme Court of the United States",
        "significance": "Declared racial segregation in public schools unconstitutional",
    },
}


def is_landmark_case(citation):
    """
    Check if a citation corresponds to a landmark case in our database.

    Args:
        citation (str): The citation to check

    Returns:
        dict: Case information if found, None otherwise
    """
    # Clean the citation for matching
    clean_citation = citation.strip()

    # Direct lookup
    if clean_citation in LANDMARK_CASES:
        return LANDMARK_CASES[clean_citation]

    # Try to normalize U.S. citations
    if "U.S." in clean_citation:
        import re

        match = re.search(r"(\d+)\s*U\.S\.\s*(\d+)", clean_citation)
        if match:
            volume, page = match.groups()
            normalized = f"{volume} U.S. {page}"
            if normalized in LANDMARK_CASES:
                return LANDMARK_CASES[normalized]

    # Try to normalize S.Ct. citations
    if "S.Ct." in clean_citation or "S. Ct." in clean_citation:
        import re

        match = re.search(r"(\d+)\s*S\.?\s*Ct\.?\s*(\d+)", clean_citation)
        if match:
            volume, page = match.groups()
            normalized = f"{volume} S.Ct. {page}"
            if normalized in LANDMARK_CASES:
                return LANDMARK_CASES[normalized]

    return None
