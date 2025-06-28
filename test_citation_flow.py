#!/usr/bin/env python3
"""
Test script to verify citation verification flow with both extracted and canonical case names.
"""

import requests
import json
import time

def test_citation_verification():
    """Test the citation verification API with various inputs."""
    
    # API endpoint
    base_url = "http://localhost:5000"
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Simple citation with context",
            "input": {
                "text": "In the case of Brown v. Board of Education, 347 U.S. 483 (1954), the Court held that separate educational facilities are inherently unequal.",
                "type": "text"
            }
        },
        {
            "name": "Multiple citations with context",
            "input": {
                "text": "The landmark decisions in Marbury v. Madison, 5 U.S. 137 (1803) and Roe v. Wade, 410 U.S. 113 (1973) established important precedents.",
                "type": "text"
            }
        },
        {
            "name": "Citation without context (should still get canonical name)",
            "input": {
                "text": "The case 347 U.S. 483 is important.",
                "type": "text"
            }
        },
        {
            "name": "Invalid citation test",
            "input": {
                "text": "The case 999 U.S. 999 (2025) is mentioned.",
                "type": "text"
            }
        }
    ]
    
    print("=== Citation Verification Flow Test ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Test the API
            response = requests.post(
                f"{base_url}/casestrainer/api/analyze",
                json=test_case["input"],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API Response (Status: {response.status_code}):")
                
                # Check for task status
                if "task_id" in result:
                    print(f"   Task ID: {result['task_id']}")
                    print(f"   Status: {result.get('status', 'unknown')}")
                    
                    # If it's a task, poll for results
                    if result.get('status') == 'processing':
                        print("   Polling for results...")
                        task_id = result['task_id']
                        
                        for attempt in range(10):  # Poll up to 10 times
                            time.sleep(2)
                            poll_response = requests.get(
                                f"{base_url}/casestrainer/api/task_status/{task_id}",
                                timeout=10
                            )
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                if poll_result.get('status') == 'completed':
                                    result = poll_result
                                    break
                                elif poll_result.get('status') == 'failed':
                                    print(f"   ❌ Task failed: {poll_result.get('error', 'Unknown error')}")
                                    break
                            else:
                                print(f"   ⚠️  Poll failed: {poll_response.status_code}")
                                break
                
                # Analyze the results
                if "results" in result:
                    print(f"   📊 Found {len(result['results'])} citation results:")
                    
                    for j, citation_result in enumerate(result['results'], 1):
                        print(f"\n   Citation {j}: {citation_result.get('citation', 'N/A')}")
                        print(f"   ✅ Verified: {citation_result.get('verified', False)}")
                        print(f"   📝 Extracted Case Name: {citation_result.get('extracted_case_name', 'None')}")
                        print(f"   🏛️  Canonical Case Name: {citation_result.get('canonical_name', 'None')}")
                        print(f"   📅 Date: {citation_result.get('canonical_date', 'None')}")
                        print(f"   🏢 Court: {citation_result.get('court', 'None')}")
                        print(f"   🔗 URL: {citation_result.get('canonical_url', 'None')}")
                        print(f"   📊 Source: {citation_result.get('source', 'None')}")
                        
                        # Check if we have both names
                        extracted = citation_result.get('extracted_case_name')
                        canonical = citation_result.get('canonical_name')
                        
                        if extracted and canonical:
                            print(f"   ✅ SUCCESS: Both extracted ('{extracted}') and canonical ('{canonical}') names found!")
                        elif extracted:
                            print(f"   ⚠️  PARTIAL: Only extracted name found ('{extracted}')")
                        elif canonical:
                            print(f"   ⚠️  PARTIAL: Only canonical name found ('{canonical}')")
                        else:
                            print(f"   ❌ MISSING: No case names found")
                        
                        if citation_result.get('error'):
                            print(f"   ❌ Error: {citation_result['error']}")
                
                elif "error" in result:
                    print(f"   ❌ API Error: {result['error']}")
                else:
                    print(f"   ⚠️  Unexpected response format: {json.dumps(result, indent=2)}")
                    
            else:
                print(f"❌ API Error (Status: {response.status_code}): {response.text}")
                
        except requests.exceptions.Timeout:
            print("   ⏰ Timeout: Request took too long")
        except requests.exceptions.ConnectionError:
            print("   🔌 Connection Error: Could not connect to API")
        except Exception as e:
            print(f"   ❌ Unexpected Error: {str(e)}")
        
        print("\n" + "="*60 + "\n")

def test_simple_citation():
    """Test a simple citation to verify the basic flow."""
    print("=== Simple Citation Test ===")
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={
                "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that racial segregation in public schools was unconstitutional.",
                "type": "text"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting Citation Verification Flow Test...")
    print("Make sure the backend is running on http://localhost:5000")
    print("Make sure the frontend is running on http://localhost:5173")
    print()
    
    # Test simple citation first
    test_simple_citation()
    print("\n" + "="*80 + "\n")
    
    # Test comprehensive scenarios
    test_citation_verification() 