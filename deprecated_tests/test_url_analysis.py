#!/usr/bin/env python
"""
Test script to verify URL analysis functionality in CaseStrainer.
"""
import sys
import os
import json
import requests
from urllib.parse import urljoin

def test_url_analysis(url, base_url="http://localhost:5000"):
    """
    Test the URL analysis endpoint with a given URL.
    
    Args:
        url (str): The URL to analyze
        base_url (str): Base URL of the CaseStrainer API
        
    Returns:
        dict: Analysis results
    """
    endpoint = urljoin(base_url, "/casestrainer/api/analyze")
    print(f"Testing URL analysis for: {url}")
    print(f"Sending request to: {endpoint}")
    
    try:
        # Prepare the request data
        data = {
            "citation": url,  # The endpoint expects 'citation' field for the URL
            "options": {
                "return_debug": True,
                "is_url": True  # Indicate this is a URL to be fetched
            }
        }
        
        # Make the request
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Print the response
        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print("Response JSON:")
            print(json.dumps(result, indent=2))
            return result
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response.text[:1000]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def main():
    # Default test URLs (can be overridden via command line)
    test_urls = [
        "https://supreme.justia.com/cases/federal/us/347/483/",  # Brown v. Board of Education
        "https://www.supremecourt.gov/opinions/22pdf/21-1476_8n59.pdf",  # Recent SCOTUS opinion (PDF)
        "https://www.law.cornell.edu/supct/html/02-1020.ZS.html"  # Lawrence v. Texas
    ]
    
    # Get base URL from command line or use default
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Run tests
    for i, url in enumerate(test_urls, 1):
        print(f"\n=== Test {i}: {url} ===")
        result = test_url_analysis(url, base_url)
        
        # Print summary
        if result and "citations" in result:
            print(f"\nFound {len(result['citations'])} citations in {url}")
            if result["citations"]:
                print("Sample citation:", result["citations"][0])

if __name__ == "__main__":
    main()
