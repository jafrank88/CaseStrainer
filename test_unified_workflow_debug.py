#!/usr/bin/env python3
"""
Debug script to test the unified workflow directly.
"""

import sys
import os
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import json

def test_unified_workflow():
    """Test the unified workflow directly."""
    
    print("=== Testing Unified Workflow Directly ===")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test cases
    test_cases = [
        {
            "name": "Citation with context",
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that racial segregation in public schools was unconstitutional.",
            "citation": "347 U.S. 483"
        },
        {
            "name": "Citation without context",
            "text": "The case 347 U.S. 483 is important.",
            "citation": "347 U.S. 483"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        try:
            # Test the unified workflow directly
            result = verifier.verify_citation_unified_workflow(
                test_case['citation'],
                extracted_case_name=None,
                full_text=test_case['text']
            )
            
            print(f"\nUnified Workflow Result:")
            print(f"  Verified: {result.get('verified', False)}")
            print(f"  Citation: {result.get('citation', 'N/A')}")
            print(f"  Case Name: {result.get('case_name', 'N/A')}")
            print(f"  Extracted Case Name: {result.get('extracted_case_name', 'N/A')}")
            print(f"  Canonical Name: {result.get('canonical_name', 'N/A')}")
            print(f"  Hinted Case Name: {result.get('hinted_case_name', 'N/A')}")
            print(f"  Canonical Date: {result.get('canonical_date', 'N/A')}")
            print(f"  Extracted Date: {result.get('extracted_date', 'N/A')}")
            print(f"  Court: {result.get('court', 'N/A')}")
            print(f"  Docket Number: {result.get('docket_number', 'N/A')}")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Source: {result.get('source', 'N/A')}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            print(f"  Error: {result.get('error', 'N/A')}")
            
            # Check if we have both names
            extracted = result.get('extracted_case_name')
            canonical = result.get('canonical_name')
            
            if extracted and canonical:
                print(f"  ✅ SUCCESS: Both extracted ('{extracted}') and canonical ('{canonical}') names found!")
            elif extracted:
                print(f"  ⚠️  PARTIAL: Only extracted name found ('{extracted}')")
            elif canonical:
                print(f"  ⚠️  PARTIAL: Only canonical name found ('{canonical}')")
            else:
                print(f"  ❌ MISSING: No case names found")
            
            # Show full result for debugging
            print(f"\nFull Result JSON:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_unified_workflow() 