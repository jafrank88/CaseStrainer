"""
Enhanced Multi-Source Citation Verification System

This module implements a cascading verification system that checks multiple sources
to verify citations, distinguishing between real cases not in CourtListener,
hallucinations, and typographical errors.
"""

import re
import requests
import traceback
from bs4 import BeautifulSoup

# Import functions from app_final_vue.py if available
try:
    from app_final_vue import is_landmark_case, normalize_citation, check_name_match

    print("Successfully imported functions from app_final_vue.py")
except ImportError:
    print("Warning: Could not import functions from app_final_vue.py")

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


# List of verification sources to check
VERIFICATION_SOURCES = [
    "courtlistener",
    "google_scholar",
    "justia",
    "findlaw",
    "leagle",
    "casetext",
]

# API configuration for different sources
API_CONFIG = {
    "courtlistener": {
        "base_url": "https://www.courtlistener.com/api/rest/v4/search/",
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

        # Check if citation is a landmark case
        landmark_case = is_landmark_case(normalized_citation)
        if landmark_case:
            return {
                "found": True,
                "confidence": 1.0,
                "explanation": f"This is a landmark case: {landmark_case}",
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

        # Determine which sources to check
        sources_to_check = sources or VERIFICATION_SOURCES

        # Check each source
        for source in sources_to_check:
            if source not in VERIFICATION_SOURCES:
                continue

            try:
                # Call the appropriate method for this source
                method_name = f"check_{source}"
                if hasattr(self, method_name):
                    result = getattr(self, method_name)(normalized_citation, case_name)
                    self.verification_results[source] = result

                    # If found, return immediately
                    if result.get("found", False):
                        return {
                            "found": True,
                            "confidence": result.get("confidence", 0.8),
                            "explanation": result.get(
                                "explanation", f"Citation verified by {source}"
                            ),
                            "source": source,
                            "format_analysis": format_analysis,
                        }
            except Exception as e:
                print(f"Error checking {source}: {str(e)}")
                traceback.print_exc()

        # If not found in any source, calculate likelihood
        likelihood_score = self.calculate_likelihood_score(
            normalized_citation, case_name, format_analysis
        )

        # Generate explanation
        explanation = self.generate_explanation(likelihood_score, format_analysis)

        return {
            "found": False,
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

        # If format is invalid, very low likelihood
        if not format_analysis.get("valid", False):
            return 0.1

        # Adjust score based on format type
        format_type = format_analysis.get("format_type")
        if format_type == "us_reports":
            # U.S. Reports are well-documented, so less likely to be missing
            score -= 0.2
        elif format_type in ["federal_reporter", "federal_supplement"]:
            # These are also well-documented but have more volumes
            score -= 0.1

        # Check for case name presence
        if case_name:
            score += 0.1

        # Adjust for specific volume ranges
        if format_type == "us_reports":
            volume = format_analysis.get("volume")
            if volume:
                # Newer volumes are more likely to be in databases
                if volume > 500:
                    score -= 0.1
                # Very old volumes might be missing
                elif volume < 50:
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
        if not format_analysis.get("valid", False):
            return format_analysis.get("explanation", "Invalid citation format")

        format_type = format_analysis.get("format_type", "unknown")

        if likelihood_score < 0.3:
            return (
                f"This citation is likely a hallucination or contains a typographical error. "
                f"The format appears to be {format_type}, but the citation could not be verified "
                f"in any of the legal databases checked."
            )
        elif likelihood_score < 0.7:
            return (
                f"This citation could not be verified in the databases checked. "
                f"It has a valid {format_type} format, but may be a less common case "
                f"or from a jurisdiction not well-covered in the databases."
            )
        else:
            return (
                f"This citation has a valid {format_type} format and is likely a real case, "
                f"but could not be found in the databases checked. It may be from a specialized "
                f"reporter or a very recent case not yet indexed."
            )

    def check_courtlistener(self, citation_text, case_name=None):
        """
        Check a citation using the CourtListener API.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        # Check if we have an API key
        api_key = self.api_keys.get("courtlistener")
        if not api_key and API_CONFIG["courtlistener"]["requires_api_key"]:
            return {"found": False, "explanation": "CourtListener API key not provided"}

        try:
            # Prepare query parameters
            params = {"citation": citation_text}

            if case_name:
                params["case_name"] = case_name

            # Set up headers
            headers = {}
            if api_key:
                headers["Authorization"] = f"Token {api_key}"

            # Make the request
            response = self.session.get(
                API_CONFIG["courtlistener"]["base_url"], params=params, headers=headers
            )

            # Check if request was successful
            if response.status_code == 200:
                data = response.json()

                # Check if any results were found
                if data.get("count", 0) > 0:
                    result = data["results"][0]

                    # If case name was provided, check for a match
                    if case_name and not check_name_match(
                        case_name, result.get("case_name", "")
                    ):
                        return {
                            "found": False,
                            "confidence": 0.3,
                            "explanation": "Citation found but case name does not match",
                        }

                    return {
                        "found": True,
                        "confidence": 0.9,
                        "explanation": "Citation verified by CourtListener",
                        "details": result,
                    }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in CourtListener",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking CourtListener: {str(e)}",
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
        try:
            # Prepare query
            query = citation_text
            if case_name:
                query = f"{case_name} {citation_text}"

            # Prepare parameters
            params = {
                "q": query,
                "hl": "en",
                "as_sdt": "0,5",  # Search only in law
                "as_vis": "1",
            }

            # Make the request
            response = self.session.get(
                API_CONFIG["google_scholar"]["base_url"], params=params
            )

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for results
                results = soup.select(".gs_r")

                if results:
                    # Check if citation appears in any result
                    for result in results:
                        result_text = result.get_text()

                        # Check if citation appears in the result
                        if citation_text in result_text:
                            # If case name was provided, check for a match
                            if case_name and not any(
                                check_name_match(case_name, part)
                                for part in result_text.split("\n")
                            ):
                                continue

                            return {
                                "found": True,
                                "confidence": 0.8,
                                "explanation": "Citation verified by Google Scholar",
                            }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in Google Scholar",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Google Scholar: {str(e)}",
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
        try:
            # Prepare query
            query = citation_text
            if case_name:
                query = f"{case_name} {citation_text}"

            # Prepare parameters
            params = {"query": query}

            # Make the request
            response = self.session.get(API_CONFIG["justia"]["base_url"], params=params)

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for results
                results = soup.select(".result-title")

                if results:
                    # Check if citation appears in any result
                    for result in results:
                        result_text = result.get_text()

                        # Check if citation appears in the result
                        if citation_text in result_text:
                            # If case name was provided, check for a match
                            if case_name and not check_name_match(
                                case_name, result_text
                            ):
                                continue

                            return {
                                "found": True,
                                "confidence": 0.8,
                                "explanation": "Citation verified by Justia",
                            }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in Justia",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Justia: {str(e)}",
            }

    def check_findlaw(self, citation_text, case_name=None):
        """
        Check a citation using FindLaw.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        try:
            # Prepare query
            query = citation_text
            if case_name:
                query = f"{case_name} {citation_text}"

            # Prepare parameters
            params = {"query": query}

            # Make the request
            response = self.session.get(
                API_CONFIG["findlaw"]["base_url"], params=params
            )

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for results
                results = soup.select(".search-result")

                if results:
                    # Check if citation appears in any result
                    for result in results:
                        result_text = result.get_text()

                        # Check if citation appears in the result
                        if citation_text in result_text:
                            # If case name was provided, check for a match
                            if case_name and not check_name_match(
                                case_name, result_text
                            ):
                                continue

                            return {
                                "found": True,
                                "confidence": 0.8,
                                "explanation": "Citation verified by FindLaw",
                            }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in FindLaw",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking FindLaw: {str(e)}",
            }

    def check_leagle(self, citation_text, case_name=None):
        """
        Check a citation using Leagle.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        try:
            # Prepare query
            query = citation_text
            if case_name:
                query = f"{case_name} {citation_text}"

            # Prepare parameters
            params = {"q": query}

            # Make the request
            response = self.session.get(API_CONFIG["leagle"]["base_url"], params=params)

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for results
                results = soup.select(".result")

                if results:
                    # Check if citation appears in any result
                    for result in results:
                        result_text = result.get_text()

                        # Check if citation appears in the result
                        if citation_text in result_text:
                            # If case name was provided, check for a match
                            if case_name and not check_name_match(
                                case_name, result_text
                            ):
                                continue

                            return {
                                "found": True,
                                "confidence": 0.8,
                                "explanation": "Citation verified by Leagle",
                            }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in Leagle",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Leagle: {str(e)}",
            }

    def check_casetext(self, citation_text, case_name=None):
        """
        Check a citation using Casetext.

        Args:
            citation_text (str): The citation text to check
            case_name (str, optional): The case name to match

        Returns:
            dict: Verification result
        """
        try:
            # Prepare query
            query = citation_text
            if case_name:
                query = f"{case_name} {citation_text}"

            # Prepare parameters
            params = {"q": query}

            # Make the request
            response = self.session.get(
                API_CONFIG["casetext"]["base_url"], params=params
            )

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for results
                results = soup.select(".case-result")

                if results:
                    # Check if citation appears in any result
                    for result in results:
                        result_text = result.get_text()

                        # Check if citation appears in the result
                        if citation_text in result_text:
                            # If case name was provided, check for a match
                            if case_name and not check_name_match(
                                case_name, result_text
                            ):
                                continue

                            return {
                                "found": True,
                                "confidence": 0.8,
                                "explanation": "Citation verified by Casetext",
                            }

            # If no results or error
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": "Citation not found in Casetext",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Casetext: {str(e)}",
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
