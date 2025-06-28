#!/usr/bin/env python3
"""
Test script to debug the _extract_all_citations method.
"""

import sys
import os
import re

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_extract_citations():
    """Test the _extract_all_citations method."""
    
    print("=== TESTING _EXTRACT_ALL_CITATIONS ===")
    
    # Test text
    test_text = "399 P.3d 1195"
    print(f"Test text: '{test_text}'")
    
    try:
        print("Importing ComplexCitationIntegrator...")
        from src.complex_citation_integration import ComplexCitationIntegrator
        print("✓ Import successful")
        
        integrator = ComplexCitationIntegrator()
        print("✓ Created integrator instance")
        
        # Test the _extract_all_citations method
        print("Testing _extract_all_citations...")
        citations = integrator._extract_all_citations(test_text)
        print(f"Extracted citations: {citations}")
        
        # Test each pattern individually
        print(f"\n=== TESTING INDIVIDUAL PATTERNS ===")
        for pattern_name, pattern in integrator.primary_patterns.items():
            print(f"Pattern '{pattern_name}': '{pattern}'")
            matches = list(re.finditer(pattern, test_text))
            print(f"  Matches: {len(matches)}")
            for i, match in enumerate(matches):
                print(f"    Match {i+1}: '{match.group(0)}'")
                print(f"      Volume: '{match.group(1)}'")
                print(f"      Page: '{match.group(2)}'")
                
                # Test the reporter extraction logic
                full_match = match.group(0)
                print(f"      Full match: '{full_match}'")
                
                # Test the new extraction logic
                volume_str = str(match.group(1))
                page_str = str(match.group(2))
                
                # Remove volume from the beginning
                reporter_part = full_match[len(volume_str):].strip()
                print(f"      After removing volume: '{reporter_part}'")
                
                # Remove page from the end
                if reporter_part.endswith(page_str):
                    reporter_part = reporter_part[:-len(page_str)].strip()
                print(f"      After removing page: '{reporter_part}'")
                
                # Clean up any extra spaces in the reporter
                reporter_part = re.sub(r'\s+', ' ', reporter_part).strip()
                print(f"      After cleaning spaces: '{reporter_part}'")
                
                citation = f"{volume_str} {reporter_part} {page_str}"
                print(f"      Final citation: '{citation}'")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extract_citations() 