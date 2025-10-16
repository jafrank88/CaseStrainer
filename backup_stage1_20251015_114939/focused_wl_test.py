#!/usr/bin/env python3
"""
Focused test to find WL citations in the PDF
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def extract_pdf_text_simple(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def main():
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🔍 Focused WL Citation Analysis")
    print("=" * 50)
    
    # Extract text
    text = extract_pdf_text_simple(pdf_path)
    if not text:
        print("❌ Could not extract text")
        return
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Search for WL citations
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    wl_matches = re.findall(wl_pattern, text, re.IGNORECASE)
    
    print(f"\n📊 WL Citation Results:")
    print(f"  Pattern: {wl_pattern}")
    print(f"  Matches found: {len(wl_matches)}")
    
    if wl_matches:
        print(f"  WL Citations:")
        for i, match in enumerate(wl_matches, 1):
            print(f"    {i}. {match}")
            
            # Find context around each citation
            citation_pos = text.find(match)
            if citation_pos != -1:
                start = max(0, citation_pos - 100)
                end = min(len(text), citation_pos + len(match) + 100)
                context = text[start:end].replace('\n', ' ').strip()
                print(f"       Context: ...{context}...")
            print()
    
    # Now test with CaseStrainer
    print("🧪 Testing with CaseStrainer:")
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test with just the text
        print("  Processing extracted text...")
        result = processor.process_text_sync(text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"  Total citations found: {len(citations)}")
        print(f"  WL citations found: {len(wl_citations)}")
        
        if wl_citations:
            print("  ✅ WL Citations found by CaseStrainer:")
            for citation in wl_citations:
                print(f"    - {citation.get('citation')}")
                print(f"      Source: {citation.get('source')}")
                print(f"      Confidence: {citation.get('confidence')}")
        else:
            print("  ❌ No WL citations found by CaseStrainer")
            
        print(f"\n  All citations found:")
        for citation in citations:
            print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
            
    except Exception as e:
        print(f"  ❌ Error with CaseStrainer: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with URL processing
    print(f"\n🌐 Testing URL processing of same PDF:")
    try:
        # Copy the PDF to a web-accessible location for testing
        import shutil
        web_pdf_path = r"d:\dev\casestrainer\test_files\test_wl_document.pdf"
        os.makedirs(os.path.dirname(web_pdf_path), exist_ok=True)
        shutil.copy2(pdf_path, web_pdf_path)
        
        # Test URL processing (simulating what happens with URL uploads)
        from pdf_extractor import PDFExtractor
        
        pdf_extractor = PDFExtractor()
        extracted_text = pdf_extractor.extract_text(pdf_path)
        
        print(f"  PDF extractor text length: {len(extracted_text) if extracted_text else 0}")
        
        if extracted_text:
            # Process with the same processor
            url_result = processor.process_text_sync(extracted_text)
            url_citations = url_result.get('citations', [])
            url_wl_citations = [c for c in url_citations if 'WL' in c.get('citation', '')]
            
            print(f"  URL processing - Total citations: {len(url_citations)}")
            print(f"  URL processing - WL citations: {len(url_wl_citations)}")
            
            if url_wl_citations:
                print("  ✅ URL processing found WL citations:")
                for citation in url_wl_citations:
                    print(f"    - {citation.get('citation')}")
        
    except Exception as e:
        print(f"  ❌ Error with URL processing test: {e}")

if __name__ == "__main__":
    main()
