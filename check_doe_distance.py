"""
Check distance for Doe, Inc. v. Roe
"""

text = """explain why the broad scope of requested sealing is necessary such that the alternative of targeted
redactions is insufficient." Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3
(D.D.C. June 3, 2021)."""

citation = "2021 WL 3622166"
start_pos = text.find(citation)

# Find where "Doe" starts
doe_pos = text.find("Doe")
distance = start_pos - doe_pos

print(f"Citation position: {start_pos}")
print(f"'Doe' position: {doe_pos}")
print(f"Distance: {distance} characters")
print()

# Show the 150 chars before citation
context_150 = text[max(0, start_pos - 150) : start_pos]
print(f"150 chars before citation:")
print(f"'{context_150}'")

print(f"\nWith 150 chars, we should see: '{text[doe_pos:start_pos]}'")
