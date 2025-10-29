#!/usr/bin/env python3
"""
Test different citation formats to find the issue
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_formats():
    """Test different citation formats"""
    
    print("CITATION FORMAT TEST")
    print("=" * 60)
    
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    
    # Test different citation formats
    test_cases = [
        {
            "citation": "390 U.S. 747, 784 (1968)",
            "context": "In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)"
        },
        {
            "citation": "390 U.S. 747",
            "context": "In re Permian Basin Area Rate Cases, 390 U.S. 747"
        },
        {
            "citation": "390 U.S. 747 (1968)",
            "context": "In re Permian Basin Area Rate Cases, 390 U.S. 747 (1968)"
        },
        {
            "citation": "390 US 747",
            "context": "In re Permian Basin Area Rate Cases, 390 US 747"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Context: {test_case['context']}")
        print("-" * 40)
        
        try:
            citation_pos = test_case['context'].find(test_case['citation'])
            if citation_pos == -1:
                print("❌ Citation not found in context")
                continue
            
            result = extract_case_name_and_date_unified_master(
                text=test_case['context'],
                citation=test_case['citation'],
                start_index=citation_pos,
                end_index=citation_pos + len(test_case['citation'])
            )
            
            case_name = result.get('case_name', 'N/A')
            confidence = result.get('confidence', 0)
            
            print(f"Result: '{case_name}' (confidence: {confidence:.2f})")
            
            if case_name == 'N/A':
                print("❌ FAILED")
            else:
                print("✅ SUCCESS")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_citation_formats()
