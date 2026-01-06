#!/usr/bin/env python3
"""
Test to check why a 100-page PDF is being processed synchronously.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.services.citation_service import CitationService

def test_pdf_routing():
    """Test the routing logic for a large PDF."""
    print("=== Testing PDF Routing Logic ===\n")
    
    # Create a citation service instance
    service = CitationService()
    
    # Simulate different text sizes to see routing behavior
    test_cases = [
        ("Small text", 1000, "Should be sync"),
        ("Medium text", 10000, "Could be sync or async depending on citations"),
        ("Large text", 60000, "Should be async"),
        ("Very large text", 200000, "Should be async"),
    ]
    
    for name, size, expected in test_cases:
        # Create text with estimated citation density
        # Assume 1 citation per 10KB as a baseline
        estimated_citations = max(1, size // 10000)
        
        # Create dummy text with that many citations
        text = "Test document. " * (size // 20)
        # Add some citations
        for i in range(estimated_citations):
            text += f" {i+1} U.S. {i+100}. "
        
        print(f"\n{name}: {size:,} bytes, ~{estimated_citations} citations")
        print(f"Expected: {expected}")
        
        # Test routing
        mode = service.determine_processing_mode(text)
        print(f"Actual: {mode}")
        
        # Check thresholds
        print(f"  - Text size > 50KB? {size > 50000}")
        print(f"  - Citations >= 50? {estimated_citations >= 50}")
        print(f"  - COMPLEXITY_THRESHOLD = {service.COMPLEXITY_THRESHOLD}")
    
    # Test with actual PDF extraction scenario
    print("\n=== PDF Extraction Scenario ===")
    print("If a 100-page PDF (266KB) extracts to only 5KB of text:")
    small_text = "Extracted text. " * 250  # ~5KB
    small_text += " 1 U.S. 100. 2 U.S. 200. 3 U.S. 300."  # Add a few citations
    mode = service.determine_processing_mode(small_text)
    print(f"Result: {mode} (because extracted text is small)")
    
    print("\nIf the same PDF extracts to 60KB of text:")
    large_text = "Extracted text. " * 3000  # ~60KB
    for i in range(30):
        large_text += f" {i+1} U.S. {i+100}. "
    mode = service.determine_processing_mode(large_text)
    print(f"Result: {mode} (because extracted text is large)")

if __name__ == "__main__":
    test_pdf_routing()
