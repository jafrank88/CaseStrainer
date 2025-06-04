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

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

logger = logging.getLogger(__name__)


class CitationProcessor:
    """Process and validate legal citations using eyecite and external APIs."""

    def __init__(self, api_key: Optional[str] = None, max_workers: int = 5):
        """Initialize the citation processor.

        Args:
            api_key: API key for the citation validation service (CourtListener).
                    If None, will try to get from environment/config.
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.api_key = api_key or get_config_value("COURTLISTENER_API_KEY")
        self.max_workers = max_workers
        self.session = self._create_session()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.api_base_url = get_config_value(
            "COURTLISTENER_API_URL", "https://www.courtlistener.com/api/rest/v4/"
        ).rstrip("/")
        self.citation_lookup_url = f"{self.api_base_url}/citation-lookup/"

        if not self.api_key:
            logger.warning(
                "No CourtListener API key provided. Some features may be limited. "
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
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/yourusername/casestrainer; your@email.com)",
                }
            )
        else:
            session.headers.update(
                {
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/yourusername/casestrainer; your@email.com)"
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

    def extract_citations(self, text: str) -> List[CitationBase]:
        """Extract citations from text using eyecite.

        Args:
            text: The text to extract citations from

        Returns:
            List of extracted citation objects
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
            return list(resolved_citations)

        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}", exc_info=True)
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
                (r"(\d+)\s+F\.?(?:\s*\d*[a-z]*)?\s+\d+", "Federal Reporter"),
                (r"(\d+)\s+S\.?\s*Ct\.?\s+\d+", "Supreme Court Reporter"),
                (r"(\d+)\s+L\.?\s*Ed\.?\s*\d+", "Lawyers Edition"),
            ]

            for pattern, reporter in patterns:
                if re.search(pattern, citation_str, re.IGNORECASE):
                    return {
                        "citation": citation_str,
                        "valid": True,
                        "results": [
                            {
                                "source": "local_validation",
                                "reporter": reporter,
                                "confidence": "medium",
                            }
                        ],
                        "cached": False,
                        "error": None,
                    }

            # If no patterns matched
            return {
                "citation": citation_str,
                "valid": False,
                "results": [],
                "cached": False,
                "error": "Local validation failed - citation format not recognized",
                "source": "local_validation",
            }

        except Exception as e:
            logger.error(
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

    @lru_cache(maxsize=1000)
    def validate_citation(self, citation_text: str) -> Dict[str, Any]:
        """Validate a single citation with caching and fallback.

        Args:
            citation_text: The citation text to validate

        Returns:
            Dictionary with validation results
        """
        # First try to validate using the API v4
        try:
            # Call the citation-lookup endpoint
            result = self._make_api_request(
                "/citation-lookup/", params={"citation": str(citation_text)}
            )

            return {
                "citation": citation_text,
                "valid": bool(result.get("count", 0) > 0),
                "results": result.get("results", []),
                "cached": False,
                "error": None,
                "source": "api_v4",
                "api_version": "v4",
            }

        except (
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
        ) as e:
            logger.warning(
                f"API request failed for '{citation_text}': {str(e)}. Falling back to local validation."
            )
            # Fall back to local validation
            return self._validate_locally(citation_text)

        except Exception as e:
            logger.error(
                f"Unexpected error validating citation '{citation_text}': {str(e)}",
                exc_info=True,
            )
            return {
                "citation": citation_text,
                "valid": False,
                "results": [],
                "cached": False,
                "error": f"Validation error: {str(e)}",
                "source": "error",
            }

    def process_batch(
        self, citations: List[str], batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Process multiple citations in parallel with batching.

        Args:
            citations: List of citation texts to validate
            batch_size: Number of citations to process in each batch

        Returns:
            List of validation results
        """
        if not citations:
            return []

        results = []
        total = len(citations)

        logger.info(
            f"Starting batch processing of {total} citations in batches of {batch_size}"
        )

        # Process in batches to avoid overwhelming the API
        for i in range(0, total, batch_size):
            batch = citations[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(
                f"Processing batch {batch_num}/{total_batches} with {len(batch)} citations"
            )

            # Use ThreadPoolExecutor to process batch in parallel
            with ThreadPoolExecutor(
                max_workers=min(self.max_workers, len(batch))
            ) as executor:
                # Submit all tasks in current batch
                future_to_citation = {
                    executor.submit(self.validate_citation, citation): citation
                    for citation in batch
                }

                # Process results as they complete
                for future in as_completed(future_to_citation):
                    citation = future_to_citation[future]
                    try:
                        result = future.result()
                        results.append(result)

                        # Log progress for long-running batches
                        if len(results) % 5 == 0 or len(results) == len(batch):
                            logger.debug(
                                f"Processed {len(results)}/{len(batch)} in current batch"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error processing citation {citation}: {str(e)}",
                            exc_info=True,
                        )
                        results.append(
                            {
                                "citation": citation,
                                "valid": False,
                                "results": [],
                                "cached": False,
                                "error": str(e),
                                "source": "error",
                            }
                        )

            # Add a small delay between batches to be nice to the API
            if i + batch_size < total:
                time.sleep(0.5)

        logger.info(f"Completed processing {len(results)} citations")
        return results

    def close(self):
        """Clean up resources."""
        self.session.close()
        self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


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
