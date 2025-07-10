#!/usr/bin/env python3
"""
Test script for the new unified citation processor verification workflow.
This tests the functions that were moved from EnhancedMultiSourceVerifier.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_unified_verification_workflow():
    """Test the unified verification workflow."""
    print("Testing UnifiedCitationProcessor verification workflow...")
    
    # Initialize the processor
    processor = UnifiedCitationProcessor()
    
    # Test citations
    test_citations = [
        "410 U.S. 113",  # Roe v. Wade (landmark case)
        "347 U.S. 483",  # Brown v. Board of Education (landmark case)
        "5 U.S. 137",    # Marbury v. Madison (landmark case)
        "142 Wn.2d 801", # Washington Supreme Court case
        "175 Wn. App. 1", # Washington Court of Appeals case
        "16 P.3d 583",   # Pacific Reporter case
        "123 F.3d 456",  # Federal Reporter case
        "Invalid Citation", # Should fail
    ]
    
    print(f"\nTesting {len(test_citations)} citations...")
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n{i}. Testing citation: {citation}")
        
        try:
            # Test the unified workflow
            result = processor.verify_citation_unified_workflow(citation)
            
            print(f"   Verified: {result.get('verified', False)}")
            if result.get('verified'):
                print(f"   Verified by: {result.get('verified_by', 'Unknown')}")
                if result.get('case_name'):
                    print(f"   Case name: {result['case_name']}")
                if result.get('court'):
                    print(f"   Court: {result['court']}")
                if result.get('year'):
                    print(f"   Year: {result['year']}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Show which sources were checked
            sources = result.get('sources', {})
            if sources:
                print(f"   Sources checked: {list(sources.keys())}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*50)
    print("Testing batch verification...")
    
    # Test batch verification
    batch_citations = ["410 U.S. 113", "347 U.S. 483", "142 Wn.2d 801"]
    batch_results = processor.batch_verify_citations(batch_citations)
    
    for i, (citation, result) in enumerate(zip(batch_citations, batch_results), 1):
        print(f"{i}. {citation}: {'✓' if result.get('verified') else '✗'}")

def test_citation_normalization():
    """Test citation normalization functions."""
    print("\n" + "="*50)
    print("Testing citation normalization...")
    
    processor = UnifiedCitationProcessor()
    
    test_cases = [
        ("410 U.S. 113", "410 U.S. 113"),
        ("142 Wash. 2d 801", "142 Wn. 2d 801"),
        ("175 Wash. App. 1", "175 Wn. App. 1"),
        ("16 P.2d 583", "16 P.2d 583"),
        ("123 F.3d 456", "123 F.2d 456"),  # Should normalize to F.2d
    ]
    
    for original, expected in test_cases:
        normalized = processor._normalize_citation(original)
        status = "✓" if normalized == expected else "✗"
        print(f"{status} '{original}' -> '{normalized}' (expected: '{expected}')")

def test_citation_components():
    """Test citation component extraction."""
    print("\n" + "="*50)
    print("Testing citation component extraction...")
    
    processor = UnifiedCitationProcessor()
    
    test_cases = [
        "410 U.S. 113",
        "142 Wn.2d 801 (2002)",
        "175 Wn. App. 1",
        "16 P.3d 583",
    ]
    
    for citation in test_cases:
        components = processor._extract_citation_components(citation)
        print(f"\nCitation: {citation}")
        for key, value in components.items():
            if value:
                print(f"  {key}: {value}")

def test_cache_functions():
    """Test cache functionality."""
    print("\n" + "="*50)
    print("Testing cache functionality...")
    
    processor = UnifiedCitationProcessor()
    
    test_citation = "410 U.S. 113"
    
    # Test cache save
    test_result = {
        "verified": True,
        "verified_by": "Landmark Cases",
        "case_name": "Roe v. Wade",
        "test_data": "cache_test"
    }
    
    processor._save_to_cache(test_citation, test_result)
    print(f"✓ Saved test result to cache for '{test_citation}'")
    
    # Test cache retrieval
    cached_result = processor._check_cache(test_citation)
    if cached_result and cached_result.get("test_data") == "cache_test":
        print(f"✓ Retrieved cached result for '{test_citation}'")
    else:
        print(f"✗ Failed to retrieve cached result for '{test_citation}'")

if __name__ == "__main__":
    print("Unified Citation Processor Verification Test")
    print("=" * 50)
    
    try:
        test_unified_verification_workflow()
        test_citation_normalization()
        test_citation_components()
        test_cache_functions()
        
        print("\n" + "="*50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc() 