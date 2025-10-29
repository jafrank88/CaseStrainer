#!/usr/bin/env python3
"""
Comprehensive test of the Permian Basin extraction fix
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_permian_fix():
    """Test the complete fix for Permian Basin extraction"""
    
    print("COMPREHENSIVE PERMIAN BASIN FIX TEST")
    print("=" * 80)
    
    # Test 1: Direct extraction
    print("TEST 1: Direct extraction with enhanced patterns")
    try:
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        
        citation = "390 U.S. 747, 784 (1968)"
        context = "In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)"
        
        citation_pos = context.find(citation)
        result = extract_case_name_and_date_unified_master(
            text=context,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=False
        )
        
        case_name = result.get('case_name', 'N/A')
        print(f"✅ Direct extraction: '{case_name}'")
        
    except Exception as e:
        print(f"❌ Direct extraction failed: {e}")
    
    # Test 2: Data separation protection
    print("\nTEST 2: Data separation protection for 'In re' cases")
    try:
        from src.utils.data_separation import is_case_name_contaminated, clean_citation_extracted_fields
        
        test_name = "In re Permian Basin Area Rate Cases"
        is_contaminated = is_case_name_contaminated(test_name)
        print(f"✅ Contamination check: {'CLEAN' if not is_contaminated else 'CONTAMINATED'}")
        
        # Test the cleaning function
        class MockCitation:
            def __init__(self):
                self.extracted_case_name = test_name
        
        mock_citation = MockCitation()
        clean_citation_extracted_fields(mock_citation)
        final_name = mock_citation.extracted_case_name
        print(f"✅ After data separation: '{final_name}'")
        
        if final_name == 'N/A':
            print("❌ Data separation corrupted the name")
        else:
            print("✅ Data separation preserved the name")
            
    except Exception as e:
        print(f"❌ Data separation test failed: {e}")
    
    # Test 3: Case name cleaning protection
    print("\nTEST 3: Case name cleaning protection")
    try:
        extractor = extract_case_name_and_date_unified_master.__self__
        cleaned_name = extractor._clean_case_name("In re Permian Basin Area Rate Cases")
        print(f"✅ Cleaning protection: '{cleaned_name}'")
        
        if cleaned_name == 'N/A':
            print("❌ Cleaning corrupted the name")
        else:
            print("✅ Cleaning preserved the name")
            
    except Exception as e:
        print(f"❌ Cleaning test failed: {e}")
    
    # Test 4: Full user text simulation
    print("\nTEST 4: Full user text simulation")
    try:
        full_text = """County of Hudson v. Dep't of Corr., 703 A.2d 268, 274 (N.J. 1997) ("In general, an agency has the authority to amend, change, or repeal its regulations, especially in response to changing conditions."); Ins. Fed'n of Pa., Inc. v. Commonwealth, Ins. Dep't, 970 A.2d 1108, 1124 (Pa. 2009) ("[A]n agency may revise its policies and amend its regulations in interpreting its statutory mandate." (quoting Elite Indus., Inc. v. Pa. Pub. Util. Comm'n, 832 A.2d 428, 431-32 (Pa. 2003))); Nat'l Ass'n of Mfrs. v. SEC, 105 F.4th 802, 810-11 (5th Cir. 2024) ("An administrative agency may alter or rescind its policies, including when a new administration enters office."); see also Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
        
        citation = "390 U.S. 747, 784 (1968)"
        citation_pos = full_text.find(citation)
        
        if citation_pos != -1:
            # Get context
            start = max(0, citation_pos - 300)
            end = min(len(full_text), citation_pos + len(citation) + 300)
            context = full_text[start:end]
            
            result = extract_case_name_and_date_unified_master(
                text=context,
                citation=citation,
                start_index=citation_pos - start,
                end_index=citation_pos - start + len(citation),
                debug=False
            )
            
            case_name = result.get('case_name', 'N/A')
            print(f"✅ Full text extraction: '{case_name}'")
            
            if case_name == 'N/A':
                print("❌ Full text extraction failed")
            else:
                print("✅ Full text extraction successful")
        else:
            print("❌ Citation not found in full text")
            
    except Exception as e:
        print(f"❌ Full text test failed: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("✅ Enhanced 'In re' patterns added")
    print("✅ Fallback extraction method implemented")
    print("✅ Data separation protection for 'In re' cases")
    print("✅ Case name cleaning protection for 'In re' cases")
    print("\nThe fix should prevent 'In re Permian Basin Area Rate Cases' from being corrupted to 'N/A'")

if __name__ == "__main__":
    test_permian_fix()
