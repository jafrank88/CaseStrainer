#!/usr/bin/env python3
"""
Simple test script to verify citation verification with immediate results.
"""

import requests
import json
import time

def test_immediate_citation():
    """Test citation verification with text that should return immediate results."""
    
    print("=== Simple Citation Test (Immediate Results) ===")
    
    test_cases = [
        {
            "name": "Single citation with context",
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that racial segregation in public schools was unconstitutional."
        },
        {
            "name": "Citation without context",
            "text": "The case 347 U.S. 483 is important."
        },
        {
            "name": "Multiple citations",
            "text": "Marbury v. Madison, 5 U.S. 137 (1803) and Roe v. Wade, 410 U.S. 113 (1973) are landmark cases."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Input text: {test_case['text']}")
        
        try:
            response = requests.post(
                "http://localhost:5000/casestrainer/api/analyze",
                json={
                    "text": test_case["text"],
                    "type": "text"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if it's an immediate result or a task
                if "citations" in result:
                    print("✅ Immediate result received!")
                    citations = result["citations"]
                    print(f"Found {len(citations)} citations:")
                    
                    for j, citation in enumerate(citations, 1):
                        print(f"\n  Citation {j}:")
                        print(f"    Citation: {citation.get('citation', 'N/A')}")
                        print(f"    Verified: {citation.get('verified', False)}")
                        print(f"    Case Name: {citation.get('case_name', 'None')}")
                        print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                        print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
                        print(f"    Hinted Case Name: {citation.get('hinted_case_name', 'None')}")
                        print(f"    Canonical Date: {citation.get('canonical_date', 'None')}")
                        print(f"    Extracted Date: {citation.get('extracted_date', 'None')}")
                        print(f"    Court: {citation.get('court', 'None')}")
                        print(f"    Docket Number: {citation.get('docket_number', 'None')}")
                        print(f"    URL: {citation.get('url', 'None')}")
                        print(f"    Source: {citation.get('source', 'None')}")
                        print(f"    Confidence: {citation.get('confidence', 'None')}")
                        
                        # Check for extracted vs canonical case names
                        extracted = citation.get('extracted_case_name')
                        canonical = citation.get('canonical_name')
                        case_name = citation.get('case_name')
                        
                        if extracted and canonical:
                            print(f"    ✅ SUCCESS: Both extracted ('{extracted}') and canonical ('{canonical}') names found!")
                        elif extracted:
                            print(f"    ⚠️  PARTIAL: Only extracted name found ('{extracted}')")
                        elif canonical:
                            print(f"    ⚠️  PARTIAL: Only canonical name found ('{canonical}')")
                        elif case_name:
                            print(f"    ⚠️  LEGACY: Only case_name found ('{case_name}')")
                        else:
                            print(f"    ❌ MISSING: No case names found")
                        
                        # Check details for additional information
                        details = citation.get('details', {})
                        if details:
                            print(f"    Details: {json.dumps(details, indent=6)}")
                
                elif "task_id" in result:
                    print("⏳ Task created, polling for results...")
                    task_id = result['task_id']
                    
                    # Poll for results
                    for attempt in range(15):  # Poll up to 15 times
                        time.sleep(2)
                        try:
                            poll_response = requests.get(
                                f"http://localhost:5000/casestrainer/api/task_status/{task_id}",
                                timeout=10
                            )
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                print(f"  Poll {attempt + 1}: Status = {poll_result.get('status', 'unknown')}")
                                
                                if poll_result.get('status') == 'completed':
                                    print("✅ Task completed!")
                                    if "citations" in poll_result:
                                        citations = poll_result["citations"]
                                        print(f"Found {len(citations)} citations:")
                                        
                                        for j, citation in enumerate(citations, 1):
                                            print(f"\n  Citation {j}:")
                                            print(f"    Citation: {citation.get('citation', 'N/A')}")
                                            print(f"    Verified: {citation.get('verified', False)}")
                                            print(f"    Case Name: {citation.get('case_name', 'None')}")
                                            print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                                            print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
                                            print(f"    Hinted Case Name: {citation.get('hinted_case_name', 'None')}")
                                            print(f"    Canonical Date: {citation.get('canonical_date', 'None')}")
                                            print(f"    Extracted Date: {citation.get('extracted_date', 'None')}")
                                            print(f"    Court: {citation.get('court', 'None')}")
                                            print(f"    Docket Number: {citation.get('docket_number', 'None')}")
                                            print(f"    URL: {citation.get('url', 'None')}")
                                            print(f"    Source: {citation.get('source', 'None')}")
                                            print(f"    Confidence: {citation.get('confidence', 'None')}")
                                            
                                            # Check for extracted vs canonical case names
                                            extracted = citation.get('extracted_case_name')
                                            canonical = citation.get('canonical_name')
                                            case_name = citation.get('case_name')
                                            
                                            if extracted and canonical:
                                                print(f"    ✅ SUCCESS: Both extracted ('{extracted}') and canonical ('{canonical}') names found!")
                                            elif extracted:
                                                print(f"    ⚠️  PARTIAL: Only extracted name found ('{extracted}')")
                                            elif canonical:
                                                print(f"    ⚠️  PARTIAL: Only canonical name found ('{canonical}')")
                                            elif case_name:
                                                print(f"    ⚠️  LEGACY: Only case_name found ('{case_name}')")
                                            else:
                                                print(f"    ❌ MISSING: No case names found")
                                            
                                            # Check details for additional information
                                            details = citation.get('details', {})
                                            if details:
                                                print(f"    Details: {json.dumps(details, indent=6)}")
                                    
                                    break
                                elif poll_result.get('status') == 'failed':
                                    print(f"❌ Task failed: {poll_result.get('error', 'Unknown error')}")
                                    break
                            else:
                                print(f"  Poll {attempt + 1}: Failed with status {poll_response.status_code}")
                                
                        except Exception as e:
                            print(f"  Poll {attempt + 1}: Error - {e}")
                    
                    else:
                        print("⏰ Polling timed out")
                
                else:
                    print(f"⚠️  Unexpected response format: {json.dumps(result, indent=2)}")
                    
            else:
                print(f"❌ API Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    print("Starting Simple Citation Test...")
    print("Make sure the backend is running on http://localhost:5000")
    print()
    
    test_immediate_citation() 