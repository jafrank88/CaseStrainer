import json
import PyPDF2

# Load the JSON results
with open('motion_test_semicolon_fix.json', 'r') as f:
    data = json.load(f)

# Extract text from PDF
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text()

print("Verifying position indices for 2024 WL 1232082...")
print("=" * 80)

# Find citations in JSON
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text:
        start = cit.get('start_index')
        end = cit.get('end_index')
        extracted_name = cit.get('extracted_case_name')
        
        print(f"\nJSON says:")
        print(f"  Position: {start}-{end}")
        print(f"  Extracted name: {extracted_name}")
        
        # Check what's actually at that position in the PDF text
        if start is not None and end is not None:
            actual_text = full_text[start:end]
            print(f"  Actual text at position: '{actual_text}'")
            
            if '2024 WL 1232082' in actual_text:
                print(f"  ✅ Position is correct")
            else:
                print(f"  ❌ Position is WRONG - doesn't contain '2024 WL 1232082'")
                
            # Show context
            context_start = max(0, start - 100)
            context_end = min(len(full_text), end + 100)
            context = full_text[context_start:context_end]
            print(f"\n  Context:")
            print(f"  {context}")

# Now find the actual positions in the PDF
print("\n\n" + "=" * 80)
print("Finding actual positions of '2024 WL 1232082' in PDF text:")
print("=" * 80)

import re
matches = list(re.finditer(r'2024 WL 1232082', full_text))

for i, match in enumerate(matches, 1):
    start = match.start()
    end = match.end()
    
    # Get context
    context_start = max(0, start - 150)
    context_end = min(len(full_text), end + 150)
    context = full_text[context_start:context_end]
    
    print(f"\nActual occurrence {i}:")
    print(f"  Position: {start}-{end}")
    print(f"  Context: {context}")
