#!/usr/bin/env python3
"""Find a working Washington State case PDF from CourtListener"""

import requests

def find_washington_pdf():
    """Find a recent Washington Supreme Court case PDF"""
    
    # Search for recent Washington cases with PDFs
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    params = {
        'q': 'court:"wash" AND type:opinion',
        'order_by': 'date_desc',
        'page_size': 20
    }
    
    print("Searching for Washington Supreme Court cases...")
    try:
        response = requests.get(search_url, params=params, timeout=30)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Results keys: {list(results.keys())}")
            cases = results.get('results', [])
            
            print(f"Found {len(cases)} cases")
            
            for i, case in enumerate(cases[:10], 1):
                name = case.get('case_name', 'N/A')
                date = case.get('date_filed', 'N/A')
                citation = case.get('citation', 'N/A')
                pdf_url = case.get('local_path', '')
                
                print(f"\n{i}. {name}")
                print(f"   Date: {date}")
                print(f"   Citation: {citation}")
                print(f"   PDF: {pdf_url}")
                
                if pdf_url and pdf_url.endswith('.pdf'):
                    # Test if the PDF is accessible
                    try:
                        head_response = requests.head(pdf_url, timeout=10)
                        if head_response.status_code == 200:
                            print(f"   Status: WORKING!")
                            return pdf_url
                        else:
                            print(f"   Status: {head_response.status_code}")
                    except Exception as e:
                        print(f"   Error: {e}")
        
    except Exception as e:
        print(f"Error searching CourtListener: {e}")
    
    return None

if __name__ == "__main__":
    pdf_url = find_washington_pdf()
    if pdf_url:
        print(f"\nUse this URL for testing: {pdf_url}")
    else:
        print("\nNo working PDF found")
