#!/usr/bin/env python3
"""
Debug script to identify why canonical cases/URLs are not being found.
This script will help you test citation verification step by step.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from enhanced_case_name_extractor import EnhancedCaseNameExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_citation_verification(citation: str):
    """Test citation verification step by step."""
    print(f"\n{'='*60}")
    print(f"TESTING CITATION: {citation}")
    print(f"{'='*60}")
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    extractor = EnhancedCaseNameExtractor()
    
    print(f"\n1. CITATION CLEANING:")
    print(f"   Original: {citation}")
    
    # Test citation cleaning
    cleaned = verifier._clean_citation_for_lookup(citation)
    print(f"   Cleaned: {cleaned}")
    
    # Test citation components extraction
    components = verifier._extract_citation_components(citation)
    print(f"   Components: {json.dumps(components, indent=2)}")
    
    print(f"\n2. COURT LISTENER LOOKUP:")
    print(f"   Testing citation lookup...")
    
    # Test CourtListener lookup
    lookup_result = verifier._lookup_citation(citation)
    if lookup_result:
        print(f"   Lookup Result: {json.dumps(lookup_result, indent=2)}")
    else:
        print(f"   Lookup Result: None")
    
    print(f"\n3. COURT LISTENER SEARCH:")
    print(f"   Testing exact search...")
    
    # Test exact search
    exact_result = verifier._search_courtlistener_exact(citation)
    print(f"   Exact Search Result: {json.dumps(exact_result, indent=2)}")
    
    print(f"\n4. FLEXIBLE SEARCH:")
    print(f"   Testing flexible search...")
    
    # Test flexible search
    flexible_result = verifier._search_courtlistener_flexible(citation)
    print(f"   Flexible Search Result: {json.dumps(flexible_result, indent=2)}")
    
    print(f"\n5. FULL VERIFICATION:")
    print(f"   Testing full verification...")
    
    # Test full verification
    full_result = verifier.verify_citation(citation)
    print(f"   Full Verification Result: {json.dumps(full_result, indent=2)}")
    
    print(f"\n6. URL GENERATION:")
    print(f"   Testing URL generation...")
    
    # Test URL generation
    url = extractor.get_citation_url(citation)
    print(f"   Generated URL: {url}")
    
    print(f"\n7. CANONICAL CASE NAME:")
    print(f"   Testing canonical case name extraction...")
    
    # Test canonical case name extraction
    canonical_name = extractor.get_canonical_case_name(citation)
    print(f"   Canonical Case Name: {canonical_name}")
    
    return {
        'lookup_result': lookup_result,
        'exact_result': exact_result,
        'flexible_result': flexible_result,
        'full_result': full_result,
        'url': url,
        'canonical_name': canonical_name
    }

def analyze_results(results: dict):
    """Analyze the results to identify issues."""
    print(f"\n{'='*60}")
    print(f"ANALYSIS")
    print(f"{'='*60}")
    
    issues = []
    
    # Check if lookup failed
    if not results['lookup_result'] or not results['lookup_result'].get('verified'):
        issues.append("CourtListener lookup failed")
    
    # Check if exact search failed
    if not results['exact_result'] or not results['exact_result'].get('verified'):
        issues.append("CourtListener exact search failed")
    
    # Check if flexible search failed
    if not results['flexible_result'] or not results['flexible_result'].get('verified'):
        issues.append("CourtListener flexible search failed")
    
    # Check if full verification failed
    if not results['full_result'] or not results['full_result'].get('verified'):
        issues.append("Full verification failed")
    
    # Check if URL generation failed
    if not results['url']:
        issues.append("URL generation failed")
    
    # Check if canonical name extraction failed
    if not results['canonical_name']:
        issues.append("Canonical case name extraction failed")
    
    if issues:
        print(f"ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print(f"All tests passed successfully!")
    
    # Check for specific error messages
    print(f"\nERROR MESSAGES:")
    for test_name, result in results.items():
        if result and isinstance(result, dict) and result.get('error'):
            print(f"  {test_name}: {result['error']}")

def main():
    """Main function to run the debug script."""
    if len(sys.argv) < 2:
        print("Usage: python debug_citation_verification.py <citation>")
        print("Example: python debug_citation_verification.py 'Brown v. Board of Education, 347 U.S. 483 (1954)'")
        return
    
    citation = sys.argv[1]
    
    try:
        results = test_citation_verification(citation)
        analyze_results(results)
        
        # Save results to file for further analysis
        output_file = f"debug_results_{citation.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 