#!/usr/bin/env python3
"""
Test script to verify the citation matching fix.
"""

# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
from src.document_processing import extract_and_verify_citations

def test_citation_matching():
    """Test citation matching with the fix."""
    print("Testing citation matching fix...")
    
    # Test with a simple citation that should be verified
    test_text = "See State v. Richardson, 177 Wn.2d 351, 302 P.3d 156 (2013)."
    
    print(f"Test text: {test_text}")
    print("-" * 50)
    
    # Test the full processing pipeline
    try:
        processed_results, metadata = extract_and_verify_citations(test_text)
        print(f"Processing results: {len(processed_results)} citations")
        
        for i, result in enumerate(processed_results, 1):
            print(f"\nCitation {i}:")
            print(f"  Citation: '{result.get('citation')}'")
            print(f"  Verified: {result.get('verified')}")
            print(f"  Canonical name: {result.get('canonical_name')}")
            print(f"  Canonical date: {result.get('canonical_date')}")
            print(f"  URL: {result.get('url')}")
            print(f"  Source: {result.get('source')}")
            
            # Check if this citation should be verified
            citation_text = result.get('citation', '')
            if '302 P.3d 156' in citation_text or '177 Wn.2d 351' in citation_text:
                if result.get('verified') == 'true':
                    print(f"  ✅ SUCCESS: Citation verified correctly!")
                else:
                    print(f"  ❌ FAILURE: Citation should be verified but isn't")
            else:
                print(f"  ℹ️  INFO: This is not the main citation we're testing")
        
        # Summary
        verified_count = sum(1 for r in processed_results if r.get('verified') == 'true')
        total_count = len(processed_results)
        print(f"\nSummary:")
        print(f"  Total citations: {total_count}")
        print(f"  Verified citations: {verified_count}")
        print(f"  Verification rate: {verified_count/total_count*100:.1f}%" if total_count > 0 else "N/A")
        
        return processed_results
        
    except Exception as e:
        print(f"Error in processing: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_citation_matching() 