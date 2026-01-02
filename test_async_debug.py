#!/usr/bin/env python3
"""
Test async processing directly to debug the issue
"""

import requests
import json
import time

def test_async_processing():
    """Test async processing with a simple text"""
    
    print("🔍 TESTING ASYNC PROCESSING DIRECTLY")
    print("=" * 50)
    
    # Test with a simple text that should trigger async
    test_text = """
    This is a test document with multiple citations to trigger async processing.
    In Foss v. National Marine Fisheries Service, 161 F.3d 584 (9th Cir. 1998), the court held that...
    Another case is Smith v. Jones, 123 F.2d 456 (9th Cir. 1998), which established...
    Finally, in Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that...
    This should be enough text to trigger async processing since it's over 5KB.
    """ * 200  # Repeat to make it over 5KB
    
    print(f"Text length: {len(test_text)} characters")
    
    # Test the analyze endpoint
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'text',
        'text': test_text,
        'enable_verification': True
    }
    
    print(f"\n📋 Making API call to: {api_url}")
    print(f"Data size: {len(json.dumps(data))} bytes")
    
    try:
        response = requests.post(api_url, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Initial Response Analysis:")
            print(f"Success: {result.get('success')}")
            print(f"Task ID: {result.get('task_id')}")
            print(f"Request ID: {result.get('request_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
            print(f"Citations returned: {len(result.get('citations', []))}")
            print(f"Clusters returned: {len(result.get('clusters', []))}")
            
            # Check if it's actually doing async
            task_id = result.get('task_id')
            processing_mode = result.get('metadata', {}).get('processing_mode')
            
            if processing_mode == 'queued' and task_id:
                print(f"\n✅ Async processing triggered correctly")
                print(f"Task ID: {task_id}")
                
                # Test progress polling
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                
                print(f"\n🔄 Testing progress polling...")
                for i in range(10):  # Poll for 10 attempts
                    try:
                        progress_response = requests.get(progress_url, timeout=10)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            print(f"Attempt {i+1}: Status={progress_data.get('status')}, Progress={progress_data.get('progress_percent')}%, Message={progress_data.get('current_message')}")
                            
                            if progress_data.get('status') == 'completed':
                                print(f"✅ Async processing completed!")
                                print(f"Citations found: {len(progress_data.get('citations', []))}")
                                break
                        else:
                            print(f"Attempt {i+1}: Progress API returned {progress_response.status_code}")
                    except Exception as e:
                        print(f"Attempt {i+1}: Error polling progress: {e}")
                    
                    time.sleep(2)  # Wait 2 seconds between polls
            else:
                print(f"\n❌ Async processing NOT triggered")
                print(f"Expected: processing_mode='queued' with task_id")
                print(f"Actual: processing_mode='{processing_mode}', task_id='{task_id}'")
                
                if len(result.get('citations', [])) > 0:
                    print(f"ℹ️  But citations were returned immediately - sync fallback worked")
                else:
                    print(f"❌ No citations returned and no async processing - BROKEN")
                    
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_async_processing()
