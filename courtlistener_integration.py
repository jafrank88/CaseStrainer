#!/usr/bin/env python3
"""
CourtListener API integration for CaseStrainer

This module provides functions to check citations and generate case summaries using the CourtListener API.
"""

import os
import json
import time
import requests
from typing import Optional, Dict, Any, List, Tuple

# Flag to track if CourtListener API is available
COURTLISTENER_AVAILABLE = True

def setup_courtlistener_api(api_key: Optional[str] = None) -> bool:
    """
    Set up the CourtListener API with the provided key or from environment variable.
    
    Args:
        api_key: CourtListener API key. If None, will try to get from COURTLISTENER_API_KEY environment variable.
    
    Returns:
        bool: True if setup was successful, False otherwise.
    """
    global COURTLISTENER_AVAILABLE
    
    try:
        # Get API key from parameter or environment variable
        key = api_key or os.environ.get("COURTLISTENER_API_KEY")
        if not key:
            print("Warning: CourtListener API key not provided and COURTLISTENER_API_KEY environment variable not set.")
            print("CourtListener API will be used in limited mode (rate-limited).")
            return True  # CourtListener allows some requests without API key
        
        # Store the API key in an environment variable for later use
        os.environ["COURTLISTENER_API_KEY"] = key
        
        # Test the API connection with a minimal request
        try:
            # Make a minimal API call to verify connectivity
            response = requests.get("https://www.courtlistener.com/api/rest/v4/", 
                                   headers={"Authorization": f"Token {key}"})
            
            if response.status_code == 200:
                print("CourtListener API connection successful.")
                COURTLISTENER_AVAILABLE = True
                return True
            else:
                print(f"Error testing CourtListener API connection: Status code {response.status_code}")
                print(f"Response: {response.text}")
                COURTLISTENER_AVAILABLE = False
                return False
        except Exception as e:
            print(f"Error testing CourtListener API connection: {str(e)}")
            COURTLISTENER_AVAILABLE = False
            return False
    except Exception as e:
        print(f"Error setting up CourtListener API: {str(e)}")
        COURTLISTENER_AVAILABLE = False
        return False

def search_citation(citation: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Search for a case citation in the CourtListener API.
    
    Args:
        citation: The case citation to search for.
    
    Returns:
        Tuple[bool, Optional[Dict]]: A tuple containing:
            - bool: True if the citation exists, False otherwise.
            - Optional[Dict]: Case data if found, None otherwise.
    """
    if not citation or not citation.strip():
        print("Error: Citation cannot be empty")
        return False, None
    
    try:
        # Prepare the API request
        api_key = os.environ.get("COURTLISTENER_API_KEY")
        headers = {"Authorization": f"Token {api_key}"} if api_key else {}
        
        # First try to search by citation
        params = {
            "cite": citation,
            "format": "json"
        }
        
        response = requests.get(
            "https://www.courtlistener.com/api/rest/v4/search/",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("count", 0) > 0:
                # Found at least one matching case
                return True, data.get("results", [{}])[0]
            
            # If no results by citation, try searching by case name
            params = {
                "q": citation,
                "type": "o",  # opinions
                "format": "json"
            }
            
            response = requests.get(
                "https://www.courtlistener.com/api/rest/v4/search/",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("count", 0) > 0:
                    # Found at least one matching case
                    return True, data.get("results", [{}])[0]
            
            # No results found
            return False, None
        else:
            print(f"Error searching CourtListener API: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"Error searching CourtListener API: {str(e)}")
        return False, None

def get_case_details(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a case from the CourtListener API.
    
    Args:
        case_id: The CourtListener ID of the case.
    
    Returns:
        Optional[Dict]: Case details if found, None otherwise.
    """
    if not case_id:
        print("Error: Case ID cannot be empty")
        return None
    
    try:
        # Prepare the API request
        api_key = os.environ.get("COURTLISTENER_API_KEY")
        headers = {"Authorization": f"Token {api_key}"} if api_key else {}
        
        response = requests.get(
            f"https://www.courtlistener.com/api/rest/v4/opinions/{case_id}/",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting case details from CourtListener API: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting case details from CourtListener API: {str(e)}")
        return None

def generate_case_summary_from_courtlistener(citation: str) -> str:
    """
    Generate a summary of a legal case using the CourtListener API.
    
    Args:
        citation: The case citation to summarize.
    
    Returns:
        str: A summary of the case, or an error message if the case was not found.
    """
    if not COURTLISTENER_AVAILABLE:
        return f"CourtListener API is not available. Cannot generate summary for {citation}."
    
    try:
        # Search for the citation
        exists, case_data = search_citation(citation)
        
        if not exists or not case_data:
            return f"Case citation '{citation}' not found in CourtListener database."
        
        # Get more detailed information if we have a case ID
        case_id = case_data.get("id")
        if case_id:
            details = get_case_details(case_id)
            if details:
                case_data = details
        
        # Extract relevant information for the summary
        case_name = case_data.get("case_name", "Unknown case name")
        court = case_data.get("court_name", "Unknown court")
        date_filed = case_data.get("date_filed", "Unknown date")
        docket_number = case_data.get("docket_number", "Unknown docket number")
        citation_string = case_data.get("citation", citation)
        
        # Extract the opinion text
        opinion_text = case_data.get("plain_text", "")
        
        # Create a summary
        summary = f"""
        Case Summary: {case_name}
        
        Citation: {citation_string}
        Court: {court}
        Date Filed: {date_filed}
        Docket Number: {docket_number}
        
        """
        
        # Add a brief excerpt from the opinion if available
        if opinion_text:
            # Get the first 500 characters as a preview
            preview = opinion_text[:500].strip()
            if len(opinion_text) > 500:
                preview += "..."
            
            summary += f"""
            Opinion Excerpt:
            {preview}
            
            Full opinion available at: https://www.courtlistener.com/opinion/{case_id}/
            """
        
        return summary
    except Exception as e:
        print(f"Error generating summary from CourtListener: {str(e)}")
        return f"Error generating summary for {citation}: {str(e)}"

def check_citation_exists(citation: str) -> bool:
    """
    Check if a citation exists in the CourtListener database.
    
    Args:
        citation: The case citation to check.
    
    Returns:
        bool: True if the citation exists, False otherwise.
    """
    if not COURTLISTENER_AVAILABLE:
        print("CourtListener API is not available. Cannot check citation.")
        return True  # Default to assuming it exists if we can't check
    
    try:
        exists, _ = search_citation(citation)
        return exists
    except Exception as e:
        print(f"Error checking citation with CourtListener: {str(e)}")
        return True  # Default to assuming it exists if there's an error
