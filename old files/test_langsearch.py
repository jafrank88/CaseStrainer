#!/usr/bin/env python3
"""
Test script for LangSearch API integration.
"""

import os
import sys
from langsearch_integration import setup_langsearch_api, generate_case_summary_with_langsearch_api

def main():
    """Test the LangSearch API integration."""
    # Get API key from environment variable or command line
    api_key = os.environ.get('LANGSEARCH_API_KEY')
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("Error: No LangSearch API key provided.")
        print("Usage: python test_langsearch.py <api_key>")
        print("Or set the LANGSEARCH_API_KEY environment variable.")
        return 1
    
    # Initialize the API
    print("Setting up LangSearch API...")
    success = setup_langsearch_api(api_key)
    if not success:
        print("Failed to set up LangSearch API.")
        return 1
    
    # Test case citation
    test_citation = "Smith v. Jones, 123 F.3d 456 (9th Cir. 1997)"
    print(f"Testing LangSearch API with citation: {test_citation}")
    
    try:
        # Generate summary directly using LangSearch API
        print("Generating summary directly using LangSearch API...")
        summary = generate_case_summary_with_langsearch_api(test_citation)
        print("\nSummary generated successfully:")
        print("=" * 80)
        print(summary)
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
