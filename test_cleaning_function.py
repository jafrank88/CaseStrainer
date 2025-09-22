#!/usr/bin/env python3
"""
Test the _clean_extracted_case_name function to see if it's truncating case names.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_cleaning_function():
    """Test the case name cleaning function."""
    
    processor = UnifiedCitationProcessorV2()
    
    test_cases = [
        "Spokeo, Inc. v. Robins",
        "Inc. v. Robins", 
        "Smith v. Jones",
        "In re Microsoft Corp.",
        "Ex parte Johnson",
        "The Supreme Court held in Spokeo, Inc. v. Robins that standing requirements",
        "quoting Spokeo, Inc. v. Robins, 578 U.S. 330"
    ]
    
    print("🧪 TESTING CASE NAME CLEANING FUNCTION")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case}'")
        
        try:
            cleaned = processor._clean_extracted_case_name(test_case)
            print(f"   Result: '{cleaned}'")
            
            if cleaned != test_case:
                print(f"   ⚠️  CHANGED: '{test_case}' → '{cleaned}'")
            else:
                print(f"   ✅ UNCHANGED")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    test_cleaning_function()
