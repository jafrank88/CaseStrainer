#!/usr/bin/env python3
"""
Test script to check what canonical case names the citation-lookup API returns
for extracted citations from the PDF.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from process_wa_briefs import extract_citations_from_pdf, verify_citation_with_courtlistener
import requests
import json
import time

def get_canonical_case_name(citation):
    """Get canonical case name from citation-lookup API"""
    try:
        url = "https://cite.case.law/api/v1/citations/"
        params = {"cite": citation}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                # Get the first result
                result = data['results'][0]
                return result.get('name', 'Unknown')
        return None
    except Exception as e:
        print(f"Error getting canonical name for {citation}: {e}")
        return None

def main():
    # Test with the PDF file
    pdf_path = "1028814.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print("Extracting citations from PDF...")
    
    # Extract citations using the process_wa_briefs pipeline
    citations_data = extract_citations_from_pdf(pdf_path)
    
    if not citations_data:
        print("No citations found in PDF")
        return
    
    print(f"\nFound {len(citations_data)} citations")
    print("\n" + "="*80)
    print("CITATION ANALYSIS")
    print("="*80)
    
    # Test first 10 citations
    for i, citation_info in enumerate(citations_data[:10]):
        citation = citation_info['citation_text']
        context = citation_info.get('context', '')
        
        print(f"\n{i+1}. Citation: {citation}")
        print(f"   Context: {context[:100]}...")
        
        # Get canonical name from citation-lookup API
        print("   Getting canonical name from citation-lookup API...")
        canonical_name = get_canonical_case_name(citation)
        
        if canonical_name:
            print(f"   Canonical name: {canonical_name}")
        else:
            print(f"   No canonical name found")
        
        # Also try CourtListener API
        print("   Trying CourtListener API...")
        try:
            citation_dict = {"citation_text": citation}
            courtlistener_result = verify_citation_with_courtlistener(citation_dict)
            if courtlistener_result and courtlistener_result.get('case_name'):
                print(f"   CourtListener name: {courtlistener_result['case_name']}")
            else:
                print(f"   CourtListener: No case name found")
        except Exception as e:
            print(f"   CourtListener error: {e}")
        
        print("-" * 60)
        time.sleep(1)  # Be nice to the APIs

if __name__ == "__main__":
    main() 