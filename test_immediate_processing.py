#!/usr/bin/env python3
"""
Direct Immediate Processing Test
Test the immediate processing path directly to isolate the issue
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_immediate_processing_direct():
    """Test immediate processing directly."""
    print("🔍 DIRECT IMMEDIATE PROCESSING TEST")
    print("="*50)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        # Test should_process_immediately
        should_immediate = service.should_process_immediately(input_data)
        print(f"should_process_immediately: {should_immediate}")
        print(f"Text length: {len(test_text)} characters")
        print(f"Threshold: 10KB = {10 * 1024} characters")
        
        if should_immediate:
            print("✅ Text should be processed immediately")
            
            # Test process_immediately
            print("\nTesting process_immediately...")
            result = service.process_immediately(input_data)
            
            print(f"Result status: {result.get('status')}")
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
            
            if result.get('status') == 'completed':
                citations = result.get('citations', [])
                if citations:
                    citation = citations[0]
                    print(f"\nFirst citation:")
                    print(f"  Citation: {citation.get('citation')}")
                    print(f"  Extracted name: {citation.get('extracted_case_name')}")
                    print(f"  Canonical name: {citation.get('canonical_name')}")
                    print(f"  Canonical URL: {citation.get('canonical_url')}")
                    print(f"  Verified: {citation.get('verified')}")
                    
                    success = (citation.get('canonical_name') is not None and 
                              citation.get('canonical_url') is not None and
                              citation.get('verified') is True)
                    
                    print(f"\n🎯 IMMEDIATE PROCESSING: {'✅ SUCCESS' if success else '❌ FAILED'}")
                    return success
                else:
                    print("❌ No citations found")
                    return False
            else:
                print(f"❌ Processing failed: {result.get('message')}")
                return False
        else:
            print("❌ Text should NOT be processed immediately (unexpected)")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint_routing():
    """Test what happens when we call the API endpoint."""
    print("\n🌐 API ENDPOINT ROUTING TEST")
    print("="*40)
    
    try:
        import requests
        
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {"text": "Brown v. Board of Education, 347 U.S. 483 (1954)", "type": "text"}
        
        print(f"Testing API endpoint: {url}")
        print(f"Payload: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'completed':
                print("✅ API returned immediate results")
                return True
            elif status == 'processing':
                print("❌ API returned async processing (should be immediate)")
                return False
            else:
                print(f"❌ API returned unexpected status: {status}")
                return False
        else:
            print(f"❌ API returned error status: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run immediate processing tests."""
    print("🧪 IMMEDIATE PROCESSING DIAGNOSIS")
    print("="*60)
    
    direct_success = test_immediate_processing_direct()
    api_success = test_api_endpoint_routing()
    
    print(f"\n" + "="*60)
    print("📊 DIAGNOSIS RESULTS")
    print("="*60)
    
    print(f"Direct immediate processing: {'✅ WORKING' if direct_success else '❌ FAILED'}")
    print(f"API endpoint routing: {'✅ WORKING' if api_success else '❌ FAILED'}")
    
    if direct_success and not api_success:
        print("\n🔍 DIAGNOSIS: API routing issue")
        print("   The immediate processing logic works, but the API is not using it")
        print("   Check API endpoint routing and function calls")
    elif not direct_success:
        print("\n🔍 DIAGNOSIS: Immediate processing broken")
        print("   The immediate processing logic itself is not working")
        print("   Check CitationService implementation")
    elif direct_success and api_success:
        print("\n✅ DIAGNOSIS: Everything working correctly")
        print("   Both immediate processing and API routing are functional")
    
    return direct_success and api_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
