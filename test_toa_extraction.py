#!/usr/bin/env python3
"""
Simple diagnostic script to test TOA extraction and citation processing.
"""

import re
import time
import os

def test_file_reading():
    """Test if we can read the brief file."""
    print("=== TESTING FILE READING ===")
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    
    if not os.path.exists(brief_file):
        print(f"❌ File not found: {brief_file}")
        return None
    
    try:
        with open(brief_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✅ File read successfully: {len(text)} characters")
        return text
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def test_toa_extraction(text):
    """Test TOA extraction logic."""
    print("\n=== TESTING TOA EXTRACTION ===")
    
    # Look for TABLE OF AUTHORITIES
    toa_start = text.find('TABLE OF AUTHORITIES')
    if toa_start == -1:
        print("❌ Could not find 'TABLE OF AUTHORITIES' in text")
        return None
    
    print(f"✅ Found 'TABLE OF AUTHORITIES' at position {toa_start}")
    
    # Look for end markers
    end_markers = [
        'I.ASSIGNMENT OF ERRORS',
        'II.STATEMENT OF FACTS', 
        'III.ARGUMENT',
        'CONCLUSION'
    ]
    
    toa_end = len(text)
    for marker in end_markers:
        pos = text.find(marker, toa_start)
        if pos != -1 and pos < toa_end:
            toa_end = pos
            print(f"✅ Found end marker '{marker}' at position {pos}")
            break
    
    toa_section = text[toa_start:toa_end]
    print(f"✅ Extracted TOA section: {len(toa_section)} characters")
    print(f"✅ TOA preview: {toa_section[:200]}...")
    
    return toa_section

def test_simple_citation_extraction(text):
    """Test simple citation extraction."""
    print("\n=== TESTING SIMPLE CITATION EXTRACTION ===")
    
    # Simple patterns
    patterns = [
        (r'\b\d+\s+Wn\.\s*\d+\b', 'Washington Reporter'),
        (r'\b\d+\s+P\.\s*\d+\b', 'Pacific Reporter'),
        (r'\b\d+\s+U\.S\.\s*\d+\b', 'US Supreme Court'),
        (r'\b\d+\s+S\.Ct\.\s*\d+\b', 'Supreme Court Reporter'),
    ]
    
    citations = []
    for pattern_str, pattern_name in patterns:
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            print(f"✅ {pattern_name}: {len(matches)} matches")
            
            for match in matches[:5]:  # Show first 5
                citation = match.group(0)
                citations.append(citation)
                print(f"   - {citation}")
                
        except Exception as e:
            print(f"❌ Error with pattern {pattern_name}: {e}")
    
    print(f"✅ Total citations found: {len(citations)}")
    return citations

def test_toa_parser_import():
    """Test if we can import the TOA parser."""
    print("\n=== TESTING TOA PARSER IMPORT ===")
    
    try:
        from toa_parser import ToAParser
        print("✅ ToAParser imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ToAParser: {e}")
        return False

def test_unified_processor_import():
    """Test if we can import the unified processor."""
    print("\n=== TESTING UNIFIED PROCESSOR IMPORT ===")
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        print("✅ UnifiedCitationProcessorV2 imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import UnifiedCitationProcessorV2: {e}")
        return False

def main():
    """Main diagnostic function."""
    print("=== TOA EXTRACTION DIAGNOSTIC ===")
    start_time = time.time()
    
    # Test 1: File reading
    text = test_file_reading()
    if not text:
        return
    
    # Test 2: TOA extraction
    toa_section = test_toa_extraction(text)
    if not toa_section:
        return
    
    # Test 3: Simple citation extraction on TOA
    toa_citations = test_simple_citation_extraction(toa_section)
    
    # Test 4: Simple citation extraction on main body
    main_body = text.replace(toa_section, "")
    print(f"\n✅ Main body length after TOA removal: {len(main_body)} characters")
    main_body_citations = test_simple_citation_extraction(main_body[:10000])  # First 10KB
    
    # Test 5: Import tests
    toa_parser_ok = test_toa_parser_import()
    unified_processor_ok = test_unified_processor_import()
    
    # Summary
    print("\n=== DIAGNOSTIC SUMMARY ===")
    print(f"✅ File reading: OK")
    print(f"✅ TOA extraction: {len(toa_section)} characters")
    print(f"✅ TOA citations: {len(toa_citations)} found")
    print(f"✅ Main body citations: {len(main_body_citations)} found")
    print(f"✅ ToAParser import: {'OK' if toa_parser_ok else 'FAILED'}")
    print(f"✅ UnifiedProcessor import: {'OK' if unified_processor_ok else 'FAILED'}")
    
    elapsed = time.time() - start_time
    print(f"✅ Total diagnostic time: {elapsed:.2f} seconds")
    
    if len(toa_section) == len(text):
        print("\n⚠️  WARNING: TOA section is same length as full text!")
        print("   This indicates the TOA extraction is not working correctly.")
        print("   The main body will be empty, causing no citations to be found.")
    
    print("\n=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    main() 