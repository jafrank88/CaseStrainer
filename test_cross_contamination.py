#!/usr/bin/env python3
"""
Test script to reproduce the cross-contamination issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clean_extraction_pipeline import CleanExtractionPipeline

def test_cross_contamination():
    """Test the specific cross-contamination issue."""
    
    # Test text with two different citations
    test_text = """
    A & G Constr. Co. v. Reid Bros. Logging Co., 547 P.2d 1207 (1976). 
    State v. Bayer Corp., 32 So. 3d 496 (2010).
    """
    
    print("🔍 Testing cross-contamination issue...")
    print(f"Test text: {test_text.strip()}")
    
    # Create pipeline
    pipeline = CleanExtractionPipeline()
    
    # Extract citations
    citations = pipeline.extract_citations(test_text)
    
    print(f"\n📊 Found {len(citations)} citations:")
    
    for i, citation in enumerate(citations):
        print(f"\nCitation {i+1}:")
        print(f"  Citation: {citation.citation}")
        print(f"  Extracted Name: {citation.extracted_case_name}")
        print(f"  Extracted Date: {citation.extracted_date}")
        print(f"  Start Index: {citation.start_index}")
        print(f"  End Index: {citation.end_index}")
        print(f"  Method: {citation.method}")
    
    # Check for cross-contamination
    if len(citations) >= 2:
        name1 = citations[0].extracted_case_name
        name2 = citations[1].extracted_case_name
        
        if name1 == name2 and name1 != "N/A":
            print(f"\n🚨 CROSS-CONTAMINATION DETECTED!")
            print(f"Both citations have the same extracted name: '{name1}'")
            print(f"This is the bug we need to fix!")
        else:
            print(f"\n✅ No cross-contamination detected")
            print(f"Citation 1 name: '{name1}'")
            print(f"Citation 2 name: '{name2}'")

if __name__ == "__main__":
    test_cross_contamination()

