import json
import PyPDF2
import re

# Load the JSON results
with open('motion_test_position_fix.json', 'r') as f:
    data = json.load(f)

# Extract text from PDF
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    original_text = ""
    for page in pdf_reader.pages:
        original_text += page.extract_text()

# Normalize text the same way the backend does
normalized_text = re.sub(r"\s+", " ", original_text)

print("=" * 80)
print("VERIFYING POSITION FIX")
print("=" * 80)

print(f"\nOriginal text length: {len(original_text)}")
print(f"Normalized text length: {len(normalized_text)}")

# Find citations in JSON
wl_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text:
        wl_citations.append({
            'citation': citation_text,
            'start': cit.get('start_index'),
            'end': cit.get('end_index'),
            'extracted_name': cit.get('extracted_case_name')
        })

print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082' in JSON")

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    
    print(f"\n{'=' * 80}")
    print(f"Occurrence {i}:")
    print(f"  JSON position: {start}-{end}")
    print(f"  Extracted name: {cit['extracted_name']}")
    
    if start is not None and end is not None:
        # Check what's at this position in normalized text
        text_at_pos_norm = normalized_text[start:end]
        print(f"\n  Text at position in NORMALIZED text: '{text_at_pos_norm}'")
        
        if '2024 WL 1232082' in text_at_pos_norm:
            print(f"  ✅ Position matches NORMALIZED text")
            
            # Show context in normalized text
            context_start = max(0, start - 150)
            context_end = min(len(normalized_text), end + 150)
            context = normalized_text[context_start:context_end]
            print(f"\n  Context in normalized text:")
            print(f"  ...{context}...")
        else:
            print(f"  ❌ Position does NOT match normalized text")
            
        # Check what's at this position in original text
        text_at_pos_orig = original_text[start:end]
        print(f"\n  Text at position in ORIGINAL text: '{text_at_pos_orig}'")
        
        if '2024 WL 1232082' in text_at_pos_orig:
            print(f"  ✅ Position matches ORIGINAL text")
        else:
            print(f"  ❌ Position does NOT match original text")

# Find actual positions in normalized text
print(f"\n{'=' * 80}")
print("ACTUAL POSITIONS IN NORMALIZED TEXT")
print(f"{'=' * 80}")

actual_matches = list(re.finditer(r'2024 WL 1232082', normalized_text))
print(f"\nFound {len(actual_matches)} actual occurrences in normalized text:")

for i, match in enumerate(actual_matches, 1):
    start = match.start()
    end = match.end()
    
    context_start = max(0, start - 150)
    context_end = min(len(normalized_text), end + 150)
    context = normalized_text[context_start:context_end]
    
    print(f"\nActual occurrence {i}:")
    print(f"  Position: {start}-{end}")
    print(f"  Context: ...{context}...")

print(f"\n{'=' * 80}")
print("CONCLUSION")
print(f"{'=' * 80}")

if wl_citations:
    json_pos_1 = wl_citations[0]['start']
    actual_pos_1 = actual_matches[0].start() if actual_matches else None
    
    if json_pos_1 == actual_pos_1:
        print("\n✅ POSITIONS ARE ALIGNED!")
        print("The text normalization fix is working.")
    else:
        print(f"\n❌ POSITIONS STILL MISALIGNED")
        print(f"JSON reports: {json_pos_1}")
        print(f"Actual position: {actual_pos_1}")
        print(f"Difference: {json_pos_1 - actual_pos_1 if json_pos_1 and actual_pos_1 else 'N/A'}")
