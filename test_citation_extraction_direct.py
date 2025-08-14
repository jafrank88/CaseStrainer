#!/usr/bin/env python3
"""
Direct Citation Extraction Test
Tests the fixed citation extraction pipeline directly without API overhead.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_citation_extraction():
    """Test citation extraction with real legal text."""
    
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    # Test text with real legal citations
    test_text = """In Presidential Ests Apt. Assocs. v. Barrett, 129 Wn.2d 320, 325-26, 917 P.2d 100 (1996), the Washington Supreme Court held that a landlord's duty to provide a reasonably safe premises extends to protecting tenants from foreseeable criminal acts by third parties. The court in United States v. American Trucking Assns., Inc., 310 U. S. 534, 544 (1940), established the principle that administrative agencies must clearly articulate their statutory authority."""
    
    print("🔍 Testing Citation Extraction Pipeline")
    print("=" * 60)
    print(f"Test Text: {test_text[:100]}...")
    print()
    
    try:
        # Test the full unified extraction pipeline using process_text
        print("📋 Step 1: Testing full unified extraction pipeline...")
        result = processor.process_text(test_text)
        citations = result.get('citations', []) if isinstance(result, dict) else result
        
        print(f"✅ Found {len(citations)} citations")
        print()
        
        if citations:
            print("📝 Citation Details:")
            print("-" * 40)
            for i, citation in enumerate(citations, 1):
                print(f"{i}. Citation: '{citation.citation}'")
                print(f"   Method: {citation.method}")
                print(f"   Pattern: {getattr(citation, 'pattern', 'N/A')}")
                print(f"   Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
                print(f"   Date: {getattr(citation, 'extracted_date', 'N/A')}")
                print(f"   Position: {citation.start_index}-{citation.end_index}")
                print(f"   Confidence: {getattr(citation, 'confidence', 'N/A')}")
                print()
        else:
            print("❌ No citations found - extraction still failing")
            
        # Test normalization directly
        print("🔧 Step 2: Testing normalization...")
        test_citations = [
            "310 U. S. 534",
            "129 Wn.2d 320", 
            "917 P.2d 100",
            "123 F.3d 456"
        ]
        
        for cite in test_citations:
            normalized = processor._normalize_citation_comprehensive(cite, purpose="bluebook")
            print(f"'{cite}' → '{normalized}'")
        
        print()
        print("🎯 Step 3: Testing pattern matching...")
        
        # Test if patterns are finding matches
        for pattern_name in ['us', 'us_spaced', 'wn2d', 'p2d', 'f3d']:
            if pattern_name in processor.citation_patterns:
                pattern = processor.citation_patterns[pattern_name]
                matches = list(pattern.finditer(test_text))
                print(f"Pattern '{pattern_name}': {len(matches)} matches")
                for match in matches:
                    print(f"  - '{match.group(0)}' at position {match.start()}-{match.end()}")
            else:
                print(f"Pattern '{pattern_name}': NOT FOUND in citation_patterns")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_citation_extraction()
    if success:
        print("\n✅ Citation extraction test PASSED")
    else:
        print("\n❌ Citation extraction test FAILED")
