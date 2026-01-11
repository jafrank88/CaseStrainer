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

# Test if there's a pattern that extracts docket and leaves colon
pattern = r",\s*No\.\s+([^,]+)"
match = re.search(pattern, original)
if match:
    docket = match.group(1)
    print(f"\nFound docket: '{docket}'")
    if docket.startswith("2:24"):
        print("This explains it! The docket starts with '2:24'")
        print("So when ', No.' is removed, we're left with ':24-CV- 00074-APG-NJK'")
        print("\nThe transformation is:")
        print("  ', No. 2:24-CV- 00074-APG-NJK,'")
        print("  → remove ', No. '")
        print("  → '2:24-CV- 00074-APG-NJK,'")
        print("  → but somehow the '2' is also removed")
        print("  → ':24-CV- 00074-APG-NJK,'")

# Now I need to find where this is happening
print("\n" + "=" * 60)
print("SOLUTION:")
print("The issue is that the context is being modified after cleaning.")
print("Maybe in the adaptive context extraction or somewhere else.")
print("\nLet me check if the issue is in how the debug output is formatted...")
print("The debug might be truncating or modifying the display.")
