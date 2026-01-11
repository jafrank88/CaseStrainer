"""
Find where ", No." becomes ":"
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')
import re

print("FINDING WHERE ', No.' BECOMES ':'")
print("=" * 60)

original = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"Original: '{original}'")

# Check if there's a pattern that replaces ", No." with ":"
test_patterns = [
    (r",\s*No\.\s+([^:]+):", "Extracts docket and adds colon"),
    (r",\s*No\.\s+(.+)", "General docket pattern"),
    (r",\s*No\.\s+[\d\-\s:]+", "Docket with colon"),
    (r",\s*No\.\s+2:24", "Specific to our case"),
]

print("\nTesting patterns that might cause this:")
for pattern, desc in test_patterns:
    if re.search(pattern, original):
        print(f"Found: {desc}")
        print(f"  Pattern: {pattern}")
        result = re.sub(pattern, r":\1", original)
        print(f"  Result: '{result}'")

# Check if it's a character encoding issue
print("\nChecking character encoding...")
print(f"Ord(',') = {ord(',')}")
print(f"Ord(':') = {ord(':')}")

# Maybe there's a pattern that extracts the docket and leaves just the colon?
print("\nMaybe there's a docket extraction that replaces with ':'?")

# Look for patterns in the codebase
print("\nSearching for patterns that might do this replacement...")
print("The issue is that somewhere in the code:")
print("  ', No. 2:24-CV- 00074-APG-NJK,'")
print("becomes:")
print("  ':24-CV- 00074-APG-NJK,'")
print("\nThis suggests a pattern like: s/, No\. \d+/:/g")
print("Let me search for this in the codebase...")
