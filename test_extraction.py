#!/usr/bin/env python3
"""
Test script to verify extracted name, extracted date, and hinted extraction functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_extraction_workflow():
    """Test the extraction workflow with a known citation."""
    print("Testing extraction workflow...")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test with the user-provided citation and extracted/hinted names
    citation = "199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    extracted_name = "John Doe P v. Thurston County"
    hinted_name = "Thurston County"
    
    print(f"Citation: {citation}")
    print(f"Extracted name: {extracted_name}")
    print(f"Hinted name: {hinted_name}")
    print("-" * 50)
    
    # Run the verification workflow
    result = verifier.verify_citation_unified_workflow(
        citation, 
        extracted_case_name=extracted_name, 
        hinted_case_name=hinted_name
    )
    
    # Display results
    print("RESULTS:")
    print(f"Verified: {result.get('verified')}")
    print(f"Extracted case name: {result.get('extracted_case_name')}")
    print(f"Hinted case name: {result.get('hinted_case_name')}")
    print(f"Final case name: {result.get('case_name')}")
    print(f"Canonical name: {result.get('canonical_name')}")
    print(f"Canonical date: {result.get('canonical_date')}")
    print(f"URL: {result.get('url')}")
    print(f"Source: {result.get('source')}")
    print(f"Verification method: {result.get('verification_method')}")
    
    # Check if extraction is working
    print("\nEXTRACTION STATUS:")
    if result.get('extracted_case_name') == extracted_name:
        print("✅ Extracted name is preserved")
    else:
        print("❌ Extracted name is missing or incorrect")
        
    if result.get('hinted_case_name') == hinted_name:
        print("✅ Hinted name is preserved")
    else:
        print("❌ Hinted name is missing or incorrect")
        
    if result.get('canonical_date'):
        print("✅ Canonical date is extracted")
    else:
        print("❌ Canonical date is missing")
        
    if result.get('case_name') and result.get('case_name') != "Unknown Case":
        print("✅ Final case name is properly set")
    else:
        print("❌ Final case name is missing or incorrect")

if __name__ == "__main__":
    test_extraction_workflow() 