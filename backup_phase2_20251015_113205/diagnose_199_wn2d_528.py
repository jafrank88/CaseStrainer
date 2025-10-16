"""
Diagnose why 199 Wn.2d 528 (State v. M.Y.G.) is verifying to wrong cases.

The output shows:
- 199 Wn.2d 528 → "PRP Of Darcy Dean Racus" (2023) ❌
- 509 P.3d 818 → "Jeffery Moore v. Equitrans, L.P." (2022) ❌

Both are WRONG. The correct case is:
- State v. M.Y.G., 199 Wn.2d 528, 509 P.3d 818 (2022)
"""

import PyPDF2

pdf_path = "1033940.pdf"

print("=== DIAGNOSTIC: 199 Wn.2d 528 ===\n")

# Extract text from PDF
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()

# Find "199 Wn.2d 528" in the document (may have newline)
target = "199 Wn.2d 528"
pos = full_text.find(target)

if pos == -1:
    # Try with newline
    target = "199\nWn.2d 528"
    pos = full_text.find(target)
    
if pos == -1:
    # Try any whitespace
    import re
    match = re.search(r'199\s+Wn\.2d\s+528', full_text)
    if match:
        pos = match.start()
        target = match.group()
    else:
        print(f"❌ '199 Wn.2d 528' NOT FOUND in document (tried multiple formats)!")
        exit(1)

if pos == -1:
    print(f"❌ '{target}' NOT FOUND in document!")
else:
    print(f"✅ Found '{target}' at position {pos}")
    
    # Extract context
    start = max(0, pos - 300)
    end = min(len(full_text), pos + 300)
    context = full_text[start:end]
    
    print("\n=== CONTEXT (300 chars before/after) ===")
    print(repr(context))
    
    # Look for the case name before this citation
    before_text = full_text[max(0, pos - 500):pos]
    print("\n=== TEXT BEFORE (500 chars) ===")
    print(repr(before_text))
    
    # Check what's in between the citation and the case name
    import re
    # Look for "v." pattern before the citation
    matches = list(re.finditer(r'([A-Z][^.!?]+?\s+v\.\s+[^.!?,]+?)[\s,]', before_text))
    if matches:
        print("\n=== POTENTIAL CASE NAMES BEFORE CITATION ===")
        for match in matches[-3:]:  # Last 3 matches
            print(f"  - {match.group(1)}")

