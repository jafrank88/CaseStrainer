#!/usr/bin/env python3
"""
Simple script to test a specific citation and identify where verification fails.
Usage: python test_specific_citation.py "your citation here"
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging to show DEBUG level logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_citation(citation):
    """Test a specific citation step by step."""
    print(f"Testing citation: {citation}")
    print("=" * 50)
    
    try:
        from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        from enhanced_case_name_extractor import EnhancedCaseNameExtractor
        
        # Initialize
        verifier = EnhancedMultiSourceVerifier()
        extractor = EnhancedCaseNameExtractor(cache_results=False)
        
        # Step 1: Test citation cleaning
        print("\n1. Citation Cleaning:")
        cleaned = verifier._clean_citation_for_lookup(citation)
        print(f"   Original: {citation}")
        print(f"   Cleaned:  {cleaned}")
        
        # Step 2: Test component extraction
        print("\n2. Component Extraction:")
        components = verifier._extract_citation_components(citation)
        print(f"   Components: {json.dumps(components, indent=2)}")
        
        # Step 3: Test CourtListener lookup
        print("\n3. CourtListener Lookup:")
        lookup_result = verifier._lookup_citation(citation)
        if lookup_result:
            print(f"   Success: {lookup_result.get('verified', False)}")
            if lookup_result.get('error'):
                print(f"   Error: {lookup_result['error']}")
            if lookup_result.get('case_name'):
                print(f"   Case Name: {lookup_result['case_name']}")
            if lookup_result.get('url'):
                print(f"   URL: {lookup_result['url']}")
        else:
            print("   Failed: No result returned")
        
        # Step 4: Test full verification
        print("\n4. Full Verification:")
        full_result = verifier.verify_citation(citation)
        print(f"   Success: {full_result.get('verified', False)}")
        if full_result.get('error'):
            print(f"   Error: {full_result['error']}")
        if full_result.get('case_name'):
            print(f"   Case Name: {full_result['case_name']}")
        if full_result.get('url'):
            print(f"   URL: {full_result['url']}")
        
        # Step 5: Test URL generation
        print("\n5. URL Generation:")
        url = extractor.get_citation_url(citation)
        print(f"   Generated URL: {url}")
        
        # Step 6: Test canonical name
        print("\n6. Canonical Name:")
        canonical_result = extractor.get_canonical_case_name(citation)
        if canonical_result:
            print(f"   Canonical Name: {canonical_result.get('case_name')}")
            print(f"   Canonical Date: {canonical_result.get('date')}")
        else:
            print(f"   Canonical Name: None")
            print(f"   Canonical Date: None")
        
        return {
            'cleaned': cleaned,
            'components': components,
            'lookup_result': lookup_result,
            'full_result': full_result,
            'url': url,
            'canonical_name': canonical_result.get('case_name') if canonical_result else None,
            'canonical_date': canonical_result.get('date') if canonical_result else None
        }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_specific_citation.py \"your citation here\"")
        print("Example: python test_specific_citation.py \"Brown v. Board of Education, 347 U.S. 483 (1954)\"")
        return
    
    citation = sys.argv[1]
    results = test_citation(citation)
    
    if results:
        # Save results to file
        output_file = f"test_results_{citation.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main() 