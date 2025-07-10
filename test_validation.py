# TEST VALIDATION FUNCTION

"""
Test the validation function to see why case names are being rejected.
"""

import re

def test_validation():
    """Test the validation function"""
    
    # Test case names from our debugging
    test_cases = [
        "Convoyant, LLC v. DeepThink",
        "Carlsen v. Glob. Client Sols.",
        "Smith v. Jones",
        "Convoyant, LLC v. DeepThink, LLC",
    ]
    
    print("=== TESTING VALIDATION FUNCTION ===")
    
    for case_name in test_cases:
        print(f"\nTesting: '{case_name}'")
        print(f"  Length: {len(case_name)}")
        
        # Test each validation rule
        if not case_name or len(case_name) < 5:
            print("  ❌ Failed: Too short (< 5 chars)")
            continue
        
        # Check for v. pattern
        has_v_pattern = re.search(r'v\.|vs\.|In\s+re|State\s+v\.|People\s+v\.', case_name, re.IGNORECASE)
        if not has_v_pattern:
            print("  ❌ Failed: No 'v.' pattern found")
            continue
        else:
            print("  ✅ Has 'v.' pattern")
        
        # Check length requirement
        if len(case_name) < 10 or len(case_name) > 200:
            print(f"  ❌ Failed: Length {len(case_name)} not in range [10, 200]")
            continue
        else:
            print("  ✅ Length is valid")
        
        print("  ✅ VALID CASE NAME")

def test_cleaning():
    """Test the cleaning function"""
    
    raw_cases = [
        "Convoyant, LLC v. DeepThink, LLC, ",
        "Carlsen v. Glob. Client Sols., ",
        "Smith v. Jones, ",
    ]
    
    print("\n=== TESTING CLEANING FUNCTION ===")
    
    for raw_case in raw_cases:
        print(f"\nRaw: '{raw_case}'")
        
        # Apply cleaning
        cleaned = raw_case
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove trailing punctuation
        cleaned = re.sub(r'[,\s]+$', '', cleaned)
        cleaned = cleaned.rstrip('.,;:')
        
        # Normalize spacing around "v."
        cleaned = re.sub(r'\s+v\.\s+', ' v. ', cleaned)
        cleaned = re.sub(r'\s+vs\.\s+', ' v. ', cleaned)
        
        print(f"Cleaned: '{cleaned}'")
        print(f"Length: {len(cleaned)}")

if __name__ == "__main__":
    test_validation()
    test_cleaning() 