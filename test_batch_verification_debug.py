#!/usr/bin/env python3
"""
Debug script to test the batch verification process and see why canonical data is not being preserved.
"""

import json
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_batch_verification():
    """Test the complete batch verification process."""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test text from the user's output
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Testing complete batch verification process:")
    print("=" * 60)
    print(f"Test text: {test_text}")
    print("=" * 60)
    
    try:
        # Process the text
        result = processor.process_text(test_text)
        
        print(f"\nProcessing Result:")
        print(f"  Status: {result.get('status', 'N/A')}")
        print(f"  Total citations: {len(result.get('results', []))}")
        print(f"  Case names: {result.get('case_names', [])}")
        
        # Check each citation
        citations = result.get('results', [])
        for i, citation in enumerate(citations, 1):
            print(f"\n{i}. Citation: {citation.get('citation')}")
            print(f"   Verified: {citation.get('verified')}")
            print(f"   Source: {citation.get('source')}")
            print(f"   Extracted case name: {citation.get('extracted_case_name')}")
            print(f"   Extracted date: {citation.get('extracted_date')}")
            print(f"   Canonical name: {citation.get('canonical_name')}")
            print(f"   Canonical date: {citation.get('canonical_date')}")
            print(f"   URL: {citation.get('url')}")
            
            # Check if canonical data is missing
            if citation.get('verified') == 'true' and citation.get('canonical_name') == 'N/A':
                print(f"   ❌ ISSUE: Verified but canonical_name is 'N/A'")
            elif citation.get('verified') == 'true' and citation.get('canonical_date') == 'N/A':
                print(f"   ❌ ISSUE: Verified but canonical_date is 'N/A'")
            elif citation.get('verified') == 'true':
                print(f"   ✅ Canonical data present")
            else:
                print(f"   ℹ️  Not verified")
        
        # Check metadata
        metadata = result.get('metadata', {})
        print(f"\nMetadata:")
        print(f"  Processing time: {metadata.get('processing_time')}")
        print(f"  Processor used: {metadata.get('processor_used')}")
        print(f"  Text length: {metadata.get('text_length')}")
        
        # Check summary
        summary = result.get('summary', {})
        print(f"\nSummary:")
        print(f"  Total citations: {summary.get('total_citations')}")
        print(f"  Verified citations: {summary.get('verified_citations')}")
        print(f"  Unverified citations: {summary.get('unverified_citations')}")
        print(f"  Unique cases: {summary.get('unique_cases')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_individual_verification():
    """Test individual citation verification to compare with batch results."""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the specific citations from the user's output
    test_citations = [
        {
            'citation': '171 Wn.2d 486, 493, 256 P.3d 321',
            'case_name': 'Carlson v. Glob. Client Sols., LLC',
            'date': '2011'
        },
        {
            'citation': '146 Wn.2d 1, 9, 43 P.3d 4',
            'case_name': 'Campbell & Gwinn, LLC',
            'date': '2003'
        }
    ]
    
    print("\n" + "=" * 60)
    print("Testing individual verification:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_citations, 1):
        print(f"\n{i}. Individual verification for: {test_case['citation']}")
        
        try:
            # Test individual verification
            result = processor._verify_with_courtlistener_search(
                test_case['citation'],
                test_case['case_name'],
                test_case['date']
            )
            
            print(f"   Individual result:")
            print(f"     verified: {result.get('verified')}")
            print(f"     canonical_name: {result.get('canonical_name')}")
            print(f"     canonical_date: {result.get('canonical_date')}")
            print(f"     url: {result.get('url')}")
            print(f"     source: {result.get('source')}")
            
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_batch_verification()
    test_individual_verification() 