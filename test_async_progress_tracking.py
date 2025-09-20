#!/usr/bin/env python3
"""
Test async processing and progress tracking to identify the issue.
"""

import requests
import time
import json

def test_async_progress_tracking():
    """Test async processing with progress tracking."""
    
    # Large document that should trigger async processing
    large_text = """
    Legal Document for Async Testing
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """ + "\n\nAdditional content. " * 2000  # Make it very large
    
    print("🧪 Testing Async Processing and Progress Tracking")
    print("=" * 60)
    print(f"📄 Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
    print()
    
    # Step 1: Submit for processing
    print("📤 Step 1: Submitting for async processing...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Failed to submit: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
        data = response.json()
        print(f"  Response keys: {list(data.keys())}")
        print(f"  Success: {data.get('success')}")
        print(f"  Message: {data.get('message')}")
        
        # Check if we got a task_id for async processing
        task_id = data.get('task_id')
        job_id = data.get('metadata', {}).get('job_id')
        processing_mode = data.get('metadata', {}).get('processing_mode')
        
        print(f"  Task ID: {task_id}")
        print(f"  Job ID: {job_id}")
        print(f"  Processing mode: {processing_mode}")
        
        if not task_id and not job_id:
            print("  ⚠️ No task_id or job_id - might be sync fallback")
            citations = data.get('citations', [])
            print(f"  Citations found: {len(citations)}")
            if len(citations) > 0:
                print("  ✅ Sync fallback working")
                return True
            else:
                print("  ❌ No citations found")
                return False
        
        # Use task_id or job_id for tracking
        tracking_id = task_id or job_id
        print(f"  ✅ Submitted successfully, tracking ID: {tracking_id}")
        
    except Exception as e:
        print(f"  💥 Submission failed: {e}")
        return False
    
    # Step 2: Check progress endpoints
    print(f"\n📊 Step 2: Testing Progress Endpoints")
    
    # Check if we have progress endpoints available
    progress_endpoint = data.get('progress_endpoint')
    progress_stream = data.get('progress_stream')
    
    print(f"  Progress endpoint: {progress_endpoint}")
    print(f"  Progress stream: {progress_stream}")
    
    if progress_endpoint:
        print(f"  🔄 Testing progress endpoint: {progress_endpoint}")
        try:
            progress_response = requests.get(f"http://localhost:8080{progress_endpoint}")
            print(f"    Status: {progress_response.status_code}")
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f"    Progress: {progress_data}")
            else:
                print(f"    Error: {progress_response.text}")
        except Exception as e:
            print(f"    Exception: {e}")
    
    # Step 3: Poll for completion
    print(f"\n⏳ Step 3: Polling for Completion")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        print(f"  Attempt {attempt + 1}/{max_attempts}")
        
        try:
            # Try different progress endpoints
            endpoints_to_try = []
            
            if progress_endpoint:
                endpoints_to_try.append(f"http://localhost:8080{progress_endpoint}")
            
            # Try standard RQ job status
            endpoints_to_try.extend([
                f"http://localhost:8080/casestrainer/api/task_status/{tracking_id}",
                f"http://localhost:8080/casestrainer/api/progress/{tracking_id}",
                f"http://localhost:8080/casestrainer/api/analyze/progress/{tracking_id}",
                f"http://localhost:8080/casestrainer/api/analyze/results/{tracking_id}"
            ])
            
            for endpoint in endpoints_to_try:
                try:
                    check_response = requests.get(endpoint, timeout=5)
                    print(f"    {endpoint}: {check_response.status_code}")
                    
                    if check_response.status_code == 200:
                        check_data = check_response.json()
                        status = check_data.get('status', 'unknown')
                        print(f"      Status: {status}")
                        
                        if status in ['completed', 'finished', 'success']:
                            print(f"      ✅ Job completed!")
                            citations = check_data.get('citations', [])
                            result = check_data.get('result', {})
                            if isinstance(result, dict):
                                citations = result.get('citations', citations)
                            
                            print(f"      Citations found: {len(citations)}")
                            if len(citations) > 0:
                                print("      🎉 SUCCESS: Async processing working!")
                                return True
                            else:
                                print("      ⚠️ Job completed but no citations found")
                                return False
                        elif status in ['failed', 'error']:
                            print(f"      ❌ Job failed: {check_data}")
                            return False
                        else:
                            print(f"      🔄 Job still running: {status}")
                            break  # Found a working endpoint, break inner loop
                            
                except requests.exceptions.RequestException:
                    pass  # Try next endpoint
            
            time.sleep(2)
            
        except Exception as e:
            print(f"    💥 Polling error: {e}")
            time.sleep(2)
    
    print("  ❌ Timeout: Job didn't complete or couldn't get status")
    return False

def main():
    """Run async progress tracking test."""
    success = test_async_progress_tracking()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Async progress tracking test")

if __name__ == "__main__":
    main()
