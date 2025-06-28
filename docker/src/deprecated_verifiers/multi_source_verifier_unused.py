"""
Multi-Source Citation Verification System

This module implements a cascading verification system that checks multiple sources
to verify citations, distinguishing between real cases not in CourtListener,
hallucinations, and typographical errors.
"""

import os
import re
import requests
import urllib.parse
import traceback
from bs4 import BeautifulSoup

# Import functions from app_final.py if available
try:
    from app_final import is_landmark_case, normalize_citation, check_name_match

    print("Successfully imported functions from app_final.py")
except ImportError:
    print("Warning: Could not import functions from app_final.py")

    # Define fallback functions
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
        # This is a simplified version of the function
        return None


# Dictionary of verification sources
VERIFICATION_SOURCES = {
    "courtlistener": {
        "base_url": "https://www.courtlistener.com/api/rest/v3/search/",
        "requires_api_key": True,
    },
    "google_scholar": {
        "base_url": "https://scholar.google.com/scholar",
        "requires_api_key": False,
    },
    "justia": {"base_url": "https://www.justia.com/search", "requires_api_key": False},
    "leagle": {"base_url": "https://www.leagle.com/search", "requires_api_key": False},
    "findlaw": {
        "base_url": "https://caselaw.findlaw.com/search",
        "requires_api_key": False,
    },
    "casetext": {"base_url": "https://casetext.com/search", "requires_api_key": False},
}

# Citation patterns for different formats - with more flexible matching
CITATION_PATTERNS = {
    # U.S. Reports - more flexible with spacing and punctuation
    "us_reports": r"(\d+)\s*U\.?\s*S\.?\s+(\d+)\s*\(\d{4}\)",  # e.g., 410 U.S. 113 (1973), 410US113(1973)
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


# MultiSourceVerifier class implementation
class MultiSourceVerifier:
    """
    A class that verifies citations using multiple sources and distinguishes
    between real cases not in CourtListener, hallucinations, and typos.
    """

    def __init__(self, api_keys=None):
        """
        Initialize the verifier with API keys.

        Args:
            api_keys (dict): Dictionary of API keys for different sources
        """
        self.api_keys = api_keys or {}
        self.verification_results = {}
        self.session = requests.Session()

        # Set up user agent to avoid being blocked
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def verify_citation(self, citation_text, case_name=None, sources=None):
        """
        Verify a citation using multiple sources.

        Args:
            citation_text (str): The citation text to verify
            case_name (str, optional): The case name to match
            sources (list, optional): List of sources to check, defaults to all

        Returns:
            dict: Verification result with confidence score and explanation
        """
        # Reset verification results
        self.verification_results = {}

        # Normalize citation
        normalized_citation = normalize_citation(citation_text)

        # Check if it's a landmark case first
        try:
            landmark_info = is_landmark_case(normalized_citation)
            if landmark_info:
                return {
                    "found": True,
                    "confirmed": True,
                    "confidence": 0.95,
                    "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info.get('year', '')}) - {landmark_info.get('description', '')}",
                    "source": "Landmark Cases Database",
                    "case_name": landmark_info["name"],
                    "url": landmark_info.get("url", None),
                }
        except Exception as e:
            print(f"Error checking landmark case: {e}")

        # Analyze citation format
        format_analysis = self.analyze_citation_format(normalized_citation)

        # If the format is invalid, it's likely a typo or hallucination
        if not format_analysis["is_valid_format"]:
            return {
                "found": False,
                "confirmed": False,
                "confidence": 0.1,
                "explanation": f"Invalid citation format: {format_analysis['error']}",
                "source": None,
                "case_name": case_name,
                "format_analysis": format_analysis,
            }

        # Determine which sources to check
        sources_to_check = sources or VERIFICATION_SOURCES

        # Check each source in order
        for source in sources_to_check:
            try:
                # Check if we have a method for this source
                method_name = f"check_{source}"
                if hasattr(self, method_name) and callable(getattr(self, method_name)):
                    # Call the method
                    result = getattr(self, method_name)(normalized_citation, case_name)

                    # Store the result
                    self.verification_results[source] = result

                    # If the citation was found, return the result
                    if result.get("found", False):
                        # Add format analysis to the result
                        result["format_analysis"] = format_analysis
                        return result
            except Exception as e:
                print(f"Error checking {source}: {e}")
                traceback.print_exc()
                self.verification_results[source] = {"found": False, "error": str(e)}

        # If we get here, the citation was not found in any source
        # Determine if it's likely a real case not in databases or a hallucination
        likelihood_score = self.calculate_likelihood_score(
            normalized_citation, case_name, format_analysis
        )

        return {
            "found": False,
            "confirmed": False,
            "confidence": likelihood_score,
            "explanation": self.generate_explanation(likelihood_score, format_analysis),
            "source": None,
            "case_name": case_name,
            "format_analysis": format_analysis,
            "verification_results": self.verification_results,
        }

    def analyze_citation_format(self, citation_text):
        """
        Analyze a citation format and determine if it's valid.

        Args:
            citation_text (str): The citation text to analyze

        Returns:
            dict: Analysis result with format type, validity, and details
        """
        # Strip whitespace
        citation = citation_text.strip()

        # Check against each pattern
        for format_type, pattern in CITATION_PATTERNS.items():
            match = re.match(pattern, citation)
            if match:
                # Citation matches this format
                if format_type == "us_reports":
                    volume, page = match.groups()
                    volume_num = int(volume)
                    min_vol, max_vol = VALID_VOLUME_RANGES["us_reports"]
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type}"
                        )

                    return result

                elif format_type == "federal_reporter":
                    volume, series, page = match.groups()
                    volume_num = int(volume)
                    series_num = int(series)

                    # Check if series is valid - but be more flexible for future series
                    if series_num > 10:  # Allow for future F.4d, F.5d, etc. up to F.10d
                        return {
                            "format_type": format_type,
                            "is_valid_format": True,  # Consider it valid format but with a warning
                            "is_valid_volume": True,  # Consider it valid volume but with a warning
                            "warning": f"Unusual series number: F.{series}d (common series are F.1d, F.2d, and F.3d, but this could be a new series)",
                        }

                    range_key = f"federal_reporter_{series_num}"
                    min_vol, max_vol = VALID_VOLUME_RANGES.get(range_key, (1, 1000))
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "series": series_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type} series {series_num}"
                        )

                    return result

                # Default for other recognized formats
                return {
                    "format_type": format_type,
                    "is_valid_format": True,
                    "is_valid_volume": True,
                    "details": {
                        "note": "Format recognized but detailed validation not implemented"
                    },
                }

        # If we get here, the format wasn't recognized
        return {
            "format_type": "unknown",
            "is_valid_format": False,
            "is_valid_volume": False,
            "error": "Unrecognized citation format",
        }

    def calculate_likelihood_score(self, citation_text, case_name, format_analysis):
        """
        Calculate the likelihood that a citation is a real case not found in databases
        rather than a hallucination or typo.

        Args:
            citation_text (str): The citation text
            case_name (str): The case name
            format_analysis (dict): The format analysis result

        Returns:
            float: Likelihood score between 0.0 and 1.0
        """
        # Start with a base score based on format validity
        if not format_analysis["is_valid_format"]:
            return 0.1  # Very unlikely to be real if format is invalid

        if not format_analysis["is_valid_volume"]:
            return 0.2  # Unlikely to be real if volume is invalid

        # Base score for valid format
        score = 0.5

        # Adjust score based on format type
        format_type = format_analysis["format_type"]
        if format_type == "us_reports":
            # U.S. Reports are well-documented, so if not found, less likely to be real
            score -= 0.2
        elif format_type in ["federal_reporter", "federal_supplement"]:
            # Federal cases are also well-documented
            score -= 0.1
        elif format_type == "state_reporter":
            # State cases might be less well-documented in some databases
            score += 0.1

        # If we have a case name, it's more likely to be real
        if case_name and len(case_name) > 5:
            score += 0.1

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
        if not format_analysis["is_valid_format"]:
            return f"Invalid citation format: {format_analysis.get('error', 'Unrecognized format')}"

        if not format_analysis["is_valid_volume"]:
            return f"Invalid volume number: {format_analysis.get('volume_error', 'Volume number out of range')}"

        if likelihood_score < 0.3:
            return "Citation format is valid but likely a hallucination or typo as it does not appear in any legal database and has characteristics of fictional citations."
        elif likelihood_score < 0.6:
            return "Citation format is valid but not found in any legal database. It could be a real case from a less-indexed court or a well-formatted hallucination."
        else:
            return "Citation format is valid and has characteristics of a real case, but was not found in the searched legal databases. It may be from a specialized or historical court not fully indexed in the databases checked."

    def check_courtlistener(self, citation_text, case_name=None):
        """
        Check a citation using the CourtListener API.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # This is a simplified implementation
        # In a real implementation, you would make an API call to CourtListener
        return {
            "found": False,
            "confidence": 0.0,
            "explanation": "Citation not found in CourtListener",
            "source": "CourtListener",
        }

    def check_google_scholar(self, citation_text, case_name=None):
        """
        Check a citation using Google Scholar.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # This is a simplified implementation
        # In a real implementation, you would make a web request to Google Scholar
        return {
            "found": False,
            "confidence": 0.0,
            "explanation": "Citation not found in Google Scholar",
            "source": "Google Scholar",
        }

    def check_justia(self, citation_text, case_name=None):
        """
        Check a citation using Justia.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # This is a simplified implementation
        # In a real implementation, you would make a web request to Justia
        return {
            "found": False,
            "confidence": 0.0,
            "explanation": "Citation not found in Justia",
            "source": "Justia",
        }


# Example usage
if __name__ == "__main__":
    # Create verifier
    verifier = MultiSourceVerifier()

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

# Citation patterns for different formats
CITATION_PATTERNS = {
    "us_reports": r"(\d+)\s+U\.S\.\s+(\d+)\s*\(\d{4}\)",  # e.g., 410 U.S. 113 (1973)
    "federal_reporter": r"(\d+)\s+F\.(\d)d\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 F.3d 456 (9th Cir. 1997)
    "federal_supplement": r"(\d+)\s+F\.\s*Supp\.\s*(\d+)?\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 F. Supp. 2d 789 (S.D.N.Y. 2005)
    "state_reporter": r"(\d+)\s+([A-Za-z\.]+)\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 Cal. App. 4th 456 (2004)
    "regional_reporter": r"(\d+)\s+([A-Za-z\.]+)(\d+)?\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 N.E.2d 789 (N.Y. 1983)
}

# Valid volume ranges for different reporters
VALID_VOLUME_RANGES = {
    "us_reports": (1, 600),  # U.S. Reports volumes
    "federal_reporter_1": (1, 300),  # F.1d volumes
    "federal_reporter_2": (1, 1000),  # F.2d volumes
    "federal_reporter_3": (1, 1000),  # F.3d volumes
    "federal_supplement_1": (1, 1000),  # F. Supp. volumes
    "federal_supplement_2": (1, 1000),  # F. Supp. 2d volumes
    "federal_supplement_3": (1, 500),  # F. Supp. 3d volumes
    "supreme_court_reporter": (1, 140),  # S.Ct. currently goes up to around 140
    "washington_reports_1": (1, 100),  # Wn.
    "washington_reports_2": (1, 200),  # Wn.2d
    "washington_reports_3": (1, 10),  # Wn.3d (if it exists)
    "washington_app_reports": (1, 200),  # Wn. App.
    "lawyers_edition_1": (1, 100),  # L.Ed.
    "lawyers_edition_2": (1, 200),  # L.Ed.2d
    "pacific_reporter_1": (1, 1000),  # P.
    "pacific_reporter_2": (1, 1000),  # P.2d
    "pacific_reporter_3": (1, 500),  # P.3d
    "atlantic_reporter_1": (1, 1000),  # A.
    "atlantic_reporter_2": (1, 1000),  # A.2d
    "atlantic_reporter_3": (1, 200),  # A.3d
    "north_eastern_reporter_1": (1, 1000),  # N.E.
    "north_eastern_reporter_2": (1, 1000),  # N.E.2d
    "north_eastern_reporter_3": (1, 200),  # N.E.3d
    "new_york_reports_1": (1, 100),  # N.Y.
    "new_york_reports_2": (1, 100),  # N.Y.2d
    "new_york_reports_3": (1, 50),  # N.Y.3d
    "california_reports_1": (1, 50),  # Cal.
    "california_reports_2": (1, 50),  # Cal.2d
    "california_reports_3": (1, 50),  # Cal.3d
    "california_reports_4": (1, 70),  # Cal.4th
}

# Additional citation patterns
ADDITIONAL_CITATION_PATTERNS = {
    "supreme_court_reporter": r"^(\d+)\s+S\.?\s?Ct\.?\s+(\d+)$",
    "washington_reports": r"^(\d+)\s+(Wn|Wash)\.(\d+)d\s+(\d+)$",
    "washington_app_reports": r"^(\d+)\s+(Wn\.|Wash\.|Wash|Wn)\s+App\.\s+(\d+)$",
    "lawyers_edition": r"^(\d+)\s+L\.?\s?Ed\.?\s?(\d+)d\s+(\d+)$",
    "westlaw": r"^(\d{4})\s+WL\s+(\d+)$",
    "pacific_reporter": r"^(\d+)\s+P\.(\d+)d\s+(\d+)$",
    "atlantic_reporter": r"^(\d+)\s+A\.(\d+)d\s+(\d+)$",
    "north_eastern_reporter": r"^(\d+)\s+N\.E\.(\d+)d\s+(\d+)$",
    "new_york_reports": r"^(\d+)\s+N\.Y\.(\d+)d\s+(\d+)$",
    "california_reports": r"^(\d+)\s+Cal\.(\d+)th\s+(\d+)$",
}

# Update CITATION_PATTERNS with additional patterns
CITATION_PATTERNS.update(ADDITIONAL_CITATION_PATTERNS)


class MultiSourceVerifier:
    """
    A class that verifies citations using multiple sources and distinguishes
    between real cases not in CourtListener, hallucinations, and typos.
    """

    def __init__(self, api_keys=None):
        """
        Initialize the verifier with API keys.

        Args:
            api_keys (dict): Dictionary of API keys for different sources
        """
        self.api_keys = api_keys or {}
        self.verification_results = {}
        self.session = requests.Session()

        # Set up user agent to avoid being blocked
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def verify_citation(self, citation_text, case_name=None, sources=None):
        """
        Verify a citation using multiple sources.

        Args:
            citation_text (str): The citation text to verify
            case_name (str, optional): The case name to match
            sources (list, optional): List of sources to check, defaults to all

        Returns:
            dict: Verification result with confidence score and explanation
        """
        # Reset verification results
        self.verification_results = {}

        # Normalize citation
        normalized_citation = normalize_citation(citation_text)

        # Check if it's a landmark case first
        try:
            landmark_info = is_landmark_case(normalized_citation)
            if landmark_info:
                return {
                    "found": True,
                    "confirmed": True,
                    "confidence": 0.95,
                    "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['description']}",
                    "source": "Landmark Cases Database",
                    "case_name": landmark_info["name"],
                    "url": landmark_info.get("url", None),
                }
        except Exception as e:
            print(f"Error checking landmark case: {e}")

        # Analyze citation format
        format_analysis = self.analyze_citation_format(normalized_citation)

        # If the format is invalid, it's likely a typo or hallucination
        if not format_analysis["is_valid_format"]:
            return {
                "found": False,
                "confirmed": False,
                "confidence": 0.1,
                "explanation": f"Invalid citation format: {format_analysis['error']}",
                "source": None,
                "case_name": case_name,
                "format_analysis": format_analysis,
            }

        # If the volume is invalid, it's likely a typo or hallucination
        if not format_analysis["is_valid_volume"]:
            return {
                "found": False,
                "confirmed": False,
                "confidence": 0.2,
                "explanation": f"Invalid volume number: {format_analysis['volume_error']}",
                "source": None,
                "case_name": case_name,
                "format_analysis": format_analysis,
            }

        # Determine which sources to check
        sources_to_check = sources or VERIFICATION_SOURCES

        # Check each source in order
        for source in sources_to_check:
            try:
                # Check if we have a method for this source
                method_name = f"check_{source}"
                if hasattr(self, method_name) and callable(getattr(self, method_name)):
                    # Call the method
                    result = getattr(self, method_name)(normalized_citation, case_name)

                    # Store the result
                    self.verification_results[source] = result

                    # If the citation was found, return the result
                    if result.get("found", False):
                        # Add format analysis to the result
                        result["format_analysis"] = format_analysis
                        return result
            except Exception as e:
                print(f"Error checking {source}: {e}")
                traceback.print_exc()
                self.verification_results[source] = {"found": False, "error": str(e)}

        # If we get here, the citation was not found in any source
        # Determine if it's likely a real case not in databases or a hallucination
        likelihood_score = self.calculate_likelihood_score(
            normalized_citation, case_name, format_analysis
        )

        return {
            "found": False,
            "confirmed": False,
            "confidence": likelihood_score,
            "explanation": self.generate_explanation(likelihood_score, format_analysis),
            "source": None,
            "case_name": case_name,
            "format_analysis": format_analysis,
            "verification_results": self.verification_results,
        }

    def analyze_citation_format(self, citation_text):
        """
        Analyze a citation format and determine if it's valid.

        Args:
            citation_text (str): The citation text to analyze

        Returns:
            dict: Analysis result with format type, validity, and details
        """
        # Strip whitespace
        citation = citation_text.strip()

        # Check against each pattern
        for format_type, pattern in CITATION_PATTERNS.items():
            match = re.match(pattern, citation)
            if match:
                # Citation matches this format
                if format_type == "us_reports":
                    volume, page = match.groups()
                    volume_num = int(volume)
                    min_vol, max_vol = VALID_VOLUME_RANGES["us_reports"]
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type}"
                        )

                    return result

                elif format_type == "federal_reporter":
                    volume, series, page = match.groups()
                    volume_num = int(volume)
                    series_num = int(series)

                    # Check if series is valid - but be more flexible for future series
                    if series_num > 10:  # Allow for future F.4d, F.5d, etc. up to F.10d
                        return {
                            "format_type": format_type,
                            "is_valid_format": True,  # Consider it valid format but with a warning
                            "is_valid_volume": True,  # Consider it valid volume but with a warning
                            "warning": f"Unusual series number: F.{series}d (common series are F.1d, F.2d, and F.3d, but this could be a new series)",
                        }

                    range_key = f"federal_reporter_{series_num}"
                    min_vol, max_vol = VALID_VOLUME_RANGES.get(range_key, (1, 1000))
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "series": series_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type} series {series_num}"
                        )

                    return result

                # Add other format types as needed

                # Default for other recognized formats
                return {
                    "format_type": format_type,
                    "is_valid_format": True,
                    "is_valid_volume": True,
                    "details": {
                        "note": "Format recognized but detailed validation not implemented"
                    },
                }

        # If we get here, the format wasn't recognized
        return {
            "format_type": "unknown",
            "is_valid_format": False,
            "is_valid_volume": False,
            "error": "Unrecognized citation format",
        }

    def calculate_likelihood_score(self, citation_text, case_name, format_analysis):
        """
        Calculate the likelihood that a citation is a real case not found in databases
        rather than a hallucination or typo.

        Args:
            citation_text (str): The citation text
            case_name (str): The case name
            format_analysis (dict): The format analysis result

        Returns:
            float: Likelihood score between 0.0 and 1.0
        """
        # Start with a base score
        score = 0.5

        # Format validity is very important
        if not format_analysis["is_valid_format"]:
            score -= 0.3

        # Volume validity is important
        if not format_analysis.get("is_valid_volume", True):
            score -= 0.2

        # Case name presence and format
        if case_name:
            # Check if case name follows standard format (e.g., "Party v. Party")
            if re.search(r"\b[vV]\.\b", case_name):
                score += 0.1

            # Check if case name contains common legal terms
            legal_terms = [
                "state",
                "united states",
                "city",
                "county",
                "department",
                "board",
                "commission",
                "corporation",
            ]
            if any(term in case_name.lower() for term in legal_terms):
                score += 0.05
        else:
            score -= 0.1

        # Check if any sources returned partial matches or errors
        # This could indicate the case exists but wasn't found exactly
        partial_matches = 0
        for source, result in self.verification_results.items():
            if result.get("partial_match", False):
                partial_matches += 1

        if partial_matches > 0:
            score += 0.1 * min(partial_matches, 3)

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
        if not format_analysis["is_valid_format"]:
            return f"Invalid citation format: {format_analysis.get('error', 'Unknown format')}"

        if not format_analysis.get("is_valid_volume", True):
            return f"Invalid volume number: {format_analysis.get('volume_error', 'Volume number out of range')}"

        if likelihood_score < 0.3:
            return "Citation not found on legal websites. This is likely a hallucination or contains a typographical error."
        elif likelihood_score < 0.5:
            return "Citation not found on legal websites. This may be a fictional case or contain an error."
        elif likelihood_score < 0.7:
            return "Citation not found on legal websites, but the format is valid. This may be a real case not included in our databases."
        else:
            return "Citation not found on legal websites, but it appears to be a valid citation. This is likely a real case not included in our databases."

    # Source-specific verification methods

    def check_courtlistener(self, citation_text, case_name=None):
        """
        Check a citation using the CourtListener API.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # Get API key
        api_key = self.api_keys.get("courtlistener") or os.environ.get(
            "COURTLISTENER_API_KEY"
        )
        if not api_key:
            return {"found": False, "error": "CourtListener API key not found"}

        # Prepare request
        headers = {"Authorization": f"Token {api_key}"}

        params = {"citation": citation_text, "format": "json"}

        # Add case name if provided
        if case_name:
            params["case_name"] = case_name

        # Make request
        try:
            response = self.session.get(
                "https://www.courtlistener.com/api/rest/v3/search/",
                headers=headers,
                params=params,
            )

            # Check response
            if response.status_code == 200:
                data = response.json()

                # Check if any results were found
                if data.get("count", 0) > 0:
                    # Get the first result
                    result = data["results"][0]

                    # Check if case name matches
                    name_match = True
                    if case_name:
                        name_match = check_name_match(
                            case_name, result.get("case_name", "")
                        )

                    return {
                        "found": True,
                        "confirmed": True,
                        "confidence": 0.9 if name_match else 0.7,
                        "explanation": f"Citation found on CourtListener: {result.get('case_name', 'Unknown case')}",
                        "source": "CourtListener",
                        "case_name": result.get("case_name", ""),
                        "url": result.get("absolute_url", ""),
                        "name_match": name_match,
                    }
                else:
                    return {
                        "found": False,
                        "explanation": "Citation not found on CourtListener",
                        "source": "CourtListener",
                    }
            else:
                return {
                    "found": False,
                    "error": f"CourtListener API error: {response.status_code}",
                    "source": "CourtListener",
                }
        except Exception as e:
            return {
                "found": False,
                "error": f"CourtListener API error: {str(e)}",
                "source": "CourtListener",
            }

    def check_google_scholar(self, citation_text, case_name=None):
        """
        Check a citation using Google Scholar.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # Prepare search query
        query = citation_text
        if case_name:
            query = f'"{case_name}" {citation_text}'

        # Encode query
        encoded_query = urllib.parse.quote(query)

        # Prepare URL
        url = f"https://scholar.google.com/scholar?q={encoded_query}&as_sdt=2006"

        # Make request
        try:
            response = self.session.get(url)

            # Check response
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Check for results
                results = soup.select(".gs_ri")

                if results:
                    # Get the first result
                    result = results[0]

                    # Get title
                    title = result.select_one(".gs_rt")
                    title_text = title.text if title else ""

                    # Get URL
                    url = (
                        title.select_one("a")["href"]
                        if title and title.select_one("a")
                        else ""
                    )

                    # Check if citation is in the snippet
                    snippet = result.select_one(".gs_rs")
                    snippet_text = snippet.text if snippet else ""

                    citation_in_snippet = citation_text in snippet_text

                    # Check if case name matches
                    name_match = True
                    if case_name:
                        name_match = check_name_match(case_name, title_text)

                    # Calculate confidence
                    confidence = 0.8 if citation_in_snippet else 0.6
                    confidence = confidence if name_match else confidence - 0.2

                    return {
                        "found": True,
                        "confirmed": citation_in_snippet,
                        "confidence": confidence,
                        "explanation": f"Citation found on Google Scholar: {title_text}",
                        "source": "Google Scholar",
                        "case_name": title_text,
                        "url": url,
                        "name_match": name_match,
                    }
                else:
                    return {
                        "found": False,
                        "explanation": "Citation not found on Google Scholar",
                        "source": "Google Scholar",
                    }
            else:
                return {
                    "found": False,
                    "error": f"Google Scholar error: {response.status_code}",
                    "source": "Google Scholar",
                }
        except Exception as e:
            return {
                "found": False,
                "error": f"Google Scholar error: {str(e)}",
                "source": "Google Scholar",
            }

    def check_justia(self, citation_text, case_name=None):
        """
        Check a citation using Justia.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # Prepare search query
        query = citation_text
        if case_name:
            query = f'"{case_name}" {citation_text}'

        # Encode query
        encoded_query = urllib.parse.quote(query)

        # Prepare URL
        url = f"https://www.justia.com/search?cx=004471259722555877589%3A3tsvwxzwxus&q={encoded_query}"

        # Make request
        try:
            response = self.session.get(url)

            # Check response
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Check for results
                results = soup.select(".result")

                if results:
                    # Get the first result
                    result = results[0]

                    # Get title
                    title = result.select_one("h2 a")
                    title_text = title.text if title else ""

                    # Get URL
                    url = title["href"] if title else ""

                    # Get snippet
                    snippet = result.select_one(".snippet")
                    snippet_text = snippet.text if snippet else ""

                    # Check if citation is in the snippet
                    citation_in_snippet = citation_text in snippet_text

                    # Check if case name matches
                    name_match = True
                    if case_name:
                        name_match = check_name_match(case_name, title_text)

                    # Calculate confidence
                    confidence = 0.8 if citation_in_snippet else 0.6
                    confidence = confidence if name_match else confidence - 0.2

                    return {
                        "found": True,
                        "confirmed": citation_in_snippet,
                        "confidence": confidence,
                        "explanation": f"Citation found on Justia: {title_text}",
                        "source": "Justia",
                        "case_name": title_text,
                        "url": url,
                        "name_match": name_match,
                    }
                else:
                    return {
                        "found": False,
                        "explanation": "Citation not found on Justia",
                        "source": "Justia",
                    }
            else:
                return {
                    "found": False,
                    "error": f"Justia error: {response.status_code}",
                    "source": "Justia",
                }
        except Exception as e:
            return {
                "found": False,
                "error": f"Justia error: {str(e)}",
                "source": "Justia",
            }

    # Add more source-specific methods as needed


# Example usage
if __name__ == "__main__":
    # Create verifier
    verifier = MultiSourceVerifier()

    # Test citations
    test_citations = [
        # Landmark case (should be confirmed)
        {"citation": "347 U.S. 483", "case_name": "Brown v. Board of Education"},
        # Valid citation but not in databases
        {"citation": "123 F.3d 456", "case_name": "Smith v. Jones"},
        # Invalid format (hallucination)
        {"citation": "963 F.4th 578", "case_name": "Williams v. State of Washington"},
        # Invalid volume (typo)
        {"citation": "722 U.S. 866", "case_name": "Smith v. Department of Justice"},
        # Westlaw citation (might be real)
        {
            "citation": "2019 WL 6686274",
            "case_name": "Martinez v. Department of Corrections",
        },
    ]

    # Verify each citation
    for test in test_citations:
        print(f"\nVerifying: {test['citation']} ({test['case_name']})")
        result = verifier.verify_citation(test["citation"], test["case_name"])

        print(f"Found: {result['found']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Source: {result['source']}")

        if "format_analysis" in result:
            format_analysis = result["format_analysis"]
            print(f"Format Type: {format_analysis.get('format_type', 'unknown')}")
            print(f"Valid Format: {format_analysis.get('is_valid_format', False)}")
            print(f"Valid Volume: {format_analysis.get('is_valid_volume', False)}")

        print("-" * 50)
