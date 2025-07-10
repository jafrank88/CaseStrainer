#!/usr/bin/env python3
"""
Test script to verify that the frontend shows both extracted and canonical names/dates
when they differ (e.g., "Doe v. Wdae (1901)" vs canonical "Doe v. Wade (1973)")
"""

import requests
import json
import time

def test_fake_extraction():
    """Test that the API returns both extracted and canonical fields when they differ"""
    
    # Test data with intentionally wrong extracted name/date
    test_data = {
        "text": """
        The court considered the case of Doe v. Wdae (1901) in determining the outcome.
        This case established important precedent for privacy rights.
        """,
        "document_type": "legal_brief"
    }
    
    print("Testing API with fake extraction data...")
    print(f"Input text: {test_data['text'].strip()}")
    print()
    
    try:
        # Make API call
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze_enhanced",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print()
            
            # Check if we have citations
            if "citations" in result and result["citations"]:
                print(f"Found {len(result['citations'])} citations:")
                print()
                
                for i, citation in enumerate(result["citations"], 1):
                    print(f"Citation {i}:")
                    print(f"  Citation text: {citation.get('citation', 'N/A')}")
                    print(f"  Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"  Extracted date: {citation.get('extracted_date', 'N/A')}")
                    print(f"  Canonical case name: {citation.get('canonical_name', 'N/A')}")
                    print(f"  Canonical date: {citation.get('canonical_date', 'N/A')}")
                    print(f"  Verified: {citation.get('verified', 'N/A')}")
                    print(f"  Error: {citation.get('error', 'N/A')}")
                    print()
                    
                    # Verify that extracted fields are present
                    extracted_name = citation.get('extracted_case_name', 'N/A')
                    extracted_date = citation.get('extracted_date', 'N/A')
                    
                    if extracted_name != 'N/A' and extracted_name:
                        print(f"✅ Extracted case name is present: '{extracted_name}'")
                    else:
                        print(f"❌ Extracted case name is missing or 'N/A'")
                        
                    if extracted_date != 'N/A' and extracted_date:
                        print(f"✅ Extracted date is present: '{extracted_date}'")
                    else:
                        print(f"❌ Extracted date is missing or 'N/A'")
                        
                    print()
            else:
                print("❌ No citations found in response")
                print(f"Response keys: {list(result.keys())}")
                if "error" in result:
                    print(f"Error: {result['error']}")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on localhost:5000?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fake_extraction() 