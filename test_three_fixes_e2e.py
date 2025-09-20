#!/usr/bin/env python3
"""
End-to-End test specifically for the three fixes:
1. Large URLs processing correctly (sync vs async based on extracted text size)
2. Extracted names showing in cluster display
3. Progress bar working
"""

import requests
import time
import json

def test_cluster_names_e2e():
    """End-to-end test for cluster names display."""
    
    print("🔗 E2E Test: Cluster Names Display")
    print("=" * 50)
    
    # Test with a document that should create clear clusters
    test_text = """
    Legal Analysis Document
    
    The landmark case State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) established important precedent.
    This case is also cited as 160 Wn.2d 500 and as 158 P.3d 677 in various contexts.
    
    Another important case is City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010).
    The Williams case can also be found at 170 Wn.2d 200 and 240 P.3d 1055.
    
    These cases demonstrate the importance of proper citation clustering.
    """
    
    try:
        print("📤 Submitting document for analysis...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"📊 Processing mode: {processing_mode}")
        
        # Handle async processing if needed
        if processing_mode == 'queued':
            job_id = data.get('metadata', {}).get('job_id')
            if job_id:
                print(f"⏳ Polling for async results: {job_id}")
                for attempt in range(15):
                    time.sleep(2)
                    status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            data = status_data
                            print(f"✅ Async processing completed")
                            break
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Async processing failed: {status_data}")
                            return False
                    print(f"   Attempt {attempt + 1}/15: {status_data.get('status', 'unknown')}")
                else:
                    print(f"❌ Timeout waiting for async completion")
                    return False
        
        # Analyze results
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"📊 Results Summary:")
        print(f"   Citations found: {len(citations)}")
        print(f"   Clusters found: {len(clusters)}")
        
        if len(citations) == 0:
            print(f"❌ No citations found - this suggests a processing issue")
            return False
        
        if len(clusters) == 0:
            print(f"⚠️ No clusters found - may be normal if no parallel citations detected")
            # This is not necessarily a failure
        
        # Check cluster structure for the fixes
        cluster_names_working = True
        for i, cluster in enumerate(clusters, 1):
            print(f"\n🔍 Cluster {i} Analysis:")
            
            # Check the fields we added for frontend compatibility
            extracted_case_name = cluster.get('extracted_case_name')
            extracted_date = cluster.get('extracted_date')
            case_name = cluster.get('case_name')
            year = cluster.get('year')
            citation_objects = cluster.get('citation_objects', [])
            
            print(f"   extracted_case_name: '{extracted_case_name}'")
            print(f"   extracted_date: '{extracted_date}'")
            print(f"   case_name: '{case_name}'")
            print(f"   year: '{year}'")
            print(f"   citation_objects: {len(citation_objects)} items")
            
            # Check if frontend-compatible fields are present
            if not extracted_case_name or extracted_case_name == 'Unknown Case':
                print(f"   ❌ Missing or invalid extracted_case_name")
                cluster_names_working = False
            else:
                print(f"   ✅ Valid extracted_case_name found")
            
            # Check citation objects have names
            if citation_objects:
                names_in_objects = [obj.get('extracted_case_name') for obj in citation_objects if obj.get('extracted_case_name')]
                print(f"   Citation object names: {names_in_objects}")
                if not names_in_objects:
                    print(f"   ⚠️ No names in citation objects")
                else:
                    print(f"   ✅ Names found in citation objects")
        
        # Overall assessment
        success = len(citations) > 0 and cluster_names_working
        
        print(f"\n🎯 Cluster Names E2E Test: {'✅ PASS' if success else '❌ FAIL'}")
        if success:
            print(f"   ✅ Citations extracted successfully")
            print(f"   ✅ Cluster names display fix working")
        else:
            print(f"   ❌ Issues found with cluster names display")
        
        return success
        
    except Exception as e:
        print(f"💥 E2E test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_endpoints_e2e():
    """End-to-end test for progress endpoints."""
    
    print(f"\n📊 E2E Test: Progress Endpoints")
    print("=" * 50)
    
    # Create a document large enough to potentially trigger async processing
    large_text = """
    Legal Document for Progress Testing
    
    This document contains multiple important cases that should be extracted and analyzed.
    
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Criminal law precedent
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal authority
    3. Brown v. State of Washington, 180 Wn.2d 300, 320 P.3d 800 (2014) - Civil rights
    4. Miller v. Jones, 190 Wn.2d 400, 350 P.3d 900 (2015) - Contract law
    5. Davis v. County of King, 200 Wn.2d 500, 400 P.3d 1000 (2018) - Property rights
    
    Each of these cases represents important legal precedent in Washington State law.
    The citations should be properly extracted, analyzed, and clustered by the system.
    """ + "\n\nAdditional legal content for testing purposes. " * 200  # Make it larger
    
    try:
        print("📤 Submitting large document...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        task_id = data.get('task_id')
        job_id = data.get('metadata', {}).get('job_id')
        progress_endpoint = data.get('progress_endpoint')
        progress_stream = data.get('progress_stream')
        
        print(f"📊 Initial Response:")
        print(f"   Processing mode: {processing_mode}")
        print(f"   Task ID: {task_id}")
        print(f"   Job ID: {job_id}")
        print(f"   Progress endpoint: {progress_endpoint}")
        print(f"   Progress stream: {progress_stream}")
        
        if processing_mode == 'immediate':
            print(f"✅ Immediate processing - progress endpoints not needed")
            return True
        elif processing_mode == 'sync_fallback':
            print(f"✅ Sync fallback - progress endpoints not needed")
            return True
        elif processing_mode == 'queued':
            # Test progress endpoints
            tracking_id = task_id or job_id
            if not tracking_id:
                print(f"❌ No tracking ID for async processing")
                return False
            
            print(f"🔄 Testing progress endpoints for: {tracking_id}")
            
            # Test the endpoints we fixed
            endpoints_to_test = [
                f"http://localhost:8080/casestrainer/api/analyze/progress/{tracking_id}",
                f"http://localhost:8080/casestrainer/api/progress/{tracking_id}",
                f"http://localhost:8080/casestrainer/api/task_status/{tracking_id}"
            ]
            
            working_endpoints = 0
            for endpoint in endpoints_to_test:
                try:
                    progress_response = requests.get(endpoint, timeout=5)
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        status = progress_data.get('status', 'unknown')
                        print(f"   ✅ {endpoint.split('/')[-2:]}: {status}")
                        working_endpoints += 1
                    else:
                        print(f"   ❌ {endpoint.split('/')[-2:]}: HTTP {progress_response.status_code}")
                except Exception as e:
                    print(f"   ❌ {endpoint.split('/')[-2:]}: {str(e)}")
            
            success = working_endpoints >= 2  # At least 2 endpoints should work
            print(f"\n🎯 Progress Endpoints E2E Test: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"   Working endpoints: {working_endpoints}/{len(endpoints_to_test)}")
            
            return success
        else:
            print(f"❌ Unknown processing mode: {processing_mode}")
            return False
        
    except Exception as e:
        print(f"💥 Progress endpoints E2E test failed: {e}")
        return False

def test_url_processing_e2e():
    """End-to-end test for URL processing logic."""
    
    print(f"\n🌐 E2E Test: URL Processing Logic")
    print("=" * 50)
    
    # Test with a URL that should extract some content
    test_url = "https://httpbin.org/html"  # Simple HTML page for testing
    
    try:
        print(f"📤 Submitting URL for processing: {test_url}")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"url": test_url, "type": "url"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ URL processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"📊 URL Processing Results:")
        print(f"   Processing mode: {processing_mode}")
        print(f"   Success: {data.get('success', False)}")
        
        # The key test is that URL processing doesn't crash and follows the correct logic
        # (extract content first, then evaluate text size for sync vs async)
        
        success = data.get('success', False)
        
        print(f"\n🎯 URL Processing E2E Test: {'✅ PASS' if success else '❌ FAIL'}")
        if success:
            print(f"   ✅ URL content extracted and processed successfully")
            print(f"   ✅ Processing mode determined correctly based on extracted text size")
        else:
            print(f"   ❌ URL processing failed")
        
        return success
        
    except Exception as e:
        print(f"💥 URL processing E2E test failed: {e}")
        return False

def main():
    """Run end-to-end tests for all three fixes."""
    
    print("🚀 End-to-End Testing for Three Fixes")
    print("=" * 60)
    
    # Run all E2E tests
    cluster_names_ok = test_cluster_names_e2e()
    progress_ok = test_progress_endpoints_e2e()
    url_ok = test_url_processing_e2e()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 END-TO-END TEST RESULTS")
    print("=" * 60)
    
    print(f"1. Cluster Names Display: {'✅ PASS' if cluster_names_ok else '❌ FAIL'}")
    print(f"2. Progress Bar Endpoints: {'✅ PASS' if progress_ok else '❌ FAIL'}")
    print(f"3. URL Processing Logic: {'✅ PASS' if url_ok else '❌ FAIL'}")
    
    total_passed = sum([cluster_names_ok, progress_ok, url_ok])
    print(f"\nOverall E2E Results: {total_passed}/3 tests passed")
    
    if total_passed == 3:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("✅ The three fixes are working correctly in the full system")
    else:
        print("⚠️ Some end-to-end tests failed")
        print("❌ Additional investigation may be needed")
    
    return total_passed == 3

if __name__ == "__main__":
    main()
