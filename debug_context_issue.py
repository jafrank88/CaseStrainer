#!/usr/bin/env python3
"""
Debug script to investigate the context issue with Benson v. State of Wyoming
"""

import sys
import os
import PyPDF2
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def main():
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print(f"Extracting text from: {pdf_path}")
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    
    # Look for the specific citation and its context
    citation = "2010 WL 4683851"
    expected_case_name = "Benson v. State of Wyoming"
    
    print(f"\nLooking for citation: {citation}")
    print(f"Expected case name: {expected_case_name}")
    
    # Find the citation
    citation_index = text.find(citation)
    if citation_index == -1:
        print(f"Citation '{citation}' not found in text")
        return
    
    print(f"Citation found at position: {citation_index}")
    
    # Show different context windows
    context_windows = [500, 1000, 1500, 2000, 3000]
    
    for window_size in context_windows:
        print(f"\n{'='*80}")
        print(f"CONTEXT WINDOW: {window_size} characters before citation")
        print(f"{'='*80}")
        
        context_start = max(0, citation_index - window_size)
        context_end = citation_index
        context = text[context_start:context_end]
        
        print(f"Context (last 200 chars):")
        print(f"'{context[-200:]}'")
        
        # Check if expected case name is in this context
        if expected_case_name in context:
            print(f"✓ Expected case name '{expected_case_name}' FOUND in context")
            
            # Find the position of the case name in the context
            case_name_pos = context.rfind(expected_case_name)
            if case_name_pos != -1:
                print(f"  Case name found at position {case_name_pos} in context")
                print(f"  Distance from citation: {window_size - case_name_pos} characters")
        else:
            print(f"✗ Expected case name '{expected_case_name}' NOT found in context")
            
            # Look for partial matches
            case_name_parts = expected_case_name.split()
            found_parts = []
            for part in case_name_parts:
                if part in context:
                    found_parts.append(part)
            
            if found_parts:
                print(f"  Found partial matches: {found_parts}")
    
    # Also look for the case name pattern in the entire text
    print(f"\n{'='*80}")
    print("SEARCHING FOR CASE NAME PATTERNS IN ENTIRE TEXT")
    print(f"{'='*80}")
    
    # Look for "Benson v. State" pattern
    benson_pattern = r"Benson\s+v\.\s+State\s+of\s+Wyoming"
    matches = list(re.finditer(benson_pattern, text, re.IGNORECASE))
    
    print(f"Found {len(matches)} matches for 'Benson v. State of Wyoming' pattern:")
    for i, match in enumerate(matches):
        start_pos = match.start()
        end_pos = match.end()
        print(f"  Match {i+1}: Position {start_pos}-{end_pos}")
        print(f"    Text: '{match.group(0)}'")
        
        # Show context around this match
        context_start = max(0, start_pos - 100)
        context_end = min(len(text), end_pos + 100)
        context = text[context_start:context_end]
        print(f"    Context: '{context}'")
        print()

if __name__ == "__main__":
    main() 