#!/usr/bin/env python3
"""
Test the CaseStrainer API with simple text that should definitely work
"""

import requests
import json

def test_simple_api():
    """Test the CaseStrainer API with simple text containing obvious citations"""
    
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016) that standing requirements cannot be erased.'
    
    print("SIMPLE API TEST")
    print("=" * 50)
    print(f"Text: {text}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "text", "text": text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations:")
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', 'N/A')
                verified = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                
                print(f"{i}. {citation_text}")
                print(f"   case_name: '{case_name}'")
                print(f"   extracted_case_name: '{extracted_case_name}'")
                print(f"   cluster_case_name: '{cluster_case_name}'")
                print(f"   canonical_name: '{canonical_name}'")
                print(f"   verified: {verified}")
                print(f"   true_by_parallel: {true_by_parallel}")
                
                # Check if the issue is field mapping
                if case_name == 'N/A' and extracted_case_name != 'N/A':
                    print(f"   ISSUE: case_name is N/A but extracted_case_name is '{extracted_case_name}'")
                elif case_name != 'N/A' and extracted_case_name == 'N/A':
                    print(f"   ISSUE: extracted_case_name is N/A but case_name is '{case_name}'")
                elif case_name == extracted_case_name and case_name != 'N/A':
                    print(f"   OK: Both fields match and are not N/A")
                else:
                    print(f"   ISSUE: Both fields are N/A or don't match")
                print()
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_simple_api()
