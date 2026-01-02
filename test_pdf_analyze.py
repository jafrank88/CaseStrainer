#!/usr/bin/env python3
"""
Test the analyze API with a PDF file
"""

import requests
import json
import time
import os

def test_pdf_analyze():
    """Test PDF processing through the analyze API"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"Testing PDF processing with analyze API...")
    print(f"PDF: {pdf_path}")
    print(f"API: {base_url}")
    
    # Get file size
    file_size = os.path.getsize(pdf_path)
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Prepare file upload
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        data = {
            'client_request_id': f'test-{int(time.time())}',
            'force_mode': 'sync'  # Force sync for testing
        }
        
        print(f"\n=== Uploading PDF ===")
        response = requests.post(f"{base_url}/analyze", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Failed to upload PDF: {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        request_id = result.get('request_id')
        
        print(f"✅ PDF uploaded successfully")
        print(f"Request ID: {request_id}")
        print(f"Processing strategy: {result.get('processing_strategy')}")
        print(f"Success: {result.get('success')}")
        
        # If immediate result, show it
        if result.get('citations'):
            print(f"Immediate citations: {len(result.get('citations', []))}")
    
    # Poll for progress if not immediate
    if result.get('processing_strategy') != 'immediate':
        print(f"\n=== Monitoring Progress ===")
        max_wait = 180  # 3 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(f"{base_url}/task_status/{request_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    progress = status.get('progress', 0)
                    message = status.get('message', 'Unknown')
                    step = status.get('current_step', 'Unknown')
                    status_type = status.get('status', 'unknown')
                    
                    print(f"Progress: {progress}% - {step} - {message} ({status_type})")
                    
                    if status_type == 'completed':
                        print(f"\n✅ Processing completed!")
                        break
                    elif status_type == 'failed':
                        print(f"\n❌ Processing failed: {status.get('message', 'Unknown error')}")
                        break
                        
                elif status_response.status_code == 404:
                    print(f"Task not found (404) - might be completed")
                    break
                    
                time.sleep(3)  # Poll every 3 seconds
                
            except Exception as e:
                print(f"Error polling status: {e}")
                break
    else:
        print(f"\n✅ Immediate processing completed!")
    
    # Get final results
    print(f"\n=== Getting Final Results ===")
    verification_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
    
    if verification_response.status_code == 200:
        verification = verification_response.json()
        citations = verification.get('citations', [])
        clusters = verification.get('clusters', [])
        
        print(f"✅ Final results retrieved")
        print(f"Citations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        # Show first few citations
        if citations:
            print(f"\nFirst 5 citations:")
            for i, cit in enumerate(citations[:5]):
                case_name = cit.get('case_name', 'N/A')
                citation_text = cit.get('citation', 'N/A')
                verified = cit.get('verified', False)
                print(f"  {i+1}. {case_name} - {citation_text} (verified: {verified})")
        
        # Show clusters
        if clusters:
            print(f"\nFirst 3 clusters:")
            for i, cluster in enumerate(clusters[:3]):
                cluster_id = cluster.get('cluster_id', 'N/A')
                cluster_name = cluster.get('canonical_name', cluster.get('cluster_case_name', 'N/A'))
                citation_count = len(cluster.get('citations', []))
                print(f"  {i+1}. Cluster {cluster_id}: {cluster_name} ({citation_count} citations)")
        
        print(f"\n🎉 PDF processing test completed successfully!")
        
    else:
        print(f"❌ Failed to get final results: {verification_response.status_code}")
        print(verification_response.text)

if __name__ == "__main__":
    test_pdf_analyze()
