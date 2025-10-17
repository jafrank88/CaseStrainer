#!/usr/bin/env python3
"""Test if our fixes are actually working"""
import sys
sys.path.insert(0, 'src')

from src.utils.strict_context_isolator import extract_case_name_from_strict_context

# Test 1: Comma contamination fix
print("="*80)
print("TEST 1: Comma Contamination Fix")
print("="*80)
context1 = "Upper Skagit Indian Tribe v. Lundgren, Mills Indian Cmty., 572 U.S. 782"
result1 = extract_case_name_from_strict_context(context1, "572 U.S. 782")
print(f"Context: {context1}")
print(f"Result: '{result1}'")
print(f"Expected: 'Michigan v. Bay Mills Indian Cmty.' or similar")
print(f"PASS: {result1 and 'Lundgren' not in result1}")
print()

# Test 2: Should extract before comma
print("="*80)
print("TEST 2: Should Stop at Comma")
print("="*80)
context2 = "See Smith v. Jones, 123 U.S. 456"
result2 = extract_case_name_from_strict_context(context2, "123 U.S. 456")
print(f"Context: {context2}")
print(f"Result: '{result2}'")
print(f"Expected: 'Smith v. Jones'")
print(f"PASS: {result2 == 'Smith v. Jones'}")
print()

# Test 3: Corporate name with comma
print("="*80)
print("TEST 3: Corporate Name Should Work")
print("="*80)
context3 = "Spokeo, Inc. v. Robins, 578 U.S. 330"
result3 = extract_case_name_from_strict_context(context3, "578 U.S. 330")
print(f"Context: {context3}")
print(f"Result: '{result3}'")
print(f"Expected: 'Spokeo v. Robins' or similar (comma after Inc. is ok to strip)")
print(f"PASS: {result3 and 'Spokeo' in result3 and 'Robins' in result3}")
