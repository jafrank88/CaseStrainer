#!/usr/bin/env python3
"""
Test the Permian Basin Area Rate Cases extraction issue
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_permian_extraction():
    """Test extraction of In re Permian Basin Area Rate Cases"""
    
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    
    # The problematic citation text
    citation = "390 U.S. 747, 784 (1968)"
    
    # Context from the user's text
    full_context = """Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
    
    print("PERMIAN BASIN EXTRACTION TEST")
    print("=" * 60)
    print(f"Citation: {citation}")
    print(f"Full context: {full_context}")
    print()
    
    # Find the citation position
    citation_pos = full_context.find(citation)
    if citation_pos == -1:
        print("❌ Citation not found in context")
        return
    
    print(f"Citation position: {citation_pos}")
    
    # Extract context around citation (300 chars before and after)
    start = max(0, citation_pos - 300)
    end = min(len(full_context), citation_pos + len(citation) + 300)
    context = full_context[start:end]
    
    print(f"Context for extraction: {context}")
    print()
    
    # Test extraction with debug
    result = extract_case_name_and_date_unified_master(
        text=context,
        citation=citation,
        start_index=citation_pos - start,
        end_index=citation_pos - start + len(citation),
        debug=True
    )
    
    print()
    print("EXTRACTION RESULT:")
    print(f"  Case name: {result.get('case_name', 'N/A')}")
    print(f"  Date: {result.get('date', 'N/A')}")
    print(f"  Confidence: {result.get('confidence', 0):.2f}")
    print(f"  Method: {result.get('method', 'N/A')}")
    
    # Test with just the quoted part
    quoted_context = 'In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)'
    print("\n" + "=" * 60)
    print("TEST WITH QUOTED CONTEXT ONLY:")
    print(f"Context: {quoted_context}")
    
    quoted_pos = quoted_context.find(citation)
    quoted_result = extract_case_name_and_date_unified_master(
        text=quoted_context,
        citation=citation,
        start_index=quoted_pos,
        end_index=quoted_pos + len(citation),
        debug=True
    )
    
    print()
    print("QUOTED EXTRACTION RESULT:")
    print(f"  Case name: {quoted_result.get('case_name', 'N/A')}")
    print(f"  Date: {quoted_result.get('date', 'N/A')}")
    print(f"  Confidence: {quoted_result.get('confidence', 0):.2f}")
    print(f"  Method: {quoted_result.get('method', 'N/A')}")

if __name__ == "__main__":
    test_permian_extraction()
