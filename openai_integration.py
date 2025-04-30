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
    """
    if not OPENAI_AVAILABLE:
        return False
    
    # Get API key from parameter or environment variable
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        print("Error: OpenAI API key not provided and OPENAI_API_KEY environment variable not set.")
        return False
    
    # Set up the client
    openai.api_key = key
    return True

def generate_case_summary_with_openai(case_citation: str, model: str = "gpt-4") -> str:
    """
    Generate a summary of a legal case using OpenAI API.
    
    Args:
        case_citation: The case citation to summarize.
        model: The OpenAI model to use (default: gpt-4).
    
    Returns:
        str: A summary of the case.
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package is not available. Please install it using: pip install openai")
    
    # Check if API key is set
    if not openai.api_key:
        raise ValueError("OpenAI API key not set. Call setup_openai_api() first.")
    
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
    
    for attempt in range(max_retries):
        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a legal expert specializing in case law summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract and return the summary
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error calling OpenAI API: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to generate summary after {max_retries} attempts: {e}")
                raise
