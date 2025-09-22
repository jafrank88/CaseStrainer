#!/usr/bin/env python3

import PyPDF2
import io

def extract_pdf_text():
    """Extract text from the PDF to analyze its content."""
    
    pdf_path = "D:\\dev\\casestrainer\\1033940.pdf"
    
    print("📄 PDF TEXT EXTRACTION")
    print("=" * 50)
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            print(f"📁 PDF: {pdf_path}")
            print(f"📄 Pages: {len(pdf_reader.pages)}")
            print()
            
            text_parts = []
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    print(f"Page {i+1}: {len(page_text)} characters")
            
            full_text = '\n\n'.join(text_parts)
            
            print(f"\n📊 TOTAL TEXT:")
            print(f"   Total characters: {len(full_text):,}")
            print(f"   Total words: {len(full_text.split()):,}")
            print(f"   Expected routing: {'SYNC' if len(full_text) < 5120 else 'ASYNC'}")
            print()
            
            # Show first 500 characters
            print("📝 FIRST 500 CHARACTERS:")
            print("-" * 30)
            print(repr(full_text[:500]))
            print()
            
            # Look for citation patterns
            import re
            
            # Basic citation patterns
            citation_patterns = [
                r'\d+\s+Wash\.?\s*2d\s+\d+',  # Washington 2d
                r'\d+\s+P\.?\s*3d\s+\d+',     # Pacific 3d
                r'\d+\s+U\.?S\.?\s+\d+',      # U.S. Supreme Court
                r'\d+\s+S\.?\s*Ct\.?\s+\d+',  # Supreme Court Reporter
                r'\d+\s+F\.?\s*3d\s+\d+',     # Federal 3d
                r'\d+\s+F\.?\s*Supp\.?\s*3d\s+\d+',  # Federal Supplement 3d
                r'20\d{2}\s+WL\s+\d+',       # Westlaw citations
            ]
            
            print("🔍 CITATION PATTERN ANALYSIS:")
            print("-" * 35)
            
            total_matches = 0
            for pattern in citation_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    print(f"   {pattern:25}: {len(matches)} matches")
                    total_matches += len(matches)
                    # Show first few matches
                    for match in matches[:3]:
                        print(f"      - {match}")
                    if len(matches) > 3:
                        print(f"      ... and {len(matches) - 3} more")
            
            print(f"\n   Total potential citations: {total_matches}")
            
            # Look for case name patterns
            case_name_patterns = [
                r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
                r'In\s+re\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
                r'Ex\s+parte\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
            ]
            
            print("\n📝 CASE NAME PATTERN ANALYSIS:")
            print("-" * 35)
            
            case_names = set()
            for pattern in case_name_patterns:
                matches = re.findall(pattern, full_text)
                for match in matches:
                    if isinstance(match, tuple):
                        case_name = f"{match[0]} v. {match[1]}" if len(match) > 1 else match[0]
                    else:
                        case_name = match
                    
                    if len(case_name) > 5 and len(case_name) < 100:  # Reasonable length
                        case_names.add(case_name)
            
            print(f"   Unique case names found: {len(case_names)}")
            for i, name in enumerate(sorted(case_names)[:10]):
                print(f"      {i+1}. {name}")
            if len(case_names) > 10:
                print(f"      ... and {len(case_names) - 10} more")
            
            print(f"\n🎯 PDF ANALYSIS SUMMARY:")
            print("=" * 30)
            print(f"✅ Text extraction: {len(full_text):,} characters")
            print(f"✅ Citation patterns: {total_matches} potential citations")
            print(f"✅ Case names: {len(case_names)} unique names")
            print(f"📊 Processing expectation: {'SYNC' if len(full_text) < 5120 else 'ASYNC'}")
            
            # Save extracted text for further analysis
            with open("extracted_pdf_text.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"💾 Saved extracted text to: extracted_pdf_text.txt")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_pdf_text()
