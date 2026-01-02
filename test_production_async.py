#!/usr/bin/env python3
"""
Test async processing through production endpoint
"""

import requests
import time
import json

def test_production_async():
    """Test async processing with the Alaska PDF through production"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing async processing through production endpoint...")
    print(f"PDF: {pdf_path}")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print(f"PDF size: {len(pdf_bytes):,} bytes")
    
    # Create file-like object for upload
    from io import BytesIO
    pdf_file = BytesIO(pdf_bytes)
    pdf_file.name = 'sp-7788.pdf'
    
    # Test with async processing (default for large files)
    files = {'file': (pdf_file.name, pdf_file, 'application/pdf')}
    data = {
        'client_request_id': f'production-test-{int(time.time())}',
        # Don't set force_mode - let it decide automatically (should be async for 363KB PDF)
    }
    
    print(f"\n=== Submitting to Production API ===")
    
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
        
        # Check if immediate results
        citations = result.get('citations', [])
        if citations:
            print(f"Immediate citations: {len(citations)}")
            for i, cit in enumerate(citations[:3]):
                print(f"  {i+1}. {cit}")
        else:
            print(f"No immediate citations (async processing)")
        
        # Poll for progress and final results
        print(f"\n=== Polling for Progress ===")
        
        max_wait = 120  # 2 minutes max wait
        poll_interval = 5  # 5 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check task status
            status_response = requests.get(f"{base_url}/task_status/{request_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                progress = status.get('progress', {})
                
                print(f"Progress: {progress.get('progress_percent', 0)}% - {progress.get('current_message', 'No message')}")
                
                # Check if complete
                if progress.get('progress_percent') == 100:
                    print(f"✅ Processing complete!")
                    break
            else:
                print(f"Status check failed: {status_response.status_code}")
            
            time.sleep(poll_interval)
        
        # Get final results
        print(f"\n=== Getting Final Results ===")
        final_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
        
        if final_response.status_code == 200:
            final_result = final_response.json()
            
            citations = final_result.get('citations', [])
            clusters = final_result.get('clusters', [])
            
            print(f"✅ Final results retrieved")
            print(f"Total citations: {len(citations)}")
            print(f"Total clusters: {len(clusters)}")
            
            if citations:
                print(f"\nFirst 10 citations:")
                for i, cit in enumerate(citations[:10]):
                    if isinstance(cit, dict):
                        citation_text = cit.get('citation', 'N/A')
                        case_name = cit.get('canonical_name', cit.get('extracted_case_name', 'N/A'))
                        date = cit.get('canonical_date', cit.get('extracted_date', 'N/A'))
                        verified = cit.get('verified', False)
                        status = "✅" if verified else "❌"
                        print(f"  {i+1}. {citation_text} - {case_name} ({date}) {status}")
                    else:
                        print(f"  {i+1}. {cit}")
                
                # Count citation types
                p2d_count = sum(1 for cit in citations if isinstance(cit, dict) and 'P.2d' in cit.get('citation', ''))
                p3d_count = sum(1 for cit in citations if isinstance(cit, dict) and 'P.3d' in cit.get('citation', ''))
                us_count = sum(1 for cit in citations if isinstance(cit, dict) and 'U.S.' in cit.get('citation', ''))
                
                print(f"\n=== Citation Summary ===")
                print(f"P.2d citations: {p2d_count}")
                print(f"P.3d citations: {p3d_count}")
                print(f"U.S. citations: {us_count}")
                print(f"Total verified: {sum(1 for cit in citations if isinstance(cit, dict) and cit.get('verified', False))}/{len(citations)}")
                
            else:
                print("❌ No citations found in final results")
                
        else:
            print(f"❌ Failed to get final results: {final_response.status_code}")
            print(f"Response: {final_response.text}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_production_async()
