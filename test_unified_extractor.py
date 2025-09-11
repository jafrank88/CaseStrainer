#!/usr/bin/env python3
"""
Test script for the new Unified Case Name Extractor V2
Tests the problematic cases that were causing truncation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_extractor():
    """Test the new unified extractor with problematic cases"""
    
    try:
        from src.unified_case_name_extractor_v2 import get_unified_extractor, ExtractionStrategy
        
        print("🧪 Testing Unified Case Name Extractor V2")
        print("=" * 60)
        
        # Get the unified extractor
        extractor = get_unified_extractor()
        
        # Test case 1: The problematic "DeSean v. Sanger" case
        test_text_1 = '''We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 
329, 334-35, 536 P.3d 191 (2023). "The goal of statutory interpretation is to give 
effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. In determining 
the plain meaning of a statute, we look to the text of the statute, as well as its 
broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 
815, 820, 239 P.3d 354 (2010). Only if the plain text is susceptible to more than 
one interpretation do we turn to statutory construction, legislative history, and 
relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820.'''
        
        citation_1 = "2 Wn. 3d 329"
        citation_2 = "169 Wn.2d 815"
        
        print(f"\n📝 Test Text 1: {test_text_1[:100]}...")
        print(f"🔍 Citation 1: {citation_1}")
        print(f"🔍 Citation 2: {citation_2}")
        
        # Test extraction for first citation
        print(f"\n🔍 Testing extraction for '{citation_1}':")
        result_1 = extractor.extract_case_name_and_date(
            text=test_text_1,
            citation=citation_1,
            debug=True
        )
        
        print(f"✅ Result 1: '{result_1.case_name}' (confidence: {result_1.confidence:.2f}, method: {result_1.method})")
        print(f"📅 Date: {result_1.date}, Year: {result_1.year}")
        print(f"🎯 Strategy: {result_1.strategy.value}")
        
        # Test extraction for second citation
        print(f"\n🔍 Testing extraction for '{citation_2}':")
        result_2 = extractor.extract_case_name_and_date(
            text=test_text_1,
            citation=citation_2,
            debug=True
        )
        
        print(f"✅ Result 2: '{result_2.case_name}' (confidence: {result_2.confidence:.2f}, method: {result_2.method})")
        print(f"📅 Date: {result_2.date}, Year: {result_2.year}")
        print(f"🎯 Strategy: {result_2.strategy.value}")
        
        # Test case 2: "Dep't of Ecology v. Campbell & Gwinn, LLC"
        test_text_2 = '''We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).'''
        citation_3 = "146 Wn.2d 1"
        
        print(f"\n📝 Test Text 2: {test_text_2}")
        print(f"🔍 Citation 3: {citation_3}")
        
        result_3 = extractor.extract_case_name_and_date(
            text=test_text_2,
            citation=citation_3,
            debug=True
        )
        
        print(f"✅ Result 3: '{result_3.case_name}' (confidence: {result_3.confidence:.2f}, method: {result_3.method})")
        print(f"📅 Date: {result_3.date}, Year: {result_3.year}")
        print(f"🎯 Strategy: {result_3.strategy.value}")
        
        # Test case 3: "Convoyant, LLC v. DeepThink, LLC"
        test_text_3 = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).'''
        citation_4 = "200 Wn.2d 72"
        
        print(f"\n📝 Test Text 3: {test_text_3}")
        print(f"🔍 Citation 4: {citation_4}")
        
        result_4 = extractor.extract_case_name_and_date(
            text=test_text_3,
            citation=citation_4,
            debug=True
        )
        
        print(f"✅ Result 4: '{result_4.case_name}' (confidence: {result_4.confidence:.2f}, method: {result_4.method})")
        print(f"📅 Date: {result_4.date}, Year: {result_4.year}")
        print(f"🎯 Strategy: {result_4.strategy.value}")
        
        # Summary
        print(f"\n🎯 SUMMARY:")
        print(f"   Citation 1: '{citation_1}' → '{result_1.case_name}' (Expected: 'DeSean v. Sanger')")
        print(f"   Citation 2: '{citation_2}' → '{result_2.case_name}' (Expected: 'State v. Ervin')")
        print(f"   Citation 3: '{citation_3}' → '{result_3.case_name}' (Expected: 'Dep't of Ecology v. Campbell & Gwinn, LLC')")
        print(f"   Citation 4: '{citation_4}' → '{result_4.case_name}' (Expected: 'Convoyant, LLC v. DeepThink, LLC')")
        
        # Check if all expected results are correct
        expected_results = [
            ("DeSean v. Sanger", result_1.case_name),
            ("State v. Ervin", result_2.case_name),
            ("Dep't of Ecology v. Campbell & Gwinn, LLC", result_3.case_name),
            ("Convoyant, LLC v. DeepThink, LLC", result_4.case_name)
        ]
        
        all_correct = True
        for expected, actual in expected_results:
            if expected not in actual and actual not in expected:
                print(f"❌ FAIL: Expected '{expected}', got '{actual}'")
                all_correct = False
            else:
                print(f"✅ PASS: '{expected}' matches '{actual}'")
        
        if all_correct:
            print(f"\n🎉 ALL TESTS PASSED! The unified extractor is working correctly.")
        else:
            print(f"\n❌ SOME TESTS FAILED. The unified extractor needs more work.")
        
        return all_correct
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the unified extractor is properly installed.")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_unified_extractor()
    sys.exit(0 if success else 1)
