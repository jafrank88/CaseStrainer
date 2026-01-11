"""
Test to verify position misalignment between PDF extraction and eyecite positions.
"""
import PyPDF2
import re

# Extract text from PDF
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    original_text = ""
    for page in pdf_reader.pages:
        original_text += page.extract_text()

# Simulate the normalization that happens in the extraction pipeline
normalized_text = re.sub(r"\s+", " ", original_text)

print("=" * 80)
print("POSITION ALIGNMENT TEST")
print("=" * 80)

print(f"\nOriginal text length: {len(original_text)}")
print(f"Normalized text length: {len(normalized_text)}")
print(f"Difference: {len(original_text) - len(normalized_text)} characters")

# Find "2024 WL 1232082" in both texts
import re
pattern = r'2024 WL 1232082'

print("\n" + "=" * 80)
print("FINDING CITATION IN ORIGINAL TEXT")
print("=" * 80)

original_matches = list(re.finditer(pattern, original_text))
print(f"\nFound {len(original_matches)} occurrences in original text:")
for i, match in enumerate(original_matches, 1):
    print(f"\nOccurrence {i}: Position {match.start()}-{match.end()}")
    context_start = max(0, match.start() - 100)
    context_end = min(len(original_text), match.end() + 100)
    context = original_text[context_start:context_end]
    print(f"Context: ...{context}...")

print("\n" + "=" * 80)
print("FINDING CITATION IN NORMALIZED TEXT")
print("=" * 80)

normalized_matches = list(re.finditer(pattern, normalized_text))
print(f"\nFound {len(normalized_matches)} occurrences in normalized text:")
for i, match in enumerate(normalized_matches, 1):
    print(f"\nOccurrence {i}: Position {match.start()}-{match.end()}")
    context_start = max(0, match.start() - 100)
    context_end = min(len(normalized_text), match.end() + 100)
    context = normalized_text[context_start:context_end]
    print(f"Context: ...{context}...")

print("\n" + "=" * 80)
print("POSITION COMPARISON")
print("=" * 80)

for i in range(len(original_matches)):
    orig_pos = original_matches[i].start()
    norm_pos = normalized_matches[i].start() if i < len(normalized_matches) else None
    
    if norm_pos is not None:
        diff = orig_pos - norm_pos
        print(f"\nOccurrence {i+1}:")
        print(f"  Original position: {orig_pos}")
        print(f"  Normalized position: {norm_pos}")
        print(f"  Difference: {diff} characters")
        
        # Check what's at the normalized position in the original text
        if norm_pos < len(original_text):
            text_at_norm_pos = original_text[norm_pos:norm_pos+15]
            print(f"  Text at normalized position in original: '{text_at_norm_pos}'")
            print(f"  ❌ MISMATCH!" if '2024 WL 1232082' not in text_at_norm_pos else "  ✅ MATCH")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if len(original_text) != len(normalized_text):
    print("\n❌ TEXT NORMALIZATION CHANGES LENGTH")
    print("This causes position misalignment between:")
    print("  1. Eyecite positions (from normalized text)")
    print("  2. Case name extraction (trying to use positions on original text)")
    print("\nSOLUTION: Ensure all text operations use the same normalized text")
else:
    print("\n✅ No length change detected")
