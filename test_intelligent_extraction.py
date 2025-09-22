#!/usr/bin/env python3
"""
Test the intelligent case name extraction directly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_extraction_architecture import get_unified_extractor

def test_intelligent_extraction():
    """Test the intelligent extraction method directly."""
    
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    citation = "578 U.S. 330"
    start_index = text.find(citation)
    end_index = start_index + len(citation)
    
    print("🧠 TESTING INTELLIGENT CASE NAME EXTRACTION")
    print("=" * 60)
    print(f"📝 Text: {text}")
    print(f"🎯 Citation: {citation}")
    print(f"📍 Position: {start_index}-{end_index}")
    print()
    
    # Get the extractor and test the intelligent method
    extractor = get_unified_extractor()
    
    print("🔍 Testing intelligent extraction...")
    result = extractor._extract_case_name_intelligent(text, citation, start_index, end_index, debug=True)
    
    if result:
        print(f"✅ SUCCESS: Extracted case name: '{result.case_name}'")
        print(f"   Method: {result.method}")
        print(f"   Confidence: {result.confidence}")
    else:
        print("❌ FAILED: No case name extracted")
    
    print()
    print("🔍 Testing full extraction (should use intelligent first)...")
    full_result = extractor.extract_case_name_and_year(text, citation, start_index, end_index, debug=True)
    
    if full_result and full_result.case_name:
        print(f"✅ FULL RESULT: '{full_result.case_name}'")
        print(f"   Method: {full_result.method}")
    else:
        print("❌ FULL EXTRACTION FAILED")

if __name__ == "__main__":
    test_intelligent_extraction()
