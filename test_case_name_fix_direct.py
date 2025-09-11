#!/usr/bin/env python3
"""
Direct test script to verify the case name extraction fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_similarity():
    """Test the case name similarity function directly"""
    
    # Import the function we want to test
    from enhanced_sync_processor import EnhancedSyncProcessor
    
    # Create an instance
    processor = EnhancedSyncProcessor()
    
    # Test cases
    test_cases = [
        # Test case 1: Should be similar
        {
            'extracted': 'In re Marriage of Black',
            'verification': 'In re Marriage of Black',
            'expected': True,
            'description': 'Exact match'
        },
        # Test case 2: Should be similar (subset)
        {
            'extracted': 'In re Marriage of Black',
            'verification': 'Marriage of Black',
            'expected': True,
            'description': 'One is subset of other'
        },
        # Test case 3: Should NOT be similar (completely different)
        {
            'extracted': 'In re Marriage of Black',
            'verification': 'Alsager v. Bd. of Osteopathic Med. & Surgery',
            'expected': False,
            'description': 'Completely different cases'
        },
        # Test case 4: Should NOT be similar (different parties)
        {
            'extracted': 'In re Marriage of Black',
            'verification': 'Blackmon v. Blackmon',
            'expected': False,
            'description': 'Different parties'
        },
        # Test case 5: Should be similar (word overlap)
        {
            'extracted': 'In re Marriage of Black',
            'verification': 'Marriage of Black, In re',
            'expected': True,
            'description': 'Word overlap'
        }
    ]
    
    print("=== Testing Case Name Similarity Function ===")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        extracted = test_case['extracted']
        verification = test_case['verification']
        expected = test_case['expected']
        description = test_case['description']
        
        try:
            result = processor._are_case_names_similar(extracted, verification)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            
            print(f"Test {i}: {description}")
            print(f"  Extracted: '{extracted}'")
            print(f"  Verification: '{verification}'")
            print(f"  Expected: {expected}")
            print(f"  Actual: {result}")
            print(f"  Status: {status}")
            print()
            
        except Exception as e:
            print(f"Test {i}: ❌ ERROR - {e}")
            print()
    
    print("=== Summary ===")
    print("This test verifies that the case name similarity function correctly")
    print("identifies when verification results should NOT override extracted case names.")
    print()
    print("The key test case is #3, where 'In re Marriage of Black' should NOT")
    print("be considered similar to 'Alsager v. Bd. of Osteopathic Med. & Surgery'.")
    print()
    print("If this test passes, the backend fix should prevent the wrong case name")
    print("from overriding the correctly extracted 'In re Marriage of Black'.")

if __name__ == "__main__":
    test_case_name_similarity()
