#!/usr/bin/env python3
"""
Quick test to diagnose the "No citations found" issue.
"""

import requests
import json

def test_basic_citation_extraction():
    """Test basic citation extraction to see if the system is working."""
    
    print("🔍 Testing Basic Citation Extraction")
    print("=" * 50)
    
    # Test with a simple, known-working citation
    simple_test = "This case cites Brown v. Board of Education, 347 U.S. 483 (1954)."
    
    print(f"📝 Simple Test Text: {simple_test}")
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": simple_test, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        print(f"📊 Simple Test Results:")
        print(f"   Status: {response.status_code}")
        print(f"   Success: {data.get('success', False)}")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Processing mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        if len(data.get('citations', [])) == 0:
            print(f"❌ PROBLEM: No citations found in simple test!")
            print(f"Full response: {json.dumps(data, indent=2)}")
            return False
        else:
            print(f"✅ Simple test passed - found citations")
            
        # Test with the nested citation text that was working
        nested_test = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
        
        print(f"\n📝 Nested Test Text: {nested_test[:100]}...")
        
        response2 = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": nested_test, "type": "text"},
            timeout=30
        )
        
        if response2.status_code != 200:
            print(f"❌ API Error: {response2.status_code}")
            return False
        
        data2 = response2.json()
        
        print(f"📊 Nested Test Results:")
        print(f"   Citations: {len(data2.get('citations', []))}")
        print(f"   Processing mode: {data2.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        if len(data2.get('citations', [])) == 0:
            print(f"❌ PROBLEM: Nested citation test failed!")
            return False
        else:
            print(f"✅ Nested test passed - found {len(data2.get('citations', []))} citations")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

def check_system_health():
    """Check if the system is running properly."""
    
    print(f"\n🏥 System Health Check")
    print("=" * 50)
    
    try:
        # Check if API is responding
        response = requests.get("http://localhost:8080/casestrainer/api/health", timeout=10)
        
        if response.status_code == 200:
            print(f"✅ API is responding")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
        # Check progress endpoint
        progress_response = requests.get("http://localhost:8080/casestrainer/api/processing_progress", timeout=10)
        
        if progress_response.status_code == 200:
            print(f"✅ Progress endpoint is responding")
        else:
            print(f"⚠️ Progress endpoint issue: {progress_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ System health check failed: {e}")
        return False

def main():
    """Run no citations diagnosis."""
    
    print("🚀 No Citations Found - Diagnosis")
    print("=" * 60)
    
    # Check system health first
    health_ok = check_system_health()
    
    if not health_ok:
        print("\n❌ System health issues detected - fix these first")
        return False
    
    # Test citation extraction
    citations_ok = test_basic_citation_extraction()
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS RESULTS")
    print("=" * 60)
    
    if citations_ok:
        print("✅ Citation extraction is working")
        print("🔍 The 'No citations found' issue might be:")
        print("   - Specific to your current text")
        print("   - A frontend display issue")
        print("   - A temporary glitch")
        print("\n💡 Try refreshing the page or testing with different text")
    else:
        print("❌ Citation extraction is broken")
        print("🔧 Possible causes:")
        print("   - Backend processing pipeline issue")
        print("   - Recent code changes broke something")
        print("   - Docker container issues")
        print("\n💡 Need to investigate the backend processing")
    
    return citations_ok

if __name__ == "__main__":
    main()
