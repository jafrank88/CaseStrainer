#!/usr/bin/env python3
"""
Step 1: Test PDF extraction to ensure WL citations are preserved
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_pdf_extraction_methods():
    """Test different PDF extraction methods to see which preserves WL citations best."""
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🔍 Step 1: PDF Extraction Testing")
    print("=" * 60)
    print(f"Testing PDF: {os.path.basename(pdf_path)}")
    print()
    
    # Method 1: Direct PyMuPDF (what we used to confirm WL citations exist)
    print("📄 Method 1: Direct PyMuPDF")
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text1 = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text1 += page.get_text() + "\n"
        doc.close()
        
        wl_matches1 = re.findall(r'\b\d{4}\s+WL\s+\d+\b', text1, re.IGNORECASE)
        print(f"  ✅ Extracted {len(text1)} chars, found {len(wl_matches1)} WL citations")
        for match in wl_matches1[:3]:
            print(f"    - {match}")
        if len(wl_matches1) > 3:
            print(f"    ... and {len(wl_matches1) - 3} more")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        text1 = None
        wl_matches1 = []
    
    print()
    
    # Method 2: CaseStrainer's PDFExtractor
    print("📄 Method 2: CaseStrainer PDFExtractor")
    try:
        from pdf_extractor import PDFExtractor
        
        pdf_extractor = PDFExtractor()
        text2 = pdf_extractor.extract_text(pdf_path)
        
        if text2:
            wl_matches2 = re.findall(r'\b\d{4}\s+WL\s+\d+\b', text2, re.IGNORECASE)
            print(f"  ✅ Extracted {len(text2)} chars, found {len(wl_matches2)} WL citations")
            for match in wl_matches2[:3]:
                print(f"    - {match}")
            if len(wl_matches2) > 3:
                print(f"    ... and {len(wl_matches2) - 3} more")
        else:
            print(f"  ❌ No text extracted")
            wl_matches2 = []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        text2 = None
        wl_matches2 = []
    
    print()
    
    # Method 3: UnifiedSyncProcessor file processing
    print("📄 Method 3: UnifiedSyncProcessor")
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        
        # Read PDF as binary
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Process as file upload
        result = processor.process_file_upload(pdf_content, 'test.pdf')
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"  ✅ Processed file, found {len(citations)} total citations")
        print(f"  🎯 WL citations found: {len(wl_citations)}")
        
        if wl_citations:
            print("    WL Citations:")
            for citation in wl_citations:
                print(f"      - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("    ❌ No WL citations found by UnifiedSyncProcessor")
            print("    Other citations found:")
            for citation in citations[:5]:
                print(f"      - {citation.get('citation')} (source: {citation.get('source')})")
            if len(citations) > 5:
                print(f"      ... and {len(citations) - 5} more")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Comparison
    print("📊 Extraction Comparison:")
    if text1 and text2:
        print(f"  Direct PyMuPDF: {len(wl_matches1)} WL citations")
        print(f"  CaseStrainer PDFExtractor: {len(wl_matches2)} WL citations")
        
        if len(wl_matches1) != len(wl_matches2):
            print("  ⚠️  Different results between extraction methods!")
            print("     This suggests PDF extraction is the issue.")
        else:
            print("  ✅ Both extraction methods find same number of WL citations")
            print("     PDF extraction is working correctly.")
    
    return text1, text2

def test_text_normalization():
    """Test if text normalization is affecting WL citations."""
    
    print("\n🔧 Text Normalization Testing")
    print("=" * 60)
    
    # Sample text with potential formatting issues
    test_cases = [
        "2006 WL 3801910",  # Normal
        "2006  WL  3801910",  # Extra spaces
        "2006\nWL\n3801910",  # Newlines
        "2006\tWL\t3801910",  # Tabs
        "2006 WL\n3801910",  # Mixed
    ]
    
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    
    print("Testing WL pattern against various formats:")
    for i, test_case in enumerate(test_cases, 1):
        matches = re.findall(wl_pattern, test_case, re.IGNORECASE)
        status = "✅" if matches else "❌"
        print(f"  {i}. '{repr(test_case)}' -> {status} {len(matches)} matches")
        if matches:
            print(f"     Found: {matches[0]}")
    
    print()
    
    # Test normalization function
    print("Testing text normalization effects:")
    original = "In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court"
    normalized = ' '.join(original.split())  # This is what CaseStrainer does
    
    original_matches = re.findall(wl_pattern, original, re.IGNORECASE)
    normalized_matches = re.findall(wl_pattern, normalized, re.IGNORECASE)
    
    print(f"  Original: '{original}'")
    print(f"  Normalized: '{normalized}'")
    print(f"  Original matches: {len(original_matches)}")
    print(f"  Normalized matches: {len(normalized_matches)}")
    
    if len(original_matches) != len(normalized_matches):
        print("  ⚠️  Normalization is affecting WL citation detection!")
    else:
        print("  ✅ Normalization preserves WL citations")

def main():
    """Main function for Step 1 testing."""
    
    # Test PDF extraction
    text1, text2 = test_pdf_extraction_methods()
    
    # Test text normalization
    test_text_normalization()
    
    print("\n" + "=" * 60)
    print("📋 Step 1 Summary:")
    print("=" * 60)
    
    if text1 and text2:
        wl_matches1 = re.findall(r'\b\d{4}\s+WL\s+\d+\b', text1, re.IGNORECASE)
        wl_matches2 = re.findall(r'\b\d{4}\s+WL\s+\d+\b', text2, re.IGNORECASE)
        
        if len(wl_matches1) > 0 and len(wl_matches2) == 0:
            print("🔍 ISSUE FOUND: CaseStrainer PDFExtractor is losing WL citations")
            print("   The PDF contains WL citations but PDFExtractor isn't preserving them")
        elif len(wl_matches1) > 0 and len(wl_matches2) > 0:
            print("✅ PDF extraction is working correctly")
            print("   Issue must be in the citation processing pipeline")
        else:
            print("❓ Unexpected result - need to investigate further")
    else:
        print("❌ Could not complete PDF extraction testing")
    
    print("\n🎯 Next: Proceed to Step 2 - Debug citation processing pipeline")

if __name__ == "__main__":
    main()
