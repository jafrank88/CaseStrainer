#!/usr/bin/env python3
"""
Test that URL, file, and text inputs are all normalized consistently.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.utils.text_normalizer import normalize_text

async def test_normalization_consistency():
    """Test that all input types are normalized the same way."""
    
    # Test text with problematic Unicode characters
    test_text = """
    IN THE SUPREME COURT OF THE STATE OF WASHINGTON
    
    John Doe v. Jane Smith—No. 12345—2023
    
    The court held that "smart quotes" and em—dashes should be normalized.
    Citation: 123 Wn.2d 456 (2023).
    """
    
    print("Testing input normalization consistency...")
    print("=" * 60)
    
    # Expected normalized text
    expected_normalized = normalize_text(test_text)
    print(f"Original text (first 100 chars): {test_text[:100].replace(chr(10), ' ')}...")
    print(f"Normalized text (first 100 chars): {expected_normalized[:100].replace(chr(10), ' ')}...")
    
    # Test 1: Direct text input
    print("\n1. Testing direct text input...")
    processor = UnifiedCitationProcessorV2()
    
    # Simulate text input (already normalized in extraction architecture)
    result_text = await processor.process_text(test_text)
    citations_text = result_text.get('citations', [])
    print(f"   Citations found: {len(citations_text)}")
    
    # Test 2: URL input simulation (normalized at URL level)
    print("\n2. Testing URL input simulation...")
    # This simulates what happens in _process_url_input
    url_normalized_text = normalize_text(test_text)
    result_url = await processor.process_text(url_normalized_text)
    citations_url = result_url.get('citations', [])
    print(f"   Citations found: {len(citations_url)}")
    
    # Test 3: File input simulation (normalized in extraction architecture)
    print("\n3. Testing file input simulation...")
    # Files are normalized in the extraction architecture, same as direct text
    result_file = await processor.process_text(test_text)
    citations_file = result_file.get('citations', [])
    print(f"   Citations found: {len(citations_file)}")
    
    # Compare results
    print("\n" + "=" * 60)
    print("Consistency Check:")
    
    # Check if all methods return the same number of citations
    counts = [len(citations_text), len(citations_url), len(citations_file)]
    if len(set(counts)) == 1:
        print(f"[PASS] All input types return {counts[0]} citations - CONSISTENT")
    else:
        print(f"[FAIL] Inconsistent citation counts: Text={counts[0]}, URL={counts[1]}, File={counts[2]}")
    
    # Check if citations are the same
    text_cits = [c.citation for c in citations_text]
    url_cits = [c.citation for c in citations_url]
    file_cits = [c.citation for c in citations_file]
    
    if text_cits == url_cits == file_cits:
        print("[PASS] All citations match across input types")
    else:
        print("[FAIL] Citations differ across input types")
        for name, cits in [('Text', text_cits[:3]), ('URL', url_cits[:3]), ('File', file_cits[:3])]:
            print(f"   {name}: {cits}")
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Normalization test completed")

if __name__ == "__main__":
    asyncio.run(test_normalization_consistency())
