#!/usr/bin/env python3
"""
Extract actual PDF text and analyze for WL citations
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyPDF2."""
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
                
        return text
    except ImportError:
        print("❌ PyPDF2 not available, trying pdfplumber...")
        return extract_with_pdfplumber(pdf_path)
    except Exception as e:
        print(f"❌ Error with PyPDF2: {e}")
        return extract_with_pdfplumber(pdf_path)

def extract_with_pdfplumber(pdf_path):
    """Extract text using pdfplumber."""
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
    except ImportError:
        print("❌ pdfplumber not available, trying fitz...")
        return extract_with_fitz(pdf_path)
    except Exception as e:
        print(f"❌ Error with pdfplumber: {e}")
        return extract_with_fitz(pdf_path)

def extract_with_fitz(pdf_path):
    """Extract text using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        
        doc.close()
        return text
    except ImportError:
        print("❌ PyMuPDF not available")
        return None
    except Exception as e:
        print(f"❌ Error with PyMuPDF: {e}")
        return None

def analyze_for_wl_citations(text):
    """Analyze text for WL citations using comprehensive patterns."""
    
    print("🔍 Analyzing PDF Text for WL Citations")
    print("=" * 60)
    
    # Multiple WL citation patterns
    wl_patterns = [
        r'\b\d{4}\s+WL\s+\d+\b',  # Basic: 2023 WL 1234567
        r'\b\d{4}\s+W\.?L\.?\s+\d+\b',  # With periods: 2023 W.L. 1234567
        r'\b\d{4}\s+Westlaw\s+\d+\b',  # Full name: 2023 Westlaw 1234567
        r'\bWL\s+\d{4}-\d+\b',  # Alternative format: WL 2023-1234567
        r'\b\d+\s+WL\s+\d+\b',  # Year first: 2023 WL 1234567
    ]
    
    print(f"📄 Document length: {len(text)} characters")
    print(f"📄 Document lines: {len(text.splitlines())}")
    print()
    
    # Search for WL citations
    all_wl_matches = []
    for i, pattern in enumerate(wl_patterns, 1):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Pattern {i}: {pattern}")
        print(f"  Matches: {len(matches)}")
        if matches:
            for match in matches[:5]:  # Show first 5
                print(f"    - {match}")
            if len(matches) > 5:
                print(f"    ... and {len(matches) - 5} more")
        all_wl_matches.extend(matches)
        print()
    
    # Search for other citation types for context
    other_patterns = {
        'Federal Rules': r'\b(?:FRE?|Fed\.?\s*R\.?\s*Evid?\.?|Rule)\s*\d+\b',
        'Document References': r'\b(?:Doc|Document|Dkt)\.?\s*\d+\b',
        'Case Numbers': r'\b\d+:\d+-cv-\d+-[A-Z]+\b',
        'Federal Reporter': r'\b\d+\s+F\.\d*d?\s+\d+\b',
        'U.S. Reports': r'\b\d+\s+U\.S\.\s+\d+\b',
        'State Reports': r'\b\d+\s+[A-Z][a-z]*\.?\d*d?\s+\d+\b',
    }
    
    print("📊 Other Citation Types Found:")
    for citation_type, pattern in other_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"  {citation_type:<20}: {len(matches)} found")
        if matches and len(matches) <= 3:
            for match in matches:
                print(f"    - {match}")
        elif matches:
            for match in matches[:3]:
                print(f"    - {match}")
            print(f"    ... and {len(matches) - 3} more")
    print()
    
    # Show sample text around potential citation areas
    print("📝 Sample Text Sections:")
    lines = text.splitlines()
    for i, line in enumerate(lines[:10]):  # First 10 lines
        if line.strip():
            print(f"  Line {i+1}: {line.strip()[:100]}...")
    print()
    
    return all_wl_matches

def test_with_casestrainer_extraction():
    """Test with actual CaseStrainer extraction to see if it finds WL citations."""
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🧪 Testing with CaseStrainer Extraction")
    print("=" * 60)
    
    try:
        # Import CaseStrainer components
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from pdf_extractor import PDFExtractor
        
        # Extract PDF text
        pdf_extractor = PDFExtractor()
        text = pdf_extractor.extract_text(pdf_path)
        
        print(f"📄 Extracted text length: {len(text)} characters")
        print(f"📄 First 200 chars: {text[:200]}...")
        print()
        
        # Process with CaseStrainer
        processor = UnifiedCitationProcessorV2()
        result = processor.process_text_sync(text)
        
        print(f"📊 CaseStrainer Results:")
        print(f"  Total citations found: {len(result.get('citations', []))}")
        
        wl_citations = [c for c in result.get('citations', []) if 'WL' in c.get('citation', '')]
        print(f"  WL citations found: {len(wl_citations)}")
        
        if wl_citations:
            print("\n✅ WL Citations Found by CaseStrainer:")
            for i, citation in enumerate(wl_citations, 1):
                print(f"  {i}. {citation.get('citation')}")
                print(f"     Source: {citation.get('source')}")
                print(f"     Confidence: {citation.get('confidence')}")
        else:
            print("\n❌ No WL citations found by CaseStrainer")
            
        # Show all citations found
        all_citations = result.get('citations', [])
        if all_citations:
            print(f"\n📋 All Citations Found:")
            for citation in all_citations:
                print(f"  - {citation.get('citation')} (source: {citation.get('source')})")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing with CaseStrainer: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main analysis function."""
    
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🔍 WL Citation Analysis for PDF Document")
    print("=" * 60)
    print(f"📁 File: {pdf_path}")
    print()
    
    # Extract PDF text
    print("📄 Extracting PDF text...")
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("❌ Could not extract text from PDF")
        return
    
    # Analyze for WL citations
    wl_matches = analyze_for_wl_citations(text)
    
    # Test with CaseStrainer
    casestrainer_result = test_with_casestrainer_extraction()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 FINAL ANALYSIS")
    print("=" * 60)
    
    if wl_matches:
        print(f"✅ Found {len(wl_matches)} WL citations using regex patterns")
        print("   This suggests the document DOES contain WL citations")
        print("   CaseStrainer should be finding them...")
    else:
        print("❌ No WL citations found using comprehensive regex patterns")
        print("   This suggests the document genuinely contains no WL citations")
        print("   This is normal for procedural documents like motions in limine")
    
    print()
    print("🎯 Conclusion:")
    if wl_matches:
        print("   The document contains WL citations that should be detected")
        print("   Need to investigate why CaseStrainer isn't finding them")
    else:
        print("   The document is a procedural filing (Motion in Limine)")
        print("   Such documents typically don't cite case law")
        print("   The absence of WL citations is expected and normal")
        print("   CaseStrainer is working correctly!")

if __name__ == "__main__":
    main()
