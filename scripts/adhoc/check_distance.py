"""
Check the distance from citation to case name
"""

text = """This presumption of public access does not appear to be rebutted here, though of course Volokh
is handicapped in elaborating on this point by the very facts that Plaintiff's motions are sealed and
that no motion to seal those motions is publicly available. "A motion to seal itself should not
generally require sealing or redaction because litigants should be able to address the applicable
standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer,
No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022)."""

citation = "2022 WL 2819734"
start_pos = text.find(citation)

# Find where "Allegiant" starts
allegiant_pos = text.find("Allegiant")
distance = start_pos - allegiant_pos

print(f"Citation position: {start_pos}")
print(f"'Allegiant' position: {allegiant_pos}")
print(f"Distance: {distance} characters")
print()

# Show the 50 chars before citation
context_50 = text[max(0, start_pos - 50) : start_pos]
print(f"50 chars before citation:")
print(f"'{context_50}'")

# Show what we need
print(f"\nWhat we need (distance chars):")
print(f"'{text[allegiant_pos:start_pos]}'")

print(f"\nPROBLEM: The case name is {distance} chars away,")
print(f"but the function only looks 50 chars back!")
