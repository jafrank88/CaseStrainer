#!/usr/bin/env python3
"""
Simple test to directly test the unified workflow.
"""

import sys
import os
sys.path.append('src')

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import time

def test_unified_workflow():
    """Test the unified workflow directly."""
    
    print("=== Testing Unified Workflow Directly ===")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid U.S. citation",
            "citation": "347 U.S. 483",
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court held that separate educational facilities are inherently unequal."
        },
        {
            "name": "Invalid citation (should fail fast)",
            "citation": "410 F.2d 123",
            "text": "The case 410 F.2d 123 is important."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Citation: {test_case['citation']}")
        print(f"Text: {test_case['text']}")
        
        start_time = time.time()
        
        try:
            # Test the unified workflow
            result = verifier.verify_citation_unified_workflow(
                test_case['citation'],
                full_text=test_case['text']
            )
            
            processing_time = time.time() - start_time
            print(f"Processing time: {processing_time:.2f}s")
            
            print(f"Verified: {result.get('verified', False)}")
            print(f"Case Name: {result.get('case_name', 'None')}")
            print(f"Extracted Case Name: {result.get('extracted_case_name', 'None')}")
            print(f"Canonical Name: {result.get('canonical_name', 'None')}")
            print(f"Error: {result.get('error', 'None')}")
            
            if processing_time > 5:
                print("⚠ WARNING: Processing took too long!")
            else:
                print("✅ Processing time is acceptable")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_unified_workflow() 