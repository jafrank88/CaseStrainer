#!/usr/bin/env python3
"""Simple test for case name and date extraction"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from unified_case_name_extractor import extract_case_name_and_date_unified
    
    # Simple test
    text = "In Presidential Ests Apt. Assocs. v. Barrett, 129 Wn.2d 320 (1996), the court held..."
    
    result = extract_case_name_and_date_unified(
        text=text,
        citation="129 Wn.2d 320",
        citation_start=46,
        citation_end=59
    )
    
    print("Case Name:", result.get('case_name', 'None'))
    print("Year:", result.get('year', 'None'))
    print("Confidence:", result.get('confidence', 0))
    
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
