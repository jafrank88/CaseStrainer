#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to identify which citation cases are NOT going to the complex citation processing branch.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# DEPRECATED: # DEPRECATED: from src.complex_citation_integration import ComplexCitationIntegrator
# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_complex_branch_coverage():
    """Test which citation cases are not going to the complex citation processing branch."""
    
    # Test cases that might NOT go to complex processing
    test_cases = [
        # Single citations (should NOT go to complex processing)
        "199 Wash. App. 280",
        "399 P.3d 1195", 
        "410 U.S. 113",
        "Miranda v. Arizona, 384 U.S. 436",
        
        # Complex citations (should go to complex processing)
        "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)",
        "Roe v. Wade, 410 U.S. 113, 93 S. Ct. 705, 35 L. Ed. 2d 147 (1973)",
        "Miranda v. Arizona, 384 U.S. 436, 86 S. Ct. 1602, 16 L. Ed. 2d 694 (1966)",
        
        # Edge cases
        "See 199 Wash. App. 280",
        "But see 399 P.3d 1195",
        "Cf. 410 U.S. 113",
        
        # Citations with pinpoint pages
        "199 Wash. App. 280, 283",
        "410 U.S. 113, 116",
        
        # Citations with docket numbers
        "No. 48000-0-II. 199 Wash. App. 280",
        "199 Wash. App. 280 (No. 48000-0-II)",
        
        # Citations with case history
        "Doe v. Smith (Doe I), 199 Wash. App. 280",
        "Doe v. Smith (Doe II), 399 P.3d 1195",
        
        # Citations with publication status
        "199 Wash. App. 280 (unpublished)",
        "399 P.3d 1195 (published)",
        
        # Mixed cases
        "199 Wash. App. 280, 283 (unpublished)",
        "Doe v. Smith, 199 Wash. App. 280, No. 48000-0-II",
    ]
    
    integrator = ComplexCitationIntegrator()
    extractor = CitationExtractor(use_eyecite=False, use_regex=True, extract_case_names=True)
    
    print("Testing Complex Citation Branch Coverage")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case} ---")
        
        # Check what the CitationExtractor finds
        extracted_citations = extractor.extract_citations(test_case)
        print(f"  CitationExtractor found {len(extracted_citations)} citations: {[c.get('citation', 'N/A') for c in extracted_citations]}")
        
        # Check if it's considered complex
        is_complex = integrator.is_complex_citation(test_case)
        print(f"  Is complex citation: {is_complex}")
        
        # Determine which branch it would go to
        if is_complex and len(extracted_citations) > 1:
            branch = "COMPLEX PROCESSING (multiple citations + complex features)"
        elif not extracted_citations:
            if is_complex:
                branch = "COMPLEX PROCESSING (no citations found but complex features)"
            else:
                branch = "SIMPLE PROCESSING (no citations found)"
        else:
            branch = "SIMPLE PROCESSING (single citation or no complex features)"
        
        print(f"  Branch: {branch}")
        
        # Test the actual processing
        try:
            results = integrator.process_text_with_complex_citations_original(test_case)
            print(f"  Results returned: {len(results)}")
            for j, result in enumerate(results, 1):
                print(f"    Result {j}: citation={result.get('citation')}, verified={result.get('verified')}, is_complex={result.get('is_complex_citation', False)}")
        except Exception as e:
            print(f"  Error in processing: {e}")

def test_specific_edge_cases():
    """Test specific edge cases that might be problematic."""
    
    print("\n\nTesting Specific Edge Cases")
    print("=" * 80)
    
    edge_cases = [
        # Single citation with case name
        "Miranda v. Arizona, 384 U.S. 436",
        
        # Single citation without case name
        "384 U.S. 436",
        
        # Citation with "See" prefix
        "See Miranda v. Arizona, 384 U.S. 436",
        
        # Citation with pinpoint page
        "384 U.S. 436, 444",
        
        # Citation that looks complex but might not be detected
        "Miranda v. Arizona, 384 U.S. 436, 86 S. Ct. 1602",
    ]
    
    integrator = ComplexCitationIntegrator()
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n--- Edge Case {i}: {test_case} ---")
        
        # Check complex citation detection
        is_complex = integrator.is_complex_citation(test_case)
        print(f"  Is complex: {is_complex}")
        
        # Parse as complex citation to see what it finds
        try:
            complex_data = integrator.parse_complex_citation(test_case)
            print(f"  Primary citation: {complex_data.primary_citation}")
            print(f"  Parallel citations: {complex_data.parallel_citations}")
            print(f"  Case name: {complex_data.case_name}")
            print(f"  Pinpoint pages: {complex_data.pinpoint_pages}")
            print(f"  Is complex: {complex_data.is_complex}")
        except Exception as e:
            print(f"  Error parsing: {e}")

if __name__ == "__main__":
    test_complex_branch_coverage()
    test_specific_edge_cases() 