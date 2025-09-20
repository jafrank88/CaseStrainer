#!/usr/bin/env python3
"""
Debug test for "No Citations" issue.
This test will help identify why some documents return no citations.
"""

import requests
import time
import json

def test_simple_citation_extraction():
    """Test with very simple, obvious citations."""
    
    print("🔍 Testing Simple Citation Extraction")
    print("=" * 50)
    
    # Very simple, obvious citations that should always be found
    test_cases = [
        {
            "name": "Basic Washington Citation",
            "text": "The case State v. Johnson, 160 Wn.2d 500 (2007) is important."
        },
        {
            "name": "US Supreme Court Citation", 
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954) changed everything."
        },
        {
            "name": "Multiple Simple Citations",
            "text": """
            Legal Analysis:
            1. State v. Johnson, 160 Wn.2d 500 (2007)
            2. Brown v. Board, 347 U.S. 483 (1954)
            3. Miranda v. Arizona, 384 U.S. 436 (1966)
            """
        },
        {
            "name": "Federal Circuit Citation",
            "text": "See Smith v. Jones, 123 F.3d 456 (9th Cir. 2000) for precedent."
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"   Text: {test_case['text'][:100]}...")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_case['text'], "type": "text"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"   ❌ API Error: {response.status_code}")
                results.append({"name": test_case['name'], "citations": 0, "error": f"HTTP {response.status_code}"})
                continue
            
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            
            # Handle async processing
            if processing_mode == 'queued':
                job_id = data.get('metadata', {}).get('job_id')
                if job_id:
                    print(f"   ⏳ Async processing: {job_id}")
                    for attempt in range(10):
                        time.sleep(1)
                        status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('status') == 'completed':
                                data = status_data
                                break
                        print(f"     Attempt {attempt + 1}: {status_data.get('status', 'unknown')}")
                    else:
                        print(f"   ❌ Async timeout")
                        results.append({"name": test_case['name'], "citations": 0, "error": "Async timeout"})
                        continue
            
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            success = data.get('success', False)
            
            print(f"   📊 Results:")
            print(f"     Processing: {processing_mode}")
            print(f"     Success: {success}")
            print(f"     Citations: {len(citations)}")
            print(f"     Clusters: {len(clusters)}")
            
            if len(citations) > 0:
                print(f"   ✅ Citations found:")
                for j, citation in enumerate(citations[:3], 1):
                    print(f"     {j}. {citation.get('citation', 'N/A')}")
            else:
                print(f"   ❌ No citations found")
                # Debug information
                if 'error' in data:
                    print(f"     Error: {data['error']}")
                if 'debug_info' in data:
                    print(f"     Debug: {data['debug_info']}")
            
            results.append({
                "name": test_case['name'],
                "citations": len(citations),
                "success": success,
                "processing_mode": processing_mode
            })
            
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({"name": test_case['name'], "citations": 0, "error": str(e)})
    
    # Summary
    print(f"\n📊 Simple Citation Test Summary:")
    total_tests = len(results)
    successful_tests = len([r for r in results if r.get('citations', 0) > 0])
    
    for result in results:
        status = "✅" if result.get('citations', 0) > 0 else "❌"
        print(f"   {status} {result['name']}: {result.get('citations', 0)} citations")
    
    print(f"\nOverall: {successful_tests}/{total_tests} tests found citations")
    
    return successful_tests > 0

def test_processing_modes():
    """Test different processing modes to see where citations are lost."""
    
    print(f"\n🔄 Testing Different Processing Modes")
    print("=" * 50)
    
    # Test with different document sizes to trigger different processing modes
    base_text = "The case State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) is important."
    
    test_sizes = [
        {"name": "Tiny (Sync)", "multiplier": 1},
        {"name": "Small (Sync)", "multiplier": 5},
        {"name": "Medium (Sync/Async)", "multiplier": 20},
        {"name": "Large (Async)", "multiplier": 100}
    ]
    
    for test_size in test_sizes:
        print(f"\n📄 Testing {test_size['name']}")
        
        # Create document of specified size
        test_text = (base_text + " ") * test_size['multiplier']
        text_length = len(test_text)
        
        print(f"   Document size: {text_length:,} characters")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_text, "type": "text"},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"   ❌ API Error: {response.status_code}")
                continue
            
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"   Processing mode: {processing_mode}")
            
            # Handle async processing
            if processing_mode == 'queued':
                job_id = data.get('metadata', {}).get('job_id')
                if job_id:
                    print(f"   ⏳ Waiting for async processing...")
                    for attempt in range(15):
                        time.sleep(2)
                        status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('status') == 'completed':
                                data = status_data
                                print(f"   ✅ Async completed")
                                break
                            elif status_data.get('status') == 'failed':
                                print(f"   ❌ Async failed: {status_data}")
                                break
                        print(f"     Attempt {attempt + 1}: {status_data.get('status', 'unknown')}")
                    else:
                        print(f"   ❌ Async timeout")
                        continue
            
            citations = data.get('citations', [])
            success = data.get('success', False)
            
            print(f"   📊 Results:")
            print(f"     Success: {success}")
            print(f"     Citations: {len(citations)}")
            
            if len(citations) == 0:
                print(f"   ❌ No citations found in {test_size['name']} document")
                # Look for error information
                if 'error' in data:
                    print(f"     Error: {data['error']}")
            else:
                print(f"   ✅ {len(citations)} citations found")
            
        except Exception as e:
            print(f"   💥 Exception: {e}")

def test_api_endpoint_health():
    """Test that the API endpoint is working correctly."""
    
    print(f"\n🏥 Testing API Endpoint Health")
    print("=" * 50)
    
    try:
        # Test basic endpoint availability
        response = requests.get("http://localhost:8080/casestrainer/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint responding")
        else:
            print(f"⚠️ Health endpoint returned: {response.status_code}")
    except:
        print("❌ Health endpoint not available")
    
    # Test analyze endpoint with minimal data
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": "Test", "type": "text"},
            timeout=10
        )
        
        print(f"📊 Analyze endpoint test:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Success: {data.get('success')}")
            print(f"   ✅ Analyze endpoint working")
        else:
            print(f"   ❌ Analyze endpoint error: {response.text}")
            
    except Exception as e:
        print(f"   💥 Analyze endpoint exception: {e}")

def main():
    """Run comprehensive no-citations debugging."""
    
    print("🚀 Debugging 'No Citations' Issue")
    print("=" * 60)
    
    # Run diagnostic tests
    simple_ok = test_simple_citation_extraction()
    test_processing_modes()
    test_api_endpoint_health()
    
    print("\n" + "=" * 60)
    print("📋 NO CITATIONS DEBUG RESULTS")
    print("=" * 60)
    
    if simple_ok:
        print("✅ Basic citation extraction is working")
        print("🔍 Issue may be with:")
        print("   - Specific document types or formats")
        print("   - Async processing pipeline")
        print("   - Large document handling")
        print("   - URL content extraction")
    else:
        print("❌ Basic citation extraction is broken")
        print("🔍 Issue is likely with:")
        print("   - Core citation processing pipeline")
        print("   - API endpoint configuration")
        print("   - Backend service connectivity")
    
    return simple_ok

if __name__ == "__main__":
    main()
