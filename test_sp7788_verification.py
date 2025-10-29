#!/usr/bin/env python3
"""
Test script to verify the reporter-first verification is working with sp-7788.pdf
"""

import requests
import json
import time
import os

def test_sp7788_verification():
    """Test reporter-first verification with the sp-7788.pdf file"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("Testing reporter-first verification with sp-7788.pdf...")
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Prepare the request
        request_data = {
            "client_request_id": f"test_sp7788_{int(time.time())}"
        }
        
        files = {
            'file': ('sp-7788.pdf', pdf_content, 'application/pdf')
        }
        
        print(f"Request ID: {request_data['client_request_id']}")
        print(f"PDF size: {len(pdf_content)} bytes")
        
        # Send request to the API
        response = requests.post(
            'https://wolf.law.uw.edu/casestrainer/api/analyze?debug=1',
            data=request_data,
            files=files,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"\nFound {len(citations)} citations:")
            
            # Check for citations with missing/invalid case names
            problematic_citations = []
            for citation in citations:
                extracted_name = citation.get('extracted_case_name', 'N/A')
                if not extracted_name or extracted_name == "N/A" or len(extracted_name.strip()) < 3:
                    problematic_citations.append(citation)
            
            print(f"\nFound {len(problematic_citations)} citations with missing/invalid case names:")
            
            for i, citation in enumerate(problematic_citations[:10]):  # Show first 10
                citation_text = citation.get('citation', 'Unknown')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', None)
                canonical_date = citation.get('canonical_date', None)
                verified = citation.get('verified', False)
                source = citation.get('verification_source', None)
                
                print(f"\n{i+1}. Citation: {citation_text}")
                print(f"   Extracted name: '{extracted_name}'")
                print(f"   Canonical name: {canonical_name}")
                print(f"   Canonical date: {canonical_date}")
                print(f"   Verified: {verified}")
                print(f"   Source: {source}")
                
                # Check if reporter-first verification worked
                if canonical_name and canonical_date and verified and source and "reporter-first" in source.lower():
                    print("   ✅ SUCCESS: Reporter-first verification worked!")
                elif canonical_name and verified:
                    print("   ⚠️  Verified by another source (not reporter-first)")
                else:
                    print("   ❌ FAILED: No verification obtained")
            
            if len(problematic_citations) > 10:
                print(f"\n... and {len(problematic_citations) - 10} more citations with missing case names")
                
            # Summary
            verified_count = sum(1 for c in citations if c.get('verified', False))
            reporter_first_count = sum(1 for c in citations if c.get('verification_source', '').lower().find('reporter-first') != -1)
            
            print(f"\n=== SUMMARY ===")
            print(f"Total citations: {len(citations)}")
            print(f"Citations with missing case names: {len(problematic_citations)}")
            print(f"Verified citations: {verified_count}")
            print(f"Verified via reporter-first: {reporter_first_count}")
            
            if reporter_first_count > 0:
                print("✅ Reporter-first verification is working!")
            else:
                print("❌ Reporter-first verification is not working")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sp7788_verification()
