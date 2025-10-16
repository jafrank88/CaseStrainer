import PyPDF2
import re

pdf = open('24-2626.pdf', 'rb')
reader = PyPDF2.PdfReader(pdf)
text = ''.join([p.extract_text() for p in reader.pages])

# Find the specific citations the user mentioned
target_citations = ['783 F.3d', '936 F.3d', '910 F.3d', '897 F.3d 1224']

print("Searching for user's citations in 24-2626.pdf:")
print("=" * 80)

for target in target_citations:
    matches = [(m.start(), m.group()) for m in re.finditer(re.escape(target), text)]
    print(f"\n{target}:")
    if matches:
        for pos, match in matches:
            # Show context around the citation
            context_start = max(0, pos - 200)
            context_end = min(len(text), pos + len(match) + 200)
            context = text[context_start:context_end]
            print(f"  Position {pos}: ...{context}...")
    else:
        print(f"  NOT FOUND")

# Also check for "La Liberte" mentioned in user's clustering issue
print("\n" + "=" * 80)
print("Checking for 'La Liberte v. Reid':")
matches = [(m.start(), m.group()) for m in re.finditer(r'La Liberte.*?Reid', text, re.IGNORECASE)]
if matches:
    for pos, match in matches[:3]:
        context_start = max(0, pos - 100)
        context_end = min(len(text), pos + len(match) + 100)
        context = text[context_start:context_end]
        print(f"  Position {pos}: ...{context}...")
else:
    print("  NOT FOUND")
