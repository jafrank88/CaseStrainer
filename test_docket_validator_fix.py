"""
Test the docket number fix in the validator
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Force reload
import importlib
import src.case_name_validator
importlib.reload(src.case_name_validator)

from src.case_name_validator import is_valid_case_name, has_docket_number, clean_docket_from_case_name, validate_and_clean_case_name

print("TESTING DOCKET NUMBER FIX")
print("=" * 60)

# Test cases
test_cases = [
    "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK",
    "Doe v. Roe, No. 123",
    "Smith v. Jones:2023-CV-456",
    "Brown v. Board, No. 5:2024-APG-789",
    "Normal Case Name v. Defendant",
    "In re Matter of Estate",
]

print("\n1. Testing docket detection:")
print("-" * 50)
for case in test_cases:
    has_docket = has_docket_number(case)
    print(f"'{case}'")
    print(f"  Has docket: {has_docket}")

print("\n2. Testing validation (should reject docket cases):")
print("-" * 50)
for case in test_cases:
    is_valid = is_valid_case_name(case)
    print(f"'{case}'")
    print(f"  Valid: {is_valid}")

print("\n3. Testing validate_and_clean (returns cleaned version):")
print("-" * 50)
for case in test_cases:
    is_valid, result = validate_and_clean_case_name(case)
    print(f"'{case}'")
    print(f"  Valid: {is_valid}")
    print(f"  Result: '{result}'")

print("\n4. Testing the problematic case specifically:")
print("-" * 50)
problematic = "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK"
is_valid, result = validate_and_clean_case_name(problematic)
print(f"Input: '{problematic}'")
print(f"Valid: {is_valid}")
print(f"Cleaned: '{result}'")
print(f"Expected: 'Alexander v. Las Vegas Metro. Police Dep''t'")
print(f"Match: {result == 'Alexander v. Las Vegas Metro. Police Dep''t'}")
