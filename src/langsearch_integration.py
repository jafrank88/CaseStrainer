#!/usr/bin/env python3
"""
LangSearch API integration for CaseStrainer

This module provides functions to generate case summaries using the LangSearch API.
It first checks if the case is found in CourtListener, and if not, then uses the LangSearch API.
"""

import os
import requests
from typing import Optional, Dict, Any
import time
import logging

# Import CourtListener functions
from .courtlistener_integration import (
    search_citation,
)

# Flag to track if LangSearch API is available
LANGSEARCH_AVAILABLE = True

logger = logging.getLogger(__name__)


def setup_langsearch_api(api_key: Optional[str] = None):
    """
    Set up the LangSearch API with the provided key or from environment variable.

    Args:
        api_key: LangSearch API key. If None, will try to get from LANGSEARCH_API_KEY environment variable.

    Returns:
        bool: True if setup was successful, False otherwise.
    """
    try:
        # Get API key from parameter or environment variable
        key = api_key or os.environ.get("LANGSEARCH_API_KEY")
        if not key:
            logger.error(
                "Error: LangSearch API key not provided and LANGSEARCH_API_KEY environment variable not set."
            )
            return False

        # Validate API key format (basic check)
        if not key.startswith("sk-"):
            logger.warning(
                "Warning: API key format doesn't match expected pattern. Key should start with 'sk-'."
            )

        # Store the API key in an environment variable for later use
        os.environ["LANGSEARCH_API_KEY"] = key

        # Test the API connection with a minimal request
        try:
            # Make a minimal API call to verify the key works
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }

            # Use a simple query to test the API connection
            payload = {"query": "test query", "count": 1}

            response = requests.post(
                "https://api.langsearch.com/v1/web-search",
                headers=headers,
                json=payload,
                timeout=10,
            , timeout=30)

            if response.status_code == 200:
                logger.info("LangSearch API connection successful.")
                return True
            else:
                logger.error(
                    f"Error testing LangSearch API connection: Status code {response.status_code}"
                )
                # Safely print the response text to avoid Unicode encoding errors
                try:
                    logger.error(f"Response: {response.text}")
                except UnicodeEncodeError:
                    # If Unicode fails, print a safe version
                    safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                    logger.error(f"Response (safe): {safe_text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing LangSearch API connection: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error setting up LangSearch API: {str(e)}")
        return False


def generate_case_summary_with_langsearch_api(case_citation: str) -> str:
    """
    Generate a summary of a legal case using LangSearch API.

    Args:
        case_citation: The case citation to summarize.

    Returns:
        str: A summary of the case.

    Raises:
        ValueError: If the API key is not set or if parameters are invalid.
        RuntimeError: If the API call fails after multiple retries.
    """
    # Check if API key is set
    api_key = os.environ.get("LANGSEARCH_API_KEY")
    if not api_key:
        raise ValueError(
            "LangSearch API key not set. Call setup_langsearch_api() first."
        )

    # Validate inputs
    if not case_citation or not case_citation.strip():
        raise ValueError("Case citation cannot be empty")

    # Create the prompt

    # Maximum retry attempts
    max_retries = 3
    retry_delay = 2  # seconds
    last_error = None

    for attempt in range(max_retries):
        try:
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "query": f"summarize the legal case {case_citation}",
                "count": 5,
                "timeframe": "oneYear",
                "summary": True,
            }

            # Call the LangSearch API
            response = requests.post(
                "https://api.langsearch.com/v1/web-search",
                headers=headers,
                json=payload,
                timeout=30,
            , timeout=30)

            # Check for successful response
            if response.status_code == 200:
                response_data = response.json()

                # Validate response structure
                if not response_data or "data" not in response_data:
                    raise ValueError(
                        "Invalid response from LangSearch API: No data returned"
                    )

                data = response_data["data"]
                if "_type" not in data or data["_type"] != "SearchResponse":
                    raise ValueError(
                        "Invalid response from LangSearch API: Not a SearchResponse"
                    )

                if "webPages" not in data or "value" not in data["webPages"]:
                    raise ValueError(
                        "Invalid response from LangSearch API: No web pages returned"
                    )

                # Compile a summary from the search results
                summary = f"Summary for case: {case_citation}\n\n"

                for i, result in enumerate(data["webPages"]["value"], 1):
                    if "name" in result and "url" in result:
                        summary += f"Source {i}: {result['name']}\n"
                        summary += f"URL: {result['url']}\n"

                        if "snippet" in result:
                            summary += f"Excerpt: {result['snippet']}\n"

                        if "summary" in result:
                            summary += f"Summary: {result['summary']}\n"

                        summary += "\n"

                if not summary:
                    raise ValueError("Empty summary returned from LangSearch API")

                return summary
            elif response.status_code == 429:  # Too Many Requests
                last_error = f"Rate limit exceeded: {response.text}"
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Rate limit exceeded. Waiting {wait_time} seconds before retrying..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts.")
                    raise RuntimeError(
                        f"Failed to generate summary due to rate limits: {response.text}"
                    )
            elif response.status_code == 401:  # Unauthorized
                # Safely print the authentication error to avoid Unicode encoding errors
                try:
                    logger.error(f"Authentication error: {response.text}")
                except UnicodeEncodeError:
                    # If Unicode fails, print a safe version
                    safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                    logger.error(f"Authentication error (safe): {safe_text}")
                raise ValueError(
                    f"LangSearch API authentication failed: {response.text}"
                )
            elif response.status_code == 400:  # Bad Request
                # Safely print the invalid request error to avoid Unicode encoding errors
                try:
                    logger.error(f"Invalid request: {response.text}")
                except UnicodeEncodeError:
                    # If Unicode fails, print a safe version
                    safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                    logger.error(f"Invalid request (safe): {safe_text}")
                raise ValueError(f"Invalid request to LangSearch API: {response.text}")
            else:
                last_error = (
                    f"API error (status code {response.status_code}): {response.text}"
                )
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    logger.error(f"API error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error after {max_retries} attempts.")
                    raise RuntimeError(
                        f"Failed to generate summary: API error (status code {response.status_code}): {response.text}"
                    )
        except requests.exceptions.Timeout:
            last_error = "Request timed out"
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                logger.error(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Request timed out after {max_retries} attempts.")
                logger.error(
                    "This may be due to a large file or server load. Processing will continue with other methods."
                )
                raise RuntimeError(
                    f"Failed to generate summary: Request timed out after {max_retries} attempts"
                )
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                logger.error(f"Request error: {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Request error after {max_retries} attempts.")
                raise RuntimeError(
                    f"Failed to generate summary: Request error: {str(e)}"
                )
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                logger.error(
                    f"Error calling LangSearch API: {str(e)}. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to generate summary after {max_retries} attempts")
                raise RuntimeError(
                    f"Failed to generate summary after {max_retries} attempts: {str(e)}"
                )

    # This should never be reached due to the raise in the loop, but just in case
    if last_error:
        raise RuntimeError(f"Failed to generate summary: {last_error}")
    else:
        raise RuntimeError("Failed to generate summary for unknown reasons")


def generate_case_summary_from_data(case_data: Dict[str, Any]) -> str:
    """
    Generate a summary of a legal case using the provided case data.

    Args:
        case_data: The case data from CourtListener.

    Returns:
        str: A summary of the case.

    Note:
        If the summary contains mostly "Unknown" values, the caller should
        consider the case as not verified.
    """
    try:
        # Extract relevant information for the summary
        case_name = case_data.get("case_name", "Unknown case name")
        court = case_data.get("court_name", "Unknown court")
        date_filed = case_data.get("date_filed", "Unknown date")
        docket_number = case_data.get("docket_number", "Unknown docket number")
        citation_string = case_data.get("citation", "Unknown citation")

        # Extract the opinion text
        opinion_text = case_data.get("plain_text", "")

        # Check if we have mostly unknown values
        unknown_count = 0
        if case_name == "Unknown case name":
            unknown_count += 1
        if court == "Unknown court":
            unknown_count += 1
        if date_filed == "Unknown date":
            unknown_count += 1
        if docket_number == "Unknown docket number":
            unknown_count += 1
        if citation_string == "Unknown citation":
            unknown_count += 1

        # Create a summary
        summary = f"""
        Case Summary: {case_name}
        
        Citation: {citation_string}
        Court: {court}
        Date Filed: {date_filed}
        Docket Number: {docket_number}
        
        """

        # Add a warning if most values are unknown
        if unknown_count >= 3:
            summary = (
                "WARNING: CASE VERIFICATION FAILED - INSUFFICIENT DATA\n\n" + summary
            )

        # Add a brief excerpt from the opinion if available
        if opinion_text:
            # Get the first 500 characters as a preview
            preview = opinion_text[:500].strip()
            if len(opinion_text) > 500:
                preview += "..."

            summary += f"""
            Opinion Excerpt:
            {preview}
            
            Full opinion available at: https://www.courtlistener.com/opinion/{case_data.get('id', '')}/
            """

        return summary
    except Exception as e:
        return f"Error generating summary from case data: {str(e)}"


def generate_case_summary_with_langsearch(case_citation: str) -> str:
    """
    Generate a summary of a legal case.
    First checks if the case is found in CourtListener, and if so, returns that information.
    If the case is not found in CourtListener, then uses the LangSearch API.

    Args:
        case_citation: The case citation to summarize.

    Returns:
        str: A summary of the case.
    """
    # Validate inputs
    if not case_citation or not case_citation.strip():
        raise ValueError("Case citation cannot be empty")

    # First, check if the case is found in CourtListener
    exists, case_data = search_citation(case_citation)

    if exists:
        # Case found in CourtListener, use the case data directly
        logger.info(
            f"Case '{case_citation}' found in CourtListener. Generating summary from case data."
        )

        # Get more detailed information if we have a case ID
        case_id = case_data.get("id")
        if case_id:
            from .courtlistener_integration import get_case_details

            details = get_case_details(case_id)
            if details:
                case_data = details

        return generate_case_summary_from_data(case_data)
    else:
        # Case not found in CourtListener, use LangSearch API
        logger.info(
            f"Case '{case_citation}' not found in CourtListener. Using LangSearch API."
        )
        try:
            return generate_case_summary_with_langsearch_api(case_citation)
        except Exception as e:
            logger.error(f"Error generating summary with LangSearch API: {str(e)}")
            return f"Error: Could not generate summary for '{case_citation}'. Case not found in CourtListener and LangSearch API failed: {str(e)}"
