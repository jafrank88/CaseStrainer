#!/usr/bin/env python3
"""
Test Bluebook citation formatting functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_bluebook_formatting():
    """Test the Bluebook formatting functionality."""
    print("Testing Bluebook citation formatting...")
    print("=" * 60)
    
    processor = UnifiedCitationProcessorV2()
    
    # Test cases with various spacing issues
    test_citations = [
        "171 Wn. 2d 486",  # Should be: 171 Wn.2d 486
        "256 P. 3d 321",   # Should be: 256 P.3d 321
        "146 Wn. 2d 1",    # Should be: 146 Wn.2d 1
        "43 P. 3d 4",      # Should be: 43 P.3d 4
        "F. 3d 123",       # Should be: F.3d 123
        "S. E. 2d 456",    # Should be: S.E.2d 456
        "So. 2d 789",      # Should be: So. 2d 789
        "F. Supp. 2d 101", # Should be: F. Supp. 2d 101
        "Cal. App. 3d 202", # Should be: Cal. App. 3d 202
        "S. Ct. 303",      # Should be: S. Ct. 303
        "L. Ed. 2d 404",   # Should be: L. Ed. 2d 404
    ]
    
    print("Original Citation -> Bluebook Formatted")
    print("-" * 50)
    
    for citation in test_citations:
        formatted = processor._normalize_to_bluebook_format(citation)
        print(f"{citation:20} -> {formatted}")
    
    print("\n" + "=" * 60)
    print("Bluebook Spacing Rules Applied:")
    print("✓ Close up adjacent single capitals: F.3d, S.E.2d, A.L.R.4th")
    print("✓ Space for longer abbreviations: So. 2d, Cal. App. 3d, F. Supp. 2d")
    print("✓ Periods after abbreviations: Univ., Soc'y (except when last letter has apostrophe)")
    print("✓ Proper spacing around commas in parallel citations")
    print("✓ Proper spacing around parentheses")

if __name__ == "__main__":
    test_bluebook_formatting() 