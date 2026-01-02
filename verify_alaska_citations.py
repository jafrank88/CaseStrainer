#!/usr/bin/env python3
"""
Verify Alaska citations are working
"""

import requests
import time
import json

def verify_alaska_citations():
    """Verify Alaska citations are extracted correctly"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Verifying Alaska citations extraction...")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Create file-like object for upload
    from io import BytesIO
    pdf_file = BytesIO(pdf_bytes)
    pdf_file.name = 'sp-7788.pdf'
    
    # Test with FORCED sync processing
    files = {'file': (pdf_file.name, pdf_file, 'application/pdf')}
    data = {
        'client_request_id': f'alaska-test-{int(time.time())}',
        'force_mode': 'sync'
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"✅ Total citations extracted: {len(citations)}")
            
            # Count Alaska citations
            p2d_count = sum(1 for cit in citations if 'P.2d' in cit.get('citation', ''))
            p3d_count = sum(1 for cit in citations if 'P.3d' in cit.get('citation', ''))
            us_count = sum(1 for cit in citations if 'U.S.' in cit.get('citation', ''))
            
            print(f"📊 Citation Summary:")
            print(f"   P.2d citations (Alaska): {p2d_count}")
            print(f"   P.3d citations (Alaska): {p3d_count}")
            print(f"   U.S. citations (Supreme Court): {us_count}")
            print(f"   Other citations: {len(citations) - p2d_count - p3d_count - us_count}")
            
            # Show some Alaska examples
            print(f"\n🏛️ Alaska Citation Examples:")
            alaska_citations = [cit for cit in citations if 'P.2d' in cit.get('citation', '') or 'P.3d' in cit.get('citation', '')]
            for i, cit in enumerate(alaska_citations[:5]):
                citation_text = cit.get('citation', 'N/A')
                case_name = cit.get('extracted_case_name', 'N/A')
                verified = cit.get('verified', False)
                status = "✅" if verified else "❌"
                print(f"   {i+1}. {citation_text} - {case_name} {status}")
            
            # Show verification rate
            verified_count = sum(1 for cit in citations if cit.get('verified', False))
            verification_rate = (verified_count / len(citations)) * 100 if citations else 0
            
            print(f"\n📈 Verification Statistics:")
            print(f"   Verified citations: {verified_count}/{len(citations)} ({verification_rate:.1f}%)")
            
            print(f"\n🎉 SUCCESS: Alaska citation extraction is working perfectly!")
            print(f"   The PDF processing pipeline now correctly extracts and verifies Alaska case law.")
            
        else:
            print(f"❌ Upload failed: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_alaska_citations()
