#!/usr/bin/env python3
"""
Test script to verify improvements to citation verification and case name extraction.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

def test_improvements():
    """Test the improvements to citation processing and case name extraction."""
    
    # Test text with Washington citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)."""
    
    print("Testing citation processing improvements...")
    print("=" * 60)
    
    # Test citation processing
    processor = UnifiedCitationProcessorV2()
    result = processor.process_text(test_text)
    
    # Handle different result structures
    if isinstance(result, dict) and 'citations' in result:
        citations = result['citations']
    elif isinstance(result, list):
        citations = result
    else:
        print(f"Unexpected result structure: {type(result)}")
        print(f"Result: {result}")
        return
    
    print(f"Citations found: {len(citations)}")
    print()
    
    for i, citation in enumerate(citations, 1):
        print(f"Citation {i}:")
        print(f"  Text: {citation['citation']}")
        print(f"  Verified: {citation['verified']}")
        print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
        print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
        print(f"  URL: {citation.get('url', 'N/A')}")
        print(f"  Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
        print(f"  Extracted Date: {citation.get('extracted_date', 'N/A')}")
        print()
    
    print("Testing case name extraction improvements...")
    print("=" * 60)
    
    # Test case name extraction
    case_name, date, confidence = extract_case_name_triple_comprehensive(test_text)
    print(f"Extracted Case Name: {case_name}")
    print(f"Extracted Date: {date}")
    print(f"Confidence: {confidence:.2f}")
    
    # Test with specific citation context
    print("\nTesting with citation context...")
    citation_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)"
    case_name2, date2, confidence2 = extract_case_name_triple_comprehensive(citation_text)
    print(f"Citation: {citation_text}")
    print(f"Extracted Case Name: {case_name2}")
    print(f"Extracted Date: {date2}")
    print(f"Confidence: {confidence2:.2f}")

if __name__ == "__main__":
    test_improvements() 