#!/usr/bin/env python3
"""
Test script to debug Washington Court of Appeals citation extraction
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_citation_extraction():
    """Test citation extraction with the problematic text"""
    
    # Test text from the user
    test_text = """We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"""
    
    print("🔍 Testing Citation Extraction")
    print("=" * 50)
    print(f"Test text length: {len(test_text)} characters")
    print(f"Test text: {test_text}")
    print()
    
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    # Test individual patterns
    print("🔍 Testing Individual Patterns")
    print("-" * 30)
    
    # Test Washington Court of Appeals patterns
    wn_app_pattern = re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE)
    wn_app_space_pattern = re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE)
    wash_app_pattern = re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE)
    wash_app_space_pattern = re.compile(r'\b(\d+)\s+Wash\.\s*App\s+(\d+)\b', re.IGNORECASE)
    
    patterns_to_test = [
        ('wn_app', wn_app_pattern),
        ('wn_app_space', wn_app_space_pattern),
        ('wash_app', wash_app_pattern),
        ('wash_app_space', wash_app_space_pattern)
    ]
    
    for pattern_name, pattern in patterns_to_test:
        matches = list(pattern.finditer(test_text))
        print(f"{pattern_name}: {len(matches)} matches")
        for match in matches:
            print(f"  - Match: '{match.group(0)}' at positions {match.start()}-{match.end()}")
    
    print()
    
    # Test the full extraction
    print("🔍 Testing Full Citation Extraction")
    print("-" * 40)
    
    try:
        # Process the text using the regex extraction directly
        citations = processor._extract_with_regex(test_text)
        
        print(f"Citations found: {len(citations)}")
        
        # Show all citations
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Text: {citation.citation}")
            print(f"  Method: {citation.method}")
            print(f"  Pattern: {citation.pattern}")
            print(f"  Start: {citation.start_index}, End: {citation.end_index}")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_extraction()
