#!/usr/bin/env python3
"""
Test script to verify citation parsing for regional reporters with series indicators.
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.citation_utils import extract_citations_from_text
from citation_verification import CitationVerifier

def test_regional_reporter_parsing():
    """Test that regional reporters with series indicators are parsed correctly."""
    
    # Test cases for regional reporters (valid and invalid)
    test_cases = [
        # Valid
        "123 N.E.2d 456",  # Northeastern Reporter, 2d Series
        "456 N.W.3d 789",  # Northwestern Reporter, 3d Series
        "789 S.E.4th 123",  # Southeastern Reporter, 4th Series
        "321 S.W.5th 654",  # Southwestern Reporter, 5th Series
        "45 A.7th 999",     # Atlantic Reporter, 7th Series
        "181 Wash.2d 123",  # Washington Reports, 2d Series
        "22 Cal.4th 1000",  # California Reports, 4th Series
        "397 So.2d 456",    # Southern Reporter, 2d Series
        "246 S.E.6th 888",  # Southeastern Reporter, 6th Series
        "333 P.3d 111",     # Pacific Reporter, 3d Series
        # Invalid/partial (should NOT match)
        "181 Wash.2",       # Invalid (missing 'd' and page)
        "45 A.3",           # Invalid (missing 'd' and page)
        "789 S.E.4",        # Invalid (missing 'th' and page)
        "321 S.W.5",        # Invalid (missing 'th' and page)
        "397 So. 2",        # Invalid (missing 'd' and page)
        "333 P. 3",         # Invalid (missing 'd' and page)
        "246 S.E.6",        # Invalid (missing 'th' and page)
    ]

    expected_valid = [
        "123 N.E.2d 456",
        "456 N.W.3d 789",
        "789 S.E.4th 123",
        "321 S.W.5th 654",
        "45 A.7th 999",
        "181 Wash.2d 123",
        "22 Cal.4th 1000",
        "397 So.2d 456",
        "246 S.E.6th 888",
        "333 P.3d 111",
    ]

    text = "\n".join(test_cases)
    found = extract_citations_from_text(text)
    print("Extracted:", found)
    for citation in expected_valid:
        assert citation in found, f"Should extract: {citation}"
    for citation in test_cases:
        if citation not in expected_valid:
            assert citation not in found, f"Should NOT extract: {citation}"
    print("All tests passed.")

def test_mixed_text():
    """Test extraction from text containing multiple citations."""
    
    test_text = """
    The court in 123 N.E.2d 456 held that the plaintiff failed to state a claim.
    In 456 N.W.2d 789, the court reached a different conclusion.
    The case of 789 S.E.2d 123 established important precedent.
    Additionally, 321 S.W.2d 654 provided guidance on this issue.
    """
    
    print("Testing extraction from mixed text...")
    print("=" * 50)
    print(f"Text: {test_text.strip()}")
    print()
    
    extracted = extract_citations_from_text(test_text)
    print(f"Extracted citations: {extracted}")
    
    expected_citations = [
        "123 N.E.2d 456",
        "456 N.W.2d 789", 
        "789 S.E.2d 123",
        "321 S.W.2d 654"
    ]
    
    print()
    print("Verification:")
    for expected in expected_citations:
        if expected in extracted:
            print(f"  ✓ {expected}")
        else:
            print(f"  ✗ {expected} (missing)")

if __name__ == "__main__":
    print("Citation Parsing Test")
    print("=" * 50)
    print()
    
    test_regional_reporter_parsing()
    print()
    test_mixed_text()
    
    print()
    print("Test completed!") 