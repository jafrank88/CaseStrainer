#!/usr/bin/env python3
"""
Test to check format mismatch between backend and frontend
"""

import requests
import json

def test_format_mismatch():
    """Test the exact format being sent vs expected"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test data
    test_data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions",
        "citations": ["200 Wn.2d 72, 514 P.3d 643"]
    }
    
    print("🔍 TESTING FORMAT MISMATCH...")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Backend Response Structure:")
            print(json.dumps(result, indent=2))
            
            if 'citations' in result and result['citations']:
                citation = result['citations'][0]
                
                print("\n🔍 FRONTEND EXPECTATIONS vs BACKEND REALITY:")
                print()
                
                # Check what frontend expects vs what backend sends
                frontend_expectations = {
                    'extracted_case_name': 'string (not null, not "N/A")',
                    'extracted_date': 'string (not null, not "")',
                    'canonical_name': 'string (not null, not "N/A")',
                    'canonical_date': 'string (not null, not "N/A")',
                    'verified': 'string ("true"/"false") or boolean',
                    'citation': 'string',
                    'source': 'string'
                }
                
                backend_reality = {
                    'extracted_case_name': f"'{citation.get('extracted_case_name', 'NOT_FOUND')}' (type: {type(citation.get('extracted_case_name'))})",
                    'extracted_date': f"'{citation.get('extracted_date', 'NOT_FOUND')}' (type: {type(citation.get('extracted_date'))})",
                    'canonical_name': f"'{citation.get('canonical_name', 'NOT_FOUND')}' (type: {type(citation.get('canonical_name'))})",
                    'canonical_date': f"'{citation.get('canonical_date', 'NOT_FOUND')}' (type: {type(citation.get('canonical_date'))})",
                    'verified': f"'{citation.get('verified', 'NOT_FOUND')}' (type: {type(citation.get('verified'))})",
                    'citation': f"'{citation.get('citation', 'NOT_FOUND')}' (type: {type(citation.get('citation'))})",
                    'source': f"'{citation.get('source', 'NOT_FOUND')}' (type: {type(citation.get('source'))})"
                }
                
                print("📋 FIELD COMPARISON:")
                for field, expectation in frontend_expectations.items():
                    reality = backend_reality[field]
                    print(f"  {field}:")
                    print(f"    Frontend expects: {expectation}")
                    print(f"    Backend sends: {reality}")
                    
                    # Check if there's a mismatch
                    if field in citation:
                        value = citation[field]
                        if field in ['extracted_case_name', 'extracted_date']:
                            if value in [None, '', 'N/A']:
                                print(f"    ❌ MISMATCH: Frontend expects non-empty value, got '{value}'")
                            else:
                                print(f"    ✅ MATCH: Frontend should display this")
                        elif field == 'verified':
                            if value in ['true', True]:
                                print(f"    ✅ MATCH: Citation is verified")
                            else:
                                print(f"    ✅ MATCH: Citation is not verified")
                    else:
                        print(f"    ❌ MISMATCH: Field missing from backend response")
                    print()
                
                # Check Vue component logic
                print("🔍 VUE COMPONENT LOGIC ANALYSIS:")
                extracted_name = citation.get('extracted_case_name')
                extracted_date = citation.get('extracted_date')
                
                print(f"getExtractedCaseName() returns: '{extracted_name}'")
                print(f"getExtractedDate() returns: '{extracted_date}'")
                
                # Check the Vue template conditions
                print(f"\nVue template conditions:")
                print(f"v-if=\"getExtractedCaseName(citation)\": {bool(extracted_name and extracted_name != 'N/A')}")
                print(f"v-if=\"getExtractedDate(citation)\": {bool(extracted_date and extracted_date != 'N/A')}")
                print(f"v-if=\"getExtractedCaseName(citation) || getExtractedDate(citation)\": {bool((extracted_name and extracted_name != 'N/A') or (extracted_date and extracted_date != 'N/A'))}")
                
                # Check if the section will be displayed
                will_display = bool((extracted_name and extracted_name != 'N/A') or (extracted_date and extracted_date != 'N/A'))
                print(f"\n🎯 RESULT: Extracted info section will {'✅ DISPLAY' if will_display else '❌ NOT DISPLAY'}")
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_format_mismatch() 