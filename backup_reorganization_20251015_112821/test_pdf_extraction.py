"""
Test case extraction from PDF file 1028814.pdf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
from src.citation_extractor import CitationExtractor
from src.unified_case_extraction_master import UnifiedCaseExtractionMaster

def extract_pdf_text(pdf_path, max_pages=None):
    """Extract text from PDF file."""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        pages = reader.pages if max_pages is None else reader.pages[:max_pages]
        for i, page in enumerate(pages):
            text += page.extract_text()
        return text

def test_pdf_extraction():
    """Test case extraction from the PDF."""
    
    pdf_path = '1028814.pdf'
    
    print("=" * 80)
    print("TESTING CASE EXTRACTION FROM PDF: 1028814.pdf")
    print("=" * 80)
    
    # Extract text from PDF
    print("\n1. Extracting text from PDF...")
    text = extract_pdf_text(pdf_path)  # Extract all pages
    print(f"   ✓ Extracted {len(text)} characters from entire document")
    
    # Show sample of text
    print("\n2. Sample text from document:")
    print("   " + "-" * 76)
    sample = text[:500].replace('\n', '\n   ')
    print(f"   {sample}")
    print("   " + "-" * 76)
    
    # Test with CitationExtractor
    print("\n3. Testing CitationExtractor...")
    extractor = CitationExtractor()
    citations = extractor.extract_citations(text, use_eyecite=False)
    
    print(f"   ✓ Found {len(citations)} citations")
    
    # Group by case name
    case_names = {}
    for citation in citations:
        if citation.extracted_case_name:
            name = citation.extracted_case_name
            if name not in case_names:
                case_names[name] = []
            case_names[name].append(citation.citation)
    
    print(f"   ✓ Found {len(case_names)} unique case names")
    
    # Show first 10 citations with details
    print("\n4. First 10 citations extracted:")
    for i, citation in enumerate(citations[:10], 1):
        print(f"\n   {i}. Citation: {citation.citation}")
        if citation.extracted_case_name:
            print(f"      Case name: {citation.extracted_case_name}")
        if citation.extracted_date:
            print(f"      Year: {citation.extracted_date}")
        if hasattr(citation, 'extraction_method') and citation.extraction_method:
            print(f"      Method: {citation.extraction_method}")
    
    # Show unique case names
    print("\n5. Unique case names extracted:")
    for i, (name, cites) in enumerate(list(case_names.items())[:15], 1):
        print(f"   {i}. {name}")
        print(f"      Citations: {', '.join(cites[:3])}")
        if len(cites) > 3:
            print(f"      ... and {len(cites) - 3} more")
    
    # Test specific case names we expect to find
    print("\n6. Testing for expected case names:")
    expected_cases = [
        "Cockrum v. C.H. Murphy/Clark-Ullman, Inc.",
        "Cockrum",
        "JEFFERY L. COCKRUM",
    ]
    
    for expected in expected_cases:
        found = False
        for extracted_name in case_names.keys():
            if expected.lower() in extracted_name.lower() or extracted_name.lower() in expected.lower():
                print(f"   ✓ Found match for '{expected}': {extracted_name}")
                found = True
                break
        if not found:
            print(f"   ✗ Did not find: '{expected}'")
    
    # Test with UnifiedCaseExtractionMaster on specific citations
    print("\n7. Testing UnifiedCaseExtractionMaster on sample citations:")
    master = UnifiedCaseExtractionMaster()
    
    # Find some citations in the text to test
    test_patterns = [
        "102881-4",
        "Cockrum v.",
        "Howmet Aerospace",
    ]
    
    for pattern in test_patterns:
        if pattern in text:
            pos = text.find(pattern)
            context_start = max(0, pos - 200)
            context_end = min(len(text), pos + 200)
            context = text[context_start:context_end]
            
            print(f"\n   Testing pattern: '{pattern}'")
            print(f"   Context: ...{context[:100]}...")
            
            result = master.extract_case_name_and_date(
                text=text,
                citation=pattern,
                start_index=pos,
                end_index=pos + len(pattern)
            )
            
            if result and result.case_name:
                print(f"   ✓ Extracted: {result.case_name}")
                if result.year:
                    print(f"   ✓ Year: {result.year}")
                print(f"   ✓ Method: {result.method}")
            else:
                print(f"   ✗ No case name extracted")
    
    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total citations found: {len(citations)}")
    print(f"Citations with case names: {sum(1 for c in citations if c.extracted_case_name)}")
    print(f"Citations with years: {sum(1 for c in citations if c.extracted_date)}")
    print(f"Unique case names: {len(case_names)}")
    
    success_rate = (sum(1 for c in citations if c.extracted_case_name) / len(citations) * 100) if citations else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate > 50:
        print("\n✅ EXTRACTION WORKING WELL")
    elif success_rate > 25:
        print("\n⚠️  EXTRACTION PARTIALLY WORKING")
    else:
        print("\n❌ EXTRACTION NEEDS IMPROVEMENT")
    
    print("=" * 80)

if __name__ == "__main__":
    test_pdf_extraction()
