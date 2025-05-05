#!/usr/bin/env python3
"""
LangSearch API integration for CaseStrainer

This module provides functions to generate case summaries using the LangSearch API.
"""

import os
import time
import requests
from typing import Optional

# Flag to track if LangSearch API is available
LANGSEARCH_AVAILABLE = True

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
            print("Error: LangSearch API key not provided and LANGSEARCH_API_KEY environment variable not set.")
            return False
        
        # Validate API key format (basic check)
        if not key.startswith('sk-'):
            print("Warning: API key format doesn't match expected pattern. Key should start with 'sk-'.")
        
        # Store the API key in an environment variable for later use
        os.environ["LANGSEARCH_API_KEY"] = key
        
        # Test the API connection with a minimal request
        try:
            # Make a minimal API call to verify the key works
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                "https://api.langsearch.ai/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("LangSearch API connection successful.")
                return True
            else:
                print(f"Error testing LangSearch API connection: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error testing LangSearch API connection: {str(e)}")
            return False
    except Exception as e:
        print(f"Error setting up LangSearch API: {str(e)}")
        return False

def generate_case_summary_with_langsearch(case_citation: str, model: str = "gpt-4") -> str:
    """
    Generate a summary of a legal case using LangSearch API.
    
    Args:
        case_citation: The case citation to summarize.
        model: The model to use (default: gpt-4).
    
    Returns:
        str: A summary of the case.
        
    Raises:
        ValueError: If the API key is not set or if parameters are invalid.
        RuntimeError: If the API call fails after multiple retries.
    """
    # Check if API key is set
    api_key = os.environ.get("LANGSEARCH_API_KEY")
    if not api_key:
        raise ValueError("LangSearch API key not set. Call setup_langsearch_api() first.")
    
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
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a legal expert specializing in case law summaries."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Call the LangSearch API
            response = requests.post(
                "https://api.langsearch.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                response_data = response.json()
                
                # Validate response structure
                if not response_data or "choices" not in response_data or not response_data["choices"]:
                    raise ValueError("Invalid response from LangSearch API: No choices returned")
                
                if "message" not in response_data["choices"][0] or not response_data["choices"][0]["message"]:
                    raise ValueError("Invalid response from LangSearch API: No message in first choice")
                
                if "content" not in response_data["choices"][0]["message"]:
                    raise ValueError("Invalid response from LangSearch API: No content in message")
                
                # Extract and return the summary
                summary = response_data["choices"][0]["message"]["content"].strip()
                
                if not summary:
                    raise ValueError("Empty summary returned from LangSearch API")
                
                return summary
            elif response.status_code == 429:  # Too Many Requests
                last_error = f"Rate limit exceeded: {response.text}"
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit exceeded. Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    print(f"Rate limit exceeded after {max_retries} attempts.")
                    raise RuntimeError(f"Failed to generate summary due to rate limits: {response.text}")
            elif response.status_code == 401:  # Unauthorized
                print(f"Authentication error: {response.text}")
                raise ValueError(f"LangSearch API authentication failed: {response.text}")
            elif response.status_code == 400:  # Bad Request
                print(f"Invalid request: {response.text}")
                raise ValueError(f"Invalid request to LangSearch API: {response.text}")
            else:
                last_error = f"API error (status code {response.status_code}): {response.text}"
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"API error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"API error after {max_retries} attempts.")
                    raise RuntimeError(f"Failed to generate summary: API error (status code {response.status_code}): {response.text}")
        except requests.exceptions.Timeout:
            last_error = "Request timed out"
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Request timed out after {max_retries} attempts.")
                raise RuntimeError(f"Failed to generate summary: Request timed out after {max_retries} attempts")
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"Request error: {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Request error after {max_retries} attempts.")
                raise RuntimeError(f"Failed to generate summary: Request error: {str(e)}")
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"Error calling LangSearch API: {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to generate summary after {max_retries} attempts")
                raise RuntimeError(f"Failed to generate summary after {max_retries} attempts: {str(e)}")
    
    # This should never be reached due to the raise in the loop, but just in case
    if last_error:
        raise RuntimeError(f"Failed to generate summary: {last_error}")
    else:
        raise RuntimeError("Failed to generate summary for unknown reasons")
