#!/usr/bin/env python3
"""
Test production verification to identify why citations are unverified
"""

import requests
import json

def test_production_verification():
    """Test the production API to see what's happening with verification"""
    
    print("TESTING PRODUCTION VERIFICATION")
    print("=" * 50)
    
    # Test the known working citation
    citation = "17 L. Ed. 2d 562"
    expected_case = "Garrity v. New Jersey"
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    print(f"Testing: {citation}")
    print(f"Expected: {expected_case}")
    print(f"Endpoint: {endpoint}")
    print("-" * 50)
    
    # Create test input
    test_text = f"This case cites {citation}."
    
    try:
        print("Making API request...")
        response = requests.post(
            endpoint,
            json={"text": test_text, "type": "text"},
            timeout=30  # Longer timeout
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API responded successfully")
            
            # Check if citations were extracted
            citations_found = result.get('citations', [])
            print(f"Citations extracted: {len(citations_found)}")
            
            if citations_found:
                citation_result = citations_found[0]
                
                print("\nCitation Details:")
                print(f"  Citation Text: {citation_result.get('citation', 'N/A')}")
                print(f"  Verified: {citation_result.get('verified', False)}")
                print(f"  Canonical Name: {citation_result.get('canonical_name', 'N/A')}")
                print(f"  Canonical Date: {citation_result.get('canonical_date', 'N/A')}")
                print(f"  Source: {citation_result.get('source', 'N/A')}")
                print(f"  Confidence: {citation_result.get('confidence', 'N/A')}")
                
                # Analyze the result
                verified = citation_result.get('verified', False)
                canonical_name = citation_result.get('canonical_name', '')
                source = citation_result.get('source', '')
                
                if verified:
                    if expected_case.lower() in canonical_name.lower():
                        print("\n🎯 SUCCESS: Citation verified correctly!")
                        print("The enhanced verification system is working!")
                    else:
                        print(f"\n⚠️  ISSUE: Citation verified but wrong case")
                        print(f"Expected: {expected_case}")
                        print(f"Found: {canonical_name}")
                        print("This suggests our context validation isn't working")
                else:
                    print(f"\n❌ ISSUE: Citation not verified")
                    print(f"Source: {source}")
                    
                    if source == 'N/A' or not source:
                        print("Possible causes:")
                        print("1. CourtListener API key not working in Docker")
                        print("2. Enhanced verification logic has bugs")
                        print("3. Network connectivity issues")
                        print("4. Citation not found in CourtListener")
                    elif 'CourtListener' in source:
                        print("CourtListener was contacted but verification failed")
                        print("This suggests our enhanced validation is too strict")
                    else:
                        print(f"Verification attempted via: {source}")
                        
            else:
                print("\n❌ CRITICAL: No citations extracted from text")
                print("This suggests citation extraction is completely broken")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            if response.status_code == 500:
                print("Internal server error - check container logs")
            elif response.status_code == 404:
                print("Endpoint not found - check container status")
            
            try:
                error_text = response.text[:500]
                print(f"Error response: {error_text}")
            except:
                pass
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach the API")
        print("Check if Docker containers are running on port 5001")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: API taking too long to respond")
        print("This suggests the verification process is hanging")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    print(f"\n{'='*50}")
    print("DIAGNOSIS SUMMARY")
    print(f"{'='*50}")
    print("If you see 'Citation not verified' above, the most likely causes are:")
    print("1. Enhanced verification validation is too strict")
    print("2. Citation array validation is failing due to format differences")
    print("3. CourtListener API key authentication issues in Docker")
    print("4. Network connectivity problems between containers")

if __name__ == "__main__":
    test_production_verification()
