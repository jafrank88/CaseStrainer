#!/usr/bin/env python3
"""Check the exact text at position 4463"""

import PyPDF2

reader = PyPDF2.PdfReader('1033940.pdf')
text = ''.join([page.extract_text() for page in reader.pages])

# Position 4463 is where citation starts
pos = 4463

# Show text around this position
before = text[pos-20:pos]
at_pos = text[pos:pos+50]
after = text[pos+50:pos+100]

print(f"Position: {pos}")
print(f"20 chars BEFORE: {repr(before)}")
print(f"50 chars AT position: {repr(at_pos)}")
print(f"50 chars AFTER: {repr(after)}")
print()

# Check if citation has line break
citation_text = text[pos:pos+20]
print(f"Citation text (20 chars): {repr(citation_text)}")

if '\n' in citation_text:
    print("⚠️  Citation CONTAINS line break!")
    parts = citation_text.split('\n')
    print(f"   Part 1: {repr(parts[0])}")
    print(f"   Part 2: {repr(parts[1] if len(parts) > 1 else '')}")
else:
    print("✅ No line break in citation")

# Now check context slice
context_start = pos - 200
context_end = pos
context = text[context_start:context_end]

print(f"\nContext [{context_start}:{context_end}]:")
print(f"First 30 chars: {repr(context[:30])}")
print(f"Last 30 chars: {repr(context[-30:])}")

if "183" in context:
    print("⚠️  '183' IS in context!")
elif "3 Wn.2d" in context:
    print("⚠️  '3 Wn.2d' IS in context!")
else:
    print("✅ Citation NOT in context")

