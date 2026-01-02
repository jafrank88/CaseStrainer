#!/usr/bin/env python3
"""
Test forced sync processing through production endpoint
"""

import requests
import time
import json

def test_force_sync_production():
    """Test forced sync processing with the Alaska PDF through production"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing FORCED SYNC processing through production endpoint...")
    print(f"PDF: {pdf_path}")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print(f"PDF size: {len(pdf_bytes):,} bytes")
    
    # Create file-like object for upload
    from io import BytesIO
    pdf_file = BytesIO(pdf_bytes)
    pdf_file.name = 'sp-7788.pdf'
    
    # Test with FORCED sync processing
    files = {'file': (pdf_file.name, pdf_file, 'application/pdf')}
    data = {
        'client_request_id': f'sync-test-{int(time.time())}',
        'force_mode': 'sync'  # FORCE sync processing regardless of size
    }
    
    print(f"\n=== Submitting to Production API (FORCED SYNC) ===")
    
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
        
        # Check immediate results (should be there for sync)
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"Immediate citations: {len(citations)}")
        print(f"Immediate clusters: {len(clusters)}")
        
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
            
            print(f"\n🎉 SUCCESS: Forced sync processing works!")
            print(f"   The citation extraction engine is working perfectly.")
            print(f"   The issue is with the async processing pipeline.")
            
        else:
            print(f"❌ No citations in immediate response")
            print(f"   This indicates a problem with the sync processing too")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_force_sync_production()
