import re

# Test the pattern directly
text_before_comma = "see In re Dependency of G.J.A."
pattern = r'(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$'

match = re.search(pattern, text_before_comma, re.IGNORECASE)
if match:
    print(f"✓ Pattern MATCHED!")
    print(f"  Captured: '{match.group(1)}'")
else:
    print(f"✗ Pattern DID NOT MATCH")
    print(f"  Text: '{text_before_comma}'")
    print(f"  Pattern: {pattern}")
    
# Try with the actual context from the PDF
actual_context = "see In re Dependency of G.J.A."
print(f"\nTesting with actual context: '{actual_context}'")
match2 = re.search(pattern, actual_context, re.IGNORECASE)
if match2:
    print(f"✓ MATCHED: '{match2.group(1)}'")
else:
    print(f"✗ NO MATCH")
