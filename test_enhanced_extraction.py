#!/usr/bin/env python3
"""
Test the enhanced extraction with "In re" fallback
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_extraction():
    """Test the enhanced extraction with fallback"""
    
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    
    print("ENHANCED EXTRACTION TEST WITH 'IN RE' FALLBACK")
    print("=" * 60)
    
    # Test cases that should trigger the fallback
    test_cases = [
        {
            "name": "Standard In re case",
            "citation": "390 U.S. 747, 784 (1968)",
            "context": "In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)"
        },
        {
            "name": "In re with parentheses",
            "citation": "390 U.S. 747",
            "context": "(quoting In re Permian Basin Area Rate Cases, 390 U.S. 747)"
        },
        {
            "name": "Complex context",
            "citation": "390 U.S. 747, 784 (1968)",
            "context": """Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Citation: {test_case['citation']}")
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
                end_index=citation_pos + len(test_case['citation']),
                debug=True  # Enable debug to see fallback in action
            )
            
            case_name = result.get('case_name', 'N/A')
            confidence = result.get('confidence', 0)
            method = result.get('method', 'N/A')
            
            print(f"✅ Result: '{case_name}'")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Method: {method}")
            
            if case_name == 'N/A':
                print("❌ STILL FAILED - Even with fallback")
            else:
                print("✅ SUCCESS - Extraction working")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_extraction()
