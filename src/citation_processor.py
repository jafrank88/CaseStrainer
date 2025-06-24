"""
Enhanced Citation Processor for CaseStrainer

This module provides a robust way to process and validate legal citations
using eyecite and external APIs with caching, retries, and parallel processing.
"""

import functools
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from eyecite import get_citations, clean_text, resolve_citations
from eyecite.models import CitationBase
from eyecite.tokenizers import AhocorasickTokenizer

# Import get_config_value from the full path to avoid circular imports
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import get_config_value, configure_logging
from src.extract_case_name import extract_case_name_from_text, find_shared_case_name_for_citations
from src.cache_manager import get_cache_manager
from src.enhanced_case_name_extractor import EnhancedCaseNameExtractor

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

class CitationProcessor:
    """Process and validate legal citations using eyecite and external APIs."""

    def __init__(self, api_key: Optional[str] = None, max_workers: int = 5):
        """Initialize the citation processor.

        Args:
            api_key: API key for the citation validation service (CourtListener).
                    If None, will try to get from environment/config.
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or get_config_value("COURTLISTENER_API_KEY")
        self.max_workers = max_workers
        self.session = self._create_session()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.api_base_url = get_config_value(
            "COURTLISTENER_API_URL", "https://www.courtlistener.com/api/rest/v4/"
        ).rstrip("/")
        self.citation_lookup_url = f"{self.api_base_url}/citation-lookup/"
        self.cache_manager = get_cache_manager()

        # Initialize enhanced case name extractor with API key
        self.enhanced_case_name_extractor = EnhancedCaseNameExtractor(
            api_key=self.api_key, 
            cache_results=True
        ) if self.api_key else None

        if not self.api_key:
            self.logger.warning(
                "No CourtListener API key provided. Enhanced case name extraction will be limited. "
                "Set COURTLISTENER_API_KEY in your environment or .env file."
            )

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic and timeout."""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Reduced from 3 to fail faster
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 522, 524],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,
        )

        # Configure timeouts
        timeout = 10  # seconds

        # Configure adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default timeout for all requests
        session.request = functools.partial(session.request, timeout=timeout)

        # Add API key to headers if provided
        if self.api_key:
            session.headers.update(
                {
                    "Authorization": f"Token {self.api_key}",
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/jafrank88/casestrainer; your@email.com)",
                }
            )
        else:
            session.headers.update(
                {
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/jafrank88/casestrainer; your@email.com)"
                }
            )

        return session

    def clean_text(self, text: str, steps: Optional[List[str]] = None) -> str:
        """Clean and normalize text for citation extraction.

        Args:
            text: The text to clean
            steps: List of cleaning steps to apply. If None, applies all steps.
                  Possible values: 'all_whitespace', 'inline_whitespace', 'underscores',
                  'hyphens', 'quotes', 'unicode'

        Returns:
            str: The cleaned text
        """
        if not text:
            return text

        if steps is None:
            steps = [
                "all_whitespace",
                "inline_whitespace",
                "underscores",
                "hyphens",
                "quotes",
                "unicode",
            ]

        cleaned = str(text)

        if "all_whitespace" in steps:
            # Replace all whitespace sequences with a single space
            cleaned = re.sub(r"\s+", " ", cleaned)

        if "inline_whitespace" in steps:
            # Remove extra spaces around punctuation
            cleaned = re.sub(
                r"\s+([.,;:!?])", r"\1", cleaned
            )  # Remove space before punctuation
            cleaned = re.sub(
                r'([({\[\'"])[ \t]+', r"\1", cleaned
            )  # Remove space after opening brackets/quotes
            cleaned = re.sub(
                r'[ \t]+([)}\]\'"])', r"\1", cleaned
            )  # Remove space before closing brackets/quotes

        if "underscores" in steps:
            # Replace underscores with spaces
            cleaned = cleaned.replace("_", " ")

        if "hyphens" in steps:
            # Normalize different types of hyphens and dashes to simple hyphen
            cleaned = re.sub(r"[\u2010-\u2015]", "-", cleaned)

        if "quotes" in steps:
            # Normalize different types of quotes to straight quotes
            cleaned = re.sub(
                r"[\u2018\u2019]", "'", cleaned
            )  # Left/right single quotes
            cleaned = re.sub(
                r"[\u201C\u201D]", '"', cleaned
            )  # Left/right double quotes

        if "unicode" in steps:
            # Normalize unicode characters (e.g., accented characters)
            try:
                import unicodedata

                cleaned = unicodedata.normalize("NFKC", cleaned)
            except ImportError:
                pass

        return cleaned.strip()

    def extract_citations(self, text: str, extract_case_names: bool = True) -> List[Dict[str, Any]]:
        """
        Extract citations from text with enhanced case name extraction.
        
        Args:
            text: The text to extract citations from
            extract_case_names: Whether to extract case names using enhanced method
            
        Returns:
            List of dictionaries with citation and case name information
        """
        try:
            # Clean the text
            cleaned_text = clean_text(
                text, steps=["all_whitespace", "inline_whitespace", "underscores"]
            )

            # Extract citations with context
            citations = get_citations(
                cleaned_text, tokenizer=AhocorasickTokenizer(), remove_ambiguous=True
            )

            # Resolve citations to group duplicates
            resolved_citations = resolve_citations(citations)
            
            # Convert to enhanced format with case names
            enhanced_citations = []
            for citation in resolved_citations:
                citation_str = str(citation)
                
                # Extract the actual citation text (not the full eyecite object)
                if hasattr(citation, 'citation'):
                    # For eyecite citations, get the actual citation text
                    if hasattr(citation.citation, 'groups'):
                        # This is a FullCaseCitation object, extract the text
                        volume = citation.citation.groups.get('volume', '')
                        reporter = citation.citation.groups.get('reporter', '')
                        page = citation.citation.groups.get('page', '')
                        actual_citation_text = f"{volume} {reporter} {page}".strip()
                    else:
                        actual_citation_text = str(citation.citation)
                else:
                    actual_citation_text = citation_str
                
                # Create citation object with position info for shared case name detection
                citation_obj = {
                    'citation': actual_citation_text,
                    'start_index': getattr(citation, 'start', None),
                    'end_index': getattr(citation, 'end', None),
                }
                enhanced_citations.append(citation_obj)
            
            # Use enhanced case name extraction if available
            if self.enhanced_case_name_extractor and extract_case_names:
                try:
                    enhanced_results = self.enhanced_case_name_extractor.extract_enhanced_case_names(text)
                    
                    # Create a mapping of citations to enhanced results
                    enhanced_map = {result['citation']: result for result in enhanced_results}
                    
                    # Combine results
                    results = []
                    for citation_info in enhanced_citations:
                        citation = citation_info['citation']
                        enhanced_result = enhanced_map.get(citation, {})
                        
                        result = {
                            'citation': citation,
                            'case_name': enhanced_result.get('case_name'),  # Extracted from document
                            'canonical_case_name': enhanced_result.get('canonical_name'),  # From API
                            'confidence': enhanced_result.get('confidence', 0.0),
                            'method': enhanced_result.get('method', 'none'),
                            'extracted_name': enhanced_result.get('extracted_name'),  # Document text
                            'position': citation_info.get('start_index'),
                            'verified': enhanced_result.get('canonical_name') is not None,
                            'similarity': enhanced_result.get('similarity_score', 0.0) if enhanced_result.get('canonical_name') and enhanced_result.get('extracted_name') else None,
                            'canonical_source': enhanced_result.get('source', 'none'),  # Track source of canonical name
                            'citation_url': self.enhanced_case_name_extractor.get_citation_url(citation) if self.enhanced_case_name_extractor else None,
                            'url_source': self._get_url_source(citation) if self.enhanced_case_name_extractor else None
                        }
                        results.append(result)
                    
                    return results
                    
                except Exception as e:
                    # Fallback to original method if enhanced extraction fails
                    self.logger.warning(f"Enhanced case name extraction failed: {e}. Falling back to original method.")
                    return self._extract_citations_fallback(text, enhanced_citations)
            else:
                # Use fallback method if enhanced extractor not available
                return self._extract_citations_fallback(text, enhanced_citations)

        except Exception as e:
            self.logger.error(f"Error extracting citations: {str(e)}", exc_info=True)
            return []

    def _extract_citations_fallback(self, text: str, enhanced_citations: List[Dict]) -> List[Dict[str, Any]]:
        """Fallback method for citation extraction when enhanced extractor is not available."""
        try:
            # Use the original case name extraction method
            from src.extract_case_name import extract_case_name_from_text
            
            results = []
            for citation_info in enhanced_citations:
                citation = citation_info['citation']
                
                # Extract case name using original method
                case_name = extract_case_name_from_text(text, citation)
                
                result = {
                    'citation': citation,
                    'case_name': case_name,
                    'canonical_case_name': None,
                    'confidence': 0.7 if case_name else 0.0,
                    'method': 'fallback',
                    'extracted_name': case_name,
                    'position': citation_info.get('start_index'),
                    'verified': False,
                    'similarity': None
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in fallback citation extraction: {str(e)}", exc_info=True)
            return []

    def _validate_locally(self, citation_text: Union[str, Any]) -> Dict[str, Any]:
        """Perform local validation when API is unavailable."""
        try:
            if not isinstance(citation_text, str):
                citation_str = str(citation_text)
            else:
                citation_str = citation_text

            # Simple pattern matching for common citation formats
            patterns = [
                (r"(\d+)\s+U\.?\s*S\.?\s+(\d+)", "U.S. Reports"),
                (r"(\d+)\s+F\.?(:?\s*\d*[a-z]*)?\s+\d+", "Federal Reporter"),
                (r"(\d+)\s+S\.?\s*Ct\.?\s+\d+", "Supreme Court Reporter"),
                (r"(\d+)\s+L\.?\s*Ed\.?\s*\d+", "Lawyers Edition"),
            ]

            for pattern, reporter in patterns:
                if re.search(pattern, citation_str, re.IGNORECASE):
                    return {
                        "citation": citation_str,
                        "valid": True,
                        "verified": False,
                        "results": [
                            {
                                "source": "local_validation",
                                "reporter": reporter,
                                "confidence": "medium",
                            }
                        ],
                        "cached": False,
                        "error": "Not verified in database",
                        "source": "local_validation",
                    }

            # If no patterns matched
            return {
                "citation": citation_str,
                "valid": False,
                "verified": False,
                "results": [],
                "cached": False,
                "error": "Local validation failed - citation format not recognized",
                "source": "local_validation",
            }

        except Exception as e:
            self.logger.error(
                f"Error in local validation for '{citation_text}': {str(e)}",
                exc_info=True,
            )
            return {
                "citation": (
                    str(citation_text)
                    if not isinstance(citation_text, str)
                    else citation_text
                ),
                "valid": False,
                "verified": False,
                "results": [],
                "cached": False,
                "error": f"Local validation error: {str(e)}",
                "source": "error",
            }

    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an authenticated request to the CourtListener API."""
        url = f"{self.api_base_url}{endpoint}"
        headers = {
            "Authorization": f"Token {self.api_key}" if self.api_key else None,
            "Content-Type": "application/json",
        }

        try:
            response = self.session.get(
                url,
                params=params,
                headers={k: v for k, v in headers.items() if v is not None},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                error_msg += f" (Status: {e.response.status_code})"
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail.get('detail', 'No details')}"
                except:
                    pass
            raise Exception(error_msg) from e

    def validate_citation(self, citation_text: str) -> Dict[str, Any]:
        """Validate a single citation with unified caching and fallback.

        Args:
            citation_text: The citation text to validate

        Returns:
            Dictionary with validation results
        """
        # Check cache first
        cached_result = self.cache_manager.get_citation(citation_text)
        if cached_result:
            verification_result = json.loads(cached_result.get('verification_result', '{}'))
            return {
                "citation": citation_text,
                "valid": verification_result.get('valid', False),
                "results": verification_result.get('results', []),
                "cached": True,
                "error": None,
                "source": "cache",
                "case_name": verification_result.get('case_name'),
                "year": verification_result.get('year'),
                "parallel_citations": json.loads(verification_result.get('parallel_citations', '[]'))
            }

        # First try to validate using the API v4
        try:
            # Call the citation-lookup endpoint
            result = self._make_api_request(
                "/citation-lookup/", params={"citation": str(citation_text)}
            )

            validation_result = {
                "citation": citation_text,
                "valid": bool(result.get("count", 0) > 0),
                "results": result.get("results", []),
                "cached": False,
                "error": None,
                "source": "api_v4",
                "api_version": "v4",
            }

            # Cache the result
            self.cache_manager.set_citation(citation_text, {
                'case_name': '',  # Will be extracted later if needed
                'year': None,
                'parallel_citations': [],
                'verification_result': json.dumps(validation_result)
            })

            return validation_result

        except (
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
        ) as e:
            self.logger.warning(
                f"API request failed for '{citation_text}': {str(e)}. Falling back to local validation."
            )
            # Fall back to local validation
            local_result = self._validate_locally(citation_text)
            
            # Cache the local validation result
            self.cache_manager.set_citation(citation_text, {
                'case_name': '',
                'year': None,
                'parallel_citations': [],
                'verification_result': json.dumps(local_result)
            })
            
            return local_result

        except Exception as e:
            self.logger.error(
                f"Unexpected error validating citation '{citation_text}': {str(e)}",
                exc_info=True,
            )
            error_result = {
                "citation": citation_text,
                "valid": False,
                "results": [],
                "cached": False,
                "error": f"Validation error: {str(e)}",
                "source": "error",
            }
            
            # Cache the error result
            self.cache_manager.set_citation(citation_text, {
                'case_name': '',
                'year': None,
                'parallel_citations': [],
                'verification_result': json.dumps(error_result)
            })
            
            return error_result

    def process_batch(
        self, citations: List[str], batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Process multiple citations in parallel with batching, using the CourtListener batch API if possible."""
        if not citations:
            return []

        results = []
        total = len(citations)

        self.logger.info(
            f"Starting batch processing of {total} citations in batches of {batch_size}"
        )

        # Try to use the new batch CourtListener API if available
        try:
            from src.citation_verification import CitationVerifier
            verifier = CitationVerifier()
            self.logger.info("Using CourtListener batch API for citation verification.")
            batch_results = verifier.verify_citations_batch_courtlistener(citations)
            
            # Since the batch API might not return results for all citations (e.g., non-CourtListener ones),
            # we need to handle the remaining ones.
            # This part assumes batch_results contains valid data for some citations.
            
            # Create a dictionary for quick lookup of batch results
            batch_results_map = {res['citation']: res for res in batch_results if res}
            
            processed_citations = set(batch_results_map.keys())
            
            # Add successful batch results
            for cit in citations:
                if cit in batch_results_map:
                    results.append(batch_results_map[cit])
            
            # Identify citations that were not processed by the batch API
            remaining_citations = [cit for cit in citations if cit not in processed_citations]
            
            if remaining_citations:
                self.logger.info(f"Processing {len(remaining_citations)} remaining citations individually.")
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_citation = {
                        executor.submit(self.validate_citation, cit): cit
                        for cit in remaining_citations
                    }
                    for future in as_completed(future_to_citation):
                        citation = future_to_citation[future]
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as exc:
                            self.logger.error(
                                f"'{citation}' generated an exception: {exc}",
                                exc_info=True,
                            )
                            results.append({"citation": citation, "error": str(exc)})
            
            # Re-order results to match the original citation list order
            final_results = sorted(results, key=lambda x: citations.index(x['citation']))
            return final_results

        except Exception as e:
            self.logger.warning(f"Could not use batch API: {e}. Falling back to individual processing.")
            
            # Fallback to original individual processing if batch fails entirely
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_citation = {
                    executor.submit(self.validate_citation, cit): cit
                    for cit in citations
                }
                for future in as_completed(future_to_citation):
                    citation = future_to_citation[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        self.logger.error(
                            f"'{citation}' generated an exception: {exc}", exc_info=True
                        )
                        results.append({"citation": citation, "error": str(exc)})

            # Re-order results to match the original citation list order
            final_results = sorted(results, key=lambda x: citations.index(x['citation']))
            return final_results

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_url_source(self, citation: str) -> str:
        """Determine the source of the citation URL."""
        if not self.enhanced_case_name_extractor:
            return "none"
        
        try:
            # Get the URL first
            url = self.enhanced_case_name_extractor.get_citation_url(citation)
            if not url:
                return "none"
            
            # Determine source based on URL
            if "courtlistener.com" in url:
                return "courtlistener"
            elif "scholar.google.com" in url:
                return "google_scholar"
            elif "vlex.com" in url:
                return "vlex"
            elif "casemine.com" in url:
                return "casemine"
            elif "leagle.com" in url:
                return "leagle"
            elif "justia.com" in url:
                return "justia"
            else:
                return "unknown"
            
        except Exception as e:
            self.logger.warning(f"Error determining URL source for '{citation}': {e}")
            return "unknown"

# Example usage
if __name__ == "__main__":
    # Initialize the processor
    with CitationProcessor(api_key="your_api_key_here") as processor:
        # Example text with citations
        text = """
        The court in Brown v. Board of Education, 347 U.S. 483 (1954), 
        held that racial segregation in public schools was unconstitutional.
        This was later affirmed in Cooper v. Aaron, 358 U.S. 1 (1958).
        """

        # Extract citations
        citations = processor.extract_citations(text)
        print(f"Extracted {len(citations)} citations")

        # Validate citations
        citation_texts = [str(citation) for citation in citations]
        results = processor.process_batch(citation_texts)

        # Print results
        for result in results:
            print(f"{result['citation']}: {'Valid' if result['valid'] else 'Invalid'}")
            if result.get("error"):
                print(f"  Error: {result['error']}")
