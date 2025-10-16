#!/usr/bin/env python3
"""
Simple Context Check
===================

Simple test to check if citations appear in their context.
"""

import sys
import os
sys.path.append('src')

def check_citation_in_context():
    """Simple check if citations appear in context"""
    
    print("Citation Context Check")
    print("=" * 30)
    
    test_cases = [
        {
            "citation": "107 P.3d 90",
            "context": "Branson v. Washington Fine Wine & Spirits, 107 P.3d 90 (2005)"
        },
        {
            "citation": "118 Wash.2d 46", 
            "context": "Wilmot v. Kaiser, 118 Wash.2d 46, 821 P.2d 18 (1991)"
        },
        {
            "citation": "495 P.3d 808",
            "context": "Something Inc. v. Federal Communications Commission, 495 P.3d 808 (2021)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Citation: '{test['citation']}'")
        print(f"Context: '{test['context']}'")
        
        # Check if citation is in context
        pos = test['context'].find(test['citation'])
        print(f"Citation found: {'YES' if pos != -1 else 'NO'}")
        if pos != -1:
            print(f"Position: {pos}")
            
            # Show what context extraction would produce
            context_start = max(0, pos - 150)
            context_end = min(len(test['context']), pos + len(test['citation']) + 50)
            extracted_context = test['context'][context_start:context_end]
            print(f"Extracted context: '{extracted_context}'")
            print(f"Citation in extracted: {'YES' if test['citation'] in extracted_context else 'NO'}")

def test_basic_extraction():
    """Test basic extraction without complex logging"""
    
    print("\n\nBasic Extraction Test")
    print("=" * 25)
    
    # Simple test case
    citation = "107 P.3d 90"
    context = "Branson v. Washington Fine Wine & Spirits, 107 P.3d 90 (2005)"
    
    print(f"Citation: {citation}")
    print(f"Context: {context}")
    
    pos = context.find(citation)
    print(f"Position: {pos}")
    
    if pos != -1:
        try:
            # Import without triggering complex logging
            import importlib
            import sys
            
            # Temporarily disable logging to avoid encoding issues
            import logging
            logging.disable(logging.CRITICAL)
            
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            result = extract_case_name_and_date_master(
                text=context,
                citation=citation,
                citation_start=pos,
                citation_end=pos + len(citation),
                debug=False
            )
            
            # Re-enable logging
            logging.disable(logging.NOTSET)
            
            print(f"Result: {result.get('case_name', 'N/A')}")
            print(f"Method: {result.get('method', 'unknown')}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_citation_in_context()
    test_basic_extraction()
