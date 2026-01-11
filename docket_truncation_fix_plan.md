"""
Fix the docket number truncation issue
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("FIXING DOCKET NUMBER TRUNCATION")
print("=" * 60)

# The issue is in the strict_context_isolator patterns
# We need to update Pattern 3 to properly stop at docket numbers

print("\nCURRENT ISSUE:")
print("- When patterns don't match, fallback includes docket number")
print("- Need to improve pattern matching for long case names")

print("\nSOLUTION:")
print("1. Update Pattern 3 in strict_context_isolator to better handle long case names")
print("2. Add lookahead to stop at docket numbers: ', No.'")

print("\nPATTERN TO FIX:")
print("Line 856 in strict_context_isolator.py")
print("Current: r\"([A-Z][A-Za-z'\\.\\&,\\s\\n\\-]{2,120}(?:,\\s*(?:LLC|Inc\\.?|Corp\\.?|Co\\.?|Ltd\\.?|L\\.P\\.?|L\\.L\\.C\\.?))?)\\s+v\\.\\s+([A-Z][A-Za-z'\\.\\&,\\s\\n\\-]{2,120}(?:,\\s*(?:LLC|Inc\\.?|Corp\\.?|Co\\.?|Ltd\\.?|L\\.P\\.?|L\\.L\\.C\\.?))?)(?:\\s*[\\(\\;,]|,\\s*\\d+|,\\s*No\\.|$)\"")

print("\nFIXED PATTERN:")
print("Add positive lookahead to stop at docket numbers more aggressively")
print("Use: (?=,\\s*No\\.|,\\s*\\d+|\\s*[\\(\\;,]|$)")

print("\nFILES TO MODIFY:")
print("- src/utils/strict_context_isolator.py (line 856)")

print("\nTEST AFTER FIX:")
print("2025 WL 1410708 should extract: 'Alexander v. Las Vegas Metro. Police Dep't'")
print("Without the ':24-CV- 00074-APG-NJK' part")
