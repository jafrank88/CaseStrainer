#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app/src')

from unified_case_extraction_master import extract_case_name_and_date_unified_master

test_cases = [
    ("Department of Education v. California, 604 U.S. 650", "604 U.S. 650"),
    ("E. Palo Alto v. U.S. Dep't of Health, 780 F. Supp. 3d 897", "780 F. Supp. 3d 897"),
    ("Tootle v. Sec'y of Navy, 446 F.3d 167", "446 F.3d 167"),
]

for text, citation in test_cases:
    result = extract_case_name_and_date_unified_master(text, citation, 0, len(text))
    print(f"{result['case_name']}")
