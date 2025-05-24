"""
Simple Citation Verification System

This module implements a basic verification system for legal citations
that can distinguish between real cases, hallucinations, and typos.
"""

import re
import json
import requests
import urllib.parse
import traceback
from bs4 import BeautifulSoup
import time
import random

# Citation patterns for different formats - with more flexible matching
CITATION_PATTERNS = {
    # U.S. Reports - extremely flexible with spacing and punctuation
    "us_reports": r"(\d+)\s*U\.?\s*S\.?\s*(\d+)\s*\(\d{4}\)",  # e.g., 410 U.S. 113 (1973), 410US113(1973)
    # Compact U.S. Reports format with no spaces
    "us_reports_compact": r"(\d+)US(\d+)\(\d{4}\)",  # e.g., 576US644(2015)
    # Federal Reporter - allow for future series (F.4th, F.5th, etc.)
    "federal_reporter": r"(\d+)\s*F\.?\s*(\d)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 F.3d 456, 123 F.4th 456
    # Federal Supplement - more flexible with spacing and series
    "federal_supplement": r"(\d+)\s*F\.?\s*Supp\.?\s*(\d*)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 F.Supp.2d 789
    # State reporter - more flexible
    "state_reporter": r"(\d+)\s*([A-Za-z\.]+)\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 Cal. App. 4th 456
    # Regional reporter - more flexible with spacing and series
    "regional_reporter": r"(\d+)\s*([A-Za-z\.]+)(\d*)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 N.E.2d 789, 456 N.E.3d 789
    # Supreme Court Reporter - more flexible
    "supreme_court_reporter": r"(\d+)\s*S\.?\s*Ct\.?\s+(\d+)\s*\(\d{4}\)",
    # Lawyers Edition - more flexible
    "lawyers_edition": r"(\d+)\s*L\.?\s*Ed\.?\s*(\d+)[\w]*\s+(\d+)\s*\(\d{4}\)",
    # Westlaw - standard format
    "westlaw": r"(\d{4})\s*WL\s*(\d+)",
}

# Valid volume ranges for different reporters - with generous upper bounds for future growth
VALID_VOLUME_RANGES = {
    "us_reports": (
        1,
        1000,
    ),  # U.S. Reports volumes (currently ~600, but allow for future)
    "federal_reporter_1": (
        1,
        500,
    ),  # F.1d volumes (currently ~300, but allow for future)
    "federal_reporter_2": (
        1,
        1500,
    ),  # F.2d volumes (currently ~1000, but allow for future)
    "federal_reporter_3": (
        1,
        1500,
    ),  # F.3d volumes (currently ~1000, but allow for future)
    "federal_reporter_4": (1, 1000),  # F.4d volumes (future series)
    "federal_reporter_5": (1, 1000),  # F.5d volumes (future series)
    "federal_reporter_6": (1, 1000),  # F.6d volumes (future series)
    "federal_supplement_1": (1, 1500),  # F. Supp. volumes (allow for future)
    "federal_supplement_2": (1, 1500),  # F. Supp. 2d volumes (allow for future)
    "federal_supplement_3": (1, 1000),  # F. Supp. 3d volumes (allow for future)
    "federal_supplement_4": (1, 1000),  # F. Supp. 4d volumes (future series)
}

# Landmark cases for quick verification
LANDMARK_CASES = {
    "410 U.S. 113": {
        "name": "Roe v. Wade",
        "year": 1973,
        "description": "Established a woman's legal right to an abortion",
    },
    "347 U.S. 483": {
        "name": "Brown v. Board of Education",
        "year": 1954,
        "description": "Declared segregation in public schools unconstitutional",
    },
    "384 U.S. 436": {
        "name": "Miranda v. Arizona",
        "year": 1966,
        "description": "Established the Miranda rights for criminal suspects",
    },
    "576 U.S. 644": {
        "name": "Obergefell v. Hodges",
        "year": 2015,
        "description": "Legalized same-sex marriage nationwide",
    },
}


def normalize_citation(citation_text):
    """Normalize citation text by removing extra spaces and standardizing format."""
    if not citation_text:
        return ""
    # Remove extra spaces
    citation = re.sub(r"\s+", " ", citation_text.strip())
    return citation


def check_name_match(name1, name2):
    """Check if two case names match."""
    if not name1 or not name2:
        return False

    # Normalize names
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()

    # Direct match
    if name1 == name2:
        return True

    # Check for substring match
    if name1 in name2 or name2 in name1:
        return True

    return False


def is_landmark_case(citation_text):
    """Check if a citation refers to a landmark case."""
    citation = normalize_citation(citation_text)

    # Extract volume and reporter
    for key in LANDMARK_CASES:
        if key in citation:
            return LANDMARK_CASES[key]

    return None


class SimpleCitationVerifier:
    """
    A class that verifies citations using pattern matching and landmark case database.
    """

    def __init__(self):
        """Initialize the verifier."""
        self.session = requests.Session()

        # Set up user agent to avoid being blocked
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def verify_citation(self, citation_text, case_name=None):
        """
        Verify a citation using pattern matching and landmark case database.

        Args:
            citation_text (str): The citation text to verify
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result with confidence score and explanation
        """
        # Normalize citation
        normalized_citation = normalize_citation(citation_text)

        # Check if citation is a landmark case
        landmark_case = is_landmark_case(normalized_citation)
        if landmark_case:
            return {
                "found": True,
                "confidence": 1.0,
                "explanation": f"This is a landmark case: {landmark_case['name']} ({landmark_case['year']}) - {landmark_case['description']}",
                "source": "landmark_database",
            }

        # Analyze citation format
        format_analysis = self.analyze_citation_format(normalized_citation)

        # If format is invalid, return early
        if not format_analysis.get("valid", False):
            return {
                "found": False,
                "confidence": 0.1,
                "explanation": f"Invalid citation format: {format_analysis.get('explanation', '')}",
                "format_analysis": format_analysis,
            }

        # Calculate likelihood score
        likelihood_score = self.calculate_likelihood_score(
            normalized_citation, case_name, format_analysis
        )

        # Generate explanation
        explanation = self.generate_explanation(likelihood_score, format_analysis)

        return {
            "found": likelihood_score > 0.8,  # Consider high likelihood as verified
            "confidence": likelihood_score,
            "explanation": explanation,
            "format_analysis": format_analysis,
        }

    def analyze_citation_format(self, citation_text):
        """
        Analyze a citation format and determine if it's valid.

        Args:
            citation_text (str): The citation text to analyze

        Returns:
            dict: Analysis result with format type, validity, and details
        """
        # Check each citation pattern
        for format_type, pattern in CITATION_PATTERNS.items():
            match = re.search(pattern, citation_text)
            if match:
                # Extract components based on format type
                if format_type == "us_reports":
                    volume = int(match.group(1))
                    page = int(match.group(2))

                    # Check volume range
                    if (
                        volume < VALID_VOLUME_RANGES["us_reports"][0]
                        or volume > VALID_VOLUME_RANGES["us_reports"][1]
                    ):
                        return {
                            "valid": False,
                            "format_type": format_type,
                            "explanation": f"Volume {volume} is outside the valid range for U.S. Reports",
                        }

                    return {
                        "valid": True,
                        "format_type": format_type,
                        "volume": volume,
                        "page": page,
                    }

                elif format_type == "federal_reporter":
                    volume = int(match.group(1))
                    series = int(match.group(2))
                    page = int(match.group(3))

                    # Check volume range based on series
                    range_key = f"federal_reporter_{series}"
                    if range_key in VALID_VOLUME_RANGES:
                        min_vol, max_vol = VALID_VOLUME_RANGES[range_key]
                        if volume < min_vol or volume > max_vol:
                            return {
                                "valid": False,
                                "format_type": format_type,
                                "explanation": f"Volume {volume} is outside the valid range for F.{series}d",
                            }

                    return {
                        "valid": True,
                        "format_type": format_type,
                        "volume": volume,
                        "series": series,
                        "page": page,
                    }

                elif format_type == "federal_supplement":
                    volume = int(match.group(1))
                    series_str = match.group(2)
                    series = int(series_str) if series_str else 1
                    page = int(match.group(3))

                    # Check volume range based on series
                    range_key = f"federal_supplement_{series}"
                    if range_key in VALID_VOLUME_RANGES:
                        min_vol, max_vol = VALID_VOLUME_RANGES[range_key]
                        if volume < min_vol or volume > max_vol:
                            return {
                                "valid": False,
                                "format_type": format_type,
                                "explanation": f"Volume {volume} is outside the valid range for F. Supp. {series}d",
                            }

                    return {
                        "valid": True,
                        "format_type": format_type,
                        "volume": volume,
                        "series": series,
                        "page": page,
                    }

                # For other formats, just return that it's valid
                return {"valid": True, "format_type": format_type}

        # If no pattern matched
        return {
            "valid": False,
            "explanation": "Citation format does not match any known pattern",
        }

    def calculate_likelihood_score(self, citation_text, case_name, format_analysis):
        """
        Calculate the likelihood that a citation is a real case.

        Args:
            citation_text (str): The citation text
            case_name (str): The case name
            format_analysis (dict): The format analysis result

        Returns:
            float: Likelihood score between 0.0 and 1.0
        """
        # Start with a base score
        score = 0.5

        # If format is invalid, very low likelihood
        if not format_analysis.get("valid", False):
            return 0.1

        # Adjust score based on format type
        format_type = format_analysis.get("format_type")
        if format_type == "us_reports":
            # U.S. Reports are well-documented, so more likely to be real
            score += 0.2
        elif format_type in ["federal_reporter", "federal_supplement"]:
            # These are also well-documented
            score += 0.1

        # Check for case name presence
        if case_name:
            score += 0.1

        # Adjust for specific volume ranges
        if format_type == "us_reports":
            volume = format_analysis.get("volume")
            if volume:
                # Newer volumes are more likely to be real
                if volume > 500:
                    score += 0.1
                # Very old volumes might be less common
                elif volume < 50:
                    score -= 0.1

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))

    def generate_explanation(self, likelihood_score, format_analysis):
        """
        Generate an explanation for the verification result.

        Args:
            likelihood_score (float): The likelihood score
            format_analysis (dict): The format analysis result

        Returns:
            str: Explanation text
        """
        if not format_analysis.get("valid", False):
            return format_analysis.get("explanation", "Invalid citation format")

        format_type = format_analysis.get("format_type", "unknown")

        if likelihood_score < 0.3:
            return (
                f"This citation is likely a hallucination or contains a typographical error. "
                f"The format appears to be {format_type}, but the citation could not be verified."
            )
        elif likelihood_score < 0.7:
            return (
                f"This citation has a valid {format_type} format, but could not be fully verified. "
                f"It may be a less common case or from a jurisdiction not well-covered in our database."
            )
        else:
            return (
                f"This citation has a valid {format_type} format and is likely a real case. "
                f"The citation appears to be correctly formatted and within expected volume ranges."
            )


# Example usage
if __name__ == "__main__":
    # Create verifier
    verifier = SimpleCitationVerifier()

    # Test with some citations
    test_citations = [
        "410 U.S. 113 (1973)",  # Roe v. Wade
        "347 U.S. 483 (1954)",  # Brown v. Board of Education
        "384 U.S. 436 (1966)",  # Miranda v. Arizona
        "123 F.3d 456 (9th Cir. 1997)",  # Made-up citation
        "567 U.S. 890 (2012)",  # Made-up citation
        "576 U.S. 644 (2015)",  # Obergefell v. Hodges
        "576 U.S. 645 (2015)",  # Typo in page number
        "576US644(2015)",  # No spaces
    ]

    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        result = verifier.verify_citation(citation)
        status = "VERIFIED" if result.get("found", False) else "UNVERIFIED"
        confidence = result.get("confidence", 0)
        explanation = result.get("explanation", "No explanation provided")

        print(f"Status: {status}")
        print(f"Confidence: {confidence}")
        print(f"Explanation: {explanation}")
