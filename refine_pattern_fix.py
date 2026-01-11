"""
Refined pattern fix
"""

import re

print("REFINING PATTERN FIX")
print("=" * 60)

context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"Context: '{context}'")
print()

# The issue is we need to extract just the case name part
# Let's try a different approach - extract from the "v." outward
v_based_pattern = r"([A-Z][a-zA-Z\'\.\&\-\s]*?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\-\s]*?)(?=\s*,\s*(?:No\.|\d+)|\s*[;\(,]|$)"

print("Testing v.-based pattern...")
match = re.search(v_based_pattern, context)
if match:
    print(f"Matches: '{match.group()}'")
    print(f"Plaintiff: '{match.group(1)}'")
    print(f"Defendant: '{match.group(2)}'")
    
    # Clean up the plaintiff - remove signal words
    plaintiff = match.group(1).strip()
    # Remove common signal words from the beginning
    signal_words = ["see also", "see", "cf.", "e.g.", "accord", "compare"]
    for signal in signal_words:
        if plaintiff.lower().startswith(signal):
            plaintiff = plaintiff[len(signal):].strip(", ")
            break
    
    full_case = f"{plaintiff} v. {match.group(2)}"
    print(f"Cleaned case name: '{full_case}'")
else:
    print("No match")

print("\n" + "=" * 60)
print("BETTER APPROACH:")
print("Instead of complex patterns, we can:")
print("1. Find the 'v.' in the text")
print("2. Expand backwards to find the start of the case name")
print("3. Expand forwards to find the end (before docket)")
print("4. Clean up any signal words")
