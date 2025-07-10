#!/usr/bin/env python3
"""
Test the full pipeline with date protection mechanisms, bypassing regex compilation issues.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor, CitationResult
from src.standalone_citation_parser import DateExtractor

def test_protected_pipeline():
    """Test the full pipeline with date protection mechanisms."""
    
    print("=== TESTING PROTECTED PIPELINE ===")
    print()
    
    # Sample legal document text
    test_text = """
    The Washington Supreme Court in State v. Smith, 171 Wash. 2d 486 (2011), 
    addressed the issue of search and seizure. The court decided this case on 
    May 12, 2011. This decision was later cited in State v. Johnson, 200 Wash. 2d 72 (2023).
    
    In another case, Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
    held that separate educational facilities are inherently unequal.
    
    The Pacific Reporter citation is 514 P.3d 643 (2023).
    """
    
    print(f"Test document text:")
    print(f"'{test_text.strip()}'")
    print()
    
    # Create citations manually to bypass regex compilation issues
    citations = []
    
    # Citation 1: 171 Wash. 2d 486 (2011)
    citation1 = CitationResult(
        citation="171 Wash. 2d 486",
        method='manual',
        pattern='wash2d',
        confidence=0.8,
        start_index=test_text.find("171 Wash. 2d 486"),
        end_index=test_text.find("171 Wash. 2d 486") + len("171 Wash. 2d 486"),
        context=test_text[max(0, test_text.find("171 Wash. 2d 486") - 100):test_text.find("171 Wash. 2d 486") + 100]
    )
    citations.append(citation1)
    
    # Citation 2: 200 Wash. 2d 72 (2023)
    citation2 = CitationResult(
        citation="200 Wash. 2d 72",
        method='manual',
        pattern='wash2d',
        confidence=0.8,
        start_index=test_text.find("200 Wash. 2d 72"),
        end_index=test_text.find("200 Wash. 2d 72") + len("200 Wash. 2d 72"),
        context=test_text[max(0, test_text.find("200 Wash. 2d 72") - 100):test_text.find("200 Wash. 2d 72") + 100]
    )
    citations.append(citation2)
    
    # Citation 3: 347 U.S. 483 (1954)
    citation3 = CitationResult(
        citation="347 U.S. 483",
        method='manual',
        pattern='us',
        confidence=0.8,
        start_index=test_text.find("347 U.S. 483"),
        end_index=test_text.find("347 U.S. 483") + len("347 U.S. 483"),
        context=test_text[max(0, test_text.find("347 U.S. 483") - 100):test_text.find("347 U.S. 483") + 100]
    )
    citations.append(citation3)
    
    # Citation 4: 514 P.3d 643 (2023)
    citation4 = CitationResult(
        citation="514 P.3d 643",
        method='manual',
        pattern='p3d',
        confidence=0.8,
        start_index=test_text.find("514 P.3d 643"),
        end_index=test_text.find("514 P.3d 643") + len("514 P.3d 643"),
        context=test_text[max(0, test_text.find("514 P.3d 643") - 100):test_text.find("514 P.3d 643") + 100]
    )
    citations.append(citation4)
    
    print(f"Created {len(citations)} citations manually")
    print()
    
    # Initialize processor
    processor = UnifiedCitationProcessor()
    
    # Test verify_citations with date protection
    print("Testing verify_citations with date protection...")
    verified_citations = processor.verify_citations(citations, test_text)
    
    print(f"\n=== VERIFICATION RESULTS ===")
    print(f"Total citations processed: {len(verified_citations)}")
    print()
    
    # Check each citation result
    citations_with_dates = 0
    for i, citation in enumerate(verified_citations, 1):
        print(f"Citation {i}:")
        print(f"  Citation text: {citation.citation}")
        print(f"  Extracted date: '{citation.extracted_date or 'N/A'}'")
        print(f"  Canonical date: '{citation.canonical_date or 'N/A'}'")
        print(f"  Extracted case name: '{citation.extracted_case_name or 'N/A'}'")
        print(f"  Canonical name: '{citation.canonical_name or 'N/A'}'")
        print(f"  Verified: {citation.verified}")
        print(f"  Method: {citation.method}")
        print(f"  Pattern: {citation.pattern}")
        print()
        
        if citation.extracted_date and citation.extracted_date != 'N/A':
            citations_with_dates += 1
    
    print(f"Citations with extracted dates: {citations_with_dates}/{len(verified_citations)}")
    
    if citations_with_dates > 0:
        print("✅ SUCCESS: extracted_date fields are being populated with protection!")
        for citation in verified_citations:
            if citation.extracted_date and citation.extracted_date != 'N/A':
                print(f"  - {citation.citation}: {citation.extracted_date}")
    else:
        print("❌ ISSUE: No extracted_date fields are populated")
    
    print()
    
    # Test format_for_frontend
    print("Testing format_for_frontend...")
    formatted_results = processor.format_for_frontend(verified_citations)
    
    print(f"\n=== FORMATTED RESULTS ===")
    for i, result in enumerate(formatted_results, 1):
        print(f"Result {i}:")
        print(f"  Citation: {result.get('citation', 'N/A')}")
        print(f"  Extracted date: '{result.get('extracted_date', 'N/A')}'")
        print(f"  Canonical date: '{result.get('canonical_date', 'N/A')}'")
        print(f"  Extracted case name: '{result.get('extracted_case_name', 'N/A')}'")
        print(f"  Canonical name: '{result.get('canonical_name', 'N/A')}'")
        print(f"  Verified: {result.get('verified', False)}")
        print()
    
    # Save results
    output_file = "protected_pipeline_results.json"
    with open(output_file, 'w') as f:
        json.dump(formatted_results, f, indent=2)
    print(f"Results saved to: {output_file}")
    
    return formatted_results

if __name__ == "__main__":
    test_protected_pipeline() 