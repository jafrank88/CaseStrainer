"""
Test the actual function with the fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Force reload to pick up changes
import importlib
import src.utils.strict_context_isolator
importlib.reload(src.utils.strict_context_isolator)

from src.utils.strict_context_isolator import extract_case_name_from_strict_context

print("TESTING ACTUAL FUNCTION WITH FIX")
print("=" * 60)

# Test context
context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
citation = "2025 WL 1410708"

print(f"Context: '{context}'")
print(f"Citation: {citation}")
print()

result = extract_case_name_from_strict_context(context, citation)

print(f"Result: '{result}'")
print()

if result:
    if "No. 2:24-CV- 00074-APG-NJK" not in result:
        print("✅ SUCCESS: Docket number excluded!")
    else:
        print("❌ FAILED: Docket number still included")
        
    if result == "Alexander v. Las Vegas Metro. Police Dep't":
        print("✅ PERFECT: Exact match!")
    else:
        print(f"⚠️  Got: '{result}'")
else:
    print("❌ No result returned")
