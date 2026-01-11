import json
import re

try:
    import fitz  # PyMuPDF
    
    # Extract text the same way the backend does (UnifiedTextExtractor._extract_pdf_enhanced)
    doc = fitz.open('motion.pdf')
    text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        width, height = rect.width, rect.height
        
        # Define text area (exclude headers and footers)
        text_area = fitz.Rect(0, 65, width, height - 50)
        
        # Extract text from defined area
        text = page.get_text("text", clip=text_area)
        
        if text.strip():
            text_parts.append(text)
    
    doc.close()
    pymupdf_text = "\n".join(text_parts)
    
    print(f"PyMuPDF raw extraction: {len(pymupdf_text)} chars")
    
    # Now normalize the same way the backend does
    # Step 1: Remove problematic characters
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", pymupdf_text)
    
    # Step 2: Collapse all whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    
    # Step 3: Strip
    normalized = normalized.strip()
    
    print(f"After normalization: {len(normalized)} chars")
    print(f"Backend text (from logs): 12934 chars")
    print(f"Match: {'✅ YES' if len(normalized) == 12934 else '❌ NO (diff: ' + str(len(normalized) - 12934) + ' chars)'}")
    
    # Load JSON results
    with open('motion_test_final_norm.json', 'r') as f:
        data = json.load(f)
    
    # Find citations
    wl_citations = []
    for cit in data.get('citations', []):
        citation_text = cit.get('citation', '')
        if '2024 WL 1232082' in citation_text:
            wl_citations.append({
                'citation': citation_text,
                'start': cit.get('start_index'),
                'end': cit.get('end_index'),
                'extracted_name': cit.get('extracted_case_name'),
            })
    
    print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082'")
    
    # Find actual positions
    actual_matches = list(re.finditer(r'2024 WL 1232082', normalized))
    print(f"Actual positions: {len(actual_matches)}")
    
    print("\n" + "=" * 80)
    print("POSITION ALIGNMENT TEST")
    print("=" * 80)
    
    success_count = 0
    for i, cit in enumerate(wl_citations, 1):
        start = cit['start']
        end = cit['end']
        actual_start = actual_matches[i-1].start() if i <= len(actual_matches) else None
        
        print(f"\nOccurrence {i}:")
        print(f"  JSON: {start}-{end}")
        print(f"  Actual: {actual_start}-{actual_matches[i-1].end() if i <= len(actual_matches) else None}")
        
        if start and actual_start:
            offset = start - actual_start
            print(f"  Offset: {offset} chars")
        
        if start is not None and end is not None:
            text_at_pos = normalized[start:end]
            
            if '2024 WL 1232082' in text_at_pos:
                print(f"  ✅ ALIGNED!")
                success_count += 1
            else:
                print(f"  ❌ MISALIGNED: '{text_at_pos}'")
    
    print(f"\n{'=' * 80}")
    if success_count == len(wl_citations):
        print(f"✅ ✅ ✅ ALL {success_count} POSITIONS ALIGNED! ✅ ✅ ✅")
    else:
        print(f"⚠️  {success_count}/{len(wl_citations)} aligned")
        
except ImportError:
    print("PyMuPDF (fitz) not installed")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
