"""
Check context length and truncation
"""

context = "also, e.g., Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK,"
print(f"Context length: {len(context)}")
print(f"Context: '{context}'")

# The issue might be that the context is being truncated somewhere
# Let me check if this is the full context or if it's been modified

original = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"\nOriginal length: {len(original)}")
print(f"Original: '{original}'")

print("\nDifferences:")
print("- 'See ' removed from start")
print("- ', No. 2:' changed to ':'")
print("- This suggests there's preprocessing happening")

# Let me check if there's a pattern that does this replacement
import re

# Maybe there's a pattern that extracts docket numbers
docket_pattern = r",\s*No\.\s+([^,]+)"
match = re.search(docket_pattern, original)
if match:
    print(f"\nFound docket: '{match.group(1)}'")
    print("Maybe there's code that extracts docket numbers and leaves just ':'?")

# Check if the context is being truncated at 80 chars in debug
if len(context) == 80:
    print("\nContext is exactly 80 chars - might be truncated in debug output!")
