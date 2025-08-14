#!/usr/bin/env python3
"""
Debug Immediate Processing Path
Test the immediate processing path with detailed logging to find the issue
"""

import sys
import os
import json
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_immediate_processing_debug():
    """Test immediate processing with detailed debugging."""
    print("🔍 IMMEDIATE PROCESSING DEBUG TEST")
    print("="*50)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        input_data = {'text': test_text, 'type': 'text'}
        
        print(f"Test text: {test_text}")
        print(f"Text length: {len(test_text)} characters")
        print(f"Threshold: 10KB = {10 * 1024} characters")
        
        # Test should_process_immediately
        should_immediate = service.should_process_immediately(input_data)
        print(f"should_process_immediately result: {should_immediate}")
        
        if should_immediate:
            print("✅ Text should be processed immediately")
            
            # Test process_immediately with detailed error handling
            print("\nTesting process_immediately with detailed logging...")
            try:
                result = service.process_immediately(input_data)
                print(f"✅ process_immediately completed successfully")
                print(f"Result keys: {list(result.keys())}")
                print(f"Status: {result.get('status')}")
                print(f"Citations: {len(result.get('citations', []))}")
                print(f"Clusters: {len(result.get('clusters', []))}")
                
                if result.get('status') == 'completed':
                    print("✅ Immediate processing returned completed status")
                    return True
                else:
                    print(f"❌ Immediate processing returned unexpected status: {result.get('status')}")
                    print(f"Message: {result.get('message')}")
                    return False
                    
            except Exception as e:
                print(f"❌ process_immediately failed with exception: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("❌ Text should NOT be processed immediately (unexpected)")
            return False
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_with_debug():
    """Test API endpoint with debug logging."""
    print("\n🌐 API ENDPOINT DEBUG TEST")
    print("="*40)
    
    try:
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {"text": "Brown v. Board of Education, 347 U.S. 483 (1954)", "type": "text"}
        
        print(f"Testing API endpoint: {url}")
        print(f"Payload: {data}")
        
        # Make the request
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                status = result.get('status')
                
                print(f"Response status: {status}")
                
                if status == 'completed':
                    print("✅ API returned immediate results")
                    citations = result.get('citations', [])
                    print(f"Citations returned: {len(citations)}")
                    if citations:
                        citation = citations[0]
                        print(f"First citation: {citation.get('citation')}")
                        print(f"Canonical name: {citation.get('canonical_name')}")
                        print(f"Verified: {citation.get('verified')}")
                    return True
                elif status == 'processing':
                    print("❌ API returned async processing (should be immediate)")
                    task_id = result.get('task_id')
                    print(f"Task ID: {task_id}")
                    return False
                else:
                    print(f"❌ API returned unexpected status: {status}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                return False
        else:
            print(f"❌ API returned error status: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests."""
    print("🧪 IMMEDIATE PROCESSING DEBUG ANALYSIS")
    print("="*60)
    
    direct_success = test_immediate_processing_debug()
    api_success = test_api_with_debug()
    
    print(f"\n" + "="*60)
    print("📊 DEBUG RESULTS")
    print("="*60)
    
    print(f"Direct immediate processing: {'✅ WORKING' if direct_success else '❌ FAILED'}")
    print(f"API endpoint routing: {'✅ WORKING' if api_success else '❌ FAILED'}")
    
    if direct_success and not api_success:
        print("\n🔍 ISSUE IDENTIFIED: API routing problem")
        print("   - The immediate processing logic works correctly")
        print("   - The API endpoint is not using the immediate processing path")
        print("   - Check for exceptions in the API immediate processing code")
        print("   - Verify that the immediate processing path is being reached")
    elif not direct_success:
        print("\n🔍 ISSUE IDENTIFIED: Immediate processing broken")
        print("   - The immediate processing logic itself has issues")
        print("   - Check CitationService.process_immediately implementation")
    elif direct_success and api_success:
        print("\n✅ SUCCESS: Everything working correctly")
        print("   - Both immediate processing and API routing are functional")
    
    return direct_success and api_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
