#!/usr/bin/env python3
"""
Quick API Test for WL Citation Extraction

This script performs a quick test to verify WL citation extraction
is working through the CaseStrainer API.
"""

import requests
import json
import time

def test_api_wl_extraction():
    """Quick test of WL citation extraction via API."""
    
    base_url = "http://localhost:5000"
    api_endpoint = f"{base_url}/api/analyze"
    status_endpoint = f"{base_url}/api/task_status"
    
    # Test content with WL citations
    test_content = """
    In the landmark case of Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006), 
    the court established important precedent. This decision was later referenced 
    in Doe v. Roe, 2023 WL 1234567 (9th Cir. 2023), which further clarified 
    the legal standard.
    """
    
    print("🔍 Quick WL Citation API Test")
    print("=" * 40)
    print(f"API Endpoint: {api_endpoint}")
    print(f"Test Content: {test_content.strip()}")
    print()
    
    try:
        # Submit the text for analysis
        print("Submitting text for analysis...")
        response = requests.post(api_endpoint, data={
            'text': test_content,
            'type': 'text'
        }, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ API request successful")
        
        # Handle both sync and async responses
        if 'task_id' in result:
            print(f"📋 Task ID: {result['task_id']}")
            print("⏳ Waiting for async processing...")
            
            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < 60:  # 60 second timeout
                status_response = requests.get(f"{status_endpoint}/{result['task_id']}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('status') == 'completed':
                        final_result = status_data.get('result')
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"❌ Task failed: {status_data.get('error')}")
                        return False
                time.sleep(2)
            else:
                print("❌ Task timed out")
                return False
        else:
            print("⚡ Processed synchronously")
            final_result = result
        
        # Analyze results
        if not final_result or 'citations' not in final_result:
            print("❌ No citations found in result")
            return False
        
        citations = final_result['citations']
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"📊 Results:")
        print(f"   Total citations: {len(citations)}")
        print(f"   WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print(f"✅ WL Citations Found:")
            for i, citation in enumerate(wl_citations, 1):
                print(f"   {i}. {citation.get('citation')}")
                print(f"      Year: {citation.get('extracted_date', 'N/A')}")
                print(f"      Source: {citation.get('source', 'N/A')}")
                print(f"      Confidence: {citation.get('confidence', 'N/A')}")
                
                # Check metadata
                metadata = citation.get('metadata', {})
                if metadata:
                    print(f"      Type: {metadata.get('citation_type', 'N/A')}")
                    print(f"      Doc Number: {metadata.get('document_number', 'N/A')}")
                print()
            
            # Verify expected citations
            citation_texts = [c.get('citation', '') for c in wl_citations]
            expected_citations = ['2006 WL 3801910', '2023 WL 1234567']
            
            found_expected = 0
            for expected in expected_citations:
                if any(expected in ct for ct in citation_texts):
                    found_expected += 1
                    print(f"✅ Found expected citation: {expected}")
                else:
                    print(f"❌ Missing expected citation: {expected}")
            
            if found_expected == len(expected_citations):
                print(f"🎉 SUCCESS: All {len(expected_citations)} expected WL citations found!")
                return True
            else:
                print(f"⚠️  PARTIAL: Found {found_expected}/{len(expected_citations)} expected citations")
                return False
        else:
            print("❌ No WL citations found")
            return False
            
    except requests.RequestException as e:
        print(f"❌ API connection error: {e}")
        print("   Make sure CaseStrainer is running with: ./cslaunch")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_wl_extraction()
    
    if success:
        print("\n🎉 WL Citation API Test PASSED!")
        print("   The WL citation extraction is working correctly through the API.")
    else:
        print("\n❌ WL Citation API Test FAILED!")
        print("   Please check the output above for details.")
    
    exit(0 if success else 1)
