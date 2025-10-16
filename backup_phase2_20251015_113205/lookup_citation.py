#!/usr/bin/env python3
"""
Look up a citation using the CourtListener API v4.
"""

import os
import requests
import json
from typing import Dict, Optional

def lookup_citation(citation: str) -> Optional[Dict]:
    """Look up a citation using the CourtListener API v4."""
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # Try to get API key from environment or use hardcoded one for testing
    api_key = os.getenv('COURTLISTENER_API_KEY') or "***REDACTED_COURTLISTENER_KEY***"
    if not api_key:
        print("Error: No API key available")
        return None
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"citation": citation},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error looking up citation: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None

def format_case_info(api_response: Dict) -> str:
    """Format the case information from the API response."""
    if not api_response or 'count' not in api_response or api_response['count'] == 0:
        return "No results found for this citation."
    
    result = []
    
    for item in api_response.get('results', [])[:3]:  # Show top 3 results
        cluster = item.get('cluster', {})
        case_name = cluster.get('case_name', 'Unknown')
        citation = cluster.get('citation', 'N/A')
        docket_number = cluster.get('docket_number', 'N/A')
        court = cluster.get('court', 'N/A')
        date_filed = cluster.get('date_filed', 'N/A')
        
        result.append(
            f"Case Name: {case_name}\n"
            f"Citation: {citation}\n"
            f"Docket Number: {docket_number}\n"
            f"Court: {court}\n"
            f"Date Filed: {date_filed}\n"
            "-" * 80
        )
    
    return "\n".join(result)

def main():
    # Try to get API key from environment
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if not api_key:
        print("Error: COURTLISTENER_API_KEY environment variable not found.")
        print("Please set the environment variable and try again.")
        return
        
    citation = "195 Wn.2d 742"
    print(f"Looking up citation: {citation}")
    print(f"Using API key: {api_key[:4]}...{api_key[-4:] if api_key else ''}\n")
    
    result = lookup_citation(citation)
    
    if result:
        print("=== Citation Lookup Results ===\n")
        print(format_case_info(result))
        
        # Save full response to file
        with open('citation_lookup_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nFull results saved to citation_lookup_result.json")
    else:
        print("Failed to look up citation.")

if __name__ == "__main__":
    main()
