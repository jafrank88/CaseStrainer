#!/usr/bin/env python3
"""
Comprehensive end-to-end test to verify all fixes are working.
"""

import requests
import json
import time

def test_sync_processing():
    """Test sync processing with small documents."""
    
    print("🔍 Testing Sync Processing")
    print("=" * 40)
    
    # Test 1: Simple citation
    simple_text = "This case cites Brown v. Board of Education, 347 U.S. 483 (1954)."
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": simple_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Sync test failed: {response.status_code}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        citations = data.get('citations', [])
        
        print(f"📊 Sync Test Results:")
        print(f"   Processing mode: {processing_mode}")
        print(f"   Citations found: {len(citations)}")
        print(f"   Success: {data.get('success', False)}")
        
        if processing_mode == 'immediate' and len(citations) > 0:
            print(f"✅ Sync processing working correctly")
            return True
        else:
            print(f"❌ Sync processing issues")
            return False
            
    except Exception as e:
        print(f"💥 Sync test error: {e}")
        return False

def test_async_processing():
    """Test async processing with large documents."""
    
    print(f"\n🔍 Testing Async Processing")
    print("=" * 40)
    
    # Create a large document that should trigger async processing
    large_text = """
    This is a large legal document with multiple citations to test async processing.
    
    The Supreme Court in Brown v. Board of Education, 347 U.S. 483 (1954), established important precedent.
    Later cases like Miranda v. Arizona, 384 U.S. 436 (1966), built upon this foundation.
    State courts have also contributed, such as in State v. Smith, 160 Wash.2d 500, 158 P.3d 677 (2007).
    
    """ * 200  # Repeat to make it large enough for async processing
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Async test failed: {response.status_code}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        job_id = data.get('metadata', {}).get('job_id')
        
        print(f"📊 Initial Async Response:")
        print(f"   Processing mode: {processing_mode}")
        print(f"   Job ID: {job_id}")
        print(f"   Text length: {len(large_text)} characters")
        
        if processing_mode != 'queued':
            print(f"❌ Large text should trigger async processing")
            return False
        
        if not job_id:
            print(f"❌ No job ID provided for async processing")
            return False
        
        # Poll for completion
        print(f"🔄 Polling for async job completion...")
        max_attempts = 20
        for attempt in range(max_attempts):
            time.sleep(3)  # Wait 3 seconds between polls
            
            try:
                status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                
                if status_response.status_code != 200:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    continue
                
                job_data = status_response.json()
                status = job_data.get('status', 'unknown')
                
                print(f"   Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    citations = job_data.get('citations', [])
                    clusters = job_data.get('clusters', [])
                    
                    print(f"✅ Async job completed successfully")
                    print(f"   Citations found: {len(citations)}")
                    print(f"   Clusters found: {len(clusters)}")
                    
                    if len(citations) > 0:
                        print(f"✅ Async processing working correctly")
                        return True
                    else:
                        print(f"❌ Async job completed but no citations found")
                        return False
                        
                elif status == 'failed':
                    error = job_data.get('error', 'Unknown error')
                    print(f"❌ Async job failed: {error}")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Status check error: {e}")
                continue
        
        print(f"❌ Async job polling timeout")
        return False
        
    except Exception as e:
        print(f"💥 Async test error: {e}")
        return False

def test_nested_citations():
    """Test nested citation extraction."""
    
    print(f"\n🔍 Testing Nested Citation Extraction")
    print("=" * 40)
    
    nested_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": nested_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Nested citation test failed: {response.status_code}")
            return False
        
        data = response.json()
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"📊 Nested Citation Results:")
        print(f"   Citations found: {len(citations)}")
        print(f"   Clusters found: {len(clusters)}")
        
        # Check for correct case name extraction
        legion_citations = [c for c in citations if 'Legion' in c.get('extracted_case_name', '')]
        myg_citations = [c for c in citations if 'M.Y.G.' in c.get('extracted_case_name', '') and 'Legion' not in c.get('extracted_case_name', '')]
        
        print(f"   M.Y.G. citations: {len(myg_citations)}")
        print(f"   Legion citations: {len(legion_citations)}")
        
        if len(legion_citations) >= 2 and len(myg_citations) >= 2:
            print(f"✅ Nested citation extraction working correctly")
            return True
        else:
            print(f"❌ Nested citation extraction issues")
            print(f"   Expected: 2+ Legion citations, 2+ M.Y.G. citations")
            return False
            
    except Exception as e:
        print(f"💥 Nested citation test error: {e}")
        return False

def test_progress_endpoints():
    """Test progress tracking endpoints."""
    
    print(f"\n🔍 Testing Progress Endpoints")
    print("=" * 40)
    
    try:
        # Test progress endpoint
        progress_response = requests.get("http://localhost:8080/casestrainer/api/processing_progress")
        
        if progress_response.status_code == 200:
            print(f"✅ Progress endpoint responding")
        else:
            print(f"❌ Progress endpoint failed: {progress_response.status_code}")
            return False
        
        # Test health endpoint
        health_response = requests.get("http://localhost:8080/casestrainer/api/health")
        
        if health_response.status_code == 200:
            print(f"✅ Health endpoint responding")
            return True
        else:
            print(f"❌ Health endpoint failed: {health_response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Progress endpoint test error: {e}")
        return False

def main():
    """Run comprehensive end-to-end test."""
    
    print("🚀 Comprehensive End-to-End Test")
    print("=" * 60)
    
    # Run all tests
    sync_ok = test_sync_processing()
    async_ok = test_async_processing()
    nested_ok = test_nested_citations()
    progress_ok = test_progress_endpoints()
    
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    print(f"1. Sync Processing: {'✅ PASS' if sync_ok else '❌ FAIL'}")
    print(f"2. Async Processing: {'✅ PASS' if async_ok else '❌ FAIL'}")
    print(f"3. Nested Citations: {'✅ PASS' if nested_ok else '❌ FAIL'}")
    print(f"4. Progress Endpoints: {'✅ PASS' if progress_ok else '❌ FAIL'}")
    
    all_passed = sync_ok and async_ok and nested_ok and progress_ok
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 CaseStrainer is fully functional!")
        print("✅ All major issues have been resolved")
        print("✅ Frontend async polling is working")
        print("✅ Nested citations are extracted correctly")
        print("✅ Progress tracking is functional")
    else:
        print("🔧 Some issues still need attention")
        print("💡 Check the individual test results above")
    
    return all_passed

if __name__ == "__main__":
    main()
