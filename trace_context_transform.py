"""
Trace the exact context transformation
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')
import re
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

print("TRACING CONTEXT TRANSFORMATION")
print("=" * 60)

original = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"Original: '{original}'")
print()

# Apply the same transformations as strict_context_isolator
context = original

# Signal word removal at start
signal_patterns_start_only = [
    r"^\s*see,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," at start
    r"^\s*see\s+also\s+",  # "See also" at start
]

print("After signal word removal:")
for pattern in signal_patterns_start_only:
    if re.search(pattern, context, re.IGNORECASE):
        context = re.sub(pattern, "", context, flags=re.IGNORECASE)
        print(f"  Applied: {pattern}")
        break
print(f"  Result: '{context}'")
print()

# FIX #13 cleaning
print("After FIX #13 cleaning:")
context_before_clean = context
context = re.sub(r"\s+No\.\s+[\d\-\s]+(?=\s+v\.)", " ", context, flags=re.IGNORECASE)
print(f"  Changed: {context != context_before_clean}")
print(f"  Result: '{context}'")
print()

# The context should still have ", No. 2:24-CV- 00074-APG-NJK"
# But the debug shows it as ":24-CV- 00074-APG-NJK"
# This suggests something else is happening

print("\n" + "=" * 60)
print("The context still has the docket number intact.")
print("The issue must be happening somewhere else in the code.")
print("Maybe in the adaptive context extraction?")
