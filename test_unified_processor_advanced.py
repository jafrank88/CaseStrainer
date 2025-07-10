#!/usr/bin/env python3
"""
Comprehensive test for UnifiedCitationProcessor advanced features.

This test covers:
1. Advanced semantic clustering for parallel citations
2. Debug mode and verbose logging
3. Configurable context windows
4. OCR error correction
5. Confidence scoring
6. Statute filtering (U.S.C., C.F.R., etc.)
"""

import sys
import os
import logging
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_advanced_features():
    """Test all advanced features of the UnifiedCitationProcessor."""
    
    print("=== Testing UnifiedCitationProcessor Advanced Features ===\n")
    
    # Initialize processor with debug mode
    processor = UnifiedCitationProcessor()
    processor.set_debug_mode(enabled=True, verbose=True)
    processor.set_context_window(500)  # Larger context window
    processor.enable_ocr_correction(True)
    processor.enable_confidence_scoring(True)
    processor.enable_statute_filtering(True, include_statutes=False)  # Exclude statutes
    
    # Test text with various citation types
    test_text = """
    The court in State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321 (2011) held that 
    the defendant's rights were violated. This was consistent with the holding in 
    State v. Johnson, 199 Wn. App. 280, 285, 399 P.3d 1195 (2017), which also 
    addressed similar issues.
    
    The plaintiff argued that under 42 U.S.C. § 1983, they had a valid claim. 
    Additionally, the regulations at 28 C.F.R. § 0.85 supported their position.
    
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
    the Supreme Court established important precedent. This was later reinforced 
    by the holding in Miranda v. Arizona, 384 U.S. 436 (1966).
    
    The defendant cited RCW 9A.08.010 in support of their motion, and argued 
    that WAC 296-800-100 was applicable to the facts of this case.
    
    The court also considered the parallel citations: 171 Wn.2d 486, 256 P.3d 321, 
    which refer to the same case as State v. Smith.
    """
    
    print("Test text:")
    print(test_text)
    print("\n" + "="*80 + "\n")
    
    # Process the text
    print("Processing text with all advanced features enabled...")
    result = processor.process_text(
        text=test_text,
        extract_case_names=True,
        verify_citations=True
    )
    
    # Display results
    print(f"\nResults Summary:")
    print(f"Total citations: {result['summary']['total_citations']}")
    print(f"Verified citations: {result['summary']['verified_citations']}")
    print(f"Unverified citations: {result['summary']['unverified_citations']}")
    print(f"Unique cases: {result['summary']['unique_cases']}")
    
    print(f"\nMetadata:")
    for key, value in result['metadata'].items():
        print(f"  {key}: {value}")
    
    print(f"\nDetailed Results:")
    for i, citation in enumerate(result['results'], 1):
        print(f"\n{i}. Citation: {citation['citation']}")
        print(f"   Is cluster: {citation['is_cluster']}")
        print(f"   Is statute: {citation.get('is_statute', False)}")
        print(f"   Method: {citation.get('method', 'N/A')}")
        print(f"   Pattern: {citation.get('pattern', 'N/A')}")
        print(f"   Extracted case name: {citation['extracted_case_name']}")
        print(f"   Extracted date: {citation['extracted_date']}")
        print(f"   Canonical name: {citation['canonical_name']}")
        print(f"   Canonical date: {citation['canonical_date']}")
        print(f"   Verified: {citation['verified']}")
        print(f"   Confidence: {citation.get('confidence', 'N/A')}")
        print(f"   Source: {citation.get('source', 'N/A')}")
        print(f"   Context length: {len(citation.get('context', ''))}")
        
        if citation.get('is_statute'):
            statute_info = citation.get('statute_info', {})
            print(f"   Statute type: {statute_info.get('type', 'N/A')}")
            print(f"   Statute example: {statute_info.get('example', 'N/A')}")
        
        if citation.get('is_cluster'):
            print(f"   Cluster members: {citation.get('cluster_members', [])}")
        
        if citation.get('pinpoint_pages'):
            print(f"   Pinpoint pages: {citation['pinpoint_pages']}")
        
        if citation.get('docket_numbers'):
            print(f"   Docket numbers: {citation['docket_numbers']}")
    
    return result

def test_ocr_correction():
    """Test OCR error correction functionality."""
    print("\n" + "="*80)
    print("=== Testing OCR Error Correction ===\n")
    
    processor = UnifiedCitationProcessor()
    processor.enable_ocr_correction(True)
    
    # Text with common OCR errors
    ocr_text = """
    The case of State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321 (2011) 
    was cited as authority. The court also referenced 42 U.S.C. § 1983 
    and 28 C.F.R. § 0.85 in their analysis.
    """
    
    # Simulate OCR errors
    corrupted_text = ocr_text.replace('171', 'l7l').replace('486', '4B6').replace('493', '493')
    corrupted_text = corrupted_text.replace('256', '2S6').replace('321', '32l')
    corrupted_text = corrupted_text.replace('42', '4Z').replace('1983', 'l983')
    corrupted_text = corrupted_text.replace('28', '2B').replace('0.85', '0.B5')
    
    print("Original text:")
    print(ocr_text)
    print("\nCorrupted text (simulated OCR errors):")
    print(corrupted_text)
    
    # Process with OCR correction
    result = processor.process_text(corrupted_text, extract_case_names=False, verify_citations=False)
    
    print(f"\nCitations found after OCR correction: {len(result['results'])}")
    for citation in result['results']:
        print(f"  - {citation['citation']}")
    
    return result

def test_statute_filtering():
    """Test statute filtering functionality."""
    print("\n" + "="*80)
    print("=== Testing Statute Filtering ===\n")
    
    processor = UnifiedCitationProcessor()
    processor.enable_statute_filtering(True, include_statutes=False)  # Exclude statutes
    
    statute_text = """
    The plaintiff argued that under 42 U.S.C. § 1983, they had a valid claim. 
    Additionally, the regulations at 28 C.F.R. § 0.85 supported their position.
    The defendant cited RCW 9A.08.010 in support of their motion, and argued 
    that WAC 296-800-100 was applicable to the facts of this case.
    
    The court in State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321 (2011) held that 
    the defendant's rights were violated.
    """
    
    print("Test text with statutes and cases:")
    print(statute_text)
    
    # Test excluding statutes
    result_exclude = processor.process_text(statute_text, extract_case_names=False, verify_citations=False)
    print(f"\nResults with statutes excluded: {len(result_exclude['results'])} citations")
    for citation in result_exclude['results']:
        print(f"  - {citation['citation']} (statute: {citation.get('is_statute', False)})")
    
    # Test including statutes
    processor.enable_statute_filtering(True, include_statutes=True)
    result_include = processor.process_text(statute_text, extract_case_names=False, verify_citations=False)
    print(f"\nResults with statutes included: {len(result_include['results'])} citations")
    for citation in result_include['results']:
        print(f"  - {citation['citation']} (statute: {citation.get('is_statute', False)})")
        if citation.get('is_statute'):
            statute_info = citation.get('statute_info', {})
            print(f"    Type: {statute_info.get('type', 'N/A')}")
    
    return result_exclude, result_include

def test_confidence_scoring():
    """Test confidence scoring functionality."""
    print("\n" + "="*80)
    print("=== Testing Confidence Scoring ===\n")
    
    processor = UnifiedCitationProcessor()
    processor.enable_confidence_scoring(True)
    processor.set_debug_mode(True, verbose=True)
    
    confidence_text = """
    The court in State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321 (2011) held that 
    the defendant's rights were violated. This was consistent with the holding in 
    State v. Johnson, 199 Wn. App. 280, 285, 399 P.3d 1195 (2017).
    
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
    the Supreme Court established important precedent.
    """
    
    print("Test text for confidence scoring:")
    print(confidence_text)
    
    result = processor.process_text(confidence_text, extract_case_names=True, verify_citations=True)
    
    print(f"\nResults with confidence scores:")
    for citation in result['results']:
        print(f"\nCitation: {citation['citation']}")
        print(f"  Confidence: {citation.get('confidence', 'N/A')}")
        print(f"  Verified: {citation['verified']}")
        print(f"  Source: {citation.get('source', 'N/A')}")
        print(f"  Method: {citation.get('method', 'N/A')}")
        print(f"  Pattern: {citation.get('pattern', 'N/A')}")
    
    return result

def test_semantic_clustering():
    """Test semantic clustering for parallel citations."""
    print("\n" + "="*80)
    print("=== Testing Semantic Clustering ===\n")
    
    processor = UnifiedCitationProcessor()
    processor.set_debug_mode(True, verbose=True)
    
    # Text with parallel citations that refer to the same case
    parallel_text = """
    The court in State v. Smith, 171 Wn.2d 486, 493, 256 P.3d 321 (2011) held that 
    the defendant's rights were violated. Later in the opinion, the court 
    referenced the same case as 171 Wn.2d 486, 256 P.3d 321, and also as 
    256 P.3d 321, 171 Wn.2d 486.
    
    The plaintiff also cited State v. Johnson, 199 Wn. App. 280, 399 P.3d 1195 (2017),
    and later referenced it as 399 P.3d 1195, 199 Wn. App. 280.
    """
    
    print("Test text with parallel citations:")
    print(parallel_text)
    
    result = processor.process_text(parallel_text, extract_case_names=False, verify_citations=False)
    
    print(f"\nResults with semantic clustering:")
    for citation in result['results']:
        print(f"\nCitation: {citation['citation']}")
        print(f"  Is cluster: {citation['is_cluster']}")
        print(f"  Method: {citation.get('method', 'N/A')}")
        print(f"  Pattern: {citation.get('pattern', 'N/A')}")
        if citation.get('is_cluster'):
            print(f"  Cluster members: {citation.get('cluster_members', [])}")
            print(f"  Cluster type: {citation.get('metadata', {}).get('cluster_type', 'N/A')}")
    
    return result

def main():
    """Run all tests."""
    try:
        # Test all advanced features together
        test_advanced_features()
        
        # Test individual features
        test_ocr_correction()
        test_statute_filtering()
        test_confidence_scoring()
        test_semantic_clustering()
        
        print("\n" + "="*80)
        print("=== All Tests Completed Successfully ===")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 