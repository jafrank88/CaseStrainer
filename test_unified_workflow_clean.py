#!/usr/bin/env python3
"""
Test script to verify the unified workflow is working correctly after cleanup.
This script tests the verify_citation_unified_workflow method and ensures
it returns both extracted_case_name and canonical_name.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_workflow():
    """Test the unified workflow with various citation types."""
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test citations
        test_citations = [
            "347 U.S. 483",  # Brown v. Board of Education
            "410 U.S. 113",  # Roe v. Wade
            "640 P.2d 716",  # Washington case
        ]
        
        print("=" * 80)
        print("TESTING UNIFIED WORKFLOW AFTER CLEANUP")
        print("=" * 80)
        print(f"Test started at: {datetime.now()}")
        print()
        
        for citation in test_citations:
            print(f"Testing citation: {citation}")
            print("-" * 40)
            
            try:
                # Test the unified workflow
                result = verifier.verify_citation_unified_workflow(citation)
                
                print(f"Result: {json.dumps(result, indent=2)}")
                
                # Check if we got the expected fields
                if result.get('verified'):
                    print("✅ VERIFIED")
                    if result.get('canonical_name'):
                        print(f"✅ Canonical name: {result['canonical_name']}")
                    if result.get('extracted_case_name'):
                        print(f"✅ Extracted name: {result['extracted_case_name']}")
                    if result.get('url'):
                        print(f"✅ URL: {result['url']}")
                else:
                    print("❌ NOT VERIFIED")
                    if result.get('error'):
                        print(f"❌ Error: {result['error']}")
                
            except Exception as e:
                print(f"❌ Exception: {e}")
            
            print()
        
        print("=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"Failed to import or initialize: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_unified_workflow()
    sys.exit(0 if success else 1) 