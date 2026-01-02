#!/usr/bin/env python3
"""
Test the improved case name extraction with fallback names
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_fallback_case_names():
    """Test the new fallback case name generation"""
    
    print("🧪 TESTING FALLBACK CASE NAME GENERATION")
    print("=" * 60)
    
    test_citations = [
        "161 F.3d 584",  # Foss case - should generate "Federal Appeals Case"
        "521 U.S. 811",  # Supreme Court case
        "123 F. Supp. 456",  # Federal District case
        "456 Wn.2d 789",  # Washington State case
        "789 P.3d 123",  # Pacific Reporter case
    ]
    
    for citation in test_citations:
        print(f"\n📋 Testing citation: {citation}")
        
        # Test with no context (should trigger fallback)
        result = extract_case_name_and_date_unified_master(
            text="",  # No context to force fallback
            citation=citation,
            debug=True
        )
        
        print(f"  Case name: {result.get('case_name', 'N/A')}")
        print(f"  Method: {result.get('method', 'unknown')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        
        # Check if we got a meaningful fallback instead of "N/A"
        case_name = result.get('case_name', 'N/A')
        if case_name != 'N/A' and result.get('method') == 'fallback_generated':
            print(f"  ✅ SUCCESS: Got meaningful fallback name instead of N/A")
        elif case_name == 'N/A':
            print(f"  ❌ FAIL: Still returning N/A")
        else:
            print(f"  ✅ SUCCESS: Got extracted name: {case_name}")

if __name__ == "__main__":
    test_fallback_case_names()
