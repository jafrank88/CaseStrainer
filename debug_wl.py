from src.document_processing_unified import extract_text_from_file
import re

# Extract text from the file
text = extract_text_from_file(r'D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf')
print(f"Text length: {len(text)}")

# Find all WL occurrences
wl_positions = []
pos = 0
while True:
    pos = text.find('WL', pos)
    if pos == -1:
        break
    wl_positions.append(pos)
    pos += 1

print(f"Found {len(wl_positions)} WL occurrences at positions: {wl_positions[:5]}")

# Show context around each WL
for i, pos in enumerate(wl_positions[:5]):
    start = max(0, pos - 30)
    end = min(len(text), pos + 30)
    context = text[start:end]
    print(f"WL {i+1} at position {pos}: '{context}'")

# Try different regex patterns
patterns = [
    r'\d{4}\s+WL\s+\d+',
    r'\b\d{4}\s+WL\s+\d+\b',
    r'\d{4}\s+WL\s+\d{1,12}',
    r'\b\d{4}\s+WL\s+\d{1,12}\b'
]

for pattern in patterns:
    matches = re.findall(pattern, text)
    print(f"Pattern '{pattern}': found {len(matches)} matches")
    if matches:
        print(f"  First few: {matches[:3]}") 