#!/usr/bin/env python3
"""
Test script to check web search extraction functionality.
UPDATED: Now uses the unified workflow instead of deprecated web search methods.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_workflow_extraction():
    """Test the unified workflow with case name extraction."""
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test citations with context
        test_cases = [
            {
                "citation": "347 U.S. 483",
                "context": "In Brown v. Board of Education, the Supreme Court held that separate educational facilities are inherently unequal.",
                "expected_case": "Brown v. Board of Education"
            },
            {
                "citation": "410 U.S. 113",
                "context": "Roe v. Wade established the constitutional right to abortion.",
                "expected_case": "Roe v. Wade"
            },
            {
                "citation": "384 U.S. 436",
                "context": "Miranda v. Arizona established the requirement for police to inform suspects of their rights.",
                "expected_case": "Miranda v. Arizona"
            }
        ]
        
        print(f"Testing unified workflow with case name extraction...")
        print("=" * 60)
        
        for test_case in test_cases:
            citation = test_case["citation"]
            context = test_case["context"]
            expected_case = test_case["expected_case"]
            
            print(f"\nTesting: {citation}")
            print(f"Context: {context}")
            print(f"Expected: {expected_case}")
            print("-" * 40)
            
            try:
                # Use the unified workflow with context for case name extraction
                result = verifier.verify_citation_unified_workflow(
                    citation=citation,
                    full_text=context
                )
                
                print(f"Verified: {result.get('verified', False)}")
                print(f"Source: {result.get('source', 'Unknown')}")
                print(f"Extracted Case Name: {result.get('extracted_case_name', 'N/A')}")
                print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                
                # Check if case name extraction worked
                extracted_name = result.get('extracted_case_name')
                if extracted_name and expected_case.lower() in extracted_name.lower():
                    print("✅ Case name extraction successful!")
                else:
                    print("⚠️ Case name extraction may need improvement")
                
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
                    
            except Exception as e:
                print(f"Error testing {citation}: {e}")
        
        print("\n" + "=" * 60)
        print("Unified workflow extraction test completed!")
        
    except Exception as e:
        print(f"Error initializing verifier: {e}")

if __name__ == "__main__":
    test_unified_workflow_extraction() 