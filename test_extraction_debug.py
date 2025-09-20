#!/usr/bin/env python3
"""
Test to debug the extraction pipeline and see where the nested citation fix should be applied.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.config import ProcessingConfig

def test_extraction_pipeline():
    """Test the extraction pipeline directly to see where the issue is."""
    
    print("🔍 Testing Extraction Pipeline Directly")
    print("=" * 60)
    
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    print(f"📝 Test Text Length: {len(test_text)} characters")
    
    # Test direct processor
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=False  # Skip verification for faster testing
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    print(f"\n🔄 Processing with UnifiedCitationProcessorV2...")
    
    try:
        result = processor.process_text(test_text)
        
        print(f"📊 Direct Processing Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Citations: {len(result.get('citations', []))}")
        print(f"   Clusters: {len(result.get('clusters', []))}")
        
        citations = result.get('citations', [])
        
        print(f"\n📋 Citation Analysis:")
        for i, citation in enumerate(citations, 1):
            citation_text = citation.get('citation', 'N/A')
            extracted_name = citation.get('extracted_case_name', 'N/A')
            extracted_date = citation.get('extracted_date', 'N/A')
            start_index = citation.get('start_index', 'N/A')
            end_index = citation.get('end_index', 'N/A')
            
            print(f"   Citation {i}: '{citation_text}'")
            print(f"     Position: {start_index}-{end_index}")
            print(f"     Extracted name: '{extracted_name}'")
            print(f"     Extracted date: '{extracted_date}'")
            
            # Check if this should be the Am. Legion case
            if citation_text in ["116 Wash.2d 1", "802 P.2d 784"]:
                expected_name = "Am. Legion Post No. 32 v. City of Walla Walla"
                if extracted_name == expected_name:
                    print(f"     ✅ CORRECT")
                else:
                    print(f"     ❌ INCORRECT: Expected '{expected_name}'")
                    
                    # Debug the context around this citation
                    if start_index != 'N/A' and isinstance(start_index, int):
                        context_start = max(0, start_index - 100)
                        context_end = min(len(test_text), start_index + 50)
                        context = test_text[context_start:context_end]
                        print(f"     🔍 Context: '...{context}...'")
            print()
        
        return True
        
    except Exception as e:
        print(f"💥 Direct processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_extraction():
    """Test manual extraction to see what should happen."""
    
    print(f"\n🔧 Manual Extraction Test")
    print("=" * 60)
    
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    # Find the positions of the problematic citations
    citations_to_check = ["116 Wn.2d 1", "802 P.2d 784"]
    
    for citation in citations_to_check:
        pos = test_text.find(citation)
        if pos != -1:
            print(f"📍 Citation '{citation}' at position {pos}")
            
            # Look backwards for "quoting"
            text_before = test_text[:pos]
            quoting_pos = text_before.rfind("quoting")
            
            if quoting_pos != -1:
                print(f"   'quoting' found at position {quoting_pos}")
                
                # Extract text from "quoting" to citation
                quoting_context = test_text[quoting_pos:pos + len(citation)]
                print(f"   Context from 'quoting': '{quoting_context}'")
                
                # Try to extract case name from this context
                import re
                case_pattern = r'quoting\s+([A-Z][a-zA-Z\'\.\&\s]*\s+v\.\s+[A-Z][a-zA-Z\'\.\&\s]*)'
                match = re.search(case_pattern, quoting_context)
                
                if match:
                    extracted_case = match.group(1)
                    print(f"   ✅ Manual extraction found: '{extracted_case}'")
                else:
                    print(f"   ❌ Manual extraction failed")
                    
                    # Try a broader pattern
                    broader_pattern = r'quoting\s+([^,]+)'
                    broader_match = re.search(broader_pattern, quoting_context)
                    if broader_match:
                        broader_case = broader_match.group(1).strip()
                        print(f"   🔍 Broader pattern found: '{broader_case}'")
            else:
                print(f"   ❌ 'quoting' not found before citation")

def main():
    """Run extraction debugging."""
    
    print("🚀 Extraction Pipeline Debugging")
    print("=" * 70)
    
    # Test the current pipeline
    pipeline_ok = test_extraction_pipeline()
    
    # Test manual extraction
    test_manual_extraction()
    
    print("\n" + "=" * 70)
    print("📋 EXTRACTION DEBUG RESULTS")
    print("=" * 70)
    
    if pipeline_ok:
        print("✅ Pipeline is working but case name extraction needs improvement")
        print("🔧 Need to implement better nested citation handling")
    else:
        print("❌ Pipeline has fundamental issues")
    
    return pipeline_ok

if __name__ == "__main__":
    main()
