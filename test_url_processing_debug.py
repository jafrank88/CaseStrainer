#!/usr/bin/env python3
"""
Debug script to investigate URL processing getting stuck at 5%
"""

import sys
import os
import time
import requests
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_url_processing_direct():
    """Test URL processing directly to identify where it gets stuck"""
    
    # The problematic PDF URL
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 DEBUGGING URL PROCESSING - STUCK AT 5%")
    print("=" * 60)
    print(f"PDF URL: {pdf_url}")
    print()
    
    # Test 1: Check if URL is accessible
    print("📡 Test 1: URL Accessibility")
    try:
        # Use GET with allow_redirects=True like the fixed code
        response = requests.get(pdf_url, timeout=10, allow_redirects=True)
        print(f"   Status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        if response.status_code == 200:
            print("   ✅ URL is accessible")
        else:
            print(f"   ❌ URL returned {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ URL access failed: {e}")
        return
    
    print()
    
    # Test 2: Try direct API call to see progress updates
    print("🚀 Test 2: Direct API Processing")
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    
    payload = {
        "url": pdf_url,
        "processing_strategy": "full_with_verification"
    }
    
    try:
        print("   Submitting URL for processing...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            request_id = result.get('request_id')
            print(f"   ✅ Submitted successfully, request_id: {request_id}")
            
            # Monitor progress
            status_url = f"http://localhost:5000/casestrainer/api/task_status/{request_id}"
            print(f"   Monitoring progress at: {status_url}")
            print()
            
            max_wait = 120  # 2 minutes max
            start_time = time.time()
            last_progress = 0
            
            while time.time() - start_time < max_wait:
                try:
                    status_response = requests.get(status_url, timeout=10)
                    if status_response.status_code == 200:
                        status = status_response.json()
                        progress = status.get('progress', 0)
                        status_text = status.get('status', 'unknown')
                        step = status.get('current_step', 'unknown')
                        
                        if progress != last_progress:
                            print(f"   📊 Progress: {progress}% - {status_text} ({step})")
                            last_progress = progress
                        
                        if progress >= 100 or status_text in ['completed', 'error']:
                            print(f"   🏁 Processing finished: {status_text}")
                            break
                        
                        # If stuck at 5% for more than 30 seconds, investigate
                        if progress == 5 and (time.time() - start_time) > 30:
                            print(f"   🚨 STUCK at 5% for >30 seconds - investigating...")
                            print(f"   Status: {status}")
                            break
                    
                    time.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    print(f"   ⚠️  Status check failed: {e}")
                    time.sleep(5)
            
            # Get final status
            if time.time() - start_time >= max_wait:
                print("   ⏰ Timeout reached after 2 minutes")
            
            final_response = requests.get(status_url, timeout=10)
            if final_response.status_code == 200:
                final_status = final_response.json()
                print(f"   📋 Final Status: {json.dumps(final_status, indent=2)}")
                
        else:
            print(f"   ❌ API submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
    
    print()
    print("🔍 POSSIBLE CAUSES FOR 5% STUCK:")
    print("1. PDF extraction hanging (pdfplumber/fitz issues)")
    print("2. Redis connection problems in async worker")
    print("3. Citation extraction pipeline failure")
    print("4. Verification system timeout")
    print("5. RQ worker not processing the job")

if __name__ == "__main__":
    test_url_processing_direct()
