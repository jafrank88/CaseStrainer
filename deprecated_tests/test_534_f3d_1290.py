#!/usr/bin/env python3
"""
Test script to extract case name for citation "534 F.3d 1290"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract_case_name import extract_case_name_from_context

def test_534_f3d_1290():
    """Test case name extraction for citation 534 F.3d 1290"""
    
    # Context from the PDF around the citation
    context = """Evidence is unfairly prejudicial if it has ôan undue tendency to suggest [a] decision on an improper basis, commonly, though not necessarily, an emotional one.ö U.S. v. Caraway , 534 F.3d 1290, 1301 (10th Cir. 2008) (quoting Rule 402 adv. comm. notes)."""
    
    citation = "534 F.3d 1290"
    
    print(f"Testing citation: {citation}")
    print(f"Context: {context}")
    print("-" * 80)
    
    # Extract case name
    case_name = extract_case_name_from_context(context, citation)
    
    print(f"Extracted case name: '{case_name}'")
    print(f"Expected case name: 'U.S. v. Caraway'")
    print(f"Match: {case_name == 'U.S. v. Caraway'}")
    
    return case_name

if __name__ == "__main__":
    test_534_f3d_1290() 