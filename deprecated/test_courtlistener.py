#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for CourtListener API integration.

This script tests the citation validation functionality using the CourtListener API.
It requires the COURTLISTENER_API_KEY environment variable to be set.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# API configuration
API_BASE_URL = 'https://www.courtlistener.com/api/rest/v4'
API_ENDPOINT = '/citation-lookup/'
API_KEY = os.getenv('COURTLISTENER_API_KEY')

if not API_KEY:
    logger.error("COURTLISTENER_API_KEY environment variable is not set")
    logger.info("Please set the COURTLISTENER_API_KEY in your .env file or environment variables")
    sys.exit(1)

def check_courtlistener_api(citation_text):
    """
    Check a citation against the CourtListener API.
    
    Args:
        citation_text (str): The citation text to validate
        
    Returns:
        dict: API response or error information
    """
    headers = {
        'Authorization': f'Token {API_KEY}',
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer/1.0 (https://github.com/jafrank88/CaseStrainer)'
    }
    
    payload = {
        'text': citation_text,
        'type': 'citation',
        'return_models': True
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{API_ENDPOINT}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        # Ensure we always return a dictionary with consistent structure
        if isinstance(data, list):
            return {
                'status': 'success',
                'results': data,
                'count': len(data)
            }
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            try:
                logger.error(f"Response body: {e.response.text}")
            except:
                pass
        return {
            'error': str(e),
            'status': 'error',
            'details': {
                'type': type(e).__name__,
                'message': str(e)
            }
        }

def format_citation_result(item):
    """Format a single citation result for display."""
    # Extract basic information
    citation = item.get('citation', 'N/A')
    status = item.get('status', 'N/A')
    
    # Build the result string
    result = f"Citation: {citation} (Status: {status})\n"
    
    # Add case name if available
    if 'case_name' in item and item['case_name']:
        result += f"Case: {item['case_name']}\n"
    
    # Add court information if available
    if 'court' in item and item['court']:
        result += f"Court: {item['court']}\n"
    
    # Add docket number if available
    if 'docket_number' in item and item['docket_number']:
        result += f"Docket: {item['docket_number']}\n"
    
    # Add decision date if available
    if 'decision_date' in item and item['decision_date']:
        result += f"Date: {item['decision_date']}\n"
    
    # Add URL if available
    if 'absolute_url' in item and item['absolute_url']:
        result += f"URL: https://www.courtlistener.com{item['absolute_url']}"
    
    return result

def main():
    """Main function to test the API."""
    test_citations = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483",  # Brown v. Board of Education
        "163 U.S. 537",  # Plessy v. Ferguson
        "5 U.S. 137"     # Marbury v. Madison
    ]
    
    print("\n" + "="*80)
    print("COURTLISTENER API CITATION VALIDATION TEST")
    print("="*80 + "\n")
    
    for citation in test_citations:
        print(f"\n{'='*80}")
        print(f"TESTING CITATION: {citation}")
        print("-"*80)
        
        # Make the API request
        result = check_courtlistener_api(citation)
        
        # Handle errors
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            if 'details' in result:
                print(f"Details: {result['details']}")
            continue
        
        # Process successful response
        if 'results' in result and result['results']:
            print(f"✅ Found {len(result['results'])} result(s):\n")
            for i, item in enumerate(result['results'], 1):
                print(f"Result {i}:")
                print("-" * 40)
                print(format_citation_result(item))
                print()
        else:
            print("ℹ️  No results found for this citation.")
        
        # Print search link for manual verification
        search_url = f"https://www.courtlistener.com/?q={citation.replace(' ', '+')}&type=o&order_by=score+desc"
        print(f"\n🔍 View in browser: {search_url}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)
    print("\nAPI Documentation: https://www.courtlistener.com/api/rest-info/#citation-lookup")

if __name__ == "__main__":
    main()
