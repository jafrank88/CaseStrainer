#!/usr/bin/env python3
"""
Test the improvement functions directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_improvements_direct():
    """Test the improvement functions directly"""
    
    print("🔍 TESTING IMPROVEMENT FUNCTIONS DIRECTLY")
    print("=" * 50)
    
    from src.utils.strict_context_isolator import _expand_abbreviations, _add_missing_words, _fix_formatting_issues
    
    # Test 1: Abbreviation expansion
    print("📝 Test 1: Abbreviation Expansion")
    print("-" * 35)
    
    test_cases = [
        ("Dep't of Ecology v. Campbell", "Department of Ecology v. Campbell"),
        ("Lakeside Indus. v. Thurston", "Lakeside Industries v. Thurston"),
        ("Bd. of Regents v. Roth", "Board of Regents v. Roth"),
        ("No abbreviation here", "No abbreviation here")
    ]
    
    for input_name, expected in test_cases:
        result = _expand_abbreviations(input_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status} '{input_name}' → '{result}' (expected: '{expected}')")
    
    # Test 2: Missing words
    print(f"\n🔤 Test 2: Missing Words Detection")
    print("-" * 38)
    
    context_with_city = "The court reviewed City of Bellevue ordinances and found in Rozner v. Bellevue that..."
    context_with_county = "Snohomish County regulations were cited in Lakeside v. Snohomish case..."
    
    missing_words_cases = [
        ("Rozner v. Bellevue", context_with_city, "Rozner v. City of Bellevue"),
        ("Lakeside v. Snohomish", context_with_county, "Lakeside v. Snohomish County"),
        ("No missing words", "Random context", "No missing words")
    ]
    
    for input_name, context, expected in missing_words_cases:
        result = _add_missing_words(input_name, context)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status} '{input_name}' → '{result}' (expected: '{expected}')")
    
    # Test 3: Formatting fixes
    print(f"\n🎨 Test 3: Formatting Issues")
    print("-" * 30)
    
    formatting_cases = [
        ("Name  v.  Name", "Name v. Name"),
        ("Name,Name", "Name, Name"),
        ("Name & Name", "Name & Name"),
        ("Name Inc", "Name Inc."),
        ("No formatting issues", "No formatting issues")
    ]
    
    for input_name, expected in formatting_cases:
        result = _fix_formatting_issues(input_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status} '{input_name}' → '{result}' (expected: '{expected}')")
    
    print(f"\n🎯 OVERALL TEST RESULTS:")
    print("-" * 25)
    
    # Test the full pipeline
    print(f"\n🔄 Testing Full Pipeline:")
    test_case = "Dep't of Ecology v. Campbell"
    context = "The Department of Ecology case was cited in Dep't of Ecology v. Campbell"
    
    step1 = _expand_abbreviations(test_case)
    step2 = _add_missing_words(step1, context)
    step3 = _fix_formatting_issues(step2)
    
    print(f"  Input: '{test_case}'")
    print(f"  Step 1 (abbreviations): '{step1}'")
    print(f"  Step 2 (missing words): '{step2}'")
    print(f"  Step 3 (formatting): '{step3}'")
    
    if step3 == "Department of Ecology v. Campbell":
        print(f"  ✅ Full pipeline working correctly!")
    else:
        print(f"  ❌ Full pipeline has issues")

if __name__ == "__main__":
    test_improvements_direct()
