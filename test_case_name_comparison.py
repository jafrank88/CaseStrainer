#!/usr/bin/env python3
"""
Test script to compare extracted case names with proper case names from citation lookup.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from file_utils import extract_text_from_file
from citation_utils import extract_citations
from enhanced_multi_source_verifier import verify_citation
from citation_extractor import CitationExtractor
import json

# Try to import eyecite
try:
    from eyecite import get_citations, resolve_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    print("✓ Eyecite available")
except ImportError:
    EYECITE_AVAILABLE = False
    print("✗ Eyecite not available")

# Try to import citation-lookup
try:
    from citation_lookup import lookup_citation
    CITATION_LOOKUP_AVAILABLE = True
    print("✓ Citation-lookup available")
except ImportError:
    CITATION_LOOKUP_AVAILABLE = False
    print("✗ Citation-lookup not available")

def extract_case_names_with_eyecite(text, citations):
    """Extract case names using Eyecite's resolve_citations for comparison."""
    if not EYECITE_AVAILABLE:
        return {}
    
    try:
        # Get all citations from text
        all_citations = get_citations(text, tokenizer=AhocorasickTokenizer())
        print(f"   ✓ Eyecite found {len(all_citations)} citations")
        
        # Resolve citations to get canonical case names
        resolved = resolve_citations(all_citations)
        print(f"   ✓ Resolved to {len(resolved)} unique cases")
        
        # Extract case names from resolved citations
        case_names = {}
        for citation in all_citations:
            citation_text = str(citation)
            case_name = "Unknown"
            # Prefer resolved_case_name if available
            if hasattr(citation, 'resolved_case') and citation.resolved_case and getattr(citation.resolved_case, 'case_name', None):
                case_name = citation.resolved_case.case_name
            else:
                # Try to construct from plaintiff/defendant
                plaintiff = getattr(citation, 'plaintiff', None)
                defendant = getattr(citation, 'defendant', None)
                if plaintiff and defendant:
                    case_name = f"{plaintiff} v. {defendant}"
                elif plaintiff:
                    case_name = plaintiff
                elif defendant:
                    case_name = defendant
            case_names[citation_text] = case_name
        return case_names
    except Exception as e:
        print(f"   ✗ Error with Eyecite: {e}")
        return {}

def lookup_case_name_with_citation_lookup(citation_text):
    """Look up case name using citation-lookup if available."""
    if not CITATION_LOOKUP_AVAILABLE:
        return "Citation-lookup not available"
    
    try:
        result = lookup_citation(citation_text)
        if result and hasattr(result, 'case_name'):
            return result.case_name
        else:
            return "No case name found"
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=== Case Name Extraction Comparison Test ===\n")
    
    # Step 1: Load the PDF text
    pdf_path = "1028814.pdf"
    print(f"1. Loading PDF: {pdf_path}")
    
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        print(f"   ✓ Loaded PDF with {len(text)} characters")
    except Exception as e:
        print(f"   ✗ Error loading PDF: {e}")
        return
    
    # Step 2: Extract citations and case names
    print("\n2. Extracting citations and case names...")
    try:
        citations, debug_info = extract_citations(text, return_debug=True)
        print(f"   ✓ Found {len(citations)} citations")
        print(f"   ✓ Found {len(debug_info['citations'])} citation details")
        
        # Debug: Check if citations are actually in the text
        print(f"\nDEBUG: Checking if citations are in text...")
        print(f"Text length: {len(text)}")
        print(f"First 200 chars of text: {text[:200]}")
        
        for i, citation_info in enumerate(debug_info['citations'][:5], 1):
            citation_text = citation_info['citation']
            found_in_text = citation_text in text
            print(f"Citation {i}: '{citation_text}' - Found in text: {found_in_text}")
            if found_in_text:
                pos = text.find(citation_text)
                context = text[max(0, pos-50):pos+len(citation_text)+50]
                print(f"  Context: ...{context}...")
        
        # Extract case names using improved method
        extractor = CitationExtractor()
        case_names = extractor.extract_case_names_from_text(text, citations)
        print(f"   ✓ Found {len(case_names)} case names from context")
        
        # Create mapping of citations to our extracted case names
        our_citation_to_case = {}
        for case_info in case_names:
            our_citation_to_case[case_info['citation']] = case_info['case_name']
            
    except Exception as e:
        print(f"   ✗ Error extracting citations: {e}")
        return
    
    # Step 3: Extract case names using Eyecite
    print("\n3. Extracting case names using Eyecite...")
    eyecite_case_names = extract_case_names_with_eyecite(text, citations)
    
    # Step 4: Compare results for the first 10 citations that Eyecite found
    print("\n4. Comparing extracted case names (first 10 Eyecite citations):")
    print("=" * 80)
    
    # Use the citations that Eyecite actually found
    eyecite_citation_list = list(eyecite_case_names.keys())[:10]
    
    for i, citation in enumerate(eyecite_citation_list, 1):
        print(f"\nCitation {i}: {citation}")
        
        # Our extracted case name
        our_case_name = our_citation_to_case.get(citation, "No case name extracted")
        print(f"  Our method:     {our_case_name}")
        
        # Eyecite case name
        eyecite_case_name = eyecite_case_names.get(citation, "Not found by Eyecite")
        print(f"  Eyecite:        {eyecite_case_name}")
        
        # Citation-lookup case name (if available)
        if CITATION_LOOKUP_AVAILABLE:
            lookup_case_name = lookup_case_name_with_citation_lookup(citation)
            print(f"  Citation-lookup: {lookup_case_name}")
        
        # Compare case names
        if our_case_name != "No case name extracted" and eyecite_case_name != "Unknown":
            if our_case_name.lower() == eyecite_case_name.lower():
                print(f"  ✓ EXACT MATCH!")
            elif any(word in our_case_name.lower() for word in eyecite_case_name.lower().split()):
                print(f"  ~ PARTIAL MATCH")
            else:
                print(f"  ✗ NO MATCH")
        else:
            print(f"  ? CANNOT COMPARE (missing data)")
        
        print("-" * 60)
    
    # Step 5: Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS:")
    print(f"Total citations tested: {len(eyecite_citation_list)}")
    
    # Count our extractions
    our_extractions = sum(1 for citation in eyecite_citation_list 
                         if our_citation_to_case.get(citation) != "No case name extracted")
    print(f"Our method extracted case names: {our_extractions}/{len(eyecite_citation_list)} ({our_extractions/len(eyecite_citation_list)*100:.1f}%)")
    
    # Count eyecite extractions
    eyecite_extractions = sum(1 for citation in eyecite_citation_list 
                             if eyecite_case_names.get(citation) != "Unknown")
    print(f"Eyecite found citations: {len(eyecite_citation_list)}/{len(eyecite_citation_list)} ({100:.1f}%)")
    print(f"Eyecite extracted case names: {eyecite_extractions}/{len(eyecite_citation_list)} ({eyecite_extractions/len(eyecite_citation_list)*100:.1f}%)")
    
    # Debug: Show why our method isn't working
    print(f"\nDEBUG: Our method found {len(our_citation_to_case)} total case names")
    print(f"DEBUG: Eyecite found {len(eyecite_case_names)} total case names")
    
    # Show some examples of what our method found
    print(f"\nDEBUG: First 5 case names our method found:")
    for i, (citation, case_name) in enumerate(list(our_citation_to_case.items())[:5], 1):
        print(f"  {i}. {citation} -> {case_name}")
    
    # Show some examples of what eyecite found
    print(f"\nDEBUG: First 5 case names eyecite found:")
    for i, (citation, case_name) in enumerate(list(eyecite_case_names.items())[:5], 1):
        print(f"  {i}. {citation} -> {case_name}")

    # Quick Eyecite test for a single citation
    print("\n=== Eyecite test for '347 U.S. 483' ===")
    test_citation = "347 U.S. 483"
    if EYECITE_AVAILABLE:
        test_citations = get_citations(test_citation)
        for i, citation in enumerate(test_citations, 1):
            print(f"Citation {i}: {citation}")
            for attr in dir(citation):
                if not attr.startswith("_") and not callable(getattr(citation, attr)):
                    print(f"  {attr}: {getattr(citation, attr)}")
    else:
        print("Eyecite not available.")
    print("=== End Eyecite test ===\n")

if __name__ == "__main__":
    main() 