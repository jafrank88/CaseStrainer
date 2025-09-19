#!/usr/bin/env python3
"""
Debug why CaseStrainer isn't finding WL citations
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def extract_pdf_text(pdf_path):
    """Extract text from PDF."""
    try:
        import fitz
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

def test_casestrainer_wl_extraction():
    """Test CaseStrainer WL extraction step by step."""
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🔍 Debugging CaseStrainer WL Extraction")
    print("=" * 60)
    
    # Step 1: Extract PDF text
    text = extract_pdf_text(pdf_path)
    if not text:
        print("❌ Could not extract PDF text")
        return
    
    print(f"✅ Extracted {len(text)} characters from PDF")
    
    # Step 2: Manual regex test
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    manual_matches = re.findall(wl_pattern, text, re.IGNORECASE)
    print(f"✅ Manual regex found {len(manual_matches)} WL citations")
    
    if manual_matches:
        print("   Manual matches:")
        for match in manual_matches:
            print(f"     - {match}")
    
    # Step 3: Test CaseStrainer patterns
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Check the patterns used
        print(f"\n🔧 CaseStrainer WL Patterns:")
        if hasattr(processor, 'enhanced_patterns'):
            for name, pattern in processor.enhanced_patterns.items():
                if 'wl' in name.lower() or 'westlaw' in name.lower():
                    print(f"   {name}: {pattern.pattern}")
        
        # Test the processor
        print(f"\n🧪 Testing CaseStrainer processor...")
        result = processor.process_text_sync(text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"   Total citations found: {len(citations)}")
        print(f"   WL citations found: {len(wl_citations)}")
        
        if wl_citations:
            print("   ✅ CaseStrainer WL citations:")
            for citation in wl_citations:
                print(f"     - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("   ❌ CaseStrainer found NO WL citations")
            
        print(f"\n   All citations found by CaseStrainer:")
        for citation in citations:
            print(f"     - {citation.get('citation')} (source: {citation.get('source')})")
            
        # Step 4: Test individual extraction methods
        print(f"\n🔬 Testing individual extraction methods:")
        
        # Test enhanced regex
        if hasattr(processor, '_extract_with_enhanced_regex'):
            enhanced_citations = processor._extract_with_enhanced_regex(text)
            enhanced_wl = [c for c in enhanced_citations if 'WL' in c.citation]
            print(f"   Enhanced regex WL citations: {len(enhanced_wl)}")
            for c in enhanced_wl:
                print(f"     - {c.citation}")
        
        # Test eyecite
        if hasattr(processor, '_extract_with_eyecite'):
            eyecite_citations = processor._extract_with_eyecite(text)
            eyecite_wl = [c for c in eyecite_citations if 'WL' in c.citation]
            print(f"   Eyecite WL citations: {len(eyecite_wl)}")
            for c in eyecite_wl:
                print(f"     - {c.citation}")
        
    except Exception as e:
        print(f"❌ Error testing CaseStrainer: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Test the actual API endpoint that would be used."""
    
    print(f"\n🌐 Testing API Endpoint Processing:")
    
    try:
        # Test the URL processing path
        pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
        
        # Copy to test_files for URL simulation
        import shutil
        test_pdf_path = r"d:\dev\casestrainer\test_files\wl_test.pdf"
        os.makedirs(os.path.dirname(test_pdf_path), exist_ok=True)
        shutil.copy2(pdf_path, test_pdf_path)
        
        # Test file upload processing
        from unified_sync_processor import UnifiedSyncProcessor
        
        sync_processor = UnifiedSyncProcessor()
        
        # Read the PDF file as binary
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Process as file upload
        result = sync_processor.process_file_upload(pdf_content, 'test.pdf')
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"   File upload processing:")
        print(f"     Total citations: {len(citations)}")
        print(f"     WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print("     ✅ File upload found WL citations:")
            for citation in wl_citations:
                print(f"       - {citation.get('citation')}")
        else:
            print("     ❌ File upload found NO WL citations")
            
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")
        import traceback
        traceback.print_exc()

def main():
    test_casestrainer_wl_extraction()
    test_api_endpoint()
    
    print(f"\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("The PDF document DOES contain WL citations (10 found manually).")
    print("If CaseStrainer is not finding them, there's a bug in the extraction pipeline.")
    print("Check the individual extraction methods to see where the issue is.")

if __name__ == "__main__":
    main()
