#!/usr/bin/env python3

def test_extraction_architecture():
    """Test the unified extraction architecture with problematic citations."""
    
    print("🔍 EXTRACTION ARCHITECTURE TEST")
    print("=" * 50)
    
    # Test cases based on the context we found
    test_cases = [
        {
            "citation": "567 P.3d 1128",
            "context": "Generally, one must be protected by the provision of a statute to gain standing to sue for a violation of the provision. McFarland v. Tompkins, 34 Wn. App. 2d 280, 301, 567 P.3d 1128 (2025). We typically interpret statutes",
            "expected": "McFarland v. Tompkins"
        },
        {
            "citation": "59 P.3d 655",
            "context": "Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002). It will not be presumed that the legislature intended absurd results.",
            "expected": "Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles"
        }
    ]
    
    try:
        for i, test_case in enumerate(test_cases):
            print(f"\n📖 TEST CASE {i+1}: {test_case['citation']}")
            print("=" * 40)
            
            citation = test_case['citation']
            context = test_case['context']
            expected = test_case['expected']
            
            # Find citation position in context
            import re
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            match = re.search(citation_pattern, context, re.IGNORECASE)
            
            if match:
                start_pos = match.start()
                end_pos = match.end()
                
                print(f"Context: {context}")
                print(f"Citation position: {start_pos}-{end_pos}")
                print(f"Expected case name: '{expected}'")
                
                # Test the unified extraction architecture directly
                try:
                    from src.unified_extraction_architecture import extract_case_name_and_year_unified
                    
                    result = extract_case_name_and_year_unified(
                        text=context,
                        citation=citation,
                        start_index=start_pos,
                        end_index=end_pos,
                        debug=True
                    )
                    
                    extracted_name = result.get('case_name', 'N/A')
                    confidence = result.get('confidence', 0.0)
                    method = result.get('method', 'unknown')
                    
                    print(f"✅ Extracted: '{extracted_name}'")
                    print(f"   Confidence: {confidence}")
                    print(f"   Method: {method}")
                    
                    # Compare with expected
                    if extracted_name == expected:
                        print(f"   ✅ PERFECT MATCH")
                    elif expected.lower() in extracted_name.lower() or extracted_name.lower() in expected.lower():
                        print(f"   ⚠️  PARTIAL MATCH")
                    else:
                        print(f"   ❌ MISMATCH")
                        
                    # Show detailed result
                    print(f"   Full result: {result}")
                    
                except Exception as e:
                    print(f"   ❌ Extraction error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ Citation not found in context")
        
        # Test with the master extraction function
        print(f"\n🔧 TESTING MASTER EXTRACTION FUNCTION")
        print("=" * 40)
        
        from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
        
        for i, test_case in enumerate(test_cases):
            print(f"\n   Test {i+1}: {test_case['citation']}")
            
            citation = test_case['citation']
            context = test_case['context']
            expected = test_case['expected']
            
            # Find citation position
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            match = re.search(citation_pattern, context, re.IGNORECASE)
            
            if match:
                start_pos = match.start()
                end_pos = match.end()
                
                try:
                    result = extract_case_name_and_date_master(
                        text=context,
                        citation=citation,
                        citation_start=start_pos,
                        citation_end=end_pos,
                        debug=True
                    )
                    
                    extracted_name = result.get('case_name', 'N/A')
                    print(f"      Master result: '{extracted_name}'")
                    
                except Exception as e:
                    print(f"      Master error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction_architecture()
