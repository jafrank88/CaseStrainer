#!/usr/bin/env python3
"""
Test script to analyze specific legal text and show backend results
"""

import sys
import os
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
from src.api.services.citation_service import CitationService

def test_specific_text():
    """Test the specific legal text provided by the user"""
    
    # The text provided by the user
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    print("=" * 80)
    print("TESTING SPECIFIC LEGAL TEXT")
    print("=" * 80)
    print(f"Input text:\n{test_text}")
    print("\n" + "=" * 80)
    
    try:
        # Initialize the processor
        processor = UnifiedCitationProcessor()
        
        # Extract citations
        print("1. EXTRACTING CITATIONS...")
        extraction_results = processor.extract_citations(test_text)
        
        print(f"Found {len(extraction_results)} citations:")
        for i, citation in enumerate(extraction_results, 1):
            print(f"  {i}. {citation.citation}")
            if citation.extracted_date:
                print(f"     Date: {citation.extracted_date}")
            if citation.extracted_case_name:
                print(f"     Case: {citation.extracted_case_name}")
            print()
        
        # Verify citations
        print("2. VERIFYING CITATIONS...")
        citation_service = CitationService()
        
        verification_results = []
        for citation in extraction_results:
            print(f"Verifying: {citation.citation}")
            
            # Verify the citation
            verification_result = citation_service.verify_citation(citation.citation)
            
            # Add extracted data to the result
            verification_result['extracted_date'] = citation.extracted_date
            verification_result['extracted_case_name'] = citation.extracted_case_name
            verification_result['citation'] = citation.citation
            
            verification_results.append(verification_result)
            
            print(f"  Status: {verification_result.get('status', 'unknown')}")
            if verification_result.get('canonical_data'):
                canonical = verification_result['canonical_data']
                print(f"  Found: {canonical.get('case_name', 'N/A')}")
                print(f"  Date: {canonical.get('decision_date', 'N/A')}")
            print()
        
        # Show final results
        print("3. FINAL RESULTS:")
        print("=" * 80)
        
        for i, result in enumerate(verification_results, 1):
            print(f"Citation {i}: {result['citation']}")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Extracted Date: {result.get('extracted_date', 'Not found')}")
            print(f"  Extracted Case: {result.get('extracted_case_name', 'Not found')}")
            
            if result.get('canonical_data'):
                canonical = result['canonical_data']
                print(f"  Verified Case: {canonical.get('case_name', 'N/A')}")
                print(f"  Verified Date: {canonical.get('decision_date', 'N/A')}")
                print(f"  Court: {canonical.get('court', 'N/A')}")
                print(f"  Reporter: {canonical.get('reporter', 'N/A')}")
            
            print()
        
        # Save detailed results to file
        output_file = "test_results_detailed.json"
        with open(output_file, 'w') as f:
            # Convert CitationResult objects to dictionaries for JSON serialization
            extraction_dicts = []
            for citation in extraction_results:
                extraction_dicts.append({
                    'citation': citation.citation,
                    'extracted_date': citation.extracted_date,
                    'extracted_case_name': citation.extracted_case_name,
                    'start_index': citation.start_index,
                    'end_index': citation.end_index
                })
            
            json.dump({
                'input_text': test_text,
                'extraction_results': extraction_dicts,
                'verification_results': verification_results
            }, f, indent=2)
        
        print(f"Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_text() 