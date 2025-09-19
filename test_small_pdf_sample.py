#!/usr/bin/env python3
"""
Test with a small PDF sample to force sync processing
"""

import sys
from pathlib import Path
import re
import os
import requests

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Testing Small PDF Sample (Force Sync Processing)")
    print("=" * 60)
    
    # Extract a small sample from the PDF that contains WL citations
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        # Get text from first few pages only to stay under sync threshold
        text = ""
        for page_num in range(min(2, len(doc))):  # First 2 pages only
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text += page_text + "\n"
            
            # Stop if we have enough text with WL citations
            if len(text) > 3000 and 'WL' in text:  # Stay under 5KB threshold
                break
        
        doc.close()
        
        print(f"📄 Sample text ({len(text)} bytes - under 5KB threshold)")
        
        # Check for WL citations in sample
        wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
        manual_matches = re.findall(wl_pattern, text, re.IGNORECASE)
        
        print(f"📊 Manual analysis of sample:")
        print(f"  WL citations found: {len(manual_matches)}")
        for match in manual_matches:
            print(f"    - {match}")
        print()
        
        if not manual_matches:
            print("❌ No WL citations in sample, trying larger sample...")
            # Try more pages
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(min(5, len(doc))):
                page = doc.load_page(page_num)
                text += page.get_text() + "\n"
            doc.close()
            
            manual_matches = re.findall(wl_pattern, text, re.IGNORECASE)
            print(f"  Larger sample ({len(text)} bytes): {len(manual_matches)} WL citations")
            for match in manual_matches:
                print(f"    - {match}")
        
        if not manual_matches:
            print("❌ No WL citations found in PDF sample")
            return
        
        # Test via API with text
        print(f"\n🌐 Testing via API with extracted text:")
        
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               data={'text': text, 'type': 'text'}, 
                               timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
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
                print("  All citations found:")
                for citation in citations:
                    print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
                    
            # Check processing mode
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            print(f"  Processing mode: {processing_mode}")
            
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
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
