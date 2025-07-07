#!/usr/bin/env python3
"""
Test script to verify that short citations are being properly filtered out.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from citation_extractor import extract_citation_text_from_eyecite
from src.citation_utils import validate_potential_citation, clean_and_validate_citations
from document_processing import extract_and_verify_citations

def test_eyecite_extraction_filtering():
    """Test that eyecite extraction properly filters out short citations."""
    print("Testing eyecite extraction filtering...")
    
    # Test cases for short citations that should be filtered out
    short_citation_tests = [
        "IdCitation('Id.', metadata=IdCitation.Metadata(parenthetical=None, pin_cite='at 748', pin_cite_span_start=None, pin_cite_span_end=None))",
        "IdCitation('id.', metadata=IdCitation.Metadata(parenthetical=None, pin_cite='at 32', pin_cite_span_start=None, pin_cite_span_end=None))",
        "IdCitation('Ibid.', metadata=IdCitation.Metadata(parenthetical=None, pin_cite=None, pin_cite_span_start=None, pin_cite_span_end=None))",
        "ShortCaseCitation('97 Wash. 2d, at 30', groups={'volume': '97', 'reporter': 'Wash. 2d', 'page': '30'})",
        "UnknownCitation('§', metadata=CitationBase.Metadata(parenthetical=None, pin_cite=None, pin_cite_span_start=None, pin_cite_span_end=None))",
        "SupraCitation('supra.', metadata=SupraCitation.Metadata(parenthetical=None, pin_cite=None, pin_cite_span_start=None, pin_cite_span_end=None, antecedent_guess='Couns.', volume=None))",
    ]
    
    # Test cases for valid citations that should NOT be filtered out
    valid_citation_tests = [
        "FullCaseCitation('97 Wash. 2d 30', groups={'volume': '97', 'reporter': 'Wash. 2d', 'page': '30'})",
        "FullCaseCitation('640 P.2d 716', groups={'volume': '640', 'reporter': 'P.2d', 'page': '716'})",
        "FullCaseCitation('410 U.S. 113', groups={'volume': '410', 'reporter': 'U.S.', 'page': '113'})",
    ]
    
    print("\nTesting short citations (should be filtered out):")
    for i, test_case in enumerate(short_citation_tests, 1):
        result = extract_citation_text_from_eyecite(test_case)
        status = "FILTERED" if not result else "NOT FILTERED"
        print(f"  {i}. {test_case[:50]}... -> {status}")
        if result:
            print(f"     Extracted: '{result}'")
    
    print("\nTesting valid citations (should NOT be filtered out):")
    for i, test_case in enumerate(valid_citation_tests, 1):
        result = extract_citation_text_from_eyecite(test_case)
        status = "EXTRACTED" if result else "NOT EXTRACTED"
        print(f"  {i}. {test_case[:50]}... -> {status}")
        if result:
            print(f"     Extracted: '{result}'")

def test_validation_filtering():
    """Test that validation functions properly filter out short citations."""
    print("\n\nTesting validation filtering...")
    
    # Test cases for short citations that should be filtered out
    short_citation_tests = [
        "IdCitation('Id.', metadata=...)",
        "97 Wash. 2d at 30",
        "id. at 748",
        "Ibid. at 32",
        "supra at 201",
        "infra at 7",
    ]
    
    # Test cases for valid citations that should NOT be filtered out
    valid_citation_tests = [
        "97 Wash. 2d 30",
        "640 P.2d 716",
        "410 U.S. 113",
        "123 F.3d 456",
    ]
    
    print("\nTesting validate_potential_citation with short citations:")
    for i, test_case in enumerate(short_citation_tests, 1):
        is_valid, reason = validate_potential_citation(test_case)
        status = "FILTERED" if not is_valid else "NOT FILTERED"
        print(f"  {i}. '{test_case}' -> {status} ({reason})")
    
    print("\nTesting validate_potential_citation with valid citations:")
    for i, test_case in enumerate(valid_citation_tests, 1):
        is_valid, reason = validate_potential_citation(test_case)
        status = "VALID" if is_valid else "INVALID"
        print(f"  {i}. '{test_case}' -> {status} ({reason})")

def test_clean_and_validate_filtering():
    """Test that clean_and_validate_citations properly filters out short citations."""
    print("\n\nTesting clean_and_validate_citations filtering...")
    
    # Mixed list of citations
    mixed_citations = [
        "97 Wash. 2d 30",  # Valid
        "IdCitation('Id.', metadata=...)",  # Short
        "640 P.2d 716",  # Valid
        "97 Wash. 2d at 30",  # Short
        "410 U.S. 113",  # Valid
        "id. at 748",  # Short
        "123 F.3d 456",  # Valid
    ]
    
    cleaned_citations, validation_stats = clean_and_validate_citations(mixed_citations)
    
    print(f"Original citations: {len(mixed_citations)}")
    print(f"Cleaned citations: {len(cleaned_citations)}")
    print(f"Validation stats: {validation_stats}")
    
    print("\nCleaned citations:")
    for i, citation in enumerate(cleaned_citations, 1):
        print(f"  {i}. {citation}")

def test_document_processing_filtering():
    """Test that document processing properly filters out short citations."""
    print("\n\nTesting document processing filtering...")
    
    # Sample text with mixed citations
    sample_text = """
    The court held in Seattle Times Co. v. Ishikawa, 97 Wash. 2d 30, 640 P.2d 716 (1982) 
    that the public has a right to access court records. See also id. at 32. 
    In Doe v. Washington State Patrol, 185 Wash. 2d 363, 374 P.3d 63 (2016), 
    the court further clarified this principle. See supra at 201.
    """
    
    print("Sample text:")
    print(sample_text)
    
    try:
        results = extract_and_verify_citations(sample_text)
        print(f"\nExtraction results: {len(results)} citations found")
        
        for i, result in enumerate(results, 1):
            citation = result.get('citation', '')
            method = result.get('method', 'unknown')
            verified = result.get('verified', 'unknown')
            print(f"  {i}. '{citation}' (method: {method}, verified: {verified})")
            
    except Exception as e:
        print(f"Error testing document processing: {e}")

if __name__ == "__main__":
    print("=== Short Citation Filtering Test ===\n")
    
    test_eyecite_extraction_filtering()
    test_validation_filtering()
    test_clean_and_validate_filtering()
    test_document_processing_filtering()
    
    print("\n=== Test Complete ===") 