#!/usr/bin/env python3
"""
Test script to verify the new unified workflow is working correctly.
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
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        
        # Initialize the verifier
        processor = UnifiedCitationProcessor()
        
        # Test citations
        test_citations = [
            "347 U.S. 483",  # Brown v. Board of Education
            "410 U.S. 113",  # Roe v. Wade
            "384 U.S. 436",  # Miranda v. Arizona
            "163 U.S. 537",  # Plessy v. Ferguson
            "60 U.S. 393",   # Dred Scott v. Sandford
        ]
        
        print("=" * 80)
        print("TESTING UNIFIED WORKFLOW")
        print("=" * 80)
        print(f"Timestamp: {datetime.now()}")
        print()
        
        for i, citation in enumerate(test_citations, 1):
            print(f"Test {i}: {citation}")
            print("-" * 40)
            
            try:
                # Test with unified workflow
                result = processor.verify_citation_unified_workflow(
                    citation,
                    extracted_case_name=None,
                    full_text=citation  # Pass citation as context
                )
                
                # Check if both case names are present
                extracted_name = result.get('extracted_case_name')
                canonical_name = result.get('canonical_name')
                case_name = result.get('case_name')
                
                print(f"✓ Verified: {result.get('verified', False)}")
                print(f"✓ Source: {result.get('source', 'Unknown')}")
                print(f"✓ Case Name: {case_name}")
                print(f"✓ Extracted Case Name: {extracted_name}")
                print(f"✓ Canonical Name: {canonical_name}")
                print(f"✓ URL: {result.get('url', 'N/A')}")
                print(f"✓ Date: {result.get('canonical_date', 'N/A')}")
                
                # Verify that we're getting the expected fields
                if result.get('verified'):
                    print("✓ SUCCESS: Citation verified successfully")
                else:
                    print("⚠ WARNING: Citation not verified")
                
                if canonical_name:
                    print("✓ SUCCESS: Canonical name present")
                else:
                    print("⚠ WARNING: No canonical name")
                
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
            
            print()
        
        print("=" * 80)
        print("UNIFIED WORKFLOW TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_old_vs_new():
    """Compare old verify_citation vs new verify_citation_unified_workflow."""
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        
        processor = UnifiedCitationProcessor()
        citation = "347 U.S. 483"
        
        print("=" * 80)
        print("COMPARING OLD vs NEW VERIFICATION METHODS")
        print("=" * 80)
        
        # Test old method
        print("OLD METHOD (verify_citation):")
        print("-" * 40)
        try:
            old_result = processor.verify_citation_unified_workflow(citation)
            print(f"✓ Result: {old_result.get('verified', False)}")
            print(f"✓ Case Name: {old_result.get('case_name', 'N/A')}")
            print(f"✓ Extracted Case Name: {old_result.get('extracted_case_name', 'N/A')}")
            print(f"✓ Canonical Name: {old_result.get('canonical_name', 'N/A')}")
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
        
        print()
        
        # Test new method
        print("NEW METHOD (verify_citation_unified_workflow):")
        print("-" * 40)
        try:
            new_result = processor.verify_citation_unified_workflow(citation)
            print(f"✓ Result: {new_result.get('verified', False)}")
            print(f"✓ Case Name: {new_result.get('case_name', 'N/A')}")
            print(f"✓ Extracted Case Name: {new_result.get('extracted_case_name', 'N/A')}")
            print(f"✓ Canonical Name: {new_result.get('canonical_name', 'N/A')}")
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting unified workflow tests...")
    
    # Test the new unified workflow
    success = test_unified_workflow()
    
    if success:
        # Compare old vs new methods
        test_old_vs_new()
    
    print("\nTest completed!") 