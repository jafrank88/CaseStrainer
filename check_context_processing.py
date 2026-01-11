"""
Check what's happening to the context
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.utils.strict_context_isolator import extract_case_name_from_strict_context

print("CHECKING CONTEXT PROCESSING")
print("=" * 60)

# The original context
original_context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
citation = "2025 WL 1410708"

print(f"Original context: '{original_context}'")
print()

# Let's trace what happens in the function
import re
import logging

# Enable logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

# Simulate the cleaning steps
context = original_context

# Check the FIX #13 cleaning
context_before_clean = context
context = re.sub(r"\s+No\.\s+[\d\-\s]+(?=\s+v\.)", " ", context, flags=re.IGNORECASE)
print(f"After FIX #13 cleaning: '{context}'")
print(f"Changed: {context != context_before_clean}")
print()

# The issue seems to be that the pattern is looking for case numbers BEFORE v.
# But our case number is AFTER the case name
# Let's check if there's other cleaning

# Maybe the issue is in how the context is extracted?
# Let me check the get_strict_context function

print("\nThe issue is that the docket number ', No. 2:24-CV- 00074-APG-NJK'")
print("is being treated as part of the case name by the pattern.")
print("\nThe pattern lookahead should stop at ', No.' but it seems it's not working.")
print("Let me check if the pattern is being applied correctly...")
