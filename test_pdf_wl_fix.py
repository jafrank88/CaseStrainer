#!/usr/bin/env python3
"""
Test the WL fix with the actual PDF file
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Testing WL Fix with Actual PDF")
    print("=" * 50)
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return
    
    # Extract text manually to confirm WL citations exist
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        
        wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
        manual_matches = re.findall(wl_pattern, text, re.IGNORECASE)
        
        print(f"📄 PDF Analysis:")
        print(f"  Text length: {len(text)} characters")
        print(f"  Manual WL citations found: {len(manual_matches)}")
        
        if manual_matches:
            print("  WL Citations in PDF:")
            for i, match in enumerate(manual_matches, 1):
                print(f"    {i}. {match}")
        print()
        
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return
    
    # Test with CaseStrainer API endpoint
    try:
        import requests
        
        print("🌐 Testing via API endpoint:")
        
        # Test file upload
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {'type': 'file'}
            
            response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                                   files=files, data=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            # Check if citations are in nested result structure
            citations = result.get('citations', [])
            if not citations and 'result' in result:
                citations = result['result'].get('citations', [])
            wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
            
            print(f"  ✅ API Response: {response.status_code}")
            print(f"  Total citations found: {len(citations)}")
            print(f"  WL citations found: {len(wl_citations)}")
            
            if wl_citations:
                print("  ✅ WL Citations found by API:")
                for citation in wl_citations:
                    print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
            else:
                print("  ❌ No WL citations found by API")
                
            # Compare results
            print(f"\n📊 Comparison:")
            print(f"  Manual extraction: {len(manual_matches)} WL citations")
            print(f"  API processing: {len(wl_citations)} WL citations")
            
            if len(wl_citations) == len(manual_matches):
                print("  🎉 SUCCESS: API found all WL citations!")
            elif len(wl_citations) > 0:
                print(f"  ⚠️  PARTIAL: API found {len(wl_citations)}/{len(manual_matches)} WL citations")
            else:
                print("  ❌ FAILURE: API found no WL citations")
                
        else:
            print(f"  ❌ API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    main()
