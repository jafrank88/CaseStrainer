#!/usr/bin/env python3
"""
Fast test with only valid citations to verify the system works quickly.
"""

import requests
import json
import time

def test_fast_valid_citations():
    """Test only valid citations to ensure fast processing."""
    
    print("=== Fast Test with Valid Citations Only ===")
    
    # Test cases with ONLY valid citations
    test_cases = [
        {
            "name": "Valid U.S. citation with context",
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court held that separate educational facilities are inherently unequal."
        },
        {
            "name": "Valid F.2d citation",
            "text": "The case 410 F.2d 123 is important."
        },
        {
            "name": "Valid L.Ed.2d citation (complete)",
            "text": "95 L.Ed.2d 123"
        }
    ]
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Input: {test_case['text']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/analyze",
                json={
                    "text": test_case['text'],
                    "type": "text"
                },
                timeout=10  # 10 second timeout
            )
            
            response_time = time.time() - start_time
            print(f"Response time: {response_time:.2f}s")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('task_id'):
                    print("⚠ Async response - task queued")
                    print(f"Task ID: {data['task_id']}")
                else:
                    print("✅ Immediate response")
                    citations = data.get('citations', [])
                    print(f"Found {len(citations)} citations:")
                    
                    for j, citation in enumerate(citations, 1):
                        print(f"\n  Citation {j}:")
                        print(f"    Citation: {citation.get('citation', 'N/A')}")
                        print(f"    Verified: {citation.get('verified', False)}")
                        print(f"    Case Name: {citation.get('case_name', 'None')}")
                        print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                        print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
                        print(f"    Canonical Date: {citation.get('canonical_date', 'None')}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fast_valid_citations() 