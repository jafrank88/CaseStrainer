#!/usr/bin/env python3
"""
Test PDF processing directly through the API endpoint
"""

import requests
import json
import time
import os
from io import BytesIO

def test_pdf_api_direct():
    """Test PDF processing through the actual API"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing PDF through API...")
    print(f"PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found")
        return
    
    # Read PDF as bytes
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print(f"PDF size: {len(pdf_bytes):,} bytes")
    
    # Create file-like object
    pdf_file = BytesIO(pdf_bytes)
    pdf_file.name = 'sp-7788.pdf'
    
    # Prepare for upload
    files = {'file': (pdf_file.name, pdf_file, 'application/pdf')}
    data = {
        'client_request_id': f'pdf-test-{int(time.time())}',
        'force_mode': 'sync'  # Force sync processing
    }
    
    print(f"\n=== Uploading to API ===")
    
    try:
        response = requests.post(f"{base_url}/analyze", files=files, data=data)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.text}")
            return
        
        result = response.json()
        request_id = result.get('request_id')
        
        print(f"✅ Upload successful")
        print(f"Request ID: {request_id}")
        print(f"Success: {result.get('success')}")
        print(f"Processing strategy: {result.get('processing_strategy')}")
        
        # Check if we got immediate results
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        if citations:
            print(f"Immediate citations: {len(citations)}")
        else:
            print(f"No immediate citations (async processing)")
        
        # Get final results
        print(f"\n=== Getting Final Results ===")
        final_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
        
        if final_response.status_code == 200:
            final_result = final_response.json()
            final_citations = final_result.get('citations', [])
            final_clusters = final_result.get('clusters', [])
            
            print(f"✅ Final results retrieved")
            print(f"Total citations: {len(final_citations)}")
            print(f"Total clusters: {len(final_clusters)}")
            
            if final_citations:
                print(f"\nFirst 5 citations:")
                for i, cit in enumerate(final_citations[:5]):
                    case_name = cit.get('case_name', 'N/A')
                    citation_text = cit.get('citation', 'N/A')
                    verified = cit.get('verified', False)
                    print(f"  {i+1}. {case_name} - {citation_text} (verified: {verified})")
            
            if final_clusters:
                print(f"\nFirst 3 clusters:")
                for i, cluster in enumerate(final_clusters[:3]):
                    cluster_id = cluster.get('cluster_id', 'N/A')
                    cluster_name = cluster.get('canonical_name', 'N/A')
                    citation_count = len(cluster.get('citations', []))
                    print(f"  {i+1}. Cluster {cluster_id}: {cluster_name} ({citation_count} citations)")
            
            print(f"\n🎉 PDF API test completed!")
            
        else:
            print(f"❌ Failed to get final results: {final_response.status_code}")
            print(final_response.text)
            
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_api_direct()
