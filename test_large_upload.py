#!/usr/bin/env python3
"""
Test large file upload to trigger async processing
"""

import requests
import json
import time
import ssl

def test_large_file_upload():
    """Test large file upload to trigger async processing"""
    
    base_url = "https://wolf.law.uw.edu"
    api_url = f"{base_url}/casestrainer/api"
    
    print("🚀 Testing Large File Upload to Trigger Async Processing")
    print("=" * 70)
    
    # Create a larger test file (over 50 words to trigger async)
    test_content = """
    This is a comprehensive test legal document for CaseStrainer that contains multiple citations and legal content.
    
    The Supreme Court of Washington has consistently held that appellate courts review trial court decisions for abuse of discretion. 
    In re Marriage of Littlefield, 133 Wn.2d 39, 46-47, 940 P.2d 1362 (1997). 
    A court abuses its discretion when its decision is manifestly unreasonable or based on untenable grounds.
    
    Sample citation: In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014).
    
    Another citation: State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999).
    
    Additional legal content: The standard of review for questions of law is de novo. 
    State v. Armenta, 134 Wn.2d 1, 9, 948 P.2d 1280 (1997). 
    Questions of law are reviewed independently of the trial court's determination.
    
    More citations: Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    This document contains extensive legal content to test the citation extraction system and ensure it triggers async processing.
    """ * 5  # Multiply to make it larger
    
    print(f"📄 Test file size: {len(test_content)} characters, {len(test_content.split())} words")
    
    # Test file upload (should create async task)
    print("\n🔍 Testing large file upload (should trigger async processing)...")
    try:
        # Create a temporary text file
        with open('test_large_upload.txt', 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        with open('test_large_upload.txt', 'rb') as f:
            files = {'file': ('test_large_upload.txt', f, 'text/plain')}
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
        
        print(f"✅ File upload response: {response.status_code}")
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        if result.get('task_id'):
            task_id = result['task_id']
            print(f"   🎯 Async task created! Monitoring task {task_id}...")
            
            # Monitor the task for up to 3 minutes
            for i in range(36):  # 36 * 5 seconds = 3 minutes
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
                print("   ⏰ Task monitoring timeout after 3 minutes")
        else:
            print("   ⚠️  No async task created - file processed immediately")
            if result.get('citations'):
                print(f"   Citations found: {len(result['citations'])}")
        
    except Exception as e:
        print(f"❌ File upload failed: {e}")
    
    print("\n" + "=" * 70)
    
    # Cleanup
    try:
        import os
        if os.path.exists('test_large_upload.txt'):
            os.remove('test_large_upload.txt')
    except:
        pass
    
    print("✅ Large file upload test completed!")
    return True

if __name__ == "__main__":
    test_large_file_upload()
