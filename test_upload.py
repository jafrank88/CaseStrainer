#!/usr/bin/env python3
"""
Test file upload to CaseStrainer Production API
"""

import requests
import json
import time
import ssl

def test_file_upload():
    """Test file upload to production API"""
    
    # Disable SSL verification for testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    base_url = "https://wolf.law.uw.edu"
    api_url = f"{base_url}/casestrainer/api"
    
    print("🚀 Testing File Upload to CaseStrainer Production API")
    print("=" * 60)
    
    # Create a simple test file
    test_content = """
    This is a test legal document for CaseStrainer.
    
    Sample citation: In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014).
    
    Another citation: State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999).
    
    This document contains multiple citations to test the extraction system.
    """
    
    # Test 1: Text analysis (should be immediate)
    print("🔍 Testing text analysis (immediate processing)...")
    try:
        data = {
            "type": "text",
            "text": test_content
        }
        
        response = requests.post(
            f"{api_url}/analyze",
            json=data,
            headers={
                'User-Agent': 'CaseStrainer-Tester/1.0',
                'Accept': 'application/json'
            },
            verify=False,
            timeout=30
        )
        
        print(f"✅ Text analysis: {response.status_code}")
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Task ID: {result.get('task_id')}")
        
        if result.get('citations'):
            print(f"   Citations found: {len(result['citations'])}")
            for i, citation in enumerate(result['citations'][:3]):
                print(f"     Citation {i+1}: {citation.get('text', 'N/A')[:80]}...")
        
    except Exception as e:
        print(f"❌ Text analysis failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test 2: File upload (should create async task)
    print("🔍 Testing file upload (async processing)...")
    try:
        # Create a temporary text file
        with open('test_upload.txt', 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        with open('test_upload.txt', 'rb') as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            data = {'type': 'file'}
            
            response = requests.post(
                f"{api_url}/analyze",
                files=files,
                data=data,
                headers={
                    'User-Agent': 'CaseStrainer-Tester/1.0',
                    'Accept': 'application/json'
                },
                verify=False,
                timeout=30
            )
        
        print(f"✅ File upload: {response.status_code}")
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Task ID: {result.get('task_id')}")
        
        if result.get('task_id'):
            task_id = result['task_id']
            print(f"   Monitoring task {task_id}...")
            
            # Monitor the task for up to 2 minutes
            for i in range(24):  # 24 * 5 seconds = 2 minutes
                time.sleep(5)
                
                try:
                    status_response = requests.get(
                        f"{api_url}/status/{task_id}",
                        headers={
                            'User-Agent': 'CaseStrainer-Tester/1.0',
                            'Accept': 'application/json'
                        },
                        verify=False,
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        current_status = status_result.get('status')
                        print(f"   [{i*5}s] Status: {current_status}")
                        
                        if current_status == 'completed':
                            citations = status_result.get('citations', [])
                            clusters = status_result.get('clusters', [])
                            print(f"   ✅ Task completed! Citations: {len(citations)}, Clusters: {len(clusters)}")
                            break
                        elif current_status == 'failed':
                            error = status_result.get('error', 'Unknown error')
                            print(f"   ❌ Task failed: {error}")
                            break
                        elif current_status == 'processing':
                            progress = status_result.get('progress', 'N/A')
                            print(f"   🔄 Processing... Progress: {progress}")
                    else:
                        print(f"   ❌ Status check failed: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Status check error: {e}")
            
            else:
                print("   ⏰ Task monitoring timeout after 2 minutes")
        
    except Exception as e:
        print(f"❌ File upload failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Cleanup
    try:
        import os
        if os.path.exists('test_upload.txt'):
            os.remove('test_upload.txt')
    except:
        pass
    
    print("✅ File upload test completed!")
    return True

if __name__ == "__main__":
    test_file_upload()
