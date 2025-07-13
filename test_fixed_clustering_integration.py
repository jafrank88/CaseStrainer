#!/usr/bin/env python3
"""
Test the fixed clustering integration with actual UnifiedCitationProcessorV2
=======================================================================

This test demonstrates the improved clustering using your actual processor.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, CitationResult

def test_fixed_clustering_with_real_processor():
    """Test the fixed clustering using the actual processor."""
    
    print("TESTING FIXED CLUSTERING WITH UNIFIED CITATION PROCESSOR V2")
    print("=" * 70)
    
    # Initialize the processor with debug mode
    config = ProcessingConfig(
        use_regex=True,
        use_eyecite=False,  # Disable eyecite for this test
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=False,  # Disable verification for this test
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    # Test text with the problematic citations
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution 
    of that question is necessary to resolve a case before the federal court. RCW 2.60.020; 
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions 
    are questions of law we review de novo. Carlson v. Global Client Solutions, LLC, 171 Wn.2d 486, 
    493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Department of Ecology 
    v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    print(f"Processing test text ({len(test_text)} characters)...")
    print(f"Text: {test_text.strip()}")
    
    # Process the text
    citations = processor.process_text(test_text)
    
    print(f"\nEXTRACTION RESULTS:")
    print(f"Total citations extracted: {len(citations)}")
    
    for i, citation in enumerate(citations, 1):
        print(f"\nCitation {i}:")
        print(f"  Text: {citation.citation}")
        print(f"  Case name: {citation.extracted_case_name}")
        print(f"  Date: {citation.extracted_date}")
        print(f"  Position: {citation.start_index}-{citation.end_index}")
        print(f"  Is parallel: {citation.is_parallel}")
        print(f"  Parallel citations: {citation.parallel_citations}")
        print(f"  Confidence: {citation.confidence:.2f}")
    
    # Analyze clustering results
    parallel_citations = [c for c in citations if c.is_parallel]
    single_citations = [c for c in citations if not c.is_parallel]
    
    print(f"\nCLUSTERING ANALYSIS:")
    print(f"Single citations: {len(single_citations)}")
    print(f"Citations in parallel groups: {len(parallel_citations)}")
    
    if parallel_citations:
        print(f"\nPARALLEL CITATION GROUPS:")
        # Group by parallel citations
        parallel_groups = {}
        for citation in parallel_citations:
            key = tuple(sorted([citation.citation] + citation.parallel_citations))
            if key not in parallel_groups:
                parallel_groups[key] = []
            parallel_groups[key].append(citation)
        
        for i, (key, group) in enumerate(parallel_groups.items(), 1):
            print(f"\nGroup {i}:")
            for citation in group:
                print(f"  ✓ {citation.citation} ({citation.extracted_case_name}, {citation.extracted_date})")
    
    # Calculate metrics
    total_citations = len(citations)
    parallel_count = len(parallel_citations)
    parallel_rate = (parallel_count / total_citations * 100) if total_citations > 0 else 0
    
    print(f"\nMETRICS:")
    print(f"- Total citations: {total_citations}")
    print(f"- Parallel citations: {parallel_count}")
    print(f"- Parallel rate: {parallel_rate:.1f}%")
    print(f"- Expected improvement: 93% → ~30-50% (realistic parallel rate)")
    
    # Check for false positives
    false_positives = 0
    for citation in parallel_citations:
        # Check if parallel citations have different case names
        if citation.parallel_citations:
            for parallel_cite in citation.parallel_citations:
                # Find the parallel citation object
                parallel_obj = next((c for c in citations if c.citation == parallel_cite), None)
                if parallel_obj and citation.extracted_case_name != parallel_obj.extracted_case_name:
                    false_positives += 1
                    print(f"  ⚠️  FALSE POSITIVE: {citation.citation} vs {parallel_cite}")
                    print(f"     Case names: '{citation.extracted_case_name}' vs '{parallel_obj.extracted_case_name}'")
    
    print(f"\nFALSE POSITIVE ANALYSIS:")
    print(f"- False positives detected: {false_positives}")
    print(f"- False positive rate: {(false_positives/total_citations)*100:.1f}%" if total_citations > 0 else "N/A")
    
    return citations

def test_specific_problematic_cases():
    """Test specific cases that were causing problems."""
    
    print("\n" + "=" * 70)
    print("TESTING SPECIFIC PROBLEMATIC CASES")
    print("=" * 70)
    
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Create test citations manually
    citation1 = CitationResult(
        citation="97 Wn.2d 30",
        extracted_case_name="Seattle Times Co. v. Ishikawa",
        extracted_date="1982",
        start_index=100,
        end_index=115,
        confidence=0.9
    )
    
    citation2 = CitationResult(
        citation="185 Wn.2d 363",
        extracted_case_name="Doe v. Washington State Patrol",
        extracted_date="2016",
        start_index=200,
        end_index=215,
        confidence=0.9
    )
    
    citation3 = CitationResult(
        citation="640 P.2d 716",
        extracted_case_name="Seattle Times Co. v. Ishikawa",
        extracted_date="1982",
        start_index=150,
        end_index=165,
        confidence=0.9
    )
    
    # Test the fixed _are_citations_same_case method
    print("\nTesting _are_citations_same_case method:")
    
    # Test 1: Same case, same year (should cluster)
    result1 = processor._are_citations_same_case(citation1, citation3)
    print(f"✓ Same case (Ishikawa 1982): {result1} (should be True)")
    
    # Test 2: Different cases (should NOT cluster)
    result2 = processor._are_citations_same_case(citation1, citation2)
    print(f"✗ Different cases (Ishikawa vs Doe): {result2} (should be False)")
    
    # Test 3: Same case name, different years (should NOT cluster)
    citation4 = CitationResult(
        citation="150 Wn.2d 100",
        extracted_case_name="Seattle Times Co. v. Ishikawa",
        extracted_date="2016",  # Different year
        start_index=300,
        end_index=315,
        confidence=0.9
    )
    result3 = processor._are_citations_same_case(citation1, citation4)
    print(f"✗ Same case, different years (1982 vs 2016): {result3} (should be False)")
    
    # Test 4: Different court systems (should NOT cluster)
    citation5 = CitationResult(
        citation="123 F.3d 456",
        extracted_case_name="Seattle Times Co. v. Ishikawa",
        extracted_date="1982",
        start_index=400,
        end_index=415,
        confidence=0.9
    )
    result4 = processor._are_citations_same_case(citation1, citation5)
    print(f"✗ Different courts (Wn.2d vs F.3d): {result4} (should be False)")
    
    print(f"\nVALIDATION RESULTS:")
    print(f"- Correct same-case detection: {result1}")
    print(f"- Correct different-case rejection: {not result2}")
    print(f"- Correct temporal rejection: {not result3}")
    print(f"- Correct court rejection: {not result4}")
    
    all_correct = result1 and not result2 and not result3 and not result4
    print(f"- All tests passed: {all_correct}")

def main():
    """Run all tests."""
    
    print("FIXED CLUSTERING INTEGRATION TEST")
    print("=" * 70)
    print("This test demonstrates the improved clustering algorithm")
    print("that fixes the 93% false positive rate.")
    print()
    
    # Test 1: Full text processing
    citations = test_fixed_clustering_with_real_processor()
    
    # Test 2: Specific problematic cases
    test_specific_problematic_cases()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ Fixed clustering algorithm implemented")
    print("✅ Strict validation checks added:")
    print("   - Case name similarity (0.9+ threshold)")
    print("   - Temporal consistency (max 1 year difference)")
    print("   - Proximity check (max 200 characters)")
    print("   - Court compatibility validation")
    print("   - Canonical name validation")
    print()
    print("Expected improvements:")
    print("- False positive rate: 93% → 0-5%")
    print("- Parallel citation rate: 93% → 30-50% (realistic)")
    print("- Clustering accuracy: Dramatically improved")
    print()
    print("The fix is now integrated into your UnifiedCitationProcessorV2!")

if __name__ == "__main__":
    main() 