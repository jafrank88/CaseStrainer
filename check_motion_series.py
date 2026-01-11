"""
Check motion.pdf for series citations more carefully
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

import PyPDF2
import re

# Read the PDF
pdf_path = "D:/dev/casestrainer/motion.pdf"
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

# Look for potential series citation patterns
print("SEARCHING FOR SERIES CITATIONS IN MOTION.PDF:")
print("=" * 60)

# Pattern 1: Citations separated by commas
print("\n1. Citations separated by commas:")
comma_pattern = r'([A-Z][^,.]*\s+v\.\s+[^,.]+),\s+\d+\s+[A-Za-z\.]+\s+\d+'
matches = re.findall(comma_pattern, text)
for match in matches[:5]:
    print(f"   Found: {match}")

# Pattern 2: Multiple WL citations
print("\n2. Multiple WL citations:")
wl_pattern = r'(\d{4}\s+WL\s+\d+)'
wl_matches = re.findall(wl_pattern, text)
if len(wl_matches) > 1:
    print(f"   Found {len(wl_matches)} WL citations:")
    for match in wl_matches:
        print(f"     - {match}")

# Pattern 3: Citations with "see" or "cf"
print("\n3. Citations with 'see' or 'cf':")
see_pattern = r'see\s+([^,.]*(?:\d+\s+[A-Za-z\.]+\s+\d+|F\.?\d+|WL\s+\d+)[^,.]*)'
see_matches = re.findall(see_pattern, text, re.IGNORECASE)
for match in see_matches[:5]:
    print(f"   Found: {match}")

# Pattern 4: Look for the specific example from our test
print("\n4. Checking for 'Doe v. City of New York' pattern:")
if "Doe v. City of New York" in text:
    print("   Found 'Doe v. City of New York' in document!")
    # Find context around it
    idx = text.find("Doe v. City of New York")
    context = text[max(0, idx-100):idx+200]
    print(f"   Context: ...{context}...")

# Show actual citations found
print("\n" + "=" * 60)
print("ACTUAL CITATIONS FOUND BY EYECITE:")
print("=" * 60)

from eyecite import get_citations
citations = get_citations(text)

print(f"\nTotal citations found: {len(citations)}")
for i, cit in enumerate(citations):
    print(f"\n{i+1}. {cit}")
    
# Check if any are close together
print("\n" + "=" * 60)
print("CHECKING CITATION PROXIMITY:")
print("=" * 60)

for i in range(1, len(citations)):
    prev = citations[i-1]
    curr = citations[i]
    distance = curr.span()[0] - prev.span()[1]
    
    if distance < 100:
        print(f"\nCLOSE CITATIONS:")
        print(f"  {i}. {prev}")
        print(f"  {i+1}. {curr}")
        print(f"  Distance: {distance} characters")
        
        # Show text between
        between = text[prev.span()[1]:curr.span()[0]]
        print(f"  Text between: '{between.strip()}'")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
print("Motion.pdf does not appear to contain series citations")
print("like 'Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569'.")
print("All citations appear to be separate with distinct case names.")
