#!/usr/bin/env python3
"""
Test the contamination detection logic
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_contamination():
    """Test if the case name is being flagged as contaminated"""
    
    from src.utils.data_separation import is_case_name_contaminated
    
    test_names = [
        "In re Permian Basin Area Rate Cases",
        "In re Permian Basin Area Rate Cases, 390 U.S. 747",
        "Permian Basin Area Rate Cases",
        "County of Hudson v. Dep't of Corr.",
        "Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co."
    ]
    
    print("CONTAMINATION DETECTION TEST")
    print("=" * 60)
    
    for name in test_names:
        result = is_case_name_contaminated(name)
        print(f"'{name}' -> {'CONTAMINATED' if result else 'CLEAN'}")
        
        if result:
            # Check which pattern is matching
            contamination_patterns = [
                r'\d{4}',  # Years
                r'https?://',  # URLs
                r'www\.',  # URLs
                r'\.com',  # URLs
                r'No\. \d+',  # Case numbers
                r'\b\d{2,}\b',  # Any 2+ digit numbers
            ]
            
            for pattern in contamination_patterns:
                if re.search(pattern, name):
                    print(f"  Matches pattern: {pattern}")
                    break

if __name__ == "__main__":
    test_contamination()
