#!/usr/bin/env python3
"""
Debug the contamination filter to see why it's not working
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.unified_case_name_extractor import _is_document_case_contamination

def test_contamination_filter():
    """Test the contamination filter with the actual problematic case names"""
    
    print("🔍 TESTING CONTAMINATION FILTER")
    print("=" * 50)
    
    # Test cases from the frontend bug
    test_cases = [
        {
            "extracted_name": "SUPREME COURT OF WASHINGTON Foss v. Nat'l Marine Fisheries Serv",
            "document_primary": "Foss v. Nat'l Marine Fisheries Serv.",
            "expected": True,
            "description": "Should detect contamination (document primary is contained in extracted)"
        },
        {
            "extracted_name": "Berst v. Snohomish County",
            "document_primary": "Foss v. Nat'l Marine Fisheries Serv.",
            "expected": False,
            "description": "Should NOT detect contamination (different cases)"
        },
        {
            "extracted_name": "City of Bellevue v. Lorang",
            "document_primary": "Foss v. Nat'l Marine Fisheries Serv.",
            "expected": False,
            "description": "Should NOT detect contamination (different cases)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        extracted = test_case["extracted_name"]
        primary = test_case["document_primary"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\n🧪 Test {i}: {description}")
        print(f"   Extracted: '{extracted}'")
        print(f"   Primary:   '{primary}'")
        print(f"   Expected:  {expected}")
        
        # Test the contamination filter
        result = _is_document_case_contamination(extracted, primary)
        print(f"   Actual:    {result}")
        
        if result == expected:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL - Expected {expected} but got {result}")
            
            # Debug normalization
            print(f"   🔧 DEBUG:")
            def normalize_for_comparison(name):
                import re
                normalized = name.lower()
                normalized = re.sub(r'[,\.\s]+', ' ', normalized)
                normalized = normalized.strip()
                return normalized
            
            extracted_norm = normalize_for_comparison(extracted)
            primary_norm = normalize_for_comparison(primary)
            
            print(f"      Extracted normalized: '{extracted_norm}'")
            print(f"      Primary normalized:   '{primary_norm}'")
            print(f"      Primary in extracted: {primary_norm in extracted_norm}")

if __name__ == "__main__":
    test_contamination_filter()
