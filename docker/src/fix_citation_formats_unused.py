"""
Script to analyze and fix citation formats in the unconfirmed citations database.

This script identifies incorrectly formatted citations and suggests corrections
based on standard legal citation formats.
"""

import json
import re
import os
import sys


def load_unconfirmed_citations(
    filename="downloaded_briefs/all_unconfirmed_citations.json",
):
    """Load unconfirmed citations from the JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading unconfirmed citations: {e}")
        return {}


def save_corrected_citations(
    citations, filename="downloaded_briefs/corrected_citations.json"
):
    """Save corrected citations to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(citations, f, indent=2)
        print(f"Corrected citations saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving corrected citations: {e}")
        return False


def analyze_citation_format(citation_text):
    """
    Analyze a citation format and determine if it's correctly formatted.
    Returns a tuple of (is_valid, format_type, correction).
    """
    # Strip whitespace
    citation = citation_text.strip()

    # U.S. Reports format (e.g., "410 U.S. 113")
    us_match = re.match(r"^(\d+)\s+U\.?\s?S\.?\s+(\d+)$", citation)
    if us_match:
        volume, page = us_match.groups()
        # Check if volume number is valid (U.S. Reports currently goes up to around 600)
        if int(volume) > 600:
            return (
                False,
                "U.S. Reports",
                f"{volume} U.S. {page}",
                "Invalid volume number (too high)",
            )
        # Standardize format
        corrected = f"{volume} U.S. {page}"
        if corrected != citation:
            return (True, "U.S. Reports", corrected, "Standardized format")
        return (True, "U.S. Reports", None, "Correctly formatted")

    # Federal Reporter format (e.g., "175 F.3d 257")
    f_match = re.match(r"^(\d+)\s+F\.(\d+)d\s+(\d+)$", citation)
    if f_match:
        volume, series, page = f_match.groups()
        # Check if series is valid (1, 2, 3, 4)
        if int(series) > 4:
            return (
                False,
                "Federal Reporter",
                f"{volume} F.{series}d {page}",
                "Invalid series number (too high)",
            )
        # Standardize format
        corrected = f"{volume} F.{series}d {page}"
        if corrected != citation:
            return (True, "Federal Reporter", corrected, "Standardized format")
        return (True, "Federal Reporter", None, "Correctly formatted")

    # Federal Supplement format (e.g., "57 F.Supp.2d 460")
    fsupp_match = re.match(r"^(\d+)\s+F\.Supp\.(\d+)d\s+(\d+)$", citation)
    if fsupp_match:
        volume, series, page = fsupp_match.groups()
        # Check if series is valid (1, 2, 3)
        if int(series) > 3:
            return (
                False,
                "Federal Supplement",
                f"{volume} F.Supp.{series}d {page}",
                "Invalid series number (too high)",
            )
        # Standardize format
        corrected = f"{volume} F.Supp.{series}d {page}"
        if corrected != citation:
            return (True, "Federal Supplement", corrected, "Standardized format")
        return (True, "Federal Supplement", None, "Correctly formatted")

    # Washington Reports format (e.g., "175 Wn.2d 257" or "175 Wash.2d 257")
    wash_match = re.match(r"^(\d+)\s+(Wn|Wash)\.(\d+)d\s+(\d+)$", citation)
    if wash_match:
        volume, state_abbr, series, page = wash_match.groups()
        # Standardize to Wn.
        state_abbr = "Wn"
        # Check if series is valid (1, 2, 3)
        if int(series) > 3:
            return (
                False,
                "Washington Reports",
                f"{volume} {state_abbr}.{series}d {page}",
                "Invalid series number (too high)",
            )
        # Standardize format
        corrected = f"{volume} {state_abbr}.{series}d {page}"
        if corrected != citation:
            return (True, "Washington Reports", corrected, "Standardized format")
        return (True, "Washington Reports", None, "Correctly formatted")

    # Washington Appellate Reports format (e.g., "175 Wn. App. 257")
    wash_app_match = re.match(
        r"^(\d+)\s+(Wn\.|Wash\.|Wash|Wn)\s+App\.\s+(\d+)$", citation
    )
    if wash_app_match:
        volume, state_abbr, page = wash_app_match.groups()
        # Standardize to Wn.
        state_abbr = "Wn."
        # Standardize format
        corrected = f"{volume} {state_abbr} App. {page}"
        if corrected != citation:
            return (
                True,
                "Washington Appellate Reports",
                corrected,
                "Standardized format",
            )
        return (True, "Washington Appellate Reports", None, "Correctly formatted")

    # Supreme Court Reporter format (e.g., "93 S.Ct. 705")
    sct_match = re.match(r"^(\d+)\s+S\.?\s?Ct\.?\s+(\d+)$", citation)
    if sct_match:
        volume, page = sct_match.groups()
        # Check if volume number is valid (S.Ct. currently goes up to around 140)
        if int(volume) > 150:
            return (
                False,
                "Supreme Court Reporter",
                f"{volume} S.Ct. {page}",
                "Invalid volume number (too high)",
            )
        # Standardize format
        corrected = f"{volume} S.Ct. {page}"
        if corrected != citation:
            return (True, "Supreme Court Reporter", corrected, "Standardized format")
        return (True, "Supreme Court Reporter", None, "Correctly formatted")

    # Westlaw citation format (e.g., "2001 WL 912403")
    wl_match = re.match(r"^(\d{4})\s+WL\s+(\d+)$", citation)
    if wl_match:
        year, number = wl_match.groups()
        # Check if year is valid (between 1980 and current year)
        current_year = 2025  # Hardcoded for simplicity
        if int(year) < 1980 or int(year) > current_year:
            return (
                False,
                "Westlaw",
                f"{year} WL {number}",
                f"Invalid year (should be between 1980 and {current_year})",
            )
        # Standardize format
        corrected = f"{year} WL {number}"
        if corrected != citation:
            return (True, "Westlaw", corrected, "Standardized format")
        return (True, "Westlaw", None, "Correctly formatted")

    # Lawyer's Edition format (e.g., "50 L.Ed.2d 397")
    led_match = re.match(r"^(\d+)\s+L\.?\s?Ed\.?\s?(\d+)d\s+(\d+)$", citation)
    if led_match:
        volume, series, page = led_match.groups()
        # Standardize format
        corrected = f"{volume} L.Ed.{series}d {page}"
        if corrected != citation:
            return (True, "Lawyer's Edition", corrected, "Standardized format")
        return (True, "Lawyer's Edition", None, "Correctly formatted")

    # If we get here, the format wasn't recognized
    return (False, "Unknown", None, "Unrecognized citation format")


def suggest_real_citation(citation_text, case_name):
    """
    Suggest a real citation that might match the case name.
    This is a simplified version that uses a mapping of known cases.
    """
    # Simplified mapping of case names to real citations
    known_cases = {
        "Roe v. Wade": "410 U.S. 113",
        "Brown v. Board of Education": "347 U.S. 483",
        "Miranda v. Arizona": "384 U.S. 436",
        "New York Times v. Sullivan": "376 U.S. 254",
        "Marbury v. Madison": "5 U.S. 137",
        "Lochner v. New York": "198 U.S. 45",
        "Plessy v. Ferguson": "163 U.S. 537",
        "Bush v. Gore": "531 U.S. 98",
        "Gideon v. Wainwright": "372 U.S. 335",
        "Mapp v. Ohio": "367 U.S. 643",
        "Obergefell v. Hodges": "576 U.S. 644",
        "Citizens United v. FEC": "558 U.S. 310",
        "District of Columbia v. Heller": "554 U.S. 570",
        "Dobbs v. Jackson Women's Health Organization": "597 U.S. ___",
    }

    # Check for exact match
    if case_name in known_cases:
        return known_cases[case_name]

    # Check for partial matches
    for known_case, citation in known_cases.items():
        # Simplify case names for comparison
        simple_known = known_case.lower().replace("v.", "").replace(".", "").strip()
        simple_case = case_name.lower().replace("v.", "").replace(".", "").strip()

        # Check if the main parts of the case name match
        if simple_known in simple_case or simple_case in simple_known:
            return citation

    return None


def fix_citation_formats():
    """
    Analyze and fix citation formats in the unconfirmed citations database.
    """
    all_citations = load_unconfirmed_citations()

    if not all_citations:
        print("No unconfirmed citations found.")
        return

    corrected_citations = {}
    format_issues = []

    for document, citations in all_citations.items():
        corrected_citations[document] = []

        for citation in citations:
            citation_text = citation["citation_text"]
            case_name = citation.get("case_name")

            # Analyze the citation format
            is_valid, format_type, correction, message = analyze_citation_format(
                citation_text
            )

            # Create a copy of the citation for the corrected database
            corrected_citation = citation.copy()

            if not is_valid:
                # Try to suggest a real citation based on case name
                suggested_citation = (
                    suggest_real_citation(case_name, citation_text)
                    if case_name
                    else None
                )

                format_issues.append(
                    {
                        "document": document,
                        "original_citation": citation_text,
                        "case_name": case_name,
                        "format_type": format_type,
                        "issue": message,
                        "suggested_correction": correction,
                        "suggested_real_citation": suggested_citation,
                    }
                )

                # Update the citation with corrections
                if correction:
                    corrected_citation["original_citation_text"] = citation_text
                    corrected_citation["citation_text"] = correction
                    corrected_citation["format_correction"] = message

                if suggested_citation:
                    corrected_citation["suggested_real_citation"] = suggested_citation

            elif correction:
                # Valid format but needs standardization
                corrected_citation["original_citation_text"] = citation_text
                corrected_citation["citation_text"] = correction
                corrected_citation["format_correction"] = message

            corrected_citations[document].append(corrected_citation)

    # Save the corrected citations
    save_corrected_citations(corrected_citations)

    # Print summary of issues found
    print(f"\nFound {len(format_issues)} citation format issues:")
    for i, issue in enumerate(format_issues, 1):
        print(f"\n{i}. {issue['original_citation']} ({issue['case_name']})")
        print(f"   Document: {issue['document']}")
        print(f"   Format: {issue['format_type']}")
        print(f"   Issue: {issue['issue']}")
        if issue["suggested_correction"]:
            print(f"   Suggested format correction: {issue['suggested_correction']}")
        if issue["suggested_real_citation"]:
            print(f"   Suggested real citation: {issue['suggested_real_citation']}")

    return corrected_citations, format_issues


if __name__ == "__main__":
    print("Analyzing and fixing citation formats...")
    fix_citation_formats()
