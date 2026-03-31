import re
import fitz

# Extract text
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

# Find the second occurrence
matches = list(re.finditer(r'2024 WL 1232082', normalized))
if len(matches) >= 2:
    second_match = matches[1]
    start = second_match.start()
    
    print("=" * 80)
    print("CHECKING CONTEXT AROUND SECOND OCCURRENCE")
    print("=" * 80)
    
    # Show large context before
    context_start = max(0, start - 1000)
    context = normalized[context_start:start]
    
    print(f"\nLast 1000 chars before citation:")
    print(f"'{context}'")
    
    # Find semicolons
    semicolons = [i for i, c in enumerate(context) if c == ';']
    print(f"\nSemicolons found: {len(semicolons)}")
    
    if semicolons:
        for i, pos in enumerate(semicolons):
            print(f"\nSemicolon {i+1} at relative position {pos}:")
            # Show text around semicolon
            semi_context_start = max(0, pos - 50)
            semi_context_end = min(len(context), pos + 100)
            print(f"  '{context[semi_context_start:semi_context_end]}'")
        
        # Show text after last semicolon
        last_semi = semicolons[-1]
        text_after_semi = context[last_semi+1:].strip()
        print(f"\nText after LAST semicolon:")
        print(f"'{text_after_semi}'")
        
        # Check if this contains the correct case name
        if 'Doe v. Teachers Council' in text_after_semi:
            print(f"\n✅ 'Doe v. Teachers Council' found after last semicolon")
        else:
            print(f"\n❌ 'Doe v. Teachers Council' NOT in text after last semicolon")
        
        if 'Schiller' in text_after_semi:
            print(f"❌ 'Schiller' found after last semicolon (contamination)")
        else:
            print(f"✅ 'Schiller' NOT in text after last semicolon")
    else:
        print(f"\n⚠️  No semicolons found in 1000-char context")
        
        # Check if there's a period that might be acting as a sentence boundary
        periods = [i for i, c in enumerate(context) if c == '.']
        print(f"\nPeriods found: {len(periods)}")
        
        if periods:
            last_period = periods[-1]
            text_after_period = context[last_period+1:].strip()
            print(f"\nText after LAST period:")
            print(f"'{text_after_period[:200]}'")
