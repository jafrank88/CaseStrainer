#!/usr/bin/env python3
"""
Debug script to test the current regex pattern
"""

import re

def test_current_regex():
    """Test the current regex pattern"""
    
    # Current regex from the code
    party_pattern = r'((?:[A-Z](?:[a-z]+|\.[A-Z]*)*\s*)+)$'
    
    test_strings = [
        "Board of Education v. Brown",
        "City of New York v. Smith", 
        "Department of Energy v. Wyoming",
        "State of California v. Brown",
        "U.S. v. Caraway",
        "United States v. Smith"
    ]
    
    print("Testing current regex pattern:")
    print(f"Pattern: {party_pattern}")
    print("=" * 50)
    
    for test_str in test_strings:
        # Find the position of " v. "
        v_pos = test_str.lower().find(' v. ')
        if v_pos != -1:
            before_v = test_str[:v_pos]
            print(f"\nTest string: {test_str}")
            print(f"Before 'v.': '{before_v}'")
            
            match = re.search(party_pattern, before_v)
            if match:
                print(f"✓ MATCH: '{match.group(1)}'")
            else:
                print("✗ NO MATCH")
        else:
            print(f"\nTest string: {test_str}")
            print("✗ No 'v.' found")

if __name__ == "__main__":
    test_current_regex() 