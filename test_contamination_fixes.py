#!/usr/bin/env python3
"""
Test script to validate the contamination pattern fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re

def test_contamination_patterns():
    """Test the new contamination patterns"""
    print("🔍 Testing contamination pattern fixes...")
    
    # New contamination patterns
    contamination_prefixes = [
        # CRITICAL FIX: Filter generic appellant/defendant contamination
        r'^(?:Appellants,?\s*|Appellant,?\s*|Petitioners,?\s*|Petitioner,?\s*|Respondents,?\s*|Respondent,?\s*)',
        r'^(?:Defendants?,?\s*|Plaintiffs?,?\s*|JAMES\s+S\.\s*SHAW|DOE\s+SHAW)\s+',
        
        # CRITICAL FIX: Filter procedural text contamination
        r'(?:\s+(?:Following|After|During|Before|In)\s+(?:a\s+)?(?:hearing|trial|proceeding|appeal|argument|motion|conference|review))\s*$',
    ]
    
    # Test cases from the network response
    test_cases = [
        {
            "input": "Appellants, v. JAMES S. SHAW and DOE SHAW, and their marital community",
            "should_contaminate": True,
            "description": "Generic appellant contamination"
        },
        {
            "input": "III Brant v. Shaw Following a hearing",
            "should_contaminate": True,
            "description": "Procedural text contamination"
        },
        {
            "input": "Keck v. Collins",
            "should_contaminate": False,
            "description": "Valid case name"
        },
        {
            "input": "Young v. Key Pharmaceuticals, Inc.",
            "should_contaminate": False,
            "description": "Valid corporate case name"
        },
        {
            "input": "Spokeo, Inc. v. Robins",
            "should_contaminate": False,
            "description": "Valid case name with Inc."
        }
    ]
    
    print(f"\n📋 Testing {len(test_cases)} case names:")
    
    for i, case in enumerate(test_cases, 1):
        input_name = case["input"]
        should_contaminate = case["should_contaminate"]
        description = case["description"]
        
        print(f"\n{i}. {description}")
        print(f"   Input: '{input_name}'")
        
        # Test contamination patterns
        is_contaminated = False
        matched_pattern = None
        
        for pattern in contamination_prefixes:
            if re.search(pattern, input_name, re.IGNORECASE):
                is_contaminated = True
                matched_pattern = pattern
                break
        
        # Apply contamination removal
        cleaned_name = input_name
        for pattern in contamination_prefixes:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE).strip()
        
        print(f"   Contaminated: {is_contaminated} (expected: {should_contaminate})")
        if matched_pattern:
            print(f"   Matched pattern: {matched_pattern}")
        if cleaned_name != input_name:
            print(f"   Cleaned: '{cleaned_name}'")
        
        # Check if result is correct
        if is_contaminated == should_contaminate:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL - Expected {should_contaminate}, got {is_contaminated}")

if __name__ == "__main__":
    test_contamination_patterns()
