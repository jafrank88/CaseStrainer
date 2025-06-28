#!/usr/bin/env python3
"""
Test script to debug frontend verification issue.
This tests the exact same code path that the frontend uses.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_frontend_verification():
    """Test the exact same verification path that the frontend uses."""
    
    print("=== TESTING FRONTEND VERIFICATION PATH ===")
    
    # Test text that should trigger immediate processing
    test_text = "199 Wn. App. 280, 399 P.3d 1195"
    
    print(f"Test text: {test_text}")
    print(f"Text length: {len(test_text)}")
    print(f"Contains numbers: {any(char.isdigit() for char in test_text)}")
    print(f"Contains citation patterns: {any(word in test_text.upper() for word in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'L.ED.2D', 'L.ED.3D', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL'])}")
    print(f"Word count: {len(test_text.split())}")
    
    # Check if it should use immediate processing
    text_trimmed = test_text.strip()
    should_use_immediate = (
        len(text_trimmed) < 50 and
        any(char.isdigit() for char in text_trimmed) and
        any(word in text_trimmed.upper() for word in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'L.ED.2D', 'L.ED.3D', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL']) and
        len(text_trimmed.split()) <= 10
    )
    
    print(f"Should use immediate processing: {should_use_immediate}")
    
    if should_use_immediate:
        print("\n=== TESTING IMMEDIATE PROCESSING ===")
        
        try:
            # Import the enhanced validator and complex citation integration
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            from src.complex_citation_integration import ComplexCitationIntegrator, format_complex_citation_for_frontend
            
            print("✓ Successfully imported modules")
            
            verifier = EnhancedMultiSourceVerifier()
            print("✓ Successfully created verifier instance")
            
            # Test if the method exists
            if hasattr(verifier, 'verify_citation_unified_workflow'):
                print("✓ verify_citation_unified_workflow method exists")
            else:
                print("✗ verify_citation_unified_workflow method NOT found")
                print(f"Available methods: {[m for m in dir(verifier) if not m.startswith('_')]}")
                return
            
            # Use complex citation processing for better handling of complex citations
            print("Calling process_text_with_complex_citations...")
            integrator = ComplexCitationIntegrator()
            results = integrator.process_text_with_complex_citations_original(test_text)
            print(f"✓ Got {len(results)} results")
            
            # Format results for frontend
            formatted_citations = []
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Citation: {result.get('citation', 'N/A')}")
                print(f"Verified: {result.get('verified', 'N/A')}")
                print(f"Valid: {result.get('valid', 'N/A')}")
                print(f"Source: {result.get('source', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                print(f"Court: {result.get('court', 'N/A')}")
                print(f"Docket: {result.get('docket_number', 'N/A')}")
                print(f"Case name: {result.get('case_name', 'N/A')}")
                print(f"Canonical name: {result.get('canonical_name', 'N/A')}")
                
                formatted_result = format_complex_citation_for_frontend(result)
                formatted_citations.append({
                    'citation': result.get('citation', test_text),
                    'valid': result.get('verified', False),
                    'verified': result.get('verified', False),
                    'case_name': result.get('case_name', ''),
                    'extracted_case_name': result.get('extracted_case_name', ''),
                    'canonical_name': result.get('canonical_name', ''),
                    'hinted_case_name': result.get('hinted_case_name', ''),
                    'canonical_date': result.get('canonical_date', ''),
                    'extracted_date': result.get('extracted_date', ''),
                    'court': result.get('court', ''),
                    'docket_number': result.get('docket_number', ''),
                    'confidence': result.get('confidence', 0.0),
                    'source': result.get('source', 'Unknown'),
                    'url': result.get('url', ''),
                    'details': result.get('details', {}),
                    'is_complex_citation': result.get('is_complex_citation', False),
                    'is_parallel_citation': result.get('is_parallel_citation', False),
                    'complex_metadata': result.get('complex_metadata', {}),
                })
            
            print(f"\n=== FINAL FORMATTED RESULTS ===")
            for i, formatted in enumerate(formatted_citations):
                print(f"\n--- Formatted Result {i+1} ---")
                print(f"Citation: {formatted['citation']}")
                print(f"Verified: {formatted['verified']}")
                print(f"Valid: {formatted['valid']}")
                print(f"Source: {formatted['source']}")
                print(f"URL: {formatted['url']}")
                print(f"Court: {formatted['court']}")
                print(f"Docket: {formatted['docket_number']}")
                print(f"Case name: {formatted['case_name']}")
                print(f"Canonical name: {formatted['canonical_name']}")
                
        except Exception as e:
            print(f"✗ Error during immediate processing: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("\n=== WOULD USE ASYNC PROCESSING ===")
        print("This text would be processed asynchronously in the frontend")

if __name__ == "__main__":
    test_frontend_verification() 