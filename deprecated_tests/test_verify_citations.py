#!/usr/bin/env python3
"""
Test script to simulate running four citations and their case names through the enhanced multi-source verification code, saving all results to the database.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract_case_name import clean_case_name
from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

# List of test citations and case names
citations_and_cases = [
    ("219 L.Ed. 2d 420", "Smith v. Arizona"),
    ("144 S.Ct. 1785", "Smith v. Arizona"),
    ("515 P.3d 1029", "City of Seattle v. Wiggins"),
    ("129 S.Ct. 2529", "Melendez-Diaz v. Massachusetts"),
]

verifier = EnhancedMultiSourceVerifier()

print("Testing enhanced multi-source verification of four citations (saving to DB)\n" + "="*70)
for citation, case_name in citations_and_cases:
    normalized_case_name = clean_case_name(case_name)
    try:
        result = verifier.verify_citation(citation, use_cache=False, use_database=True, use_api=True, force_refresh=True)
        print(f"Citation: {citation}")
        print(f"Case Name: {normalized_case_name}")
        print(f"Verification Result: {result.get('verified', False)}")
        print(f"Source: {result.get('source')}")
        print(f"Reason/Error: {result.get('error', result.get('explanation', 'No reason provided'))}")
        print(f"Details: {result}")
        print("-"*50)
    except Exception as e:
        print(f"Citation: {citation}")
        print(f"Case Name: {normalized_case_name}")
        print(f"Verification Error: {e}")
        print("-"*50) 