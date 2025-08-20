#!/usr/bin/env python3
"""
Test PDF upload to see if optimized processor prevents hanging
"""

import requests
import json
import time
import ssl

def test_pdf_upload():
    """Test PDF upload to see if optimized processor works"""
    
    base_url = "https://wolf.law.uw.edu"
    api_url = f"{base_url}/casestrainer/api"
    
    print("🚀 Testing PDF Upload with Optimized Processor")
    print("=" * 60)
    
    # Create a simple PDF-like test file (we'll use a text file with .pdf extension)
    # In production, this would be a real PDF, but for testing we'll simulate
    test_content = """
    This is a test legal document for CaseStrainer.
    
    Sample citation: In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014).
    
    Another citation: State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999).
    
    This document contains multiple citations to test the extraction system.
    
    Additional legal content to make it substantial enough for processing.
    """ * 3  # Make it larger
    
    print(f"📄 Test content size: {len(test_content)} characters, {len(test_content.split())} words")
    
    # Test PDF upload (should create async task due to file size/type)
    print("\n🔍 Testing PDF upload (should create async task)...")
    try:
        # Create a temporary file with .pdf extension
        with open('test_pdf_upload.pdf', 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        with open('test_pdf_upload.pdf', 'rb') as f:
            files = {'file': ('test_pdf_upload.pdf', f, 'application/pdf')}
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
        
        print(f"✅ PDF upload response: {response.status_code}")
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        if result.get('task_id'):
            task_id = result['task_id']
            print(f"   🎯 Async task created! Monitoring task {task_id}...")
            
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
                            
                            # Show some citation details
                            if citations:
                                print(f"   📋 Sample citations:")
                                for i, citation in enumerate(citations[:3]):
                                    print(f"     {i+1}. {citation.get('text', 'N/A')[:100]}...")
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
        else:
            print("   ⚠️  No async task created - file processed immediately")
            if result.get('citations'):
                print(f"   Citations found: {len(result['citations'])}")
                for i, citation in enumerate(result['citations'][:3]):
                    print(f"     Citation {i+1}: {citation.get('text', 'N/A')[:80]}...")
        
    except Exception as e:
        print(f"❌ PDF upload failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Cleanup
    try:
        import os
        if os.path.exists('test_pdf_upload.pdf'):
            os.remove('test_pdf_upload.pdf')
    except:
        pass
    
    print("✅ PDF upload test completed!")
    return True

if __name__ == "__main__":
    test_pdf_upload()
