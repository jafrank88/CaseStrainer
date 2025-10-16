import PyPDF2

r = PyPDF2.PdfReader('1033940.pdf')
text = ''.join([page.extract_text() for page in r.pages])

# Find all occurrences of "183 Wn.2d 649"
idx = 0
count = 0

while True:
    idx = text.find('183 Wn.2d 649', idx)
    if idx == -1:
        break
    
    count += 1
    print(f"\n{'='*80}")
    print(f"Occurrence {count} at position {idx}:")
    print("="*80)
    print("BEFORE (200 chars):")
    print(text[max(0, idx-200):idx])
    print("\n[CITATION]: 183 Wn.2d 649")
    print("\nAFTER (100 chars):")
    print(text[idx+13:idx+113])
    
    idx += 1

print(f"\n\nTotal occurrences: {count}")


