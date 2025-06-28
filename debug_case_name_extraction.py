#!/usr/bin/env python3
"""
Debug script to test case name extraction for "Valid but Not Verified" citations
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.citation_processor import CitationProcessor

def test_case_name_extraction():
    """Test case name extraction for problematic citations"""
    
    # Test text that might be causing issues
    test_texts = [
        # Test 1: Simple case with citation
        "In Terhune v. A. H. Robins Co., 90 Wn.2d 9, the court held that...",
        
        # Test 2: Multiple citations for the same case (the key scenario)
        "In Millay v. Cam, 135 Wn.2d 193, 202, 955 P.2d 791 (1998), the court established...",
        
        # Test 3: List of citations without case names
        "The court cited 90 Wn.2d 9, 315 P.3d 493, and 602 U.S. 779.",
        
        # Test 4: Case with complex name
        "In State of Washington v. Mason Blair, 415 P.3d 1232, the court...",
        
        # Test 5: Multiple citations in sequence for same case
        "The court in Smith v. Jones, 123 F.3d 456, 789, 1011 (2020) held that...",
        
        # Test 6: Citations with minimal context
        "See 90 Wn.2d 9; 315 P.3d 493; 602 U.S. 779.",
        
        # Test 7: Washington Supreme Court case with multiple citations
        "In State v. Lui, 179 Wn.2d 457, 315 P.3d 493, the court addressed...",
    ]
    
    processor = CitationProcessor()
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test_text[:50]}...")
        print(f"{'='*60}")
        
        try:
            # Extract citations with case names
            citations = processor.extract_citations(test_text, extract_case_names=True)
            
            print(f"Found {len(citations)} citations:")
            for j, citation in enumerate(citations, 1):
                print(f"  {j}. Citation: '{citation['citation']}'")
                print(f"     Case Name: '{citation.get('case_name', 'None')}'")
                print(f"     Position: {citation.get('start_index', 'N/A')} - {citation.get('end_index', 'N/A')}")
                print()
                
        except Exception as e:
            print(f"Error processing test {i}: {str(e)}")
            import traceback
            traceback.print_exc()

def test_shared_case_name_detection():
    """Test the shared case name detection specifically"""
    
    print(f"\n{'='*60}")
    print("TESTING SHARED CASE NAME DETECTION")
    print(f"{'='*60}")
    
    # Test the specific scenario mentioned by the user
    test_text = "In Millay v. Cam, 135 Wn.2d 193, 202, 955 P.2d 791 (1998), the court established..."
    
    # Create mock citation objects
    citations = [
        {'citation': '135 Wn.2d 193', 'start_index': 15, 'end_index': 28},
        {'citation': '202', 'start_index': 30, 'end_index': 33},
        {'citation': '955 P.2d 791', 'start_index': 35, 'end_index': 47},
    ]
    
    print(f"Test text: {test_text}")
    print(f"Citations: {[c['citation'] for c in citations]}")
    
    # Test individual extraction
    print(f"\nIndividual case name extraction:")
    for citation in citations:
        case_name = extract_case_name_from_text(test_text, citation['citation'], citations)
        print(f"  '{citation['citation']}' -> '{case_name}'")

if __name__ == "__main__":
    test_case_name_extraction()
    test_shared_case_name_detection() 