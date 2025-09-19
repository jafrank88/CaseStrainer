#!/usr/bin/env python3
"""
Fix WL citation extraction issue
"""

import sys
from pathlib import Path
import re
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_current_wl_extraction():
    """Test current WL extraction to confirm the issue."""
    
    print("🔍 Testing Current WL Extraction")
    print("=" * 50)
    
    # Sample text with WL citations
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled that evidence 
    regarding the defendant's prior bad acts was inadmissible. See also Johnson v. State, 2018 WL 3037217 
    (Wyo. 2018), where the court held that motions in limine are proper procedural tools.
    """
    
    print(f"Test text contains 2 WL citations:")
    print("  - 2006 WL 3801910")
    print("  - 2018 WL 3037217")
    print()
    
    # Test with UnifiedSyncProcessor (the main API path)
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        result = processor.process_text(test_text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"📊 UnifiedSyncProcessor Results:")
        print(f"  Total citations: {len(citations)}")
        print(f"  WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print("  ✅ WL Citations found:")
            for citation in wl_citations:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("  ❌ No WL citations found")
            print("  All citations found:")
            for citation in citations:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        
        return len(wl_citations) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_regex_directly():
    """Test the enhanced regex patterns directly."""
    
    print(f"\n🔧 Testing Enhanced Regex Patterns")
    print("=" * 50)
    
    test_text = "In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled."
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Check if the processor has the WL patterns
        if hasattr(processor, 'enhanced_patterns'):
            print("📋 WL Patterns in enhanced_patterns:")
            for name, pattern in processor.enhanced_patterns.items():
                if 'wl' in name.lower() or 'westlaw' in name.lower():
                    print(f"  {name}: {pattern.pattern}")
                    
                    # Test the pattern
                    matches = pattern.findall(test_text)
                    print(f"    Matches: {len(matches)} - {matches}")
        
        # Test enhanced regex extraction
        enhanced_citations = processor._extract_with_enhanced_regex(test_text)
        wl_enhanced = [c for c in enhanced_citations if 'WL' in c.citation]
        
        print(f"\n📊 Enhanced Regex Results:")
        print(f"  Total citations: {len(enhanced_citations)}")
        print(f"  WL citations: {len(wl_enhanced)}")
        
        if wl_enhanced:
            print("  ✅ Enhanced regex found WL citations:")
            for c in wl_enhanced:
                print(f"    - {c.citation} (confidence: {c.confidence})")
        else:
            print("  ❌ Enhanced regex found no WL citations")
            
        return len(wl_enhanced) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_file_directly():
    """Test the actual PDF file through the API path."""
    
    print(f"\n📄 Testing Actual PDF File")
    print("=" * 50)
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
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
        
        print(f"📊 PDF Processing Results:")
        print(f"  Total citations: {len(citations)}")
        print(f"  WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print("  ✅ PDF processing found WL citations:")
            for citation in wl_citations:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("  ❌ PDF processing found no WL citations")
            print("  Sample of other citations found:")
            for citation in citations[:5]:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        
        return len(wl_citations) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main testing function."""
    
    print("🔍 WL Citation Extraction Diagnosis")
    print("=" * 60)
    
    # Test 1: Current extraction with sample text
    text_works = test_current_wl_extraction()
    
    # Test 2: Enhanced regex directly
    regex_works = test_enhanced_regex_directly()
    
    # Test 3: Actual PDF file
    pdf_works = test_pdf_file_directly()
    
    print(f"\n" + "=" * 60)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    if text_works and regex_works and pdf_works:
        print("✅ ALL TESTS PASSED: WL extraction is working correctly")
        print("   The issue may have been resolved by previous fixes")
    elif text_works and regex_works and not pdf_works:
        print("⚠️  PDF EXTRACTION ISSUE: Text processing works but PDF doesn't")
        print("   Issue is in PDF text extraction or file processing pipeline")
    elif not text_works and not regex_works:
        print("❌ CORE EXTRACTION ISSUE: Enhanced regex patterns not working")
        print("   Issue is in the basic WL citation patterns")
    elif text_works and not pdf_works:
        print("⚠️  PIPELINE ISSUE: Simple text works but PDF processing doesn't")
        print("   Issue is in file upload processing pipeline")
    else:
        print("❓ MIXED RESULTS: Need further investigation")
    
    print(f"\n🎯 Based on memories, this is likely related to:")
    print("   1. Verification being disabled (lines 2454-2461)")
    print("   2. Sync vs async processing differences")
    print("   3. Deduplication issues filtering out WL citations")
    print("   4. PDF extraction pipeline bugs")

if __name__ == "__main__":
    main()
