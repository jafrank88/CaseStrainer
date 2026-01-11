#!/usr/bin/env python3
"""
Test script to verify citation filtering with trumpvbarbaracertpet.pdf
"""
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from robust_pdf_extractor import RobustPDFExtractor
from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from config import ProcessingConfig

def main():
    pdf_path = r"D:\dev\casestrainer\trumpvbarbaracertpet.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("="*80)
    print("TESTING CITATION FILTERING")
    print("="*80)
    print(f"PDF: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    print()
    
    # Step 1: Extract text
    print("Step 1: Extracting text from PDF...")
    extractor = RobustPDFExtractor(verbose=True)
    text, library = extractor.extract_text(pdf_path)
    
    if not text:
        print("❌ Failed to extract text")
        return
    
    print(f"✅ Extracted {len(text):,} characters using {library}")
    print()
    
    # Step 2: Extract citations
    print("Step 2: Extracting citations...")
    config = ProcessingConfig()
    processor = UnifiedCitationProcessorV2(config)
    
    citations = processor._extract_citations_unified(text)
    
    print(f"✅ Found {len(citations)} citations after filtering")
    print()
    
    # Step 3: Analyze what was found
    print("Step 3: Citation Analysis")
    print("-" * 80)
    
    if not citations:
        print("⚠️  No citations found (all filtered out or none present)")
        return
    
    # Group by type
    citation_types = {}
    short_forms = []
    id_citations = []
    supra_citations = []
    unknown_citations = []
    statute_citations = []
    
    for cite in citations:
        citation_text = cite.citation or ""
        
        # Check for patterns that should be filtered
        if " at " in citation_text:
            short_forms.append(citation_text)
        elif citation_text.lower() in ["id.", "ibid."]:
            id_citations.append(citation_text)
        elif "supra" in citation_text.lower():
            supra_citations.append(citation_text)
        elif "UnknownCitation" in citation_text:
            unknown_citations.append(citation_text)
        elif any(p in citation_text for p in ["Stat.", "U.S.C.", "C.F.R.", "Fed. Reg.", "Pub. L."]):
            statute_citations.append(citation_text)
        
        # Track all citation types
        method = cite.method or "unknown"
        citation_types[method] = citation_types.get(method, 0) + 1
    
    # Show results
    print(f"Total citations: {len(citations)}")
    print(f"Citation methods: {citation_types}")
    print()
    
    # Check for filtered items that shouldn't be there
    issues = []
    
    if short_forms:
        issues.append(f"❌ Found {len(short_forms)} short-form citations (should be filtered)")
        print(f"Short-form citations (X Y at Z): {len(short_forms)}")
        for cite in short_forms[:5]:
            print(f"  - {cite}")
        if len(short_forms) > 5:
            print(f"  ... and {len(short_forms) - 5} more")
        print()
    
    if id_citations:
        issues.append(f"❌ Found {len(id_citations)} Id. citations (should be filtered)")
        print(f"Id. citations: {len(id_citations)}")
        for cite in id_citations[:5]:
            print(f"  - {cite}")
        print()
    
    if supra_citations:
        issues.append(f"❌ Found {len(supra_citations)} supra citations (should be filtered)")
        print(f"Supra citations: {len(supra_citations)}")
        for cite in supra_citations[:5]:
            print(f"  - {cite}")
        print()
    
    if unknown_citations:
        issues.append(f"❌ Found {len(unknown_citations)} UnknownCitation objects (should be filtered)")
        print(f"UnknownCitation objects: {len(unknown_citations)}")
        for cite in unknown_citations[:5]:
            print(f"  - {cite}")
        print()
    
    if statute_citations:
        issues.append(f"❌ Found {len(statute_citations)} statute citations (should be filtered)")
        print(f"Statute citations: {len(statute_citations)}")
        for cite in statute_citations[:5]:
            print(f"  - {cite}")
        print()
    
    # Show sample of valid citations
    valid_citations = [c for c in citations if c.citation not in 
                      short_forms + id_citations + supra_citations + unknown_citations + statute_citations]
    
    if valid_citations:
        print(f"✅ Valid case citations: {len(valid_citations)}")
        print("Sample valid citations:")
        for cite in valid_citations[:10]:
            print(f"  - {cite.citation}")
        if len(valid_citations) > 10:
            print(f"  ... and {len(valid_citations) - 10} more")
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    if issues:
        print("⚠️  FILTERING ISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
        print()
        print("The filtering is NOT working correctly. These citations should have been removed.")
    else:
        print("✅ ALL FILTERING WORKING CORRECTLY")
        print(f"   - No short-form citations (X Y at Z)")
        print(f"   - No Id./supra citations")
        print(f"   - No UnknownCitation objects")
        print(f"   - No statute citations")
        print(f"   - {len(valid_citations)} valid case citations found")
    
    print()

if __name__ == "__main__":
    main()
