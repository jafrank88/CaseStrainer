#!/usr/bin/env python3

def test_extraction_fixes():
    """Test the improved extraction architecture with problematic citations."""
    
    print("🔍 EXTRACTION FIXES TEST")
    print("=" * 50)
    
    # Test cases based on our investigation
    test_cases = [
        {
            "name": "String Citation - McFarland v. Tompkins",
            "citation": "567 P.3d 1128",
            "context": "Generally, one must be protected by the provision of a statute to gain standing to sue for a violation of the provision. McFarland v. Tompkins, 34 Wn. App. 2d 280, 301, 567 P.3d 1128 (2025). We typically interpret statutes to avoid any question about their constitutionality.",
            "expected": "McFarland v. Tompkins",
            "issue": "String citation parsing"
        },
        {
            "name": "Complex Organizational Name - Fraternal Order",
            "citation": "59 P.3d 655",
            "context": "Tingey v. Haisch, 159 Wn.2d 652, 663-64, 152 P.3d 1020 (2007) (quoting Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002)). It will not be presumed that the legislature intended absurd results.",
            "expected": "Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles",
            "issue": "Complex organizational name with abbreviations and numbers"
        },
        {
            "name": "Corporate Truncation Test - Spokeo Example",
            "citation": "578 U.S. 330",
            "context": "The Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016), that Article III standing requires both injury in fact and concrete harm.",
            "expected": "Spokeo, Inc. v. Robins",
            "issue": "Corporate name truncation prevention"
        }
    ]
    
    try:
        from src.unified_extraction_architecture import extract_case_name_and_year_unified
        import re
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📖 TEST {i+1}: {test_case['name']}")
            print("=" * 40)
            
            citation = test_case['citation']
            context = test_case['context']
            expected = test_case['expected']
            issue = test_case['issue']
            
            print(f"Citation: {citation}")
            print(f"Issue: {issue}")
            print(f"Expected: '{expected}'")
            
            # Find citation position in context
            citation_pattern = citation.replace(".", r"\.").replace(" ", r"\s+")
            match = re.search(citation_pattern, context, re.IGNORECASE)
            
            if match:
                start_pos = match.start()
                end_pos = match.end()
                
                print(f"Position: {start_pos}-{end_pos}")
                
                try:
                    # Test the improved extraction
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
                    
                    print(f"✅ Result: '{extracted_name}'")
                    print(f"   Confidence: {confidence}")
                    print(f"   Method: {method}")
                    
                    # Evaluate the result
                    if extracted_name == expected:
                        print(f"   🎯 PERFECT MATCH!")
                        success = True
                    elif extracted_name != 'N/A' and (expected.lower() in extracted_name.lower() or extracted_name.lower() in expected.lower()):
                        print(f"   ⚠️  PARTIAL MATCH")
                        success = True
                    elif extracted_name == 'N/A':
                        print(f"   ❌ NO EXTRACTION")
                        success = False
                    else:
                        print(f"   ❌ MISMATCH")
                        success = False
                    
                    # Check for truncation issues
                    if extracted_name.startswith(('Inc.', 'Corp.', 'LLC', 'Ltd.')):
                        print(f"   🚨 TRUNCATION DETECTED: Case name starts with corporate suffix")
                        success = False
                    
                    print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
                    
                except Exception as e:
                    print(f"   ❌ Extraction error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ Citation not found in context")
        
        # Test the advanced cleaning function directly
        print(f"\n🧹 ADVANCED CLEANING TESTS")
        print("=" * 40)
        
        from src.unified_extraction_architecture import get_unified_extractor
        extractor = get_unified_extractor()
        
        cleaning_tests = [
            ("Inc. v. Robins", "Should be rejected as truncated"),
            ("Spokeo, Inc. v. Robins", "Should be kept as complete"),
            ("Corp. v. State", "Should be rejected as truncated"),
            ("Microsoft Corp. v. United States", "Should be kept as complete"),
            ("  The State v. Jones  ", "Should be cleaned"),
            ("Smith v. Jones,,,", "Should remove trailing punctuation")
        ]
        
        for test_name, description in cleaning_tests:
            cleaned = extractor._clean_case_name_advanced(test_name, debug=True)
            print(f"   '{test_name}' → '{cleaned}' ({description})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction_fixes()
