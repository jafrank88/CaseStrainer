"""
Enhanced Multi-Source Verifier

This module provides an enhanced citation verification system that uses multiple sources
and advanced techniques to validate legal citations.
"""

import os
import sys
import json
import logging
import requests
import re
import time
import sqlite3
from datetime import datetime
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("enhanced_verifier")


class EnhancedMultiSourceVerifier:
    """
    An enhanced citation verifier that uses multiple sources and techniques
    to validate legal citations with higher accuracy.
    """

    def __init__(self):
        """Initialize the verifier with API keys and configuration."""
        self.config = self._load_config()
        self.courtlistener_api_key = self.config.get("courtlistener_api_key", "")
        self.langsearch_api_key = self.config.get("langsearch_api_key", "")
        self.cache_dir = "citation_cache"
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "citations.db"
        )

        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Import the original MultiSourceVerifier
        try:
            spec = importlib.util.spec_from_file_location(
                "multi_source_verifier",
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "fixed_multi_source_verifier.py",
                ),
            )
            verifier_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(verifier_module)
            self.original_verifier = verifier_module.MultiSourceVerifier()
            logger.info("Successfully imported original MultiSourceVerifier")
        except Exception as e:
            logger.error(f"Error importing original MultiSourceVerifier: {e}")
            self.original_verifier = None

    def _load_config(self):
        """Load configuration from config.json."""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _normalize_citation(self, citation):
        """Normalize citation format for better matching."""
        if not citation:
            return ""

        # Replace multiple spaces with a single space
        normalized = re.sub(r"\s+", " ", citation.strip())

        # Normalize Washington citations
        normalized = re.sub(r"Wash\.\s*App\.", "Wn. App.", normalized)
        normalized = re.sub(r"Wash\.", "Wn.", normalized)

        # Normalize Pacific Reporter citations
        normalized = re.sub(r"P\.(\d+)d", "P.2d", normalized)
        normalized = re.sub(r"P\.(\d+)th", "P.3d", normalized)

        # Normalize Federal Reporter citations
        normalized = re.sub(r"F\.(\d+)d", "F.2d", normalized)
        normalized = re.sub(r"F\.(\d+)th", "F.3d", normalized)

        return normalized

    def _extract_citation_components(self, citation):
        """Extract components from a citation for flexible matching."""
        components = {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        # Extract volume, reporter, and page
        volume_reporter_page = re.search(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)", citation)
        if volume_reporter_page:
            components["volume"] = volume_reporter_page.group(1)
            components["reporter"] = volume_reporter_page.group(2).strip()
            components["page"] = volume_reporter_page.group(3)

        # Extract year
        year = re.search(r"\((\d{4})\)", citation)
        if year:
            components["year"] = year.group(1)

        # Extract court
        if "Wn. App." in citation or "Wash. App." in citation:
            components["court"] = "Washington Court of Appeals"
        elif "Wn." in citation or "Wash." in citation:
            components["court"] = "Washington Supreme Court"
        elif "U.S." in citation:
            components["court"] = "United States Supreme Court"
        elif "F." in citation:
            if "Supp." in citation:
                components["court"] = "United States District Court"
            else:
                components["court"] = "United States Court of Appeals"

        return components

    def _check_cache(self, citation):
        """Check if the citation is in the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
        )
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache for citation '{citation}': {e}")
        return None

    def _save_to_cache(self, citation, result):
        """Save the verification result to the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
        )
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache for citation '{citation}': {e}")

    def _verify_with_courtlistener(self, citation):
        """Verify a citation using the CourtListener API."""
        if not self.courtlistener_api_key:
            return {
                "verified": False,
                "source": "CourtListener",
                "error": "No API key provided",
            }

        try:
            # Extract components for flexible search
            components = self._extract_citation_components(citation)

            # Build the search query
            query = (
                f"{components['volume']} {components['reporter']} {components['page']}"
            )

            # Make the API request
            headers = {"Authorization": f"Token {self.courtlistener_api_key}"}
            params = {"q": query, "format": "json"}
            response = requests.get(
                "https://www.courtlistener.com/api/rest/v3/search/",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                return {
                    "verified": False,
                    "source": "CourtListener",
                    "error": f"API error: {response.status_code}",
                }

            data = response.json()

            # Check if any results match the citation
            if data.get("count", 0) > 0:
                for result in data.get("results", []):
                    # Check if volume, reporter, and page match
                    citation_string = result.get("citation", "")
                    if (
                        components["volume"] in citation_string
                        and components["reporter"] in citation_string
                        and components["page"] in citation_string
                    ):
                        return {
                            "verified": True,
                            "source": "CourtListener",
                            "case_name": result.get("caseName", ""),
                            "date_filed": result.get("dateFiled", ""),
                            "docket_number": result.get("docketNumber", ""),
                            "court": result.get("court", ""),
                            "citation": citation_string,
                            "absolute_url": result.get("absolute_url", ""),
                        }

            return {
                "verified": False,
                "source": "CourtListener",
                "error": "Citation not found",
            }

        except Exception as e:
            logger.error(
                f"Error verifying citation '{citation}' with CourtListener: {e}"
            )
            return {"verified": False, "source": "CourtListener", "error": str(e)}

    def _verify_with_langsearch(self, citation):
        """Verify a citation using the LangSearch API."""
        if not self.langsearch_api_key:
            return {
                "verified": False,
                "source": "LangSearch",
                "error": "No API key provided",
            }

        try:
            # Extract components for flexible search
            components = self._extract_citation_components(citation)

            # Build the search query
            query = f"legal citation {components['volume']} {components['reporter']} {components['page']}"
            if components["year"]:
                query += f" {components['year']}"
            if components["court"]:
                query += f" {components['court']}"

            # Make the API request
            headers = {
                "Authorization": f"Bearer {self.langsearch_api_key}",
                "Content-Type": "application/json",
            }
            data = {"query": query, "max_results": 3}
            response = requests.post(
                "https://api.langsearch.ai/v1/search", headers=headers, json=data
            )

            if response.status_code != 200:
                return {
                    "verified": False,
                    "source": "LangSearch",
                    "error": f"API error: {response.status_code}",
                }

            results = response.json()

            # Check if any results match the citation
            if results.get("results", []):
                for result in results.get("results", []):
                    content = result.get("content", "")
                    # Check if the content contains the citation components
                    if (
                        components["volume"] in content
                        and components["reporter"] in content
                        and components["page"] in content
                    ):
                        return {
                            "verified": True,
                            "source": "LangSearch",
                            "content": content,
                            "url": result.get("url", ""),
                            "score": result.get("score", 0),
                        }

            return {
                "verified": False,
                "source": "LangSearch",
                "error": "Citation not found",
            }

        except Exception as e:
            logger.error(f"Error verifying citation '{citation}' with LangSearch: {e}")
            return {"verified": False, "source": "LangSearch", "error": str(e)}

    def _verify_with_database(self, citation):
        """Verify a citation using the internal database of previously verified citations."""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Normalize the citation
            normalized_citation = self._normalize_citation(citation)

            # Extract components for flexible matching
            components = self._extract_citation_components(citation)

            # Check for exact match
            cursor.execute(
                "SELECT * FROM citations WHERE citation_text = ? AND found = 1",
                (citation,),
            )
            exact_match = cursor.fetchone()

            if exact_match:
                conn.close()
                return {
                    "verified": True,
                    "source": "Database",
                    "match_type": "exact",
                    "citation_id": exact_match[0],
                }

            # Check for normalized match
            cursor.execute(
                "SELECT * FROM citations WHERE citation_text = ? AND found = 1",
                (normalized_citation,),
            )
            normalized_match = cursor.fetchone()

            if normalized_match:
                conn.close()
                return {
                    "verified": True,
                    "source": "Database",
                    "match_type": "normalized",
                    "citation_id": normalized_match[0],
                }

            # Check for component match (volume, reporter, page)
            if components["volume"] and components["reporter"] and components["page"]:
                # Use LIKE queries for flexible matching
                volume_pattern = f"%{components['volume']}%"
                reporter_pattern = f"%{components['reporter']}%"
                page_pattern = f"%{components['page']}%"

                cursor.execute(
                    """
                    SELECT * FROM citations 
                    WHERE citation_text LIKE ? AND citation_text LIKE ? AND citation_text LIKE ? AND found = 1
                    """,
                    (volume_pattern, reporter_pattern, page_pattern),
                )
                component_match = cursor.fetchone()

                if component_match:
                    conn.close()
                    return {
                        "verified": True,
                        "source": "Database",
                        "match_type": "component",
                        "citation_id": component_match[0],
                    }

            conn.close()
            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database",
            }

        except Exception as e:
            logger.error(f"Error verifying citation '{citation}' with database: {e}")
            return {"verified": False, "source": "Database", "error": str(e)}

    def _verify_with_landmark_cases(self, citation):
        """Verify a citation against a database of landmark cases."""
        try:
            # Load landmark cases
            landmark_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "landmark_cases.json"
            )
            if not os.path.exists(landmark_path):
                return {
                    "verified": False,
                    "source": "Landmark Cases",
                    "error": "Landmark cases database not found",
                }

            with open(landmark_path, "r") as f:
                landmark_cases = json.load(f)

            # Normalize the citation
            normalized_citation = self._normalize_citation(citation)

            # Extract components for flexible matching
            components = self._extract_citation_components(citation)

            # Check for exact match
            for case in landmark_cases:
                if citation == case.get("citation", ""):
                    return {
                        "verified": True,
                        "source": "Landmark Cases",
                        "match_type": "exact",
                        "case_name": case.get("case_name", ""),
                        "year": case.get("year", ""),
                    }

            # Check for normalized match
            for case in landmark_cases:
                if normalized_citation == self._normalize_citation(
                    case.get("citation", "")
                ):
                    return {
                        "verified": True,
                        "source": "Landmark Cases",
                        "match_type": "normalized",
                        "case_name": case.get("case_name", ""),
                        "year": case.get("year", ""),
                    }

            # Check for component match
            if components["volume"] and components["reporter"] and components["page"]:
                for case in landmark_cases:
                    case_components = self._extract_citation_components(
                        case.get("citation", "")
                    )
                    if (
                        components["volume"] == case_components["volume"]
                        and components["reporter"] == case_components["reporter"]
                        and components["page"] == case_components["page"]
                    ):
                        return {
                            "verified": True,
                            "source": "Landmark Cases",
                            "match_type": "component",
                            "case_name": case.get("case_name", ""),
                            "year": case.get("year", ""),
                        }

            return {
                "verified": False,
                "source": "Landmark Cases",
                "error": "Citation not found in landmark cases",
            }

        except Exception as e:
            logger.error(
                f"Error verifying citation '{citation}' with landmark cases: {e}"
            )
            return {"verified": False, "source": "Landmark Cases", "error": str(e)}

    def _verify_with_fuzzy_matching(self, citation):
        """Verify a citation using fuzzy matching against known patterns."""
        try:
            # Define known citation patterns
            patterns = [
                # Washington Reports
                r"(\d+)\s+Wn\.\s*(?:App\.)?\s*(\d+)",
                r"(\d+)\s+Wash\.\s*(?:App\.)?\s*(\d+)",
                # Pacific Reporter
                r"(\d+)\s+P\.\s*(\d+)",
                r"(\d+)\s+P\.\s*\d+d\s*(\d+)",
                r"(\d+)\s+P\.\s*\d+th\s*(\d+)",
                # United States Reports
                r"(\d+)\s+U\.S\.\s*(\d+)",
                # Supreme Court Reporter
                r"(\d+)\s+S\.\s*Ct\.\s*(\d+)",
                # Federal Reporter
                r"(\d+)\s+F\.\s*(\d+)",
                r"(\d+)\s+F\.\s*\d+d\s*(\d+)",
                r"(\d+)\s+F\.\s*\d+th\s*(\d+)",
                r"(\d+)\s+F\.\s*Supp\.\s*(\d+)",
                r"(\d+)\s+F\.\s*Supp\.\s*\d+d\s*(\d+)",
            ]

            # Check if the citation matches any known pattern
            for pattern in patterns:
                match = re.search(pattern, citation)
                if match:
                    return {
                        "verified": True,
                        "source": "Fuzzy Matching",
                        "match_type": "pattern",
                        "pattern": pattern,
                        "volume": match.group(1),
                        "page": match.group(2),
                    }

            return {
                "verified": False,
                "source": "Fuzzy Matching",
                "error": "Citation does not match any known pattern",
            }

        except Exception as e:
            logger.error(
                f"Error verifying citation '{citation}' with fuzzy matching: {e}"
            )
            return {"verified": False, "source": "Fuzzy Matching", "error": str(e)}

    def _verify_with_original_verifier(self, citation):
        """Verify a citation using the original MultiSourceVerifier."""
        if not self.original_verifier:
            return {
                "verified": False,
                "source": "Original Verifier",
                "error": "Original verifier not available",
            }

        try:
            result = self.original_verifier.verify_citation(citation)
            return {
                "verified": result.get("verified", False),
                "source": "Original Verifier",
                "original_result": result,
            }

        except Exception as e:
            logger.error(
                f"Error verifying citation '{citation}' with original verifier: {e}"
            )
            return {"verified": False, "source": "Original Verifier", "error": str(e)}

    def verify_citation(self, citation):
        """
        Verify a citation using multiple sources and techniques.
        Returns a comprehensive verification result.
        """
        if not citation:
            return {"verified": False, "error": "No citation provided"}

        logger.info(f"Verifying citation: {citation}")

        # Check cache first
        cached_result = self._check_cache(citation)
        if cached_result:
            logger.info(f"Found cached result for citation: {citation}")
            return cached_result

        # Initialize verification results
        verification_results = {
            "citation": citation,
            "normalized_citation": self._normalize_citation(citation),
            "components": self._extract_citation_components(citation),
            "verified": False,
            "verification_date": datetime.now().isoformat(),
            "sources": {},
        }

        # Verify with original verifier first
        original_result = self._verify_with_original_verifier(citation)
        verification_results["sources"]["original_verifier"] = original_result

        # If original verifier verified the citation, we're done
        if original_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Original Verifier"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with database
        database_result = self._verify_with_database(citation)
        verification_results["sources"]["database"] = database_result

        if database_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Database"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with landmark cases
        landmark_result = self._verify_with_landmark_cases(citation)
        verification_results["sources"]["landmark_cases"] = landmark_result

        if landmark_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Landmark Cases"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with fuzzy matching
        fuzzy_result = self._verify_with_fuzzy_matching(citation)
        verification_results["sources"]["fuzzy_matching"] = fuzzy_result

        if fuzzy_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Fuzzy Matching"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with CourtListener
        courtlistener_result = self._verify_with_courtlistener(citation)
        verification_results["sources"]["courtlistener"] = courtlistener_result

        if courtlistener_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "CourtListener"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with LangSearch
        langsearch_result = self._verify_with_langsearch(citation)
        verification_results["sources"]["langsearch"] = langsearch_result

        if langsearch_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "LangSearch"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # If we get here, the citation could not be verified
        verification_results["verified"] = False
        verification_results["error"] = "Citation could not be verified by any source"

        # Save to cache
        self._save_to_cache(citation, verification_results)

        return verification_results

    def batch_verify_citations(self, citations):
        """
        Verify a batch of citations.
        Returns a list of verification results.
        """
        results = []

        for citation in citations:
            result = self.verify_citation(citation)
            results.append(result)

            # Add a small delay to avoid rate limiting
            time.sleep(1.0)  # 1 second delay to handle 60 citations per minute

        return results


# Example usage
if __name__ == "__main__":
    verifier = EnhancedMultiSourceVerifier()

    # Example citations
    citations = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483",  # Brown v. Board of Education
        "5 U.S. 137",  # Marbury v. Madison
        "198 Wn.2d 271",  # Washington Supreme Court case
        "175 Wn. App. 1",  # Washington Court of Appeals case
    ]

    # Verify each citation
    for citation in citations:
        result = verifier.verify_citation(citation)
        print(f"Citation: {citation}")
        print(f"Verified: {result['verified']}")
        if result["verified"]:
            print(f"Verified by: {result.get('verified_by', 'Unknown')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        print()
