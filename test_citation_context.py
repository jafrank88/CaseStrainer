#!/usr/bin/env python3

def test_citation_context():
    """Examine the specific context around problematic citations."""
    
    print("🔍 CITATION CONTEXT ANALYSIS")
    print("=" * 50)
    
    target_citations = [
        "9 P.3d 655",
        "101 Wash.2d 270", 
        "567 P.3d 1128"
    ]
    
    try:
        # Load the PDF text
        with open("d:/dev/casestrainer/extracted_pdf_text.txt", 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        import re
        
        for citation in target_citations:
            print(f"\n📖 CITATION: {citation}")
            print("=" * 30)
            
            # Find the citation in text
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            match = re.search(citation_pattern, full_text, re.IGNORECASE)
            
            if match:
                start_pos = match.start()
                end_pos = match.end()
                
                # Get 200 chars before and after for focused analysis
                context_start = max(0, start_pos - 200)
                context_end = min(len(full_text), end_pos + 200)
                context = full_text[context_start:context_end]
                
                print(f"Position: {start_pos}-{end_pos}")
                print(f"Context (±200 chars):")
                print("-" * 40)
                
                # Show context with citation highlighted
                relative_start = start_pos - context_start
                relative_end = end_pos - context_start
                
                before = context[:relative_start]
                citation_text = context[relative_start:relative_end]
                after = context[relative_end:]
                
                print(f"{before}**[{citation_text}]**{after}")
                
                # Look for case name patterns in the immediate vicinity
                print(f"\n🔍 Case name analysis:")
                
                # Check for "v." patterns within 100 chars before citation
                before_citation = full_text[max(0, start_pos - 100):start_pos]
                after_citation = full_text[end_pos:min(len(full_text), end_pos + 100)]
                
                # Look for case name patterns
                v_pattern = r'([A-Z][a-zA-Z\s&,.]+?)\s+v\.\s+([A-Z][a-zA-Z\s&,.]+?)(?=\s|,|\.|;|$)'
                in_re_pattern = r'In\s+re\s+([A-Z][a-zA-Z\s&,.]+?)(?=\s|,|\.|;|$)'
                
                # Search in the text before the citation
                v_matches = re.findall(v_pattern, before_citation + " " + after_citation)
                in_re_matches = re.findall(in_re_pattern, before_citation + " " + after_citation)
                
                if v_matches:
                    for match in v_matches[:2]:  # Show first 2
                        print(f"   Potential: {match[0].strip()} v. {match[1].strip()}")
                
                if in_re_matches:
                    for match in in_re_matches[:2]:
                        print(f"   Potential: In re {match.strip()}")
                
                if not v_matches and not in_re_matches:
                    print(f"   No clear case name patterns found near citation")
                    
                    # Look for any capitalized words that might be case names
                    cap_words = re.findall(r'\b[A-Z][a-z]+\b', before_citation + " " + after_citation)
                    if cap_words:
                        print(f"   Capitalized words nearby: {cap_words[:5]}")
                
                # Check if citation appears in a footnote or reference list
                if "footnote" in context.lower() or "fn." in context.lower() or context.count("\n") > 3:
                    print(f"   ⚠️  Appears to be in footnote or reference section")
                
                # Check if it's part of a string citation
                if ";" in context or context.count(",") > 3:
                    print(f"   ⚠️  Appears to be part of string citation")
                    
            else:
                print(f"   ❌ Citation not found in text")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_context()
