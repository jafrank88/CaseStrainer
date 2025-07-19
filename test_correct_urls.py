#!/usr/bin/env python3
"""
Test Correct URL Patterns
Verify that the proper HTTPS URLs work through nginx proxy
"""

import requests
import time

def test_correct_urls():
    """Test the correct URL patterns"""
    
    print("🔍 Testing Correct URL Patterns")
    print("=" * 50)
    
    # Test 1: Correct HTTPS URL through nginx proxy
    print("\n1. Testing correct HTTPS URL (should work):")
    print("   https://wolf.law.uw.edu/casestrainer/api/health")
    
    try:
        start_time = time.time()
        response = requests.get("https://wolf.law.uw.edu/casestrainer/api/health", timeout=10)
        duration = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {duration:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Server: {data.get('status', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
        else:
            print(f"   ❌ Error: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Citation analysis through nginx proxy
    print("\n2. Testing citation analysis (should work):")
    print("   https://wolf.law.uw.edu/casestrainer/api/analyze")
    
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
        "enable_verification": True
    }
    
    try:
        start_time = time.time()
        response = requests.post("https://wolf.law.uw.edu/casestrainer/api/analyze", 
                               json=test_data, timeout=10)
        duration = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {duration:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            print(f"   ✅ SUCCESS! Found {len(citations)} citations")
            if citations:
                citation = citations[0]
                print(f"   Citation: {citation.get('citation', 'N/A')}")
                print(f"   Case: {citation.get('case_name', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Wrong URL (should fail)
    print("\n3. Testing wrong URL (should fail):")
    print("   https://wolf.law.uw.edu:5000/casestrainer/api/health")
    
    try:
        response = requests.get("https://wolf.law.uw.edu:5000/casestrainer/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ⚠️  Unexpected success - direct HTTPS to backend worked")
        else:
            print(f"   ✅ Expected failure: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   ✅ Expected failure: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")
    print("\n💡 Expected Results:")
    print("   ✅ Tests 1 & 2 should work (through nginx proxy)")
    print("   ❌ Test 3 should fail (direct HTTPS to backend)")

if __name__ == "__main__":
    test_correct_urls() 