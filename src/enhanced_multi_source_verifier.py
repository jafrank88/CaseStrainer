"""
Enhanced Multi-Source Verifier

This module provides an enhanced citation verification system that uses multiple sources
and advanced techniques to validate legal citations.
"""

import os
import json
import logging
import requests
import re
import time
import sqlite3
import datetime
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
        """Normalize citation format for better matching.

        This method normalizes citations by:
        1. Removing extra whitespace
        2. Standardizing Washington citations (Wash. -> Wn.)
        3. Preserving reporter series (e.g., P.3d, F.4th)

        Args:
            citation (str): The citation to normalize

        Returns:
            str: The normalized citation
        """
        if not citation or not isinstance(citation, str):
            return ""

        # Replace multiple spaces with a single space and trim
        normalized = re.sub(r"\s+", " ", citation.strip())

        # Normalize Washington citations
        normalized = re.sub(r"Wash\.\s*App\.", "Wn. App.", normalized)
        normalized = re.sub(r"Wash\.", "Wn.", normalized)

        # Clean up common formatting issues
        normalized = re.sub(r"\s*,\s*", ", ", normalized)  # Standardize commas
        normalized = re.sub(r"\s+v\.?\s+", " v. ", normalized)  # Standardize v.
        normalized = re.sub(r"\s+&\.?\s+", " & ", normalized)  # Standardize &

        return normalized

    def _extract_citation_components(self, citation):
        """Extract components from a citation for flexible matching.

        Handles various citation formats including:
        - Standard: 123 Wn.2d 456
        - Pinpoint: 123 Wn.2d 456, 459
        - Parallel: 123 Wn.2d 456, 789 P.2d 123
        - Short form: Id. at 459

        Args:
            citation (str): The citation to parse

        Returns:
            dict: Dictionary containing citation components
        """
        if not citation or not isinstance(citation, str):
            return {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        components = {
            "volume": "",
            "reporter": "",
            "page": "",
            "court": "",
            "year": "",
            "pinpoint": "",
            "parallel_citations": [],
        }

        try:
            # Handle short form citations (e.g., "Id. at 459")
            if citation.lower().startswith(("id.", "idem")):
                components["short_form"] = True
                # Extract pinpoint reference if present
                pinpoint_match = re.search(r"(?:at\s+)(\d+)", citation, re.IGNORECASE)
                if pinpoint_match:
                    components["pinpoint"] = pinpoint_match.group(1)
                return components

            # Handle parallel citations (e.g., "123 Wn.2d 456, 789 P.2d 123")
            if "," in citation:
                parts = [p.strip() for p in citation.split(",")]
                if len(parts) > 1 and any(p[0].isdigit() for p in parts[1:]):
                    components["parallel_citations"] = [
                        p.strip() for p in parts[1:] if p.strip()
                    ]
                    citation = parts[0]  # Process the first citation normally

            # Extract volume, reporter, and page
            # Handle formats like: 123 Wn.2d 456, 123 Wn App 456, 123 F.3d 456, 123 F.Supp.2d 456
            volume_reporter_page = re.search(
                r"(\d+)\s+([A-Za-z\.\s]+?)(?:\s+(\d+))?(?:\s*,\s*(\d+))?", citation
            )

            if volume_reporter_page:
                components["volume"] = volume_reporter_page.group(1)
                components["reporter"] = volume_reporter_page.group(2).strip()

                # Handle both main page and pinpoint (e.g., "123 Wn.2d 456, 459")
                if volume_reporter_page.group(4):  # Has pinpoint
                    components["page"] = volume_reporter_page.group(3)
                    components["pinpoint"] = volume_reporter_page.group(4)
                elif volume_reporter_page.group(3):  # Just page number
                    components["page"] = volume_reporter_page.group(3)

            # Extract year if present (e.g., "(1999)" or ", 1999")
            year_match = re.search(r"\((\d{4})\)|,\s*(\d{4})\b", citation)
            if year_match:
                components["year"] = year_match.group(1) or year_match.group(2)

            # Determine court based on reporter
            reporter = components["reporter"].lower()
            if "wn. app" in reporter or "wash. app" in reporter:
                components["court"] = "Washington Court of Appeals"
            elif "wn." in reporter or "wash." in reporter:
                components["court"] = "Washington Supreme Court"
            elif "u.s." in reporter:
                components["court"] = "United States Supreme Court"
            elif "f.supp" in reporter:
                components["court"] = "United States District Court"
            elif "f." in reporter:
                components["court"] = "United States Court of Appeals"

            # Clean up reporter abbreviation
            components["reporter"] = (
                components["reporter"].replace(" ", "").replace("..", ".")
            )

        except Exception as e:
            logger.warning(
                f"Error extracting citation components from '{citation}': {e}"
            )

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

    def _save_to_database(self, citation, result):
        """
        Save the verification result to the database, including parallel citations.

        Args:
            citation (str): The original citation
            result (dict): Verification result with optional parallel_citations list
        """
        if not citation or not isinstance(citation, str):
            logger.error("Invalid citation provided to _save_to_database")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create tables if they don't exist with the correct schema
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_text TEXT NOT NULL UNIQUE,
                    case_name TEXT,
                    confidence REAL,
                    found BOOLEAN,
                    explanation TEXT,
                    source TEXT,
                    source_document TEXT,
                    url TEXT,
                    context TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create parallel_citations table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS parallel_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_id INTEGER NOT NULL,
                    citation TEXT NOT NULL,
                    reporter TEXT,
                    category TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citation_id) REFERENCES citations(id) ON DELETE CASCADE,
                    UNIQUE(citation_id, citation)
                )
            """
            )

            # Get current schema to handle any missing columns
            cursor.execute("PRAGMA table_info(citations)")
            columns = {column[1].lower(): column[1] for column in cursor.fetchall()}

            # Add any missing columns with proper error handling
            columns_to_add = [
                ("found", "BOOLEAN"),
                ("explanation", "TEXT"),
                ("source", "TEXT"),
                ("source_document", "TEXT"),
                ("url", "TEXT"),
                ("context", "TEXT"),
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in columns:
                    try:
                        cursor.execute(
                            f"ALTER TABLE citations ADD COLUMN {col_name} {col_type}"
                        )
                        logger.info(
                            f"Added missing column {col_name} to citations table"
                        )
                    except sqlite3.Error as e:
                        logger.warning(f"Error adding column {col_name}: {e}")

            # Always use citation_text as the column name for consistency
            citation_col = "citation_text"

            # Prepare the data for insertion/update
            case_name = result.get("case_name", "")
            found = bool(result.get("verified", False))
            explanation = f"Verified via {result.get('source', 'unknown')} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            source = result.get("source", "")
            url = result.get("absolute_url", result.get("url", ""))
            source_doc = result.get("source_document", "")
            parallel_cites = result.get("parallel_citations", [])

            try:
                # First, insert or update the main citation
                cursor.execute(
                    """
                    INSERT INTO citations (
                        citation_text, case_name, found, explanation, 
                        source, url, source_document, context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(citation_text) DO UPDATE SET
                        case_name = excluded.case_name,
                        found = excluded.found,
                        explanation = excluded.explanation,
                        source = excluded.source,
                        url = excluded.url,
                        source_document = excluded.source_document,
                        context = excluded.context
                    RETURNING id
                """,
                    (
                        citation,
                        case_name,
                        found,
                        explanation,
                        source,
                        url,
                        source_doc,
                        result.get("context", ""),  # Include context if available
                    ),
                )

                # Get the citation ID
                row = cursor.fetchone()
                if not row:
                    raise Exception("Failed to get citation ID after insert/update")

                citation_id = row[0]

                # Handle parallel citations if they exist
                if parallel_cites and isinstance(parallel_cites, list):
                    # First, get existing parallel citations to determine what needs to be updated/inserted/deleted
                    cursor.execute(
                        """
                        SELECT citation FROM parallel_citations 
                        WHERE citation_id = ?
                    """,
                        (citation_id,),
                    )
                    existing_parallels = {row[0] for row in cursor.fetchall()}

                    # Process each parallel citation
                    for parallel in parallel_cites:
                        if not isinstance(parallel, dict):
                            continue

                        cite = parallel.get("citation", "").strip()
                        if not cite:
                            continue

                        # Remove from existing_parallels set to track what needs to be deleted
                        if cite in existing_parallels:
                            existing_parallels.remove(cite)

                        # Insert or update the parallel citation
                        cursor.execute(
                            """
                            INSERT INTO parallel_citations (
                                citation_id, citation, reporter, category
                            ) VALUES (?, ?, ?, ?)
                            ON CONFLICT(citation_id, citation) DO UPDATE SET
                                reporter = excluded.reporter,
                                category = excluded.category
                        """,
                            (
                                citation_id,
                                cite,
                                parallel.get("reporter", ""),
                                parallel.get("category", ""),
                            ),
                        )

                    # Delete any remaining parallel citations that weren't in the new list
                    if existing_parallels:
                        placeholders = ",".join(["?"] * len(existing_parallels))
                        cursor.execute(
                            f"""
                            DELETE FROM parallel_citations 
                            WHERE citation_id = ? 
                            AND citation IN ({placeholders})
                            """,
                            [citation_id] + list(existing_parallels),
                        )

                # Commit the transaction
                conn.commit()
                logger.debug(
                    f"Successfully saved verification result for citation '{citation}' to database"
                )
                return True

            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database error saving citation '{citation}': {e}")
                return False
            except Exception as e:
                conn.rollback()
                logger.error(f"Unexpected error saving citation '{citation}': {e}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Database error saving citation '{citation}': {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(
                f"Error saving verification result for citation '{citation}': {e}"
            )
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def _get_parallel_citations(self, case_data):
        """Extract parallel citations from case data.

        Handles CourtListener API v4 response format where citations might be in different fields.
        """
        parallel_cites = []
        if not case_data:
            return parallel_cites

        try:
            # Try to get citations from the case data
            citations = case_data.get("citations", [])

            # If no citations array, try to get from the opinion_cites field
            if not citations and "opinion_cites" in case_data:
                citations = [
                    cite
                    for cite in case_data["opinion_cites"]
                    if isinstance(cite, dict) and "cite" in cite
                ]

            # Process all found citations
            for cite in citations:
                # Skip if it's not a dictionary
                if not isinstance(cite, dict):
                    continue

                # Get the citation text from either 'cite' or 'citation' field
                citation_text = cite.get("cite") or cite.get("citation")
                if not citation_text:
                    continue

                # Add to parallel citations with available metadata
                parallel_cites.append(
                    {
                        "citation": citation_text,
                        # Try to get reporter from various possible fields
                        "reporter": cite.get("reporter")
                        or cite.get("reporter_name", ""),
                        # Try to get category or type
                        "category": cite.get("category") or cite.get("type", ""),
                        # Include any additional metadata that might be useful
                        "url": cite.get("resource_uri") or cite.get("url", ""),
                    }
                )

        except Exception as e:
            logger.error(f"Error extracting parallel citations: {e}")

        return parallel_cites

    def _clean_citation_for_lookup(self, citation: str) -> str:
        """
        Clean and standardize a citation for the lookup API.

        Args:
            citation (str): The citation to clean

        Returns:
            str: Cleaned citation string
        """
        if not citation:
            return ""

        # Remove any surrounding quotes and extra whitespace
        clean = citation.strip("\"'").strip()

        # Handle common citation formats
        # 1. Standard format: 123 F.4th 456
        # 2. With comma: 123 F.4th 456, 789
        # 3. With 'at': 123 F.4th 456, at 789
        parts = []
        for part in clean.split():
            # Remove any non-alphanumeric characters except periods and hyphens
            part = "".join(c for c in part if c.isalnum() or c in ".-")
            if part and part.lower() not in [
                "at",
                "p.",
            ]:  # Skip common connecting words
                parts.append(part)

        # Rejoin with single spaces
        return " ".join(parts)

    def _lookup_citation(self, citation: str) -> dict:
        """
        Look up a citation using the CourtListener Citation Lookup API.

        Args:
            citation (str): The citation to look up

        Returns:
            dict: Result with case information if found, or None if not found

        The API endpoint expects a POST request to /api/rest/v4/citation-lookup/
        with the citation in the request body as form data with key 'text'.

        Authentication is done via the Authorization header with a token.
        """
        if not citation:
            logger.debug("No citation provided for lookup")
            return None

        try:
            # Clean and prepare the citation for the API
            clean_citation = self._clean_citation_for_lookup(citation)
            if not clean_citation:
                logger.warning(f"Could not clean citation for lookup: {citation}")
                return None

            # Set up headers with authentication
            headers = {
                "Authorization": (
                    f"Token {self.courtlistener_api_key}"
                    if self.courtlistener_api_key
                    else ""
                ),
                "Content-Type": "application/json",
            }

            # Remove empty headers
            headers = {k: v for k, v in headers.items() if v}

            # Ensure we have an API key
            if not self.courtlistener_api_key:
                error_msg = "No CourtListener API key provided. Please set COURTLISTENER_API_KEY in your environment."
                logger.error(error_msg)
                return {
                    "verified": False,
                    "citation": clean_citation,
                    "error": error_msg,
                    "source": "CourtListener API",
                }

            # Build the API URL
            base_url = "https://www.courtlistener.com/api/rest/v4"
            endpoint = f"{base_url}/citation-lookup/"

            logger.info(f"Looking up citation with CourtListener API: {clean_citation}")

            try:
                # Make the API request to the citation lookup endpoint using POST with JSON data
                response = requests.post(
                    endpoint,
                    json={"citation": clean_citation},  # Send as JSON
                    headers=headers,
                    timeout=15,  # 15 second timeout
                )

                # Log the response status and headers for debugging
                logger.debug(f"Lookup status: {response.status_code}")

                # Handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after + 1)
                    return self._lookup_citation(citation)  # Retry once

                # Handle other error status codes
                response.raise_for_status()

                # Parse the JSON response
                try:
                    data = response.json()
                    # Log the response data structure for debugging
                    logger.debug(
                        f"API Response: {json.dumps(data, indent=2)[:1000]}..."
                    )
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse JSON response: {str(e)}"
                    logger.error(f"{error_msg}. Response text: {response.text[:500]}")
                    return {
                        "verified": False,
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

                # Process the response based on the API version and structure
                if not data or not isinstance(data, dict):
                    error_msg = "Empty or invalid response from API"
                    logger.warning(f"{error_msg} for citation: {clean_citation}")
                    return {
                        "verified": False,
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

                # Process the response based on the structure
                result = self._process_courtlistener_result(clean_citation, data)

                if result and result.get("verified", False):
                    logger.info(
                        f"Successfully verified citation via lookup: {clean_citation}"
                    )
                    return result
                else:
                    error_msg = result.get(
                        "error", "Citation not found in CourtListener"
                    )
                    logger.info(
                        f"Citation not found via lookup: {clean_citation} - {error_msg}"
                    )
                    return {
                        "verified": False,
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

            except requests.exceptions.HTTPError as e:
                status_code = (
                    int(e.response.status_code)
                    if hasattr(e, "response") and e.response
                    else 0
                )
                error_msg = f"HTTP {status_code} error during citation lookup"

                if status_code == 400:
                    logger.warning(f"Bad request: {clean_citation} - {str(e)}")
                    error_msg = "Invalid citation format"
                elif status_code == 401:
                    error_msg = "Authentication failed. Please check your API key."
                    logger.error(error_msg)
                elif status_code == 403:
                    error_msg = "Access forbidden. Your API key may not have the required permissions."
                    logger.error(error_msg)
                elif status_code == 404:
                    error_msg = f"Citation not found: {clean_citation}"
                    logger.debug(error_msg)
                elif status_code >= 500:
                    error_msg = f"Server error during citation lookup: {status_code}"
                    logger.error(error_msg)
                else:
                    error_msg = f"HTTP {status_code} error: {str(e)}"

                # Log response details if available
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_body = e.response.json()
                        logger.debug(
                            f"Error response: {json.dumps(error_body, indent=2)}"
                        )
                        error_msg = error_body.get("detail", error_msg)
                    except:
                        error_text = e.response.text[:500]
                        logger.debug(f"Error response (non-JSON): {error_text}")
                        error_msg = f"{error_msg}: {error_text}"

                return {
                    "verified": False,
                    "citation": clean_citation,
                    "error": error_msg,
                    "source": "CourtListener API",
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")

        except Exception as e:
            logger.error(
                f"Unexpected error in citation lookup: {str(e)}", exc_info=True
            )

        return None

    def _verify_with_courtlistener(self, citation: str) -> dict:
        """
        Verify a citation using the CourtListener API v4.
        First tries the Citation Lookup API, then falls back to search.

        Args:
            citation (str): The citation to verify

        Returns:
            dict: Verification result with parallel citations if found.
                 Always contains 'verified' (bool), 'citation' (str), and 'source' (str) keys.
        """
        # First try the Citation Lookup API
        lookup_result = self._lookup_citation(citation)
        if lookup_result:
            processed = self._process_courtlistener_result(citation, lookup_result)
            if isinstance(processed, dict) and processed.get("verified", False):
                return processed

        # If lookup failed, try exact match search
        result = self._search_courtlistener_exact(citation)

        # If exact match failed, try flexible search
        if not result.get("verified", False):
            flexible_result = self._search_courtlistener_flexible(citation)
            if flexible_result.get("verified", False):
                return flexible_result

        return result

    def _search_courtlistener_exact(self, citation: str) -> dict:
        """Search for an exact citation match in CourtListener.

        Returns:
            dict: A dictionary with verification results, always containing 'verified' and 'citation' keys
        """
        result = {
            "verified": False,
            "citation": citation,
            "source": "CourtListener",
            "parallel_citations": [],
        }

        try:
            # Set up headers if not already set
            if not hasattr(self, "headers"):
                self.headers = {
                    "Authorization": (
                        f"Token {self.courtlistener_api_key}"
                        if self.courtlistener_api_key
                        else ""
                    ),
                    "Content-Type": "application/json",
                }

            # Set base URL if not already set
            if not hasattr(self, "courtlistener_base_url"):
                self.courtlistener_base_url = (
                    "https://www.courtlistener.com/api/rest/v4"
                )

            # Clean and prepare the citation for exact matching
            clean_citation = citation.strip("\"'").strip()

            # For v4 API, try an exact match with the full citation
            # First clean the citation - remove spaces and standardize format
            clean_citation = clean_citation.replace(" ", "").upper()

            # Build query parameters for exact match
            params = {
                "q": f"citation:({clean_citation})",  # No quotes around the citation
                "type": "o",  # Opinions only
                "order_by": "score desc",  # Best match first
                "filed_after": "1750-01-01",  # Include older cases
                "page_size": 1,  # We only need one match for exact search
            }

            # Make the API request to the search endpoint
            response = requests.get(
                f"{self.courtlistener_base_url}/search/",
                headers={
                    k: v for k, v in self.headers.items() if v
                },  # Remove empty headers
                params=params,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            if (
                isinstance(data, dict)
                and data.get("count", 0) > 0
                and isinstance(data.get("results"), list)
                and data["results"]
            ):
                processed_result = self._process_courtlistener_result(
                    citation, data["results"][0]
                )
                if isinstance(processed_result, dict):
                    return processed_result
                else:
                    result["error"] = "Invalid response format from CourtListener"
                    logger.error(
                        f"Unexpected response format from _process_courtlistener_result: {type(processed_result)}"
                    )
            else:
                result["warning"] = "No exact match found in CourtListener"

        except requests.exceptions.RequestException as e:
            error_msg = f"Request to CourtListener failed: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error in exact search: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg

        return result

    def _search_courtlistener_flexible(self, citation: str) -> dict:
        """
        Perform a more flexible search using citation components.

        Returns:
            dict: A dictionary with verification results, always containing 'verified' and 'citation' keys
        """
        result = {
            "verified": False,
            "citation": citation,
            "source": "CourtListener",
            "parallel_citations": [],
        }

        try:
            components = self._extract_citation_components(citation)
            if not components:
                result["error"] = "Could not extract citation components"
                return result

            # For v4 API, build a structured query using the components
            search_terms = []

            # Clean and prepare components
            if "volume" in components and components["volume"]:
                search_terms.append(f'citation.volume:{components["volume"]}')

            if "reporter" in components and components["reporter"]:
                # Clean reporter - remove periods and spaces, convert to uppercase
                reporter = (
                    components["reporter"].replace(".", "").replace(" ", "").upper()
                )
                if reporter:  # Only add if not empty after cleaning
                    search_terms.append(f"citation.reporter:{reporter}")

            if "page" in components and components["page"]:
                search_terms.append(f'citation.page:{components["page"]}')

            if not search_terms:
                result["error"] = "No valid search terms could be generated"
                return result

            # Join terms with space for OR logic (more flexible matching)
            search_query = " ".join(search_terms)

            # Set up parameters for v4 API
            params = {
                "q": search_query,
                "type": "o",  # Opinions only
                "order_by": "score desc",  # Best match first
                "filed_after": "1750-01-01",
                "page_size": 5,  # Get more results to find the best match
            }

            # Make the API request to the v4 search endpoint
            response = requests.get(
                f"{self.courtlistener_base_url}/search/",
                headers={
                    k: v for k, v in self.headers.items() if v
                },  # Remove empty headers
                params=params,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            if data.get("count", 0) > 0 and isinstance(data.get("results"), list):
                # Try to find the best match among results
                for result_item in data["results"]:
                    if self._is_best_match(citation, result_item, components):
                        processed = self._process_courtlistener_result(
                            citation, result_item
                        )
                        if isinstance(processed, dict):
                            return processed

                result["warning"] = (
                    "Matching results found but none matched all criteria"
                )
            else:
                result["warning"] = "No matching results found"

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error in flexible search: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error in flexible search: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg

        return result

    def _is_best_match(self, citation: str, result: dict, components: dict) -> bool:
        """Determine if a search result is the best match for the citation."""
        # Check if any of the citation fields match exactly
        if (
            "citation" in result
            and result["citation"]
            and citation.lower() in [c.lower() for c in result["citation"].split("; ")]
        ):
            return True

        # Check if the components match
        result_components = self._extract_citation_components(
            result.get("citation", "")
        )
        if not result_components:
            return False

        # Compare key components
        for key in ["volume", "reporter", "page"]:
            if components.get(key) and result_components.get(key):
                if str(components[key]).lower() != str(result_components[key]).lower():
                    return False

        return True

    def _process_courtlistener_result(
        self, original_citation: str, result: dict
    ) -> dict:
        """
        Process a successful CourtListener API result.

        Args:
            original_citation (str): The original citation that was searched for
            result (dict): The API response from CourtListener

        Returns:
            dict: Processed result with citation details and verification status
        """
        if not result or not isinstance(result, dict):
            return {
                "verified": False,
                "citation": original_citation,
                "error": "Invalid API response format",
                "source": "CourtListener API",
            }

        try:
            # Handle different response formats
            # 1. Direct citation lookup response
            if (
                "citations" in result
                and isinstance(result["citations"], list)
                and result["citations"]
            ):
                # Process the first citation in the list
                return self._process_citation_data(
                    original_citation, result["citations"][0]
                )

            # 2. Search result with 'results' array
            elif (
                "results" in result
                and isinstance(result["results"], list)
                and result["results"]
            ):
                # Process the first result
                return self._process_citation_data(
                    original_citation, result["results"][0]
                )

            # 3. Direct case data (from citation lookup v4)
            elif any(key in result for key in ["citation", "caseName", "resource_uri"]):
                return self._process_citation_data(original_citation, result)

            # If we get here, we couldn't process the response
            logger.warning(
                f"Unrecognized CourtListener API response format for {original_citation}"
            )
            return {
                "verified": False,
                "citation": original_citation,
                "error": "Unrecognized API response format",
                "source": "CourtListener API",
            }

        except Exception as e:
            error_msg = f"Error processing CourtListener result: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "verified": False,
                "citation": original_citation,
                "error": error_msg,
                "source": "CourtListener API",
            }

    def _process_citation_data(
        self, original_citation: str, citation_data: dict
    ) -> dict:
        """
        Process citation data from CourtListener API into a standardized format.

        Args:
            original_citation (str): The original citation that was searched for
            citation_data (dict): The citation data from the API

        Returns:
            dict: Standardized citation result
        """
        try:
            # Extract case information with fallbacks for different API versions
            case_name = (
                citation_data.get("caseName")
                or citation_data.get("name")
                or "Unknown Case"
            )
            docket_number = citation_data.get("docketNumber") or citation_data.get(
                "docket_number", ""
            )

            # Handle court information which might be a string or object
            court = ""
            court_data = citation_data.get("court") or {}
            if isinstance(court_data, dict):
                court = court_data.get("name") or court_data.get("full_name") or ""
            elif isinstance(court_data, str):
                court = court_data

            # Get the main citation, falling back to the original if not found
            citation = citation_data.get("citation") or original_citation

            # Extract parallel citations if available
            parallel_citations = []
            if "parallel_citations" in citation_data and isinstance(
                citation_data["parallel_citations"], list
            ):
                parallel_citations = citation_data["parallel_citations"]
            elif "citations" in citation_data and isinstance(
                citation_data["citations"], list
            ):
                parallel_citations = citation_data["citations"]

            # Get the URL, falling back to resource_uri or absolute_url
            url = citation_data.get("absolute_url") or citation_data.get(
                "resource_uri", ""
            )
            if url and not url.startswith(("http://", "https://")):
                url = f"https://www.courtlistener.com{url}"

            # Get the date, trying multiple possible fields
            date_filed = ""
            for date_field in [
                "date_filed",
                "decision_date",
                "date_modified",
                "date_created",
            ]:
                if date_field in citation_data and citation_data[date_field]:
                    date_filed = citation_data[date_field]
                    break

            # Format the result with all available metadata
            processed = {
                "verified": True,
                "citation": citation,
                "original_citation": original_citation,
                "case_name": case_name,
                "docket_number": docket_number,
                "court": court,
                "source": "CourtListener API",
                "url": url,
                "date_filed": date_filed,
                "parallel_citations": parallel_citations,
                "metadata": {
                    "api_version": "v4",
                    "result_type": citation_data.get("resource_type", "case"),
                    "id": str(citation_data.get("id", "")),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "jurisdiction": citation_data.get("jurisdiction", ""),
                    "reporter": citation_data.get("reporter", ""),
                    "volume": citation_data.get("volume", ""),
                    "page": citation_data.get("page", ""),
                },
            }

            # Add any additional fields that might be useful
            for field in [
                "precedential_status",
                "citation_count",
                "cite_count",
                "needs_case_date",
            ]:
                if field in citation_data:
                    processed["metadata"][field] = citation_data[field]

            logger.info(
                f"Successfully processed CourtListener result for {original_citation}"
            )
            return processed

        except Exception as e:
            logger.error(
                f"Error processing citation data for {original_citation}: {str(e)}",
                exc_info=True,
            )
            return {
                "verified": False,
                "citation": original_citation,
                "error": f"Error processing citation data: {str(e)}",
                "source": "CourtListener API",
            }

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

    def verify_citation(
        self,
        citation,
        use_cache=True,
        use_database=True,
        use_api=True,
        force_refresh=False,
    ):
        """
        Verify a citation using multiple sources with fallback strategies.

        Args:
            citation (str): The citation to verify
            use_cache (bool): Whether to check the cache first
            use_database (bool): Whether to check the database
            use_api (bool): Whether to use external APIs
            force_refresh (bool): If True, bypass cache and force a fresh verification

        Returns:
            dict: Verification result with source and confidence
        """
        if not citation or not isinstance(citation, str):
            return {
                "verified": False,
                "source": "None",
                "error": "No valid citation provided",
                "citation": "",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        try:
            # Clean and normalize the citation
            citation = citation.strip()
            if not citation:
                raise ValueError("Citation is empty after stripping whitespace")

            normalized = self._normalize_citation(citation)
            if not normalized:
                raise ValueError("Failed to normalize citation")

            # Track verification steps for debugging and transparency
            verification_steps = []
            cache_key = f"citation:{normalized}" if self.cache else None

            # 1. Check cache first if enabled and not forcing refresh
            if use_cache and self.cache and not force_refresh:
                try:
                    cached = self.cache.get(cache_key)
                    if cached is not None:
                        verification_steps.append({"step": "cache", "status": "hit"})
                        # Ensure cached result has all required fields
                        if not isinstance(cached, dict):
                            raise ValueError("Cached result is not a dictionary")
                        return {
                            **cached,
                            "cached": True,
                            "verification_steps": verification_steps,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                        }
                    verification_steps.append({"step": "cache", "status": "miss"})
                except Exception as e:
                    logger.warning(f"Cache lookup failed: {str(e)}")
                    verification_steps.append(
                        {"step": "cache", "status": "error", "error": str(e)}
                    )

            # 2. Check database if enabled and not forcing refresh
            db_result = None
            if use_database and not force_refresh:
                try:
                    db_result = self._verify_with_database(normalized)
                    if db_result and db_result.get("verified", False):
                        verification_steps.append(
                            {"step": "database", "status": "verified"}
                        )

                        # Update cache with database result
                        if self.cache:
                            result_to_cache = {
                                **db_result,
                                "verification_steps": verification_steps,
                                "cached": False,
                            }
                            self.cache.set(
                                cache_key, result_to_cache, timeout=86400
                            )  # 24 hours

                        return result_to_cache

                    verification_steps.append(
                        {"step": "database", "status": "not_found"}
                    )
                except Exception as e:
                    logger.error(
                        f"Database verification failed: {str(e)}", exc_info=True
                    )
                    verification_steps.append(
                        {"step": "database", "status": "error", "error": str(e)}
                    )

            # 3. Try external API if enabled
            api_result = None
            if use_api:
                try:
                    api_result = self._verify_with_api(normalized)
                    if api_result and api_result.get("verified", False):
                        verification_steps.append({"step": "api", "status": "verified"})

                        # Save to database for future use
                        if use_database:
                            try:
                                self._save_to_database(normalized, api_result)
                                verification_steps.append(
                                    {"step": "database_save", "status": "success"}
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to save to database: {str(e)}",
                                    exc_info=True,
                                )
                                verification_steps.append(
                                    {
                                        "step": "database_save",
                                        "status": "error",
                                        "error": str(e),
                                    }
                                )

                        # Update cache with API result
                        if self.cache:
                            result_to_cache = {
                                **api_result,
                                "verification_steps": verification_steps,
                                "cached": False,
                            }
                            self.cache.set(
                                cache_key, result_to_cache, timeout=86400
                            )  # 24 hours

                        return result_to_cache

                    verification_steps.append({"step": "api", "status": "not_found"})
                except Exception as e:
                    logger.error(f"API verification failed: {str(e)}", exc_info=True)
                    verification_steps.append(
                        {"step": "api", "status": "error", "error": str(e)}
                    )

            # 4. If we get here, no verification method succeeded
            result = {
                "verified": False,
                "source": "None",
                "error": "Citation could not be verified by any available source",
                "citation": citation,
                "normalized_citation": normalized,
                "verification_steps": verification_steps,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            # Cache negative result to avoid repeated lookups (shorter TTL for negative results)
            if self.cache:
                try:
                    self.cache.set(
                        cache_key, {**result, "cached": False}, timeout=3600
                    )  # 1 hour for negative results
                except Exception as e:
                    logger.warning(f"Failed to cache negative result: {str(e)}")

            return result

        except Exception as e:
            logger.error(
                f"Error in verify_citation for '{citation}': {str(e)}", exc_info=True
            )
            return {
                "verified": False,
                "source": "None",
                "error": f"Error verifying citation: {str(e)}",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

    def _check_database(self, citation):
        """
        Check if the citation exists in the database using multiple matching strategies.

        Args:
            citation (str): The citation to look up

        Returns:
            dict: A dictionary containing the verification result and any matching data
        """
        if not citation or not isinstance(citation, str):
            return {
                "verified": False,
                "source": "Database",
                "error": "No valid citation provided",
                "citation": "",
            }

        conn = None
        try:
            # Clean and normalize the citation
            normalized_citation = self._normalize_citation(citation)

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Strategy 1: Exact match with original citation
            cursor.execute(
                """
                SELECT * FROM citations 
                WHERE citation_text = ? 
                LIMIT 1
            """,
                (citation,),
            )

            match = cursor.fetchone()
            if match:
                result = self._format_database_match(match, "exact", citation)
                if result.get("verified", False):
                    return result

            # Strategy 2: Try normalized citation if different
            if normalized_citation != citation:
                cursor.execute(
                    """
                    SELECT * FROM citations 
                    WHERE citation_text = ? 
                    LIMIT 1
                """,
                    (normalized_citation,),
                )

                match = cursor.fetchone()
                if match:
                    result = self._format_database_match(
                        match,
                        "normalized",
                        citation,
                        "citation_text",
                        normalized_citation,
                    )
                    if result.get("verified", False):
                        return result

            # Strategy 3: Extract components and search by volume/reporter/page
            components = self._extract_citation_components(normalized_citation)
            if all(k in components for k in ["volume", "reporter", "page"]):
                cursor.execute(
                    """
                    SELECT * FROM citations 
                    WHERE citation_text LIKE ? 
                    AND citation_text LIKE ?
                    AND citation_text LIKE ?
                    LIMIT 1
                """,
                    (
                        f"%{components['volume']}%",
                        f"%{components['reporter']}%",
                        f"%{components['page']}%",
                    ),
                )

                match = cursor.fetchone()
                if match:
                    return self._format_database_match(
                        match,
                        "components",
                        citation,
                        "volume/reporter/page",
                        f"{components['volume']} {components['reporter']} {components['page']}",
                    )

            # Strategy 4: Try case-insensitive search as last resort
            cursor.execute(
                """
                SELECT * FROM citations 
                WHERE LOWER(citation_text) = LOWER(?) 
                LIMIT 1
            """,
                (citation,),
            )

            match = cursor.fetchone()
            if match:
                return self._format_database_match(match, "case_insensitive", citation)

            # If we get here, no match was found
            logger.debug(f"No database match found for citation: {citation}")
            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database",
                "citation": citation,
                "components": components,
            }

            # Strategy 1: Exact match with original citation
            cursor.execute(
                f"SELECT * FROM citations WHERE {citation_col} = ? LIMIT 1", (citation,)
            )
            exact_match = cursor.fetchone()
            if exact_match:
                return self._format_database_match(
                    exact_match, columns, "exact", citation
                )

            # Strategy 2: Normalized citation match
            normalized = self._normalize_citation(citation)
            if normalized != citation:
                cursor.execute(
                    f"SELECT * FROM citations WHERE {citation_col} = ? LIMIT 1",
                    (normalized,),
                )
                normalized_match = cursor.fetchone()
                if normalized_match:
                    return self._format_database_match(
                        normalized_match,
                        columns,
                        "normalized",
                        citation,
                        citation_col,
                        normalized,
                    )

            # Strategy 3: Extract components and search by volume/reporter/page
            components = self._extract_citation_components(citation)
            if all(k in components for k in ["volume", "reporter", "page"]):
                query = f"""
                    SELECT * FROM citations 
                    WHERE {citation_col} LIKE ? 
                    AND {citation_col} LIKE ?
                    AND {citation_col} LIKE ?
                    LIMIT 1
                """
                cursor.execute(
                    query,
                    (
                        f"%{components['volume']}%",
                        f"%{components['reporter']}%",
                        f"%{components['page']}%",
                    ),
                )
                component_match = cursor.fetchone()
                if component_match:
                    return self._format_database_match(
                        component_match, columns, "components", citation
                    )

            # Strategy 4: Fuzzy match with LIKE and wildcards
            search_terms = [citation, normalized]
            if components.get("reporter"):
                search_terms.append(
                    f"{components.get('volume', '')} {components['reporter']} {components.get('page', '')}"
                )

            for term in set(search_terms):
                if not term:
                    continue

                cursor.execute(
                    f"""
                    SELECT * FROM citations 
                    WHERE {citation_col} LIKE ? 
                    LIMIT 1
                """,
                    (f"%{term}%",),
                )

                fuzzy_match = cursor.fetchone()
                if fuzzy_match:
                    return self._format_database_match(
                        fuzzy_match, columns, "fuzzy", citation, citation_col, term
                    )

            # If we get here, no match was found
            logger.info(f"No database match found for citation: {citation}")
            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database",
                "citation": citation,
                "components": components,
            }

        except sqlite3.Error as e:
            logger.error(f"Database error when checking citation '{citation}': {e}")
            return {
                "verified": False,
                "source": "Database",
                "error": f"Database error: {str(e)}",
                "citation": citation,
            }

        finally:
            if conn:
                conn.close()

    def _format_database_match(
        self,
        match,
        match_type,
        original_citation,
        matched_column=None,
        matched_value=None,
    ):
        """
        Format a database match into a standardized result dictionary.

        Args:
            match: The database row (as a dict-like object or dictionary)
            match_type: Type of match (e.g., 'exact', 'normalized', 'components')
            original_citation: The original citation that was searched for
            matched_column: The column or criteria that produced the match
            matched_value: The value that was matched against

        Returns:
            dict: A standardized result dictionary with the match details
        """
        try:
            # Convert SQLite Row to dictionary if needed
            if hasattr(match, "keys"):
                match_dict = dict(match)
            else:
                match_dict = match or {}

            # Safely get the citation value
            citation_value = match_dict.get("citation_text", "")

            # Build the result dictionary
            result = {
                "verified": True,
                "source": "Database",
                "match_type": match_type,
                "citation": citation_value,
                "original_citation": original_citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            # Add match details if provided
            if matched_column is not None:
                result["matched_column"] = matched_column
            if matched_value is not None:
                result["matched_value"] = matched_value

            # Add all columns from the database to the result
            if hasattr(match, "keys"):
                for key in match.keys():
                    if (
                        key != "id" and key not in result
                    ):  # Skip id and any already set fields
                        result[key] = match[key]
            elif isinstance(match_dict, dict):
                for key, value in match_dict.items():
                    if (
                        key != "id" and key not in result
                    ):  # Skip id and any already set fields
                        result[key] = value

            # Add parallel citations if available
            if "id" in match_dict:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(
                        """
                        SELECT citation, reporter, category 
                        FROM parallel_citations 
                        WHERE citation_id = ?
                    """,
                        (match_dict["id"],),
                    )

                    parallel_cites = []
                    for row in cursor.fetchall():
                        parallel_cites.append(
                            {"citation": row[0], "reporter": row[1], "category": row[2]}
                        )

                    if parallel_cites:
                        result["parallel_citations"] = parallel_cites
                except Exception as e:
                    logger.warning(f"Error fetching parallel citations: {e}")

            logger.info(
                f"Database match found (type: {match_type}) for citation: {original_citation} -> "
                f"{citation_value} (matched on: {matched_column or 'N/A'})"
            )
            return result

        except Exception as e:
            logger.error(f"Error formatting database match: {e}")
            return {
                "verified": False,
                "source": "Database",
                "error": f"Error processing database match: {str(e)}",
                "original_citation": original_citation,
                "match_type": match_type,
            }

    def _verify_with_database(self, citation):
        """
        Try to verify the citation using the database with multiple strategies.

        Args:
            citation (str): The citation to verify

        Returns:
            dict: Verification result with source 'Database' if found, None otherwise
        """
        if not citation or not isinstance(citation, str):
            logger.debug("Invalid citation provided to _verify_with_database")
            return {
                "verified": False,
                "source": "Database",
                "error": "Invalid citation format",
                "citation": citation,
            }

        try:
            # First try with the exact citation
            result = self._check_database(citation)

            # If we have a verified result, return it
            if result and result.get("verified", False):
                return result

            # If we have an error (not just not found), log it
            if (
                "error" in result
                and "not found" not in str(result.get("error", "")).lower()
            ):
                logger.warning(
                    f"Database lookup error for citation '{citation}': {result.get('error')}"
                )

            # If we got here, no match was found
            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error in _verify_with_database for citation '{citation}': {str(e)}",
                exc_info=True,
            )
            return {
                "verified": False,
                "source": "Database",
                "error": f"Error verifying citation: {str(e)}",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        finally:
            try:
                if "conn" in locals():
                    conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")

    # Landmark cases functionality has been removed as it's no longer maintained

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

    def _get_parallel_citations_from_db(self, citation_id):
        """Retrieve parallel citations from the database for a given citation ID."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Set row_factory to sqlite3.Row to access columns by name
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT citation, reporter, category 
                FROM parallel_citations 
                WHERE citation_id = ?
                """,
                (citation_id,),
            )

            # Convert Row objects to dictionaries before returning
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error fetching parallel citations: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def verify_citation(self, citation):
        """
        Verify a citation using multiple sources and techniques.
        Returns a comprehensive verification result with parallel citations.

        This method tries multiple strategies to verify a citation:
        1. Check cache for exact match
        2. Check database for exact match
        3. Try normalized version of the citation
        4. Extract components and search by volume/reporter/page
        5. Try CourtListener API if available
        6. Fall back to fuzzy matching

        Args:
            citation (str): The citation to verify

        Returns:
            dict: Verification result with parallel citations if available.
                 Always contains 'verified' (bool), 'citation' (str), and 'error' (str) keys.
        """

        def create_default_result(cite):
            """Create a result dictionary with all required fields."""
            return {
                "citation": cite,
                "verified": False,
                "sources": {},
                "verified_by": None,
                "confidence": 0.0,
                "case_name": "",
                "date_filed": "",
                "docket_number": "",
                "court": "",
                "url": "",
                "context": "",
                "parallel_citations": [],
                "error": "",
                "warning": "",
                "verification_steps": [],
                "metadata": {},
            }

        def ensure_dict_result(result, citation):
            """Ensure the result is a dictionary with all required fields."""
            if isinstance(result, tuple):
                # Handle tuple return type (status, message)
                status, message = result
                result = create_default_result(citation)
                result["verified"] = status
                result["error"] = message if not status else ""
                return result
            elif not isinstance(result, dict):
                return create_default_result(str(citation) if citation else "")

            # Ensure all required fields exist
            default = create_default_result(result.get("citation", citation))
            for key in default:
                if key not in result:
                    result[key] = default[key]
            return result

        # Input validation and initialization
        if not citation or not str(citation).strip():
            return ensure_dict_result((False, "No citation provided"), "")

        original_citation = str(citation).strip()
        normalized_citation = self._normalize_citation(original_citation)
        result = create_default_result(normalized_citation)

        # Track verification steps for debugging
        def add_verification_step(method, success, message=""):
            result["verification_steps"].append(
                {
                    "method": method,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            )

        # Try cache first
        try:
            cached_result = self._check_cache(normalized_citation)
            if cached_result:
                add_verification_step("cache", True, "Found in cache")
                return ensure_dict_result(cached_result, normalized_citation)
            add_verification_step("cache", False, "Not found in cache")
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            add_verification_step("cache", False, f"Cache error: {str(e)}")

        # Try database lookup with multiple strategies
        db_verified = False
        try:
            # Try exact match first
            db_result = self._check_database(normalized_citation)
            if db_result and db_result.get("verified"):
                add_verification_step(
                    "database_exact", True, "Found exact match in database"
                )
                return ensure_dict_result(db_result, normalized_citation)

            # Try with components if available
            components = self._extract_citation_components(normalized_citation)
            if (
                components.get("volume")
                and components.get("reporter")
                and components.get("page")
            ):
                component_query = f"{components['volume']} {components['reporter']} {components['page']}"
                if component_query != normalized_citation:
                    db_result = self._check_database(component_query)
                    if db_result and db_result.get("verified"):
                        add_verification_step(
                            "database_components", True, "Found match using components"
                        )
                        return ensure_dict_result(db_result, normalized_citation)

            # If we get here, database lookup was unsuccessful but that's expected
            add_verification_step(
                "database",
                False,
                "Citation not found in database - trying other sources",
            )
            db_verified = False

        except Exception as e:
            logger.warning(f"Database lookup failed: {str(e)}")
            add_verification_step(
                "database", False, f"Database error: {str(e)} - trying other sources"
            )
            db_verified = False

        # Try CourtListener API if available
        if self.courtlistener_api_key:
            try:
                logger.debug(
                    f"Attempting to verify with CourtListener API: {normalized_citation}"
                )
                cl_result = self._verify_with_courtlistener(normalized_citation)

                if cl_result and cl_result.get("verified", False):
                    add_verification_step(
                        "courtlistener", True, "Verified with CourtListener"
                    )
                    # Cache the result for future use
                    logger.debug(
                        f"Caching CourtListener result for: {normalized_citation}"
                    )
                    self._save_to_cache(normalized_citation, cl_result)
                    self._save_to_database(
                        normalized_citation, cl_result
                    )  # Save to database for future use
                    return ensure_dict_result(cl_result, normalized_citation)
                else:
                    error_msg = (
                        cl_result.get("error", "Citation not found")
                        if cl_result
                        else "No result from CourtListener"
                    )
                    logger.debug(
                        f"CourtListener verification did not find citation: {normalized_citation}"
                    )
                    add_verification_step(
                        "courtlistener", False, f"Citation not found in CourtListener"
                    )
            except requests.exceptions.RequestException as e:
                logger.warning(f"CourtListener API request failed: {str(e)}")
                add_verification_step("courtlistener", False, f"API request failed")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse CourtListener API response: {str(e)}")
                add_verification_step(
                    "courtlistener", False, "Invalid API response format"
                )
            except Exception as e:
                logger.warning(
                    f"Unexpected error in CourtListener verification: {str(e)}",
                    exc_info=True,
                )
                add_verification_step("courtlistener", False, f"Verification error")

        # Try LangSearch API if available
        if self.langsearch_api_key:
            try:
                logger.debug(
                    f"Attempting to verify with LangSearch API: {normalized_citation}"
                )
                ls_result = self._verify_with_langsearch(normalized_citation)

                if ls_result and ls_result.get("verified", False):
                    add_verification_step(
                        "langsearch", True, "Verified with LangSearch"
                    )
                    # Cache the result for future use
                    logger.debug(
                        f"Caching LangSearch result for: {normalized_citation}"
                    )
                    self._save_to_cache(normalized_citation, ls_result)
                    self._save_to_database(
                        normalized_citation, ls_result
                    )  # Save to database for future use
                    return ensure_dict_result(ls_result, normalized_citation)
                else:
                    error_msg = (
                        ls_result.get("error", "Citation not found")
                        if ls_result
                        else "No result from LangSearch"
                    )
                    logger.debug(
                        f"LangSearch verification did not find citation: {normalized_citation}"
                    )
                    add_verification_step("langsearch", False, f"{error_msg}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"LangSearch API request failed: {str(e)}")
                add_verification_step("langsearch", False, "API request failed")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LangSearch API response: {str(e)}")
                add_verification_step(
                    "langsearch", False, "Invalid API response format"
                )
            except Exception as e:
                logger.warning(
                    f"Unexpected error in LangSearch verification: {str(e)}",
                    exc_info=True,
                )
                add_verification_step("langsearch", False, f"Verification error")

        # Try fuzzy matching as last resort
        try:
            fuzzy_result = self._verify_with_fuzzy_matching(normalized_citation)
            if fuzzy_result and fuzzy_result.get("verified"):
                add_verification_step("fuzzy", True, "Found fuzzy match")
                return ensure_dict_result(fuzzy_result, normalized_citation)
            else:
                add_verification_step("fuzzy", False, "No fuzzy match found")
        except Exception as e:
            logger.warning(f"Fuzzy matching failed: {str(e)}")
            add_verification_step("fuzzy", False, f"Fuzzy matching error")

        # Add any metadata we have from the citation
        if "metadata" not in result:
            result["metadata"] = {}

        # Add case name if available from components
        components = self._extract_citation_components(normalized_citation)
        if components and components.get("case_name"):
            result["metadata"]["case_name"] = components["case_name"]

        # Add timestamp
        result["timestamp"] = datetime.datetime.utcnow().isoformat()

        # Save to cache and database if verified
        if result.get("verified", False):
            try:
                self._save_to_cache(normalized_citation, result)
                self._save_to_database(normalized_citation, result)
            except Exception as e:
                logger.error(f"[verify_citation] Error saving verification result: {e}")

        return ensure_dict_result(result)

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


def main():
    """Example usage of the EnhancedMultiSourceVerifier."""
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
        try:
            result = verifier.verify_citation(citation)
            print(f"\nCitation: {citation}")
            print(f"Verified: {result.get('verified', False)}")
            if result.get("verified"):
                print(f"Case: {result.get('case_name', 'N/A')}")
                print(f"Court: {result.get('court', 'N/A')}")
                print(f"Date: {result.get('date_filed', 'N/A')}")
                if result.get("parallel_citations"):
                    print("Parallel Citations:")
                    for pc in result["parallel_citations"]:
                        print(f"- {pc.get('citation', 'N/A')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error processing citation {citation}: {str(e)}")


if __name__ == "__main__":
    main()
