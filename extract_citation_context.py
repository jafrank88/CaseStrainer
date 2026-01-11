import re
import fitz

# Extract text the same way the backend does
doc = fitz.open('motion.pdf')
text_parts = []
for page_num in range(len(doc)):
    page = doc[page_num]
    rect = page.rect
    width, height = rect.width, rect.height
    text_area = fitz.Rect(0, 65, width, height - 50)
    text = page.get_text("text", clip=text_area)
    if text.strip():
        text_parts.append(text)
doc.close()

pymupdf_text = "\n".join(text_parts)
normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", pymupdf_text)
normalized = re.sub(r"\s+", " ", normalized)
normalized = normalized.strip()

# Find 732 F.2d 1302
match = re.search(r'732 F\.2d 1302', normalized)
if match:
    start = match.start()
    end = match.end()
    
    # Get 500 chars before and after
    context_start = max(0, start - 500)
    context_end = min(len(normalized), end + 500)
    context = normalized[context_start:context_end]
    
    print("=" * 80)
    print(f"CONTEXT AROUND '732 F.2d 1302' (position {start}-{end})")
    print("=" * 80)
    print(context)
    print("\n" + "=" * 80)
    
    # Also find 710 F.2d 1165 for comparison
    match2 = re.search(r'710 F\.2d 1165', normalized)
    if match2:
        start2 = match2.start()
        end2 = match2.end()
        context_start2 = max(0, start2 - 300)
        context_end2 = min(len(normalized), end2 + 300)
        context2 = normalized[context_start2:context_end2]
        
        print("\nCONTEXT AROUND '710 F.2d 1165' (position {}-{})".format(start2, end2))
        print("=" * 80)
        print(context2)
