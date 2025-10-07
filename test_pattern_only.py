"""Test pattern matching only"""
import re

# Test the pattern directly
text1 = "Spokeo, Inc. v. Robins, 578 U.S. 330"
text2 = "Raines v. Byrd, 521 U.S. 811"

pattern = r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)?)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]+?)(?:,\s*\d+)'

print("Testing Spokeo:")
match1 = re.search(pattern, text1)
if match1:
    print(f"  Plaintiff: '{match1.group(1)}'")
    print(f"  Defendant: '{match1.group(2)}'")
    print(f"  Full: '{match1.group(1)} v. {match1.group(2)}'")
else:
    print("  NO MATCH")

print("\nTesting Raines:")
match2 = re.search(pattern, text2)
if match2:
    print(f"  Plaintiff: '{match2.group(1)}'")
    print(f"  Defendant: '{match2.group(2)}'")
    print(f"  Full: '{match2.group(1)} v. {match2.group(2)}'")
else:
    print("  NO MATCH")
