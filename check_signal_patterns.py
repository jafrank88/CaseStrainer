"""
Check exact signal patterns
"""

import re

context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"Original: '{context}'")

# Test the exact pattern from line 789
pattern = r"^\s*see,?\s+e\.?g\.?\s*,?\s*"
print(f"\nTesting pattern: {pattern}")

if re.search(pattern, context, re.IGNORECASE):
    print("Pattern matches!")
    result = re.sub(pattern, "", context, flags=re.IGNORECASE)
    print(f"After substitution: '{result}'")
else:
    print("Pattern doesn't match")

# Test without the comma at the end
pattern2 = r"^\s*see\s+also\s+e\.?g\.?\s*"
print(f"\nTesting pattern2: {pattern2}")

if re.search(pattern2, context, re.IGNORECASE):
    print("Pattern2 matches!")
    result = re.sub(pattern2, "", context, flags=re.IGNORECASE)
    print(f"After substitution: '{result}'")
else:
    print("Pattern2 doesn't match")

# The issue might be that "See, e.g." needs to be exact
print("\nMaybe the issue is that the pattern expects 'See, e.g.' exactly")
print("But we have 'See also, e.g.'")

# Test what would happen
pattern3 = r"^\s*see\s+also\s*,?\s*e\.?g\.?\s*,?\s*"
print(f"\nTesting pattern3: {pattern3}")

if re.search(pattern3, context, re.IGNORECASE):
    print("Pattern3 matches!")
    result = re.sub(pattern3, "", context, flags=re.IGNORECASE)
    print(f"After substitution: '{result}'")
else:
    print("Pattern3 doesn't match")
