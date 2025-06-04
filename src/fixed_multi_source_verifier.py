"""
Multi-Source Citation Verification System

This module implements a cascading verification system that checks multiple sources
to verify citations, distinguishing between real cases not in CourtListener,
hallucinations, and typographical errors.
"""

import re
import requests
import urllib.parse
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

# Manual verification sources (for human verification)
MANUAL_VERIFICATION_SOURCES = {
    "descrybe": {
        "name": "Descrybe.ai",
        "url": "https://descrybe.ai/search",
        "description": "AI-powered legal research platform with citation verification capabilities",
    }
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
        if not format_analysis.get("is_valid_format", False):
            return {
                "found": False,
                "confirmed": False,
                "confidence": 0.1,
                "explanation": f"Invalid citation format: {format_analysis.get('error', 'Unknown error')}",
                "source": None,
                "case_name": case_name,
                "format_analysis": format_analysis,
            }

        # Determine which sources to check
        sources_to_check = sources or list(VERIFICATION_SOURCES.keys())

        # Check Court Listener first (primary source)
        if "courtlistener" in sources_to_check:
            try:
                cl_result = self.check_courtlistener(normalized_citation, case_name)
                if cl_result.get("found", False):
                    return cl_result
            except Exception as e:
                print(f"Error checking CourtListener: {e}")

        # Check other sources
        for source in [s for s in sources_to_check if s != "courtlistener"]:
            try:
                # Check if we have a method for this source
                method_name = f"check_{source}"
                if hasattr(self, method_name):
                    check_method = getattr(self, method_name)
                    result = check_method(normalized_citation, case_name)
                    self.verification_results[source] = result

                    # If found, return the result
                    if result.get("found", False):
                        return result
            except Exception as e:
                print(f"Error checking {source}: {e}")

        # If not found in any source, suggest manual verification with Descrybe.ai
        # This is after Court Listener but before summarization
        descrybe_info = MANUAL_VERIFICATION_SOURCES.get("descrybe", {})
        descrybe_url = descrybe_info.get("url", "https://descrybe.ai/search")

        # Calculate likelihood score
        likelihood_score = self.calculate_likelihood_score(
            normalized_citation, case_name, format_analysis
        )

        # Generate explanation
        explanation = self.generate_explanation(likelihood_score, format_analysis)

        # Create search URL for Descrybe.ai
        search_query = urllib.parse.quote(
            f"{normalized_citation} {case_name if case_name else ''}"
        )
        descrybe_search_url = f"{descrybe_url}?q={search_query}"

        return {
            "found": False,
            "confirmed": False,
            "confidence": likelihood_score,
            "explanation": explanation,
            "source": None,
            "case_name": case_name,
            "format_analysis": format_analysis,
            "manual_verification_suggested": True,
            "manual_verification_source": "Descrybe.ai",
            "manual_verification_url": descrybe_search_url,
            "manual_verification_message": "Citation not found in automated sources. Consider checking manually with Descrybe.ai's Cytationator tool before proceeding to AI summarization.",
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
                            "is_valid_format": False,
                            "format_type": format_type,
                            "error": f"Volume {volume} is outside the valid range for U.S. Reports",
                        }

                    return {
                        "is_valid_format": True,
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
                                "is_valid_format": False,
                                "format_type": format_type,
                                "error": f"Volume {volume} is outside the valid range for F.{series}d",
                            }

                    return {
                        "is_valid_format": True,
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
                                "is_valid_format": False,
                                "format_type": format_type,
                                "error": f"Volume {volume} is outside the valid range for F. Supp. {series}d",
                            }

                    return {
                        "is_valid_format": True,
                        "format_type": format_type,
                        "volume": volume,
                        "series": series,
                        "page": page,
                    }

                # For other formats, just return that it's valid
                return {"is_valid_format": True, "format_type": format_type}

        # If no pattern matched
        return {
            "is_valid_format": False,
            "error": "Citation format does not match any known pattern",
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
        if not format_analysis.get("is_valid_format", False):
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
        if not format_analysis.get("is_valid_format", False):
            return format_analysis.get("error", "Invalid citation format")

        format_type = format_analysis.get("format_type", "unknown")

        if likelihood_score < 0.3:
            return (
                f"This citation is likely a hallucination or contains a typographical error. "
                f"The format appears to be {format_type}, but the citation could not be verified "
                f"in any of our automated sources. Consider checking manually with Descrybe.ai before proceeding."
            )
        elif likelihood_score < 0.7:
            return (
                f"This citation has a valid {format_type} format, but could not be fully verified. "
                f"It may be a less common case or from a jurisdiction not well-covered in our database. "
                f"We recommend checking manually with Descrybe.ai's Cytationator tool to confirm."
            )
        else:
            return (
                f"This citation has a valid {format_type} format and is likely a real case, "
                f"though it was not found in our automated sources. The citation appears to be "
                f"correctly formatted and within expected volume ranges. Consider checking with "
                f"Descrybe.ai for final verification before proceeding to summarization."
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
        if not api_key:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": "CourtListener API key not provided",
                "source": "courtlistener",
            }

        # Prepare the request
        headers = {"Authorization": f"Token {api_key}"}

        # Construct the query
        params = {"q": citation_text, "format": "json"}

        # Make the request
        try:
            response = self.session.get(
                VERIFICATION_SOURCES["courtlistener"]["base_url"],
                headers=headers,
                params=params,
            )

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()

                # Check if any results were found
                if data.get("count", 0) > 0:
                    # Get the first result
                    result = data["results"][0]

                    # Check if the case name matches
                    result_case_name = result.get("case_name", "")
                    name_match = (
                        check_name_match(case_name, result_case_name)
                        if case_name
                        else True
                    )

                    return {
                        "found": True,
                        "confirmed": True,
                        "confidence": 0.9 if name_match else 0.7,
                        "explanation": f"Citation found in CourtListener: {result_case_name}",
                        "source": "courtlistener",
                        "case_name": result_case_name,
                        "url": result.get("absolute_url", None),
                    }
                else:
                    return {
                        "found": False,
                        "confidence": 0.5,
                        "explanation": "Citation not found in CourtListener",
                        "source": "courtlistener",
                    }
            else:
                return {
                    "found": False,
                    "confidence": 0.0,
                    "explanation": f"CourtListener API error: {response.status_code}",
                    "source": "courtlistener",
                }
        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking CourtListener: {str(e)}",
                "source": "courtlistener",
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
        # Construct the query
        query = citation_text
        if case_name:
            query = f"{citation_text} {case_name}"

        params = {
            "q": query,
            "hl": "en",
            "as_sdt": "0,5",
            "as_vis": "1",
            "as_ylo": "",
            "as_yhi": "",
        }

        # Make the request
        try:
            response = self.session.get(
                VERIFICATION_SOURCES["google_scholar"]["base_url"], params=params
            )

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Check if any results were found
                results = soup.select(".gs_r")
                if results:
                    # Get the first result
                    result = results[0]

                    # Extract the title
                    title_elem = result.select_one(".gs_rt")
                    title = title_elem.text if title_elem else ""

                    # Check if the case name matches
                    name_match = (
                        check_name_match(case_name, title) if case_name else True
                    )

                    # Extract the URL
                    url_elem = title_elem.find("a") if title_elem else None
                    url = (
                        url_elem["href"]
                        if url_elem and "href" in url_elem.attrs
                        else None
                    )

                    return {
                        "found": True,
                        "confirmed": True,
                        "confidence": 0.8 if name_match else 0.6,
                        "explanation": f"Citation found in Google Scholar: {title}",
                        "source": "google_scholar",
                        "case_name": title,
                        "url": url,
                    }
                else:
                    return {
                        "found": False,
                        "confidence": 0.4,
                        "explanation": "Citation not found in Google Scholar",
                        "source": "google_scholar",
                    }
            else:
                return {
                    "found": False,
                    "confidence": 0.0,
                    "explanation": f"Google Scholar error: {response.status_code}",
                    "source": "google_scholar",
                }
        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Google Scholar: {str(e)}",
                "source": "google_scholar",
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
        # Construct the query
        query = citation_text
        if case_name:
            query = f"{citation_text} {case_name}"

        params = {"q": query}

        # Make the request
        try:
            response = self.session.get(
                VERIFICATION_SOURCES["justia"]["base_url"], params=params
            )

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Check if any results were found
                results = soup.select(".result")
                if results:
                    # Get the first result
                    result = results[0]

                    # Extract the title
                    title_elem = result.select_one("h2 a")
                    title = title_elem.text if title_elem else ""

                    # Check if the case name matches
                    name_match = (
                        check_name_match(case_name, title) if case_name else True
                    )

                    # Extract the URL
                    url = (
                        title_elem["href"]
                        if title_elem and "href" in title_elem.attrs
                        else None
                    )

                    return {
                        "found": True,
                        "confirmed": True,
                        "confidence": 0.8 if name_match else 0.6,
                        "explanation": f"Citation found in Justia: {title}",
                        "source": "justia",
                        "case_name": title,
                        "url": url,
                    }
                else:
                    return {
                        "found": False,
                        "confidence": 0.4,
                        "explanation": "Citation not found in Justia",
                        "source": "justia",
                    }
            else:
                return {
                    "found": False,
                    "confidence": 0.0,
                    "explanation": f"Justia error: {response.status_code}",
                    "source": "justia",
                }
        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error checking Justia: {str(e)}",
                "source": "justia",
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

        if result.get("manual_verification_suggested", False):
            print(
                f"Manual verification suggested: {result.get('manual_verification_source')}"
            )
            print(f"Manual verification URL: {result.get('manual_verification_url')}")
            print(
                f"Manual verification message: {result.get('manual_verification_message')}"
            )
