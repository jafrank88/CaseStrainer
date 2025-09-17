"""
Test Case Name Extraction Fix
Tests the improved regex patterns for handling legal abbreviations.
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_regex_patterns():
    """Test the new regex patterns against problematic case names."""
    
    print("🔍 TESTING IMPROVED CASE NAME EXTRACTION PATTERNS")
    print("=" * 60)
    
    # Test cases from your examples
    test_cases = [
        {
            'text': '"Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)"',
            'expected': 'Rest. Dev., Inc. v. Cananwill, Inc.',
            'description': 'Restaurant Development abbreviation case'
        },
        {
            'text': '"Lucid Grp. USA, Inc. v. Dep\'t of Licensing, 33 Wn. App. 2d 75, 81, 559 P.3d 545 (2024)"',
            'expected': 'Lucid Grp. USA, Inc. v. Dep\'t of Licensing',
            'description': 'Lucid Group abbreviation case'
        },
        {
            'text': '"Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011)"',
            'expected': 'Five Corners Fam. Farmers v. State',
            'description': 'Family Farmers abbreviation case'
        },
        {
            'text': '"Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)"',
            'expected': 'Bostain v. Food Express, Inc.',
            'description': 'Standard corporate case'
        }
    ]
    
    # New improved patterns
    patterns = [
        {
            'name': 'legal_abbreviation_comprehensive',
            'pattern': r'([A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*(?:\s+[A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*)*(?:\s*,\s*Inc\.|\s*,\s*LLC|\s*,\s*Corp\.|\s*Inc\.|\s*LLC|\s*Corp\.)?)\s+v\.\s+([A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*(?:\s+[A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*)*(?:\s*,\s*Inc\.|\s*,\s*LLC|\s*,\s*Corp\.|\s*Inc\.|\s*LLC|\s*Corp\.)?)',
            'confidence': 0.99
        },
        {
            'name': 'abbreviation_aware_pattern',
            'pattern': r'([A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*(?:\s+[A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*)*(?:\s*,\s*Inc\.|\s*Inc\.)?)\s+v\.\s+([A-Z][a-zA-Z\']*(?:\s+[A-Z][a-zA-Z\']*)*(?:\s*,\s*Inc\.|\s*Inc\.)?)',
            'confidence': 0.98
        },
        {
            'name': 'department_aware_pattern',
            'pattern': r'([A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*(?:\s+[A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]*)*)*(?:\s*,\s*Inc\.|\s*Inc\.)?)\s+v\.\s+([A-Z][a-zA-Z\']*(?:\s+[A-Z][a-zA-Z\']*)*(?:\s*of\s+[A-Z][a-zA-Z]*)?)',
            'confidence': 0.97
        }
    ]
    
    # Compile patterns
    for pattern in patterns:
        pattern['compiled'] = re.compile(pattern['pattern'], re.IGNORECASE)
    
    print(f"📋 Testing {len(test_cases)} case name extraction scenarios...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"TEST {i}: {test_case['description']}")
        print(f"Text: {test_case['text']}")
        print(f"Expected: {test_case['expected']}")
        
        best_match = None
        best_confidence = 0.0
        best_pattern = None
        
        for pattern in patterns:
            match = pattern['compiled'].search(test_case['text'])
            if match:
                case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                confidence = pattern['confidence']
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = case_name
                    best_pattern = pattern['name']
        
        if best_match:
            print(f"✅ Extracted: {best_match}")
            print(f"   Pattern: {best_pattern} (confidence: {best_confidence})")
            
            if best_match.strip() == test_case['expected'].strip():
                print(f"   🎯 PERFECT MATCH!")
            elif test_case['expected'].lower() in best_match.lower():
                print(f"   ✅ GOOD MATCH (contains expected)")
            else:
                print(f"   ❌ MISMATCH")
        else:
            print(f"❌ No match found")
        
        print("-" * 40)
        print()
    
    print("🧪 TESTING EDGE CASES")
    print("-" * 30)
    
    edge_cases = [
        '"Inc. v. Cananwill, Inc., 150 Wn.2d 674"',  # Current truncated version
        '"Corp. v. State, 123 Wn.2d 456"',           # Another truncated version
        '"LLC v. Dep\'t, 789 P.3d 123"'              # Department abbreviation
    ]
    
    for edge_case in edge_cases:
        print(f"Edge case: {edge_case}")
        
        best_match = None
        best_confidence = 0.0
        
        for pattern in patterns:
            match = pattern['compiled'].search(edge_case)
            if match:
                case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                confidence = pattern['confidence']
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = case_name
        
        if best_match:
            print(f"   Result: {best_match}")
        else:
            print(f"   No match (expected for truncated cases)")
        print()

def test_with_actual_extractor():
    """Test with the actual unified extractor."""
    
    print("🔧 TESTING WITH ACTUAL EXTRACTOR")
    print("=" * 40)
    
    try:
        from src.unified_case_name_extractor_v2 import get_unified_extractor
        
        extractor = get_unified_extractor()
        
        # Your actual text
        test_text = """
        "'[A] court must not add words where the legislature has
        chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
        2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
        674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)
        """
        
        citations_to_test = [
            "559 P.3d 545",
            "150 Wn.2d 674",
            "80 P.3d 598"
        ]
        
        for citation in citations_to_test:
            print(f"Testing citation: {citation}")
            result = extractor.extract_case_name_and_date(test_text, citation=citation, debug=True)
            
            print(f"  Extracted: '{result.case_name}'")
            print(f"  Confidence: {result.confidence}")
            print(f"  Method: {result.method}")
            print()
        
    except Exception as e:
        print(f"❌ Error testing with actual extractor: {e}")

if __name__ == "__main__":
    test_regex_patterns()
    print()
    test_with_actual_extractor()
