#!/usr/bin/env python3
"""
Simple test to debug reporter extraction.
"""

import re

def test_reporter_extraction():
    """Test reporter extraction logic."""
    
    print("=== TESTING REPORTER EXTRACTION ===")
    
    # Test text
    test_text = "399 P.3d 1195"
    print(f"Test text: '{test_text}'")
    
    # Pattern from complex_citation_integration.py
    pattern = r'\b(\d+)\s+P\.3d\s+(\d+)\b'
    print(f"Pattern: '{pattern}'")
    
    # Test the pattern
    match = re.search(pattern, test_text)
    if match:
        print(f"✓ Pattern matched!")
        volume = match.group(1)
        page = match.group(2)
        full_match = match.group(0)
        
        print(f"  Volume: '{volume}'")
        print(f"  Page: '{page}'")
        print(f"  Full match: '{full_match}'")
        
        # Test the extraction logic
        volume_str = str(volume)
        page_str = str(page)
        
        # Remove volume from the beginning
        reporter_part = full_match[len(volume_str):].strip()
        print(f"  After removing volume: '{reporter_part}'")
        
        # Remove page from the end
        if reporter_part.endswith(page_str):
            reporter_part = reporter_part[:-len(page_str)].strip()
        print(f"  After removing page: '{reporter_part}'")
        
        # Clean up any extra spaces in the reporter
        reporter_part = re.sub(r'\s+', ' ', reporter_part).strip()
        print(f"  After cleaning spaces: '{reporter_part}'")
        
        citation = f"{volume_str} {reporter_part} {page_str}"
        print(f"  Final citation: '{citation}'")
        
    else:
        print("✗ Pattern did not match")

if __name__ == "__main__":
    test_reporter_extraction() 