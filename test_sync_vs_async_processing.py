#!/usr/bin/env python3
"""
Test to debug sync vs async processing and why sync might be returning no citations.
"""

import requests
import time
import json

def test_processing_mode_logic():
    """Test what determines sync vs async processing."""
    
    print("🔍 Testing Processing Mode Logic")
    print("=" * 50)
    
    # Test with different document sizes
    base_citation = "State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)"
    
    test_cases = [
        {"name": "Tiny (100 chars)", "text": f"Case: {base_citation}.", "expected_mode": "immediate"},
        {"name": "Small (500 chars)", "text": f"Legal analysis: {base_citation}. " * 10, "expected_mode": "immediate"},
        {"name": "Medium (2000 chars)", "text": f"Legal document: {base_citation}. " * 50, "expected_mode": "immediate/queued"},
        {"name": "Large (10000 chars)", "text": f"Large legal document: {base_citation}. " * 200, "expected_mode": "queued"},
        {"name": "Very Large (50000 chars)", "text": f"Very large legal document: {base_citation}. " * 1000, "expected_mode": "queued"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        text_length = len(test_case['text'])
        print(f"   Text length: {text_length:,} characters")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_case['text'], "type": "text"},
                timeout=60
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code != 200:
                print(f"   ❌ API Error: {response.status_code}")
                continue
            
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            success = data.get('success', False)
            citations = data.get('citations', [])
            
            print(f"   📊 Results:")
            print(f"     Processing mode: {processing_mode}")
            print(f"     Response time: {response_time:.2f}s")
            print(f"     Success: {success}")
            print(f"     Citations found: {len(citations)}")
            print(f"     Expected mode: {test_case['expected_mode']}")
            
            # Handle async processing
            if processing_mode == 'queued':
                job_id = data.get('metadata', {}).get('job_id')
                if job_id:
                    print(f"   ⏳ Async processing job: {job_id}")
                    
                    # Wait for async completion
                    for attempt in range(15):
                        time.sleep(2)
                        status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            
                            if status == 'completed':
                                async_citations = status_data.get('citations', [])
                                async_success = status_data.get('success', False)
                                print(f"   ✅ Async completed:")
                                print(f"     Citations: {len(async_citations)}")
                                print(f"     Success: {async_success}")
                                break
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"   ❌ Async failed: {error}")
                                break
                            else:
                                print(f"     Attempt {attempt + 1}: {status}")
                    else:
                        print(f"   ❌ Async timeout after 30 seconds")
            
            # Check for issues
            if processing_mode == 'immediate' and len(citations) == 0:
                print(f"   ⚠️ SYNC PROCESSING RETURNED NO CITATIONS")
                print(f"   🔍 This might be the issue you're seeing")
                
                # Debug: Check if there's error information
                if 'error' in data:
                    print(f"     Error: {data['error']}")
                
                # Check metadata for clues
                metadata = data.get('metadata', {})
                print(f"     Metadata keys: {list(metadata.keys())}")
                
                if 'processing_error' in metadata:
                    print(f"     Processing error: {metadata['processing_error']}")
            
        except Exception as e:
            print(f"   💥 Exception: {e}")

def test_sync_processing_pipeline():
    """Test the sync processing pipeline specifically."""
    
    print(f"\n🔄 Testing Sync Processing Pipeline")
    print("=" * 50)
    
    # Simple document that should definitely work in sync mode
    simple_text = "The case State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) established important precedent."
    
    print(f"📝 Testing simple sync processing:")
    print(f"   Text: {simple_text}")
    print(f"   Length: {len(simple_text)} characters")
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": simple_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        success = data.get('success', False)
        citations = data.get('citations', [])
        
        print(f"\n   📊 Sync Processing Results:")
        print(f"     Processing mode: {processing_mode}")
        print(f"     Success: {success}")
        print(f"     Citations: {len(citations)}")
        
        if len(citations) > 0:
            print(f"   ✅ Sync processing working correctly")
            for i, citation in enumerate(citations[:3], 1):
                print(f"     {i}. {citation.get('citation', 'N/A')}")
            return True
        else:
            print(f"   ❌ Sync processing returned no citations")
            
            # Deep debug
            print(f"\n   🔍 Debug Information:")
            print(f"     Full response keys: {list(data.keys())}")
            
            if 'error' in data:
                print(f"     Error: {data['error']}")
            
            metadata = data.get('metadata', {})
            print(f"     Metadata: {metadata}")
            
            # Check if there's any processing information
            progress_data = data.get('progress_data', {})
            if progress_data:
                print(f"     Progress data: {progress_data}")
            
            return False
        
    except Exception as e:
        print(f"   💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_vs_sync_fallback():
    """Test async processing vs sync fallback behavior."""
    
    print(f"\n🔀 Testing Async vs Sync Fallback")
    print("=" * 50)
    
    # Large document that should trigger async processing
    large_text = """
    LEGAL MEMORANDUM
    
    Re: Comprehensive Citation Analysis
    
    This memorandum provides a detailed analysis of several important legal precedents
    that have shaped the current state of the law. The following cases are particularly
    relevant to our analysis:
    
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - This case established
       important precedent regarding criminal procedure and the application of 
       constitutional protections in state court proceedings.
    
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - This case
       addressed municipal authority and the scope of local government powers in
       regulating commercial activities.
    
    3. Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954) -
       The landmark civil rights case that overturned the "separate but equal" doctrine
       and mandated integration of public schools.
    
    The analysis of these cases reveals several important legal principles that continue
    to influence modern jurisprudence. Each case represents a significant development
    in its respective area of law and continues to be cited frequently in contemporary
    legal proceedings.
    """ * 10  # Make it large enough to potentially trigger async
    
    print(f"📝 Testing large document processing:")
    print(f"   Length: {len(large_text):,} characters")
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text, "type": "text"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"   ❌ API Error: {response.status_code}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"   📊 Initial Response:")
        print(f"     Processing mode: {processing_mode}")
        
        if processing_mode == 'queued':
            print(f"   ✅ Async processing triggered correctly")
            
            job_id = data.get('metadata', {}).get('job_id')
            if job_id:
                print(f"   ⏳ Waiting for async completion: {job_id}")
                
                for attempt in range(20):
                    time.sleep(2)
                    status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        
                        if status == 'completed':
                            citations = status_data.get('citations', [])
                            success = status_data.get('success', False)
                            print(f"   ✅ Async processing completed:")
                            print(f"     Citations: {len(citations)}")
                            print(f"     Success: {success}")
                            return len(citations) > 0
                        elif status == 'failed':
                            error = status_data.get('error', 'Unknown error')
                            print(f"   ❌ Async processing failed: {error}")
                            return False
                        else:
                            print(f"     Attempt {attempt + 1}: {status}")
                else:
                    print(f"   ❌ Async processing timeout")
                    return False
        
        elif processing_mode == 'immediate':
            print(f"   ⚠️ Large document processed synchronously")
            citations = data.get('citations', [])
            success = data.get('success', False)
            
            print(f"     Citations: {len(citations)}")
            print(f"     Success: {success}")
            
            if len(citations) == 0:
                print(f"   ❌ SYNC FALLBACK RETURNED NO CITATIONS")
                print(f"   🔍 This is likely the issue you're experiencing")
            
            return len(citations) > 0
        
        elif processing_mode == 'sync_fallback':
            print(f"   ⚠️ Sync fallback triggered")
            citations = data.get('citations', [])
            success = data.get('success', False)
            
            print(f"     Citations: {len(citations)}")
            print(f"     Success: {success}")
            
            if len(citations) == 0:
                print(f"   ❌ SYNC FALLBACK RETURNED NO CITATIONS")
                print(f"   🔍 This is likely the root cause of your issue")
            
            return len(citations) > 0
        
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return False

def main():
    """Run comprehensive sync vs async processing tests."""
    
    print("🚀 Debugging Sync vs Async Processing Issues")
    print("=" * 60)
    
    # Run tests
    test_processing_mode_logic()
    sync_ok = test_sync_processing_pipeline()
    async_ok = test_async_vs_sync_fallback()
    
    print("\n" + "=" * 60)
    print("📋 SYNC VS ASYNC PROCESSING DEBUG RESULTS")
    print("=" * 60)
    
    print(f"1. Sync Processing Pipeline: {'✅ WORKING' if sync_ok else '❌ BROKEN'}")
    print(f"2. Async/Fallback Processing: {'✅ WORKING' if async_ok else '❌ BROKEN'}")
    
    if not sync_ok:
        print("\n🔍 SYNC PROCESSING ISSUE IDENTIFIED:")
        print("   ❌ Sync processing is returning no citations")
        print("   🔧 Possible causes:")
        print("     - Citation extraction pipeline broken in sync mode")
        print("     - UnifiedCitationProcessorV2 not working correctly")
        print("     - Response structure issues in sync processing")
        print("     - Progress tracking interfering with citation extraction")
    
    if not async_ok:
        print("\n🔍 ASYNC/FALLBACK PROCESSING ISSUE IDENTIFIED:")
        print("   ❌ Async or sync fallback processing is failing")
        print("   🔧 Possible causes:")
        print("     - Redis connectivity issues forcing sync fallback")
        print("     - Sync fallback pipeline broken")
        print("     - Async task processing broken")
    
    return sync_ok and async_ok

if __name__ == "__main__":
    main()
