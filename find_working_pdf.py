#!/usr/bin/env python3
"""Try to find a working Washington State Courts PDF URL"""

import requests
import re

def try_known_urls():
    """Try some known Washington State Courts PDF URLs"""
    
    # Test URLs based on common patterns
    test_urls = [
        "https://www.courts.wa.gov/opinions/pdf/D1_20250105_20250105.pdf",
        "https://www.courts.wa.gov/opinions/pdf/98000-2-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/87500-9-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/86500-7-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/85500-5-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/84500-3-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/83500-1-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/82500-9-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/81500-7-I.pdf",
        "https://www.courts.wa.gov/opinions/pdf/80500-5-I.pdf",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            response = requests.head(url, timeout=10, verify=False)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"  Content-Length: {response.headers.get('Content-Length', 'N/A')}")
                print("  WORKING!")
                return url
            else:
                print("  Not accessible")
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def search_for_pdfs():
    """Search for PDFs using CourtListener API"""
    
    # Search for recent Washington Supreme Court cases
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    params = {
        'q': 'court:"wash" AND type:opinion',
        'order_by': 'date_desc',
        'page_size': 10
    }
    
    print("\nSearching CourtListener for recent Washington cases...")
    try:
        response = requests.get(search_url, params=params, timeout=30)
        if response.status_code == 200:
            results = response.json()
            cases = results.get('results', [])
            
            print(f"Found {len(cases)} recent cases:")
            for i, case in enumerate(cases[:5], 1):
                print(f"  {i}. {case.get('case_name', 'N/A')} ({case.get('date_filed', 'N/A')})")
                if case.get('local_path'):
                    print(f"     PDF: {case['local_path']}")
            
            # Return the first case with a PDF
            for case in cases:
                if case.get('local_path') and case.get('local_path').endswith('.pdf'):
                    return case['local_path']
        
    except Exception as e:
        print(f"Error searching CourtListener: {e}")
    
    return None

if __name__ == "__main__":
    # Try known URLs first
    working_url = try_known_urls()
    
    if not working_url:
        # Search CourtListener
        working_url = search_for_pdfs()
    
    if working_url:
        print(f"\nFound working URL: {working_url}")
    else:
        print("\nNo working URL found")
