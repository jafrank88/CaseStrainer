"""
Simple test to verify series citation fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Test the series citation detection directly
import re

def test_series_detection():
    print("Testing series citation detection...")
    
    # Test text
    text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    # Find citations
    wl_pos = text.find("2022 WL 15153410")
    f_pos = text.find("855 F.2d 569")
    
    print(f"WL citation at position: {wl_pos}")
    print(f"F.2d citation at position: {f_pos}")
    
    # Check what's before each citation
    look_behind_wl = text[max(0, wl_pos - 100):wl_pos]
    look_behind_f = text[max(0, f_pos - 100):f_pos]
    
    print(f"\nText before WL: '{look_behind_wl}'")
    print(f"Text before F.2d: '{look_behind_f}'")
    
    # Pattern
    prev_citation_pattern = r'\d{4}\s+WL\s+\d+|\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+|\d+\s+U\.S\.\s+\d+'
    
    print(f"\nPattern: {prev_citation_pattern}")
    
    # Check if pattern matches
    wl_match = re.search(prev_citation_pattern, look_behind_wl)
    f_match = re.search(prev_citation_pattern, look_behind_f)
    
    print(f"\nWL citation has previous citation: {bool(wl_match)}")
    print(f"F.2d citation has previous citation: {bool(f_match)}")
    
    if f_match:
        print(f"  Previous citation found: '{f_match.group()}'")
        print("  → This should trigger the series citation fix!")
    
    # Now test the actual metadata extraction
    print("\n" + "=" * 50)
    print("Testing actual extraction...")
    
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2
    import asyncio
    
    async def test():
        processor = UnifiedCitationProcessorV2()
        
        # Create a test citation object
        from src.models import CitationResult
        
        citation = CitationResult(
            citation="855 F.2d 569",
            start_index=f_pos,
            end_index=f_pos + len("855 F.2d 569"),
            method="test"
        )
        
        print(f"\nCreated test citation: {citation.citation}")
        print(f"Start index: {citation.start_index}")
        
        # Call _extract_metadata directly
        print("\nCalling _extract_metadata...")
        processor._extract_metadata(citation, text, None)
        
        print(f"Result case name: {citation.extracted_case_name}")
        
        if hasattr(citation, 'metadata') and citation.metadata:
            print(f"Eyecite fallback: {citation.metadata.get('eyecite_fallback_name')}")
    
    asyncio.run(test())

test_series_detection()
