#!/usr/bin/env python3
"""
Test the contamination filter with manual document primary case name
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_contamination_filter_manual():
    """Test contamination filter with manually set document primary case name"""
    
    print("🔍 TESTING CONTAMINATION FILTER WITH MANUAL CASE NAME")
    print("=" * 60)
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    from src.models import ProcessingConfig
    
    # Test text that contains "City of Bellevue v. Lorang" as a citation
    test_text = """
    The court considered precedent from City of Bellevue v. Lorang, 140 Wn.2d 19 (2000) 
    and also referenced Berst v. Snohomish County, 114 Wn. App. 245 (2002).
    Additional cases include State v. Manussier, 129 Wn.2d 652 (1996).
    """
    
    print("Test text:")
    print(test_text.strip())
    print()
    
    # Test 1: WITHOUT document primary case name (should have contamination)
    print("Test 1: WITHOUT document primary case name")
    print("-" * 50)
    
    config = ProcessingConfig(enable_verification=False)  # Disable verification for speed
    processor = UnifiedCitationProcessorV2(config=config)
    
    result = await processor.process_text(test_text)
    citations = result.get('citations', [])
    
    print(f"Found {len(citations)} citations:")
    for cit in citations:
        citation_text = getattr(cit, 'citation', 'N/A')
        case_name = getattr(cit, 'extracted_case_name', 'N/A')
        print(f"  {citation_text} → '{case_name}'")
    
    # Test 2: WITH correct document primary case name (should filter contamination)
    print(f"\nTest 2: WITH document primary case name = 'Cape George Land Company v. Jefferson County'")
    print("-" * 70)
    
    processor2 = UnifiedCitationProcessorV2(config=config)
    processor2.document_primary_case_name = "Cape George Land Company v. Jefferson County"
    
    result2 = await processor2.process_text(test_text)
    citations2 = result2.get('citations', [])
    
    print(f"Found {len(citations2)} citations:")
    for cit in citations2:
        citation_text = getattr(cit, 'citation', 'N/A')
        case_name = getattr(cit, 'extracted_case_name', 'N/A')
        
        is_contaminated = 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper()
        status = "❌ CONTAMINATED" if is_contaminated else ("✅ CLEAN" if case_name != 'N/A' else "⚠️  N/A")
        
        print(f"  {citation_text} → '{case_name}' ({status})")
    
    # Test 3: Test the actual PDF text section
    print(f"\nTest 3: Actual PDF text section with correct document primary case name")
    print("-" * 70)
    
    pdf_section = """
    Young v. Pierce County, 120 Wn. App. 175, 188, 84 P.3d 927 (2004) (quoting City of Bellevue v. Lorang, 140 Wn.2d 19, 32, 992 P.2d 496 (2000)). Petitioners appear to contend that the alleged errors were not harmless. Washington v. Manussier, 129 Wn.2d 652, 679-80, 921 P.2d 473 (1996) (quoting Rozner v. Bellevue, 116 Wn.2d 342, 351, 804 P.2d 24 (1991)).
    """
    
    processor3 = UnifiedCitationProcessorV2(config=config)
    processor3.document_primary_case_name = "Cape George Land Company v. Jefferson County"
    
    result3 = await processor3.process_text(pdf_section)
    citations3 = result3.get('citations', [])
    
    print(f"Found {len(citations3)} citations:")
    contaminated_count = 0
    for cit in citations3:
        citation_text = getattr(cit, 'citation', 'N/A')
        case_name = getattr(cit, 'extracted_case_name', 'N/A')
        
        is_contaminated = 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper()
        if is_contaminated:
            contaminated_count += 1
        status = "❌ CONTAMINATED" if is_contaminated else ("✅ CLEAN" if case_name != 'N/A' else "⚠️  N/A")
        
        print(f"  {citation_text} → '{case_name}' ({status})")
    
    print(f"\nContamination rate: {contaminated_count}/{len(citations3)} ({contaminated_count/len(citations3)*100:.1f}%)")
    
    if contaminated_count == 0:
        print("🎉 CONTAMINATION FILTER IS WORKING!")
    else:
        print("❌ CONTAMINATION FILTER IS NOT WORKING!")

if __name__ == "__main__":
    asyncio.run(test_contamination_filter_manual())
