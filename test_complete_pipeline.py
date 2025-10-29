#!/usr/bin/env python3
"""
Test the complete pipeline to find where the N/A is coming from
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_complete_pipeline():
    """Test the complete processing pipeline"""
    
    # The exact problematic text
    text = """Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
    
    print("COMPLETE PIPELINE TEST")
    print("=" * 80)
    print(f"Text length: {len(text)}")
    print()
    
    # Test step by step
    
    # Step 1: Citation extraction
    print("STEP 1: Citation extraction")
    try:
        # Simple regex to find citations
        citation_pattern = r'\d+\s+[A-Z\.]+\s+\d+(?:,\s+\d+)?(?:\s+\(\d{4}\))?'
        citations = re.findall(citation_pattern, text)
        print(f"Found citations: {citations}")
        
        # Look for our target citation
        target = "390 U.S. 747, 784 (1968)"
        if target in citations:
            print("✅ Target citation found in text")
        else:
            print("❌ Target citation not found")
            
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
    
    print()
    
    # Step 2: Case name extraction
    print("STEP 2: Case name extraction")
    try:
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        
        citation_pos = text.find(target)
        if citation_pos != -1:
            # Get context
            start = max(0, citation_pos - 300)
            end = min(len(text), citation_pos + len(target) + 300)
            context = text[start:end]
            
            result = extract_case_name_and_date_unified_master(
                text=context,
                citation=target,
                start_index=citation_pos - start,
                end_index=citation_pos - start + len(target)
            )
            
            extracted_name = result.get('case_name', 'N/A')
            print(f"Extracted case name: '{extracted_name}'")
            
            if extracted_name == 'N/A':
                print("❌ EXTRACTION FAILED - Got N/A")
            else:
                print("✅ Extraction successful")
                
        else:
            print("❌ Citation not found for extraction")
            
    except Exception as e:
        print(f"❌ Case name extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 3: Verification
    print("STEP 3: Verification")
    try:
        from src.courtlistener_verification import verify_with_courtlistener
        
        result = verify_with_courtlistener("390 U.S. 747", "In re Permian Basin Area Rate Cases")
        
        canonical_name = result.get('canonical_name', 'N/A')
        print(f"Canonical name: '{canonical_name}'")
        print(f"Verification status: {result.get('status', 'N/A')}")
        
        if canonical_name == 'N/A':
            print("❌ VERIFICATION FAILED - Got N/A")
        else:
            print("✅ Verification successful")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    
    print()
    
    # Step 4: Data separation check
    print("STEP 4: Data separation check")
    try:
        from src.utils.data_separation import is_case_name_contaminated, clean_citation_extracted_fields
        
        test_name = "In re Permian Basin Area Rate Cases"
        is_contaminated = is_case_name_contaminated(test_name)
        print(f"Is '{test_name}' contaminated? {is_contaminated}")
        
        # Create a mock citation object
        class MockCitation:
            def __init__(self):
                self.extracted_case_name = test_name
        
        mock_citation = MockCitation()
        clean_citation_extracted_fields(mock_citation)
        
        final_name = mock_citation.extracted_case_name
        print(f"After data separation: '{final_name}'")
        
        if final_name == 'N/A':
            print("❌ DATA SEPARATION CORRUPTED THE NAME")
        else:
            print("✅ Data separation preserved the name")
            
    except Exception as e:
        print(f"❌ Data separation test failed: {e}")

if __name__ == "__main__":
    import re
    test_complete_pipeline()
