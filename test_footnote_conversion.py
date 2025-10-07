"""
Test footnote to endnote conversion with 1033940.pdf
"""

from src.footnote_to_endnote_converter import convert_footnotes_to_endnotes
from src.robust_pdf_extractor import extract_pdf_text_robust
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_footnote_conversion():
    """Test footnote conversion on 1033940.pdf"""
    
    pdf_path = "1033940.pdf"
    
    print("=" * 80)
    print("FOOTNOTE TO ENDNOTE CONVERSION TEST")
    print("=" * 80)
    
    # Test 1: Extract WITHOUT footnote conversion
    print("\n1. Extracting PDF WITHOUT footnote conversion...")
    text_without, library = extract_pdf_text_robust(pdf_path, convert_footnotes=False)
    print(f"   Library used: {library}")
    print(f"   Text length: {len(text_without):,} characters")
    
    # Count potential footnotes in original
    footnote_indicators = text_without.count('\n1.') + text_without.count('\n2.') + text_without.count('\n3.')
    print(f"   Potential footnote indicators: {footnote_indicators}")
    
    # Test 2: Extract WITH footnote conversion
    print("\n2. Extracting PDF WITH footnote conversion...")
    text_with, library = extract_pdf_text_robust(pdf_path, convert_footnotes=True)
    print(f"   Library used: {library}")
    print(f"   Text length: {len(text_with):,} characters")
    
    # Check if endnotes section was added
    has_endnotes = "ENDNOTES" in text_with
    print(f"   Has endnotes section: {has_endnotes}")
    
    if has_endnotes:
        # Count endnotes
        endnote_count = text_with.count("[Endnote ")
        print(f"   Endnotes created: {endnote_count}")
        
        # Show sample endnotes
        print("\n3. Sample endnotes:")
        lines = text_with.split('\n')
        endnote_lines = [line for line in lines if line.strip().startswith('[Endnote ')]
        for i, line in enumerate(endnote_lines[:5]):
            print(f"   {line[:100]}...")
        
        if len(endnote_lines) > 5:
            print(f"   ... and {len(endnote_lines) - 5} more")
    
    # Test 3: Compare citation extraction quality
    print("\n4. Citation extraction comparison:")
    
    # Simple citation count (rough estimate)
    citation_patterns = [
        ' U.S. ',
        ' S. Ct. ',
        ' F.2d ',
        ' F.3d ',
        ' P.2d ',
        ' P.3d ',
    ]
    
    citations_without = sum(text_without.count(pattern) for pattern in citation_patterns)
    citations_with = sum(text_with.count(pattern) for pattern in citation_patterns)
    
    print(f"   Citations in original: ~{citations_without}")
    print(f"   Citations in converted: ~{citations_with}")
    
    # Test 4: Show text structure difference
    print("\n5. Text structure comparison:")
    print(f"   Original paragraphs: ~{text_without.count(chr(10) + chr(10))}")
    print(f"   Converted paragraphs: ~{text_with.count(chr(10) + chr(10))}")
    
    # Save samples for inspection
    print("\n6. Saving samples for inspection...")
    with open('test_output_without_conversion.txt', 'w', encoding='utf-8') as f:
        f.write(text_without[:5000])
    print("   Saved: test_output_without_conversion.txt (first 5000 chars)")
    
    with open('test_output_with_conversion.txt', 'w', encoding='utf-8') as f:
        f.write(text_with[:5000])
    print("   Saved: test_output_with_conversion.txt (first 5000 chars)")
    
    if has_endnotes:
        # Save endnotes section
        endnotes_start = text_with.find("ENDNOTES")
        if endnotes_start > 0:
            with open('test_output_endnotes.txt', 'w', encoding='utf-8') as f:
                f.write(text_with[endnotes_start:endnotes_start+5000])
            print("   Saved: test_output_endnotes.txt (endnotes section)")
    
    print("\n" + "=" * 80)
    if has_endnotes:
        print("✅ SUCCESS! Footnotes converted to endnotes")
        print(f"   {endnote_count} footnotes moved to endnotes section")
    else:
        print("ℹ️  No footnotes detected in this PDF")
        print("   This may be normal if the PDF doesn't use footnotes")
    print("=" * 80)

if __name__ == "__main__":
    test_footnote_conversion()
