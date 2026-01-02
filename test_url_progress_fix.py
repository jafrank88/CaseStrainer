#!/usr/bin/env python3
"""
Test URL processing with progress tracking
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_url_progress():
    """Test URL processing with progress tracking"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Test URL
    test_url = "https://supreme.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing URL processing with progress tracking...")
    print(f"URL: {test_url}")
    print(f"API: {base_url}")
    
    # Start analysis
    analyze_data = {
        "type": "url",
        "url": test_url
    }
    
    print("\n=== Starting Analysis ===")
    response = requests.post(f"{base_url}/analyze", json=analyze_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to start analysis: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    request_id = result.get('request_id')
    
    print(f"✅ Analysis started")
    print(f"Request ID: {request_id}")
    print(f"Processing strategy: {result.get('processing_strategy')}")
    
    # Poll for progress
    print("\n=== Monitoring Progress ===")
    max_wait = 120  # 2 minutes max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            status_response = requests.get(f"{base_url}/task_status/{request_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                
                progress = status.get('progress', 0)
                message = status.get('message', 'Unknown')
                step = status.get('current_step', 'Unknown')
                
                print(f"Progress: {progress}% - {step} - {message}")
                
                if status.get('status') == 'completed':
                    print("\n✅ Processing completed!")
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Processing failed: {status.get('message', 'Unknown error')}")
                    break
                    
            time.sleep(2)  # Poll every 2 seconds
            
        except Exception as e:
            print(f"Error polling status: {e}")
            break
    
    # Get final results
    if time.time() - start_time < max_wait:
        print("\n=== Getting Final Results ===")
        verification_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
        
        if verification_response.status_code == 200:
            verification = verification_response.json()
            citations = verification.get('citations', [])
            clusters = verification.get('clusters', [])
            
            print(f"✅ Retrieved final results")
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            # Show first few citations
            if citations:
                print("\nFirst 3 citations:")
                for i, cit in enumerate(citations[:3]):
                    case_name = cit.get('case_name', 'N/A')
                    citation_text = cit.get('citation', 'N/A')
                    print(f"  {i+1}. {case_name} - {citation_text}")
            
        else:
            print(f"❌ Failed to get final results: {verification_response.status_code}")
    else:
        print("\n⏰ Timeout - processing took too long")

if __name__ == "__main__":
    test_url_progress()
