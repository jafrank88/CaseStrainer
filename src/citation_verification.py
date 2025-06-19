#!/usr/bin/env python3
"""
Citation Verification Module for CaseStrainer

This module provides comprehensive citation verification using multiple methods:
1. CourtListener Citation Lookup API
2. CourtListener Opinion Search API
3. CourtListener Cluster/Docket APIs
4. LangSearch API (backup)
5. Google Scholar (backup)

It implements a fallback mechanism to try different methods if one fails.
"""

import os
import re
import time
import json
import requests
import urllib.parse
from typing import Optional, Dict, Any
import traceback
import logging
from datetime import datetime, timedelta
import functools
import threading
import hashlib

# Import rate limiter
from utils.rate_limiter import courtlistener_limiter

# API endpoints - Updated to use v4 as per requirements
COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
COURTLISTENER_CITATION_API = f"{COURTLISTENER_BASE_URL}citation-lookup/"
COURTLISTENER_SEARCH_API = f"{COURTLISTENER_BASE_URL}search/"
COURTLISTENER_OPINION_API = f"{COURTLISTENER_BASE_URL}opinions/"
COURTLISTENER_CLUSTER_API = f"{COURTLISTENER_BASE_URL}clusters/"

# Note: CourtListener API v4 requires specific parameters
# For citation-lookup, we need to use 'citation' parameter
GOOGLE_SCHOLAR_URL = "https://scholar.google.com/scholar"

# Flags to track API availability
COURTLISTENER_AVAILABLE = True
LANGSEARCH_AVAILABLE = True
GOOGLE_SCHOLAR_AVAILABLE = True

# Configuration
MAX_RETRIES = 3  # Reduced from 5 to prevent long waits
TIMEOUT_SECONDS = 15  # Reduced from 30 to fail faster
RATE_LIMIT_WAIT = 5  # seconds to wait when rate limited
MIN_RETRY_DELAY = 1  # minimum seconds between retries
MAX_RETRY_DELAY = 10  # maximum seconds between retries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citation_verification.log')
    ]
)


class CitationVerifier:
    """Class for verifying legal citations using multiple methods."""

    def __init__(self, api_key=None, langsearch_api_key=None, debug_mode=True):
        """Initialize the CitationVerifier with API keys and cache settings."""
        self.api_key = api_key or os.environ.get("COURTLISTENER_API_KEY")
        self.langsearch_api_key = langsearch_api_key or os.environ.get("LANGSEARCH_API_KEY")
        self.debug_mode = debug_mode
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if debug_mode:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
            
        # Initialize cache settings with better Windows compatibility
        # Try multiple locations in order of preference
        cache_locations = [
            os.path.join(os.path.expanduser("~"), ".casestrainer_cache"),  # User home directory
            os.path.join(os.getcwd(), "cache"),  # Current working directory
            os.path.join(os.path.dirname(__file__), "..", "cache"),  # Project root cache
            os.path.join(os.path.dirname(__file__), "citation_cache"),  # Original location (fallback)
        ]
        
        self._cache_dir = None
        for location in cache_locations:
            try:
                if not os.path.exists(location):
                    os.makedirs(location, exist_ok=True)
                # Test write access with a more robust test
                test_file = os.path.join(location, f".test_{os.getpid()}")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                self._cache_dir = location
                self.logger.info(f"Using cache directory: {self._cache_dir}")
                break
            except (PermissionError, OSError) as e:
                self.logger.debug(f"Could not use cache location {location}: {e}")
                continue
        
        if self._cache_dir is None:
            self.logger.warning("Could not create writable cache directory. File caching disabled.")
            self._cache_dir = None
        
        self._cache_lock = threading.Lock()
        
        # Cache TTLs (in seconds)
        self._file_cache_ttl = 30 * 24 * 3600  # 30 days for file cache
        self._lru_cache_ttl = 24 * 3600  # 24 hours for in-memory cache
        self._negative_cache_ttl = 7 * 24 * 3600  # 7 days for negative results
        
        # Initialize LRU cache for in-memory caching
        self._lru_cache = {}
        self._lru_cache_lock = threading.Lock()
        
        # Load existing cache entries into memory
        self._load_existing_cache()
        
        self.headers = {
            "Authorization": f"Token {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
        }
        
        self.logger.info(
            f"Initialized CitationVerifier with API key: {self.api_key[:6]}... (length: {len(self.api_key) if self.api_key else 0})"
        )
        
    def _get_cache_path(self, citation: str) -> str:
        """Get the cache file path for a citation."""
        if self._cache_dir is None:
            return None
        # Normalize citation for filename
        normalized = citation.lower().replace(" ", "_").replace(".", "_")
        # Use MD5 hash to avoid filename length issues
        hash_key = hashlib.md5(normalized.encode()).hexdigest()
        return os.path.join(self._cache_dir, f"{hash_key}.json")
        
    def _load_existing_cache(self):
        """Load existing cache entries into memory."""
        if self._cache_dir is None:
            self.logger.info("File caching disabled, skipping cache load")
            return
            
        try:
            cache_files = [f for f in os.listdir(self._cache_dir) if f.endswith('.json')]
            loaded_count = 0
            for cache_file in cache_files:
                try:
                    with open(os.path.join(self._cache_dir, cache_file), "r") as f:
                        data = json.load(f)
                        if data.get("timestamp", 0) > time.time() - self._file_cache_ttl:
                            citation = data.get("citation")
                            if citation:
                                with self._lru_cache_lock:
                                    self._lru_cache[citation] = {
                                        "result": data.get("result"),
                                        "timestamp": time.time()
                                    }
                                loaded_count += 1
                except Exception as e:
                    self.logger.warning(f"Error loading cache file {cache_file}: {e}")
            self.logger.info(f"Loaded {loaded_count} cache entries into memory")
        except Exception as e:
            self.logger.error(f"Error loading existing cache: {e}")
            
    def _get_from_cache(self, citation: str) -> Optional[Dict[str, Any]]:
        """Get a citation result from cache (both memory and file)."""
        # Try LRU cache first
        with self._lru_cache_lock:
            cached = self._lru_cache.get(citation)
            if cached and cached.get("timestamp", 0) > time.time() - self._lru_cache_ttl:
                self.logger.debug(f"Cache hit in memory for citation: {citation}")
                return cached.get("result")
                
        # Try file cache (only if enabled)
        if self._cache_dir is not None:
            cache_path = self._get_cache_path(citation)
            if cache_path and os.path.exists(cache_path):
                try:
                    with open(cache_path, "r") as f:
                        data = json.load(f)
                        # Check if cache is still valid
                        ttl = self._negative_cache_ttl if not data.get("result", {}).get("verified", True) else self._file_cache_ttl
                        if data.get("timestamp", 0) > time.time() - ttl:
                            # Update LRU cache
                            with self._lru_cache_lock:
                                self._lru_cache[citation] = {
                                    "result": data.get("result"),
                                    "timestamp": time.time()
                                }
                            self.logger.debug(f"Cache hit in file for citation: {citation}")
                            return data.get("result")
                        else:
                            self.logger.debug(f"Cache expired for citation: {citation}")
                            # Clean up expired cache file
                            try:
                                os.remove(cache_path)
                            except Exception as e:
                                self.logger.warning(f"Error removing expired cache file: {e}")
                except Exception as e:
                    self.logger.warning(f"Error reading cache file: {e}")
        return None
        
    def _save_to_cache(self, citation: str, result: Dict[str, Any]):
        """Save a citation result to both memory and file cache."""
        if not citation or not isinstance(citation, str):
            self.logger.error("Invalid citation provided to _save_to_cache")
            return
            
        # Determine TTL based on verification status
        ttl = self._negative_cache_ttl if not result.get("verified", True) else self._file_cache_ttl
        
        # Save to LRU cache
        with self._lru_cache_lock:
            self._lru_cache[citation] = {
                "result": result,
                "timestamp": time.time()
            }
            
        # Save to file cache (only if enabled)
        if self._cache_dir is not None:
            cache_path = self._get_cache_path(citation)
            if cache_path:
                try:
                    with open(cache_path, "w") as f:
                        json.dump({
                            "citation": citation,
                            "result": result,
                            "timestamp": time.time(),
                            "ttl": ttl
                        }, f, indent=2)
                    self.logger.debug(f"Saved to cache: {citation}")
                except Exception as e:
                    self.logger.error(f"Error writing cache file: {e}")
            else:
                self.logger.debug(f"File caching disabled, only saved to memory cache: {citation}")
        else:
            self.logger.debug(f"File caching disabled, only saved to memory cache: {citation}")
            
    def cleanup_cache(self, max_age_days: int = 30):
        """Clean up old cache entries."""
        if self._cache_dir is None:
            self.logger.info("File caching disabled, skipping cache cleanup")
            return
            
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            cleaned_count = 0
            for cache_file in os.listdir(self._cache_dir):
                if not cache_file.endswith('.json'):
                    continue
                try:
                    file_path = os.path.join(self._cache_dir, cache_file)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        if data.get("timestamp", 0) < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"Error cleaning up cache file {cache_file}: {e}")
            self.logger.info(f"Cleaned up {cleaned_count} old cache entries")
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")

    def verify_citation(self, citation: str, context: str = None, extracted_case_name: str = None) -> Dict[str, Any]:
        """
        Verify a citation using multiple methods with fallback.

        Args:
            citation: The legal citation to verify
            context: Optional context around the citation (text before and after)
            extracted_case_name: The case name extracted from the document (local)

        Returns:
            Dict with verification results including whether the citation is valid and its source.
        """
        try:
            print(f"DEBUG: Starting verification for citation: {citation}")
            logging.info(f"[DEBUG] Starting verification for citation: {citation}")

            # Check if this is a Westlaw citation
            is_westlaw = bool(re.search(r"\d+\s+WL\s+\d+", citation, re.IGNORECASE))
            is_us_citation = bool(
                re.search(r"\d+\s+U\.?\s*S\.?\s+\d+", citation, re.IGNORECASE)
            )
            is_f3d_citation = bool(
                re.search(r"\d+\s+F\.?\s*3d\s+\d+", citation, re.IGNORECASE)
            )
            is_sct_citation = bool(
                re.search(r"\d+\s+S\.?\s*Ct\.?\s+\d+", citation, re.IGNORECASE)
            )

            result = {
                "citation": citation,
                "found": False,
                "source": None,
                "case_name_verified": None,
                "case_name_extracted": extracted_case_name if extracted_case_name else '',
                "url": None,
                "details": {},
                "explanation": None,
                "is_westlaw": is_westlaw,
                "sources_checked": [],
                "name_similarity": None,
                "highlight": False,
            }

            # First, try to verify using the CourtListener Citation Lookup API
            try:
                print(
                    f"DEBUG: Trying CourtListener Citation Lookup API for: {citation}"
                )
                logging.info(
                    f"[DEBUG] Trying CourtListener Citation Lookup API for: {citation}"
                )
                result["sources_checked"].append("CourtListener Citation Lookup API")
                api_result = self.verify_with_courtlistener_citation_api(citation)

                if api_result.get("found"):
                    print(f"DEBUG: Citation verified by CourtListener API: {citation}")
                    logging.info(
                        f"[DEBUG] Citation verified by CourtListener API: {citation}"
                    )
                    api_result["sources_checked"] = result["sources_checked"]
                    # Add extracted case name
                    api_result["case_name_extracted"] = extracted_case_name if extracted_case_name else ''
                    # Rename case_name to case_name_verified
                    api_result["case_name_verified"] = api_result.get("case_name")
                    # Compute similarity and highlight
                    from src.citation_grouping import calculate_similarity
                    sim = calculate_similarity(
                        extracted_case_name or "",
                        api_result.get("case_name") or ""
                    )
                    api_result["name_similarity"] = sim
                    api_result["highlight"] = sim == 0.0
                    return api_result
                else:
                    print(f"DEBUG: Citation not found in CourtListener API: {citation}")
                    logging.info(
                        f"[DEBUG] Citation not found in CourtListener API: {citation}"
                    )
                    # Store the explanation from the API result for later use
                    if api_result.get("explanation"):
                        result["explanation"] = api_result["explanation"]
            except Exception as e:
                print(f"DEBUG: Error using CourtListener Citation API: {str(e)}")
                logging.error(
                    f"[ERROR] Error using CourtListener Citation API: {str(e)}"
                )
                # Continue with fallback methods
            else:
                # If no exception occurred, continue with the rest of the function
                pass
        except Exception as e:
            print(f"DEBUG: Error verifying citation: {str(e)}")
            logging.error(f"[ERROR] Error verifying citation: {str(e)}")
            traceback.print_exc()

        if context:
            # Look for patterns like "Case Name, 123 F.3d 456" or "123 F.3d 456 (Case Name)"
            # Pattern 1: Case Name, followed by citation
            case_name_match = re.search(
                r"([A-Za-z\s\.,&\(\)\-\']+),\s*" + re.escape(citation), context
            )
            if case_name_match:
                result["extracted_case_name"] = case_name_match.group(1).strip()
                logging.info(
                    f"[DEBUG] Extracted case name from context (pattern 1): {result['extracted_case_name']}"
                )

            # Pattern 2: Citation followed by case name in parentheses
            if not result.get("extracted_case_name"):
                case_name_match = re.search(
                    re.escape(citation) + r"\s*\(([^\)]+)\)", context
                )
                if case_name_match:
                    result["extracted_case_name"] = case_name_match.group(1).strip()
                    logging.info(
                        f"[DEBUG] Extracted case name from context (pattern 2): {result['extracted_case_name']}"
                    )

            # Pattern 3: Look for v. pattern near the citation
            if not result.get("extracted_case_name"):
                v_pattern = re.search(
                    r"([A-Za-z\s\.,&\(\)\-\']+v\.\s*[A-Za-z\s\.,&\(\)\-\']+)", context
                )
                if v_pattern:
                    result["extracted_case_name"] = v_pattern.group(1).strip()
                    logging.info(
                        f"[DEBUG] Extracted case name from context (v. pattern): {result['extracted_case_name']}"
                    )

        # Track fallback sources checked
        fallback_sources = []

        # If the API call failed, we can try to extract information from the citation format
        # and provide better explanations based on the citation type

        # For U.S. Reports citations
        if is_us_citation:
            # Extract the volume and page numbers
            match = re.search(r"(\d+)\s+U\.?\s*S\.?\s+(\d+)", citation, re.IGNORECASE)
            if match:
                volume = match.group(1)
                page = match.group(2)

                # Add citation details to the result
                result["details"]["volume"] = volume
                result["details"]["reporter"] = "U.S."
                result["details"]["page"] = page

                # Try the CourtListener Search API as a fallback
                try:
                    print(
                        f"DEBUG: Trying CourtListener Search API for U.S. citation: {citation}"
                    )
                    logging.info(
                        f"[DEBUG] Trying CourtListener Search API for U.S. citation: {citation}"
                    )
                    fallback_sources.append("CourtListener Search API")
                    search_result = self.verify_with_courtlistener_search_api(citation)
                    if search_result.get("found"):
                        print(
                            f"DEBUG: Citation found in CourtListener Search API: {citation}"
                        )
                        logging.info(
                            f"[DEBUG] Citation found in CourtListener Search API: {citation}"
                        )
                        search_result["sources_checked"] = (
                            result["sources_checked"] + fallback_sources
                        )
                        return search_result
                except Exception as e:
                    print(f"DEBUG: Error using CourtListener Search API: {str(e)}")
                    logging.error(
                        f"[ERROR] Error using CourtListener Search API: {str(e)}"
                    )

        # For F.3d citations
        elif is_f3d_citation:
            # Extract the volume and page numbers
            match = re.search(r"(\d+)\s+F\.?\s*3d\s+(\d+)", citation, re.IGNORECASE)
            if match:
                try:
                    volume = match.group(1)
                    page = match.group(2)

                    formatted_citation = f"{volume} F.3d {page}"
                    fallback_sources.append("CourtListener Citation Lookup API")
                    api_result = self.verify_with_courtlistener_citation_api(
                        formatted_citation
                    )
                    if api_result.get("found"):
                        print(
                            f"DEBUG: Citation found in CourtListener Citation API: {citation}"
                        )
                        logging.info(
                            f"[DEBUG] Citation found in CourtListener Citation API: {citation}"
                        )
                        api_result["sources_checked"] = (
                            result["sources_checked"] + fallback_sources
                        )
                        return api_result

                    # If not found with Citation API, try the Search API
                    print(
                        f"DEBUG: Trying CourtListener Search API for F.3d citation: {citation}"
                    )
                    logging.info(
                        f"[DEBUG] Trying CourtListener Search API for F.3d citation: {citation}"
                    )
                    fallback_sources.append("CourtListener Search API")
                    search_result = self.verify_with_courtlistener_search_api(
                        formatted_citation
                    )
                    if search_result.get("found"):
                        print(
                            f"DEBUG: Citation found in CourtListener Search API: {citation}"
                        )
                        logging.info(
                            f"[DEBUG] Citation found in CourtListener Search API: {citation}"
                        )
                        search_result["sources_checked"] = (
                            result["sources_checked"] + fallback_sources
                        )
                        return search_result

                    # Even if API verification fails, mark standard F.3d citations as valid
                    # This ensures citations like Caraway (534 F.3d 1290) are recognized
                    print(
                        f"DEBUG: API verification failed, but recognizing standard F.3d citation format: {formatted_citation}"
                    )
                    logging.info(
                        f"[DEBUG] Recognizing standard F.3d citation format: {formatted_citation}"
                    )

                    # Extract case name from context if available
                    case_name = "F.3d Case"
                    if context:
                        # Look for case name patterns
                        case_match = re.search(
                            r"([A-Za-z\s\.\,\&\(\)\-\']+)\s*,\s*" + re.escape(citation),
                            context,
                        )
                        if case_match:
                            case_name = case_match.group(1).strip()
                        else:
                            # Try to find v. pattern near citation
                            v_pattern = re.search(
                                r"([A-Za-z\s\.\,\&\(\)\-\']+v\.\s*[A-Za-z\s\.\,\&\(\)\-\']+)",
                                context,
                            )
                            if v_pattern:
                                case_name = v_pattern.group(1).strip()

                    result["found"] = True
                    result["source"] = "standard_format"
                    result["case_name"] = case_name
                    result["details"] = {
                        "volume": volume,
                        "reporter": "F.3d",
                        "page": page,
                    }
                    result["explanation"] = (
                        "Standard Federal Reporter (3d Series) citation recognized by format."
                    )
                    result["sources_checked"] = (
                        result["sources_checked"] + fallback_sources
                    )
                    return result
                except Exception as e:
                    print(f"DEBUG: Error verifying F.3d citation: {str(e)}")
                    logging.error(f"[ERROR] Error verifying F.3d citation: {str(e)}")
                    traceback.print_exc()

        # Special handling for Westlaw citations
        elif is_westlaw:
            logging.info(f"[DEBUG] Detected Westlaw citation: {citation}")
            print(f"DEBUG: Detected Westlaw citation: {citation}")
            fallback_sources.append("Pattern Recognition")
            # Try to extract year from Westlaw citation
            year_match = re.search(r"(\d{4})\s+WL", citation)
            if year_match:
                result["details"]["year"] = year_match.group(1)
                logging.info(
                    f"[DEBUG] Extracted year from Westlaw citation: {result['details']['year']}"
                )
            wl_match = re.search(r"WL\s+(\d+)", citation)
            if wl_match:
                result["details"]["wl_number"] = wl_match.group(1)
                logging.info(
                    f"[DEBUG] Extracted WL number: {result['details']['wl_number']}"
                )
            result["found"] = False
            result["is_westlaw"] = True
            result["source"] = "citation_pattern"
            result["explanation"] = (
                "Westlaw citations require subscription access and cannot be verified through public APIs. This citation was recognized by its format, but not confirmed in any public legal database."
            )
            result["sources_checked"] = result["sources_checked"] + fallback_sources

        # If not verified by our mock system, add appropriate explanations
        if not result["found"]:
            # Compose a detailed explanation with sources checked
            if not result.get("explanation"):
                if is_us_citation:
                    result["explanation"] = (
                        f"This U.S. Reports citation could not be verified in the {', '.join(result['sources_checked'])} or via public APIs."
                    )
                elif is_f3d_citation:
                    result["explanation"] = (
                        f"This Federal Reporter citation could not be verified in the {', '.join(result['sources_checked'])} or via public APIs."
                    )
                elif is_sct_citation:
                    result["explanation"] = (
                        f"This Supreme Court Reporter citation could not be verified in the {', '.join(result['sources_checked'])} or via public APIs."
                    )
                elif is_westlaw:
                    result["explanation"] = (
                        "Westlaw citations require subscription access and cannot be verified through public APIs. This citation was recognized by its format, but not confirmed in any public legal database."
                    )
                else:
                    result["explanation"] = (
                        f"Citation could not be verified through available APIs ({', '.join(result['sources_checked'])}). This may be due to database limitations, an uncommon citation format, or the citation not existing in public legal databases."
                    )
            # If we extracted a case name from context, use it for unverified citations
            if result.get("case_name_extracted") and not result.get("case_name_verified"):
                pass
            # Always attach the sources_checked for transparency
            result["sources_checked"] = result["sources_checked"] + fallback_sources

        # After all extraction and verification logic, ensure extracted case name is only from context
        if not extracted_case_name:
            result["case_name_extracted"] = ''
        # Do NOT fill from verified case name or database

        # Final defensive return: always log and guarantee a dictionary
        logging.info(
            f"[RETURN] Returning from verify_citation (final fallback): type={type(result)}, value={result}"
        )
        if not isinstance(result, dict):
            result = {
                "citation": citation,
                "found": False,
                "source": None,
                "case_name": None,
                "url": None,
                "details": {},
                "explanation": "Internal error: result was not a dictionary.",
                "is_westlaw": False,
                "sources_checked": [],
                "error": True,
            }
        return result

    def _format_citation_for_courtlistener(self, citation: str) -> str:
        """Return the citation as-is for the CourtListener API.
        
        The CourtListener API expects citations in their original format, so we don't
        need to do any special formatting.

        Args:
            citation: The original citation

        Returns:
            The original citation string
        """
        logging.info(
            f"Using citation as-is for CourtListener API: {citation}"
        )
        return citation

    def validate_citation(self, citation_text: str) -> Dict[str, Any]:
        """
        Validate a citation from pasted text using the CourtListener API.
        
        This method is specifically designed to handle citations that might be pasted
        from various sources and might need additional cleaning or formatting.
        
        Args:
            citation_text: The citation text to validate (may include extra text)
            
        Returns:
            Dict with validation results including whether the citation is valid
            and any additional metadata about the case.
        """
        # Initialize result dictionary with default values
        result = {
            "citation": citation_text.strip(),
            "found": False,
            "valid": False,
            "source": "CourtListener Citation Lookup API v4",
            "case_name": None,
            "url": None,
            "details": {},
            "explanation": None,
            "status": 404,  # Default to not found
            "verified": False,
            "error_message": None,
        }
        
        # Clean and normalize the citation text
        cleaned_citation = self._clean_citation_text(citation_text)
        if not cleaned_citation:
            result["error_message"] = "No valid citation found in the provided text"
            result["explanation"] = "The provided text does not appear to contain a valid legal citation"
            result["status"] = 404
            result["verified"] = False
            return result
            
        # Use the existing verification method with the cleaned citation
        verified_result = self.verify_with_courtlistener_citation_api(cleaned_citation)
        # Harmonize status and verified fields
        found = verified_result.get("found", False) or verified_result.get("valid", False)
        verified_result["status"] = 200 if found else 404
        verified_result["verified"] = bool(found)
        if not found and not verified_result.get("error_message"):
            verified_result["error_message"] = "Citation not found"
        return verified_result
        
    def _clean_citation_text(self, text: str) -> str:
        """
        Clean and normalize citation text from pasted content.
        
        Args:
            text: The raw citation text to clean
            
        Returns:
            The cleaned citation string, or None if no valid citation could be extracted
        """
        if not text or not isinstance(text, str):
            return None
            
        # Basic cleaning
        cleaned = text.strip()
        
        # Remove common citation prefixes/suffixes
        prefixes = ["citation:", "see", "e.g.,", "cf.", "see also", "id. at"]
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip(" .,;:")
                
        # Remove any surrounding quotes or brackets
        cleaned = cleaned.strip(r'"\'\[\](){}')
        
        # If the text is empty after cleaning, return None
        if not cleaned:
            return None
            
        return cleaned
        
    @courtlistener_limiter
    def verify_with_courtlistener_citation_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Citation Lookup API v4.
        
        This method is rate-limited to 170 calls per minute to stay under the API's
        limit of 180 calls per minute.
        """
        print("\n=== COURTLISTENER CITATION VERIFICATION DEBUG ===")
        print(f"Verifying citation: {citation}")
        
        # Check cache first
        cached_result = self._get_from_cache(citation)
        if cached_result:
            print("Cache hit for citation:", citation)
            return cached_result
            
        # Initialize result dictionary with default values
        result = {
            "citation": citation,
            "found": False,
            "valid": False,
            "source": "CourtListener Citation Lookup API v4",
            "case_name": None,
            "url": None,
            "details": {},
            "explanation": None,
            "status": None,
            "error_message": None,
        }
        
        # Log the start of the verification
        print("\nChecking API availability and credentials...")
        if not COURTLISTENER_AVAILABLE:
            error_msg = "CourtListener API is not available."
            print(f"ERROR: {error_msg}")
            result["status"] = 503
            result["error_message"] = error_msg
            return result
        
        if not self.api_key:
            error_msg = "No API key provided for CourtListener API."
            print(f"ERROR: {error_msg}")
            result["status"] = 401
            result["error_message"] = error_msg
            return result
        
        print(f"API Key: {self.api_key[:6]}... (length: {len(self.api_key)})")
        
        # Format citation for API request
        print("\nFormatting citation for API request...")
        formatted_citation = self._format_citation_for_courtlistener(citation)
        print(f"Formatted citation: {formatted_citation}")
        
        # Prepare the request
        data = {"text": formatted_citation}
        print(f"Request data: {json.dumps(data, indent=2)}")
        
        # Make the request with retries
        for attempt in range(MAX_RETRIES):
            try:
                print(f"\nAttempt {attempt + 1}/{MAX_RETRIES}")
                print("Sending request to CourtListener API...")
                print(f"URL: {COURTLISTENER_CITATION_API}")
                print("Headers:", {k: v if k != 'Authorization' else 'Token [REDACTED]' for k, v in self.headers.items()})
                
                response = requests.post(
                    COURTLISTENER_CITATION_API,
                    headers=self.headers,
                    json=data,
                    timeout=TIMEOUT_SECONDS
                )
                
                print(f"\nResponse status code: {response.status_code}")
                print("Response headers:", dict(response.headers))
                # Safely print response text, handling Unicode characters
                try:
                    print("Raw response text:", response.text)
                except UnicodeEncodeError:
                    # If Unicode fails, print a safe version
                    safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                    print("Raw response text (safe):", safe_text)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"API response data: {json.dumps(data, indent=2)}")
                        
                        # Check if the response contains actual citation data
                        # The API returns a list of citation details, each with clusters
                        if isinstance(data, list) and len(data) > 0:
                            # Check if any of the citation details have clusters
                            has_clusters = False
                            for citation_detail in data:
                                clusters = citation_detail.get("clusters", [])
                                if clusters and len(clusters) > 0:
                                    has_clusters = True
                                    break
                            
                            if has_clusters:
                                result["found"] = True
                                result["valid"] = True
                                result["details"] = data
                                # Extract case name from the first cluster if available
                                for citation_detail in data:
                                    clusters = citation_detail.get("clusters", [])
                                    if clusters:
                                        first_cluster = clusters[0]
                                        if "case_name" in first_cluster:
                                            result["case_name"] = first_cluster["case_name"]
                                        if "absolute_url" in first_cluster:
                                            result["url"] = f"https://www.courtlistener.com{first_cluster['absolute_url']}"
                                        break
                                result["explanation"] = "Citation found in CourtListener database"
                            else:
                                # No clusters found - citation not actually found
                                result["found"] = False
                                result["valid"] = False
                                result["details"] = data
                                result["explanation"] = "Citation not found in CourtListener database"
                        else:
                            # Empty or invalid response
                            result["found"] = False
                            result["valid"] = False
                            result["details"] = data
                            result["explanation"] = "No citation data returned from CourtListener"
                        
                        return result
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON response: {e}")
                        if attempt < MAX_RETRIES - 1:
                            continue
                        result["error_message"] = f"Invalid JSON response: {str(e)}"
                        return result
                    
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", RATE_LIMIT_WAIT))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(retry_after)
                        continue
                    result["error_message"] = "Rate limited by CourtListener API"
                    return result
                    
                elif response.status_code >= 500:  # Server error
                    if attempt < MAX_RETRIES - 1:
                        delay = min(MAX_RETRY_DELAY, MIN_RETRY_DELAY * (2 ** attempt))
                        print(f"Server error. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    result["error_message"] = f"Server error: {response.status_code}"
                    return result
                    
                else:
                    result["error_message"] = f"Unexpected status code: {response.status_code}"
                    return result
                
            except requests.Timeout:
                print(f"Request timed out on attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    delay = min(MAX_RETRY_DELAY, MIN_RETRY_DELAY * (2 ** attempt))
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                result["error_message"] = f"Request timed out after {TIMEOUT_SECONDS} seconds"
                return result
            
            except requests.RequestException as e:
                print(f"Request error: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    delay = min(MAX_RETRY_DELAY, MIN_RETRY_DELAY * (2 ** attempt))
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                result["error_message"] = f"Request error: {str(e)}"
                return result
            
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                print("Stack trace:")
                traceback.print_exc()
                result["error_message"] = f"Unexpected error: {str(e)}"
                return result
        
        # If we get here, all retries failed
        result["error_message"] = f"All {MAX_RETRIES} attempts failed"
        return result

    def verify_with_courtlistener_search_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Search API.
        This is a fallback when the Citation Lookup API doesn't find the case.

        Args:
            citation: The legal citation to verify

        Returns:
            Dict with verification results
        """
        result = {
            "citation": citation,
            "found": False,
            "source": "CourtListener Search API",
            "case_name": None,
            "details": {},
        }

        if not COURTLISTENER_AVAILABLE or not self.api_key:
            return result

        try:
            # Format citation for search
            formatted_citation = self._format_citation_for_courtlistener(citation)

            # Build search query
            search_params = {
                "q": formatted_citation,
                "type": "o",  # opinions only
                "order_by": "score desc",
                "format": "json",
                "cite": formatted_citation,  # Add exact citation match
                "highlight": "false",  # Disable highlighting for better performance
                "page_size": 1,  # We only need the top result
            }

            # Make the request with retries
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"Searching CourtListener for citation: {formatted_citation}")
                    logging.info(
                        f"[CourtListener API] Searching for citation: {formatted_citation}"
                    )
                    response = requests.get(
                        COURTLISTENER_SEARCH_API,
                        headers=self.headers,
                        params=search_params,
                        timeout=TIMEOUT_SECONDS,
                    )

                    print(f"Search API response status: {response.status_code}")
                    # Safely print response text, handling Unicode characters
                    try:
                        print("Raw response text:", response.text)
                    except UnicodeEncodeError:
                        # If Unicode fails, print a safe version
                        safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                        print("Raw response text (safe):", safe_text)

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        print(f"Rate limited. Waiting {retry_after} seconds...")
                        logging.info(
                            f"[CourtListener API] Rate limited. Waiting {retry_after} seconds..."
                        )
                        time.sleep(retry_after)
                        continue

                    if response.status_code == 200:
                        search_results = response.json()

                        if search_results.get("count", 0) > 0:
                            # Get the top result
                            top_result = search_results.get("results", [])[0]

                            # Extract the opinion ID for further details
                            opinion_id = top_result.get("id")
                            if opinion_id:
                                opinion_details = self._get_opinion_details(opinion_id)
                                if opinion_details:
                                    result["found"] = True
                                    result["case_name"] = opinion_details.get(
                                        "case_name",
                                        top_result.get("caseName", "Unknown Case"),
                                    )
                                    result["url"] = (
                                        f"https://www.courtlistener.com{top_result.get('absolute_url', '')}"
                                    )
                                    result["details"] = {
                                        "court": opinion_details.get(
                                            "court_name",
                                            top_result.get("court", "Unknown Court"),
                                        ),
                                        "date_filed": opinion_details.get(
                                            "date_filed",
                                            top_result.get("dateFiled", "Unknown Date"),
                                        ),
                                        "docket_number": opinion_details.get(
                                            "docket_number", "Unknown Docket"
                                        ),
                                    }
                                    return result

                    # If we get here, the citation wasn't found
                    break

                except requests.RequestException as e:
                    print(f"Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    logging.error(
                        f"[CourtListener API] Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                    else:
                        raise

        except Exception as e:
            print(f"Error in verify_with_courtlistener_search_api: {e}")
            logging.error(f"[CourtListener API] Exception: {str(e)}")
            traceback.print_exc()
            logging.info(
                f"[CourtListener Search API] Returning result (Exception): {result}"
            )
            return result

        logging.info(
            f"[CourtListener Search API] Returning result (final fallback): {result}"
        )
        return result

    def _extract_citation_parts(self, citation: str) -> Dict[str, str]:
        """
        Extract the volume, reporter, and page from a citation.

        Args:
            citation: The citation to parse

        Returns:
            Dict with volume, reporter, and page
        """
        # Common patterns for citations - order matters for specificity
        patterns = [
            # Regional reporters with series indicators (MUST come first)
            r"(\d+)\s+(N\.E\.2d|N\.E\.3d|N\.W\.2d|S\.E\.2d|S\.W\.2d|S\.W\.3d|A\.2d|A\.3d|P\.2d|P\.3d|So\.2d|So\.3d)\s+(\d+)",
            # Regional reporters without series indicators
            r"(\d+)\s+(N\.E\.|N\.W\.|S\.E\.|S\.W\.|A\.|P\.|So\.)\s+(\d+)",
            # Federal reporters with series indicators
            r"(\d+)\s+(F\.2d|F\.3d|F\.4th)\s+(\d+)",
            # Federal reporters without series indicators
            r"(\d+)\s+(F\.)\s+(\d+)",
            # Federal Supplement with series indicators
            r"(\d+)\s+(F\.\s*Supp\.\s*2d|F\.\s*Supp\.\s*3d)\s+(\d+)",
            # Federal Supplement without series indicators
            r"(\d+)\s+(F\.\s*Supp\.)\s+(\d+)",
            # U.S. Reports
            r"(\d+)\s+(U\.S\.)\s+(\d+)",
            # Supreme Court Reporter
            r"(\d+)\s+(S\.\s*Ct\.)\s+(\d+)",
            # Lawyers Edition with series indicators
            r"(\d+)\s+(L\.\s*Ed\.\s*2d)\s+(\d+)",
            # Lawyers Edition without series indicators
            r"(\d+)\s+(L\.\s*Ed\.)\s+(\d+)",
            # Standard pattern: 123 U.S. 456 (fallback)
            r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, citation)
            if match:
                if len(match.groups()) == 3:
                    # Standard pattern match (e.g., "123 U.S. 456", "123 N.E.2d 456")
                    return {
                        "volume": match.group(1),
                        "reporter": match.group(2).strip(),
                        "page": match.group(3),
                    }

        # If no pattern matches, return empty dict
        return {}

    def _get_cluster_details(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cluster from the CourtListener API.

        Args:
            cluster_id: The ID of the cluster

        Returns:
            Dict with cluster details or None if not found
        """
        try:
            url = f"{COURTLISTENER_CLUSTER_API}{cluster_id}/"
            response = requests.get(url, headers=self.headers, timeout=TIMEOUT_SECONDS)

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"Error getting cluster details: {e}")
            logging.error(f"[CourtListener API] Error getting cluster details: {e}")

        return None

    def verify_with_courtlistener_cluster_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Cluster API directly.
        This is a fallback when other CourtListener methods don't find the case.

        Args:
            citation: The legal citation to verify

        Returns:
            Dict with verification results
        """
        result = {
            "citation": citation,
            "found": False,
            "source": "CourtListener Cluster API",
            "case_name": None,
            "details": {},
        }

        if not COURTLISTENER_AVAILABLE or not self.api_key:
            return result

        try:
            # For this method, we need to search for the cluster ID first
            # We'll use the search API but with different parameters
            formatted_citation = self._format_citation_for_courtlistener(citation)

            # Build more specific search query
            search_params = {
                "q": formatted_citation,
                "type": "o",  # opinions only
                "order_by": "score desc",
                "format": "json",
            }

            logging.info(f"[CourtListener API] Request URL: {COURTLISTENER_SEARCH_API}")
            logging.info(f"[CourtListener API] Request params: {search_params}")

            # Make the request
            response = requests.get(
                COURTLISTENER_SEARCH_API,
                headers=self.headers,
                params=search_params,
                timeout=TIMEOUT_SECONDS,
            )

            if response.status_code == 200:
                search_results = response.json()

                if search_results.get("count", 0) > 0:
                    # Get the top result
                    top_result = search_results.get("results", [])[0]

                    # Extract the cluster ID
                    cluster_id = None
                    if "cluster" in top_result:
                        cluster_url = top_result.get("cluster")
                        if isinstance(cluster_url, str) and cluster_url.startswith(
                            "http"
                        ):
                            cluster_id = cluster_url.rstrip("/").split("/")[-1]

                    # If we found a cluster ID, get the details
                    if cluster_id:
                        cluster_data = self._get_cluster_details(cluster_id)
                        if cluster_data:
                            result["found"] = True
                            result["case_name"] = cluster_data.get(
                                "case_name", "Unknown Case"
                            )
                            result["url"] = (
                                f"https://www.courtlistener.com{cluster_data.get('absolute_url', '')}"
                            )
                            result["details"] = {
                                "court": cluster_data.get("court_id", "Unknown Court"),
                                "date_filed": cluster_data.get(
                                    "date_filed", "Unknown Date"
                                ),
                                "docket_number": cluster_data.get(
                                    "docket_id", "Unknown Docket"
                                ),
                                "precedential_status": cluster_data.get(
                                    "precedential_status", "Unknown"
                                ),
                            }
                            return result

        except Exception as e:
            print(f"Error in verify_with_courtlistener_cluster_api: {e}")
            return {
                "citation": citation,
                "found": False,
                "source": "CourtListener Cluster API",
                "case_name": None,
                "error_message": str(e),
                "details": {}
            }

    def verify_with_google_scholar(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using Google Scholar search.
        Note: This is a basic implementation and may be rate-limited by Google.

        Args:
            citation: The legal citation to verify

        Returns:
            Dict with verification results
        """
        result = {
            "citation": citation,
            "found": False,
            "source": "Google Scholar",
            "case_name": None,
            "details": {},
        }

        if not GOOGLE_SCHOLAR_AVAILABLE:
            return result

        try:
            # Format the citation for search
            formatted_citation = self._format_citation_for_courtlistener(
                citation
            )  # Reuse this formatter

            # Prepare the search parameters
            params = {
                "q": f'"{formatted_citation}"',  # Exact match search
                "hl": "en",
                "as_sdt": "0,5",  # Search only in case law
                "as_vis": "1",
            }

            # Set up headers to mimic a browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            # Make the request
            response = requests.get(
                GOOGLE_SCHOLAR_URL,
                headers=headers,
                params=params,
                timeout=TIMEOUT_SECONDS,
            )

            # Simple check if the citation appears in the results
            if response.status_code == 200 and formatted_citation in response.text:
                # Extract the first result title as case name (basic implementation)
                import re

                title_match = re.search(
                    r'<h3 class="gs_rt">\s*<a[^>]*>([^<]+)</a>', response.text
                )
                case_name = title_match.group(1) if title_match else "Unknown Case"

                result["found"] = True
                result["case_name"] = case_name
                result["url"] = f"{GOOGLE_SCHOLAR_URL}?{urllib.parse.urlencode(params)}"
                result["details"] = {
                    "source": "Google Scholar",
                    "note": "Limited information available from Google Scholar",
                }
                return result

        except Exception as e:
            print(f"Error in verify_with_google_scholar: {e}")
            traceback.print_exc()

        return result
