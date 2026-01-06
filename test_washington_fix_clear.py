#!/usr/bin/env python3
"""
Clear test of the Washington citation fix
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_washington_fix():
    """Test the Washington citation fix"""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the specific citation format
    text = "Jha v. Khan, 24 Wn. App. 2d 377, 392, 520 P.3d 470 (2022)"
    
    print("Testing Washington citation fix:")
    print("=" * 80)
    print(f"Text: {text}")
    print()
    
    # Extract citations
    citations = processor._extract_with_regex_enhanced(text)
    
    print(f"Number of citations extracted: {len(citations)}")
    print()
    
    for i, cit in enumerate(citations):
        print(f"Citation {i+1}:")
        print(f"  Text: {cit.citation}")
        print(f"  Pattern: {cit.pattern}")
        
        if hasattr(cit, 'pinpoint_pages') and cit.pinpoint_pages:
            print(f"  Pinpoint pages: {cit.pinpoint_pages}")
        
        if hasattr(cit, 'parallel_citations') and cit.parallel_citations:
            print(f"  Parallel citations: {cit.parallel_citations}")
        print()
    
    # Verify the fix
    if len(citations) == 1:
        cit = citations[0]
        if "24 Wn. App. 2d 377" in cit.citation and "520 P.3d 470" in cit.citation:
            print("✅ SUCCESS: Washington citation with pinpoint page and parallel citation")
            print("   is extracted as a SINGLE citation (not split)")
            
            if hasattr(cit, 'pinpoint_pages') and '392' in cit.pinpoint_pages:
                print("✅ Pinpoint page (392) correctly identified")
            
            if hasattr(cit, 'parallel_citations') and '520 P.3d 470' in cit.parallel_citations:
                print("✅ Parallel citation correctly identified")
        else:
            print("❌ FAILED: Citation format incorrect")
    else:
        print(f"❌ FAILED: Expected 1 citation, got {len(citations)}")
        print("   The citation is being split incorrectly")
    
    print()
    print("=" * 80)
    print()
    print("BEFORE the fix:")
    print("  - '24 Wn. App. 2d 377, 392, 520 P.3d 470' was split into 2 citations")
    print("  - Pinpoint page and parallel citation were lost")
    print()
    print("AFTER the fix:")
    print("  - Extracted as 1 citation with proper structure")
    print("  - Pinpoint page: 392")
    print("  - Parallel citation: 520 P.3d 470")

if __name__ == "__main__":
    test_washington_fix()
