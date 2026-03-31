"""
Check case name length
"""

case_name = "Alexander v. Las Vegas Metro. Police Dep't"
print(f"Case name: '{case_name}'")
print(f"Length: {len(case_name)} characters")

# Count characters in each part
plaintiff = "Alexander"
defendant = "Las Vegas Metro. Police Dep't"
print(f"\nPlaintiff: '{plaintiff}' ({len(plaintiff)} chars)")
print(f"Defendant: '{defendant}' ({len(defendant)} chars)")
print(f"Total with 'v.: {len(plaintiff) + len(' v. ') + len(defendant)} chars")

# The pattern allows 2-120 chars for each part
print("\nPattern allows 2-120 chars for plaintiff and defendant")
print(f"Plaintiff fits: {len(plaintiff) <= 120}")
print(f"Defendant fits: {len(defendant) <= 120}")

# Check the full context
full_context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"\nFull context length: {len(full_context)} chars")
print(f"Pattern looks for case name ending with: , No. or ,\\d+ or ; or ( or , or $")

# Test if the pattern should match
import re
pattern = r"([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)(?:\s*[;\(,]|,\s*\d+|,\s*No\.|$)"
match = re.search(pattern, full_context)
if match:
    print(f"\nPattern matches: '{match.group()}'")
    print(f"Plaintiff: '{match.group(1)}'")
    print(f"Defendant: '{match.group(2)}'")
else:
    print("\nPattern doesn't match - this is the problem!")
