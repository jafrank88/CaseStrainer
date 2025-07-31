#!/usr/bin/env python3
"""
Quick diagnostic test to understand why citations are showing as unverified
"""

import requests
import json

def diagnose_unverified_issue():
    """Diagnose why citations are showing as unverified"""
    
    print("DIAGNOSING UNVERIFIED CITATIONS ISSUE")
    print("=" * 50)
    
    # Test with the citation we know should work
    citation = "17 L. Ed. 2d 562"
    expected_case = "Garrity v. New Jersey"
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    print(f"Testing: {citation}")
    print(f"Expected: {expected_case}")
    print(f"Endpoint: {endpoint}")
    print("-" * 50)
    
    # Test 1: Simple API call
    test_text = f"This case cites {citation}."
    
    try:
        print("Making API request...")
        response = requests.post(
            endpoint,
            json={"text": test_text, "type": "text"},
            timeout=15
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response received successfully")
            
            citations_found = result.get('citations', [])
            print(f"Citations found: {len(citations_found)}")
            
            if citations_found:
                citation_result = citations_found[0]
                print(f"First citation result:")
                print(f"  Citation: {citation_result.get('citation', 'N/A')}")
                print(f"  Verified: {citation_result.get('verified', False)}")
                print(f"  Canonical Name: {citation_result.get('canonical_name', 'N/A')}")
                print(f"  Canonical Date: {citation_result.get('canonical_date', 'N/A')}")
                print(f"  Source: {citation_result.get('source', 'N/A')}")
                print(f"  Confidence: {citation_result.get('confidence', 'N/A')}")
                
                if not citation_result.get('verified', False):
                    print("\n❌ ISSUE IDENTIFIED: Citation is not verified")
                    print("Possible causes:")
                    print("1. CourtListener API key missing or invalid")
                    print("2. Enhanced verification logic has bugs")
                    print("3. Citation not found in CourtListener database")
                    print("4. Network/timeout issues")
                    print("5. Docker container not running enhanced verification code")
                else:
                    print("\n✅ Citation is verified - system working correctly")
            else:
                print("\n❌ ISSUE: No citations extracted from text")
                print("This suggests citation extraction is failing")
        
        elif response.status_code == 404:
            print("❌ ISSUE: API endpoint not found")
            print("Container may not be running or endpoint path is wrong")
            
        elif response.status_code == 500:
            print("❌ ISSUE: Internal server error")
            print("There's likely an exception in the verification code")
            print("Response text:", response.text[:200])
            
        else:
            print(f"❌ ISSUE: Unexpected status code {response.status_code}")
            print("Response text:", response.text[:200])
            
    except requests.exceptions.ConnectionError:
        print("❌ ISSUE: Connection error")
        print("Docker containers may not be running or port 5001 not accessible")
        
    except requests.exceptions.Timeout:
        print("❌ ISSUE: Request timeout")
        print("API is taking too long to respond")
        
    except Exception as e:
        print(f"❌ ISSUE: Exception occurred: {e}")
    
    # Test 2: Check if containers are running
    print(f"\n{'='*50}")
    print("CONTAINER STATUS CHECK")
    print(f"{'='*50}")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--filter', 'name=casestrainer'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Header + at least one container
                print("✅ Docker containers are running:")
                for line in lines[1:]:  # Skip header
                    print(f"  {line}")
            else:
                print("❌ No CaseStrainer containers running")
        else:
            print("❌ Could not check Docker status")
            
    except Exception as e:
        print(f"❌ Could not check containers: {e}")

if __name__ == "__main__":
    diagnose_unverified_issue()
