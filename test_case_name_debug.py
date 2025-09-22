#!/usr/bin/env python3
"""
Test the case name extraction with debug enabled to see what's happening.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master

def test_case_name_extraction():
    """Test case name extraction with debug enabled."""
    
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    citation = "578 U.S. 330"
    start_index = text.find(citation)
    end_index = start_index + len(citation)
    
    print("🔍 TESTING CASE NAME EXTRACTION WITH DEBUG")
    print("=" * 60)
    print(f"📝 Text: {text}")
    print(f"🎯 Citation: {citation}")
    print(f"📍 Position: {start_index}-{end_index}")
    print()
    
    print("🧠 Testing master extraction with debug enabled...")
    result = extract_case_name_and_date_master(
        text=text,
        citation=citation,
        citation_start=start_index,
        citation_end=end_index,
        debug=True  # Enable debug
    )
    
    print()
    print("📊 RESULTS:")
    print(f"   Case name: '{result.get('case_name', 'None')}'")
    print(f"   Year: '{result.get('year', 'None')}'")
    print(f"   Method: '{result.get('method', 'None')}'")
    print(f"   Confidence: {result.get('confidence', 'None')}")
    
    print()
    print("🔍 Testing direct unified extraction...")
    from src.unified_extraction_architecture import extract_case_name_and_year_unified
    
    direct_result = extract_case_name_and_year_unified(
        text=text,
        citation=citation,
        start_index=start_index,
        end_index=end_index,
        debug=True
    )
    
    print()
    print("📊 DIRECT RESULTS:")
    print(f"   Case name: '{direct_result.get('case_name', 'None')}'")
    print(f"   Year: '{direct_result.get('year', 'None')}'")
    print(f"   Method: '{direct_result.get('method', 'None')}'")
    print(f"   Confidence: {direct_result.get('confidence', 'None')}")

if __name__ == "__main__":
    test_case_name_extraction()
