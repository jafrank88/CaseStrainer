#!/usr/bin/env python3
"""
OpenAI API integration for CaseStrainer

This module provides functions to generate case summaries using the OpenAI API.
"""

import os
import time
from typing import Optional

# Try to import OpenAI
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not available. Please install it using:")
    print("pip install openai")


def setup_openai_api(api_key: Optional[str] = None):
    """
    Set up the OpenAI API with the provided key or from environment variable.

    Args:
        api_key: OpenAI API key. If None, will try to get from OPENAI_API_KEY environment variable.

    Returns:
        bool: True if setup was successful, False otherwise.

    Raises:
        ImportError: If the openai package is not available.
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "openai package is not available. Please install it using: pip install openai"
        )

    try:
        # Get API key from parameter or environment variable
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            print(
                "Error: OpenAI API key not provided and OPENAI_API_KEY environment variable not set."
            )
            return False

        # Validate API key format (basic check)
        if not key.startswith(("sk-", "org-")):
            print(
                "Warning: API key format doesn't match expected pattern. Key should start with 'sk-' or 'org-'."
            )

        # Set up the client
        openai.api_key = key

        # Test the API connection with a minimal request
        try:
            # Make a minimal API call to verify the key works
            openai.Model.list()
            print("OpenAI API connection successful.")
            return True
        except Exception as e:
            print(f"Error testing OpenAI API connection: {str(e)}")
            return False
    except Exception as e:
        print(f"Error setting up OpenAI API: {str(e)}")
        return False


def generate_case_summary_with_openai(case_citation: str, model: str = "gpt-4") -> str:
    """
    Generate a summary of a legal case using OpenAI API.

    Args:
        case_citation: The case citation to summarize.
        model: The OpenAI model to use (default: gpt-4).

    Returns:
        str: A summary of the case.

    Raises:
        ImportError: If the openai package is not available.
        ValueError: If the API key is not set or if parameters are invalid.
        RuntimeError: If the API call fails after multiple retries.
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "openai package is not available. Please install it using: pip install openai"
        )

    # Check if API key is set
    if not openai.api_key:
        raise ValueError("OpenAI API key not set. Call setup_openai_api() first.")

    # Validate inputs
    if not case_citation or not case_citation.strip():
        raise ValueError("Case citation cannot be empty")

    if not model or not model.strip():
        raise ValueError("Model name cannot be empty")

    # Create the prompt
    prompt = f"""
    Please provide a comprehensive summary of the legal case: {case_citation}
    
    Include the following information if available:
    - Court and date
    - Key facts
    - Legal issues
    - Holding/ruling
    - Legal principles established
    - Significance of the case
    
    If this is not a real case or you don't have information about it, please provide a summary based on what you know about similar cases or legal principles that might apply to a case with this name.
    """

    # Maximum retry attempts
    max_retries = 3
    retry_delay = 2  # seconds
    last_error = None

    for attempt in range(max_retries):
        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal expert specializing in case law summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            # Validate response
            if not response or not hasattr(response, "choices") or not response.choices:
                raise ValueError(
                    "Invalid response from OpenAI API: No choices returned"
                )

            if (
                not hasattr(response.choices[0], "message")
                or not response.choices[0].message
            ):
                raise ValueError(
                    "Invalid response from OpenAI API: No message in first choice"
                )

            if not hasattr(response.choices[0].message, "content"):
                raise ValueError(
                    "Invalid response from OpenAI API: No content in message"
                )

            # Extract and return the summary
            summary = response.choices[0].message.content.strip()

            if not summary:
                raise ValueError("Empty summary returned from OpenAI API")

            return summary

        except openai.error.RateLimitError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                print(
                    f"Rate limit exceeded. Waiting {wait_time} seconds before retrying..."
                )
                time.sleep(wait_time)
            else:
                print(f"Rate limit exceeded after {max_retries} attempts.")
                raise RuntimeError(
                    f"Failed to generate summary due to rate limits: {str(e)}"
                ) from e

        except openai.error.AuthenticationError as e:
            print(f"Authentication error: {str(e)}")
            raise ValueError(f"OpenAI API authentication failed: {str(e)}") from e

        except openai.error.InvalidRequestError as e:
            print(f"Invalid request: {str(e)}")
            raise ValueError(f"Invalid request to OpenAI API: {str(e)}") from e

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                print(
                    f"Error calling OpenAI API: {str(e)}. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            else:
                print(f"Failed to generate summary after {max_retries} attempts")
                raise RuntimeError(
                    f"Failed to generate summary after {max_retries} attempts: {str(e)}"
                ) from e

    # This should never be reached due to the raise in the loop, but just in case
    if last_error:
        raise RuntimeError(
            f"Failed to generate summary: {str(last_error)}"
        ) from last_error
    else:
        raise RuntimeError("Failed to generate summary for unknown reasons")
