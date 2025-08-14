#!/usr/bin/env python3
"""
Test production readiness with various citation types
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_production_readiness():
    """Test various citation types that should work in production"""
    print("=" * 60)
    print("PRODUCTION READINESS TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Federal Supreme Court",
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954)"
        },
        {
            "name": "Federal Circuit Court", 
            "text": "United States v. Nixon, 418 F.2d 1234 (D.C. Cir. 1969)"
        },
        {
            "name": "State Court Citation",
            "text": "State v. Smith, 123 Wn.2d 456, 789 P.3d 012 (2020)"
        },
        {
            "name": "Multiple Citations",
            "text": "See Brown v. Board, 347 U.S. 483 (1954); Miranda v. Arizona, 384 U.S. 436 (1966)."
        },
        {
            "name": "Parallel Citations",
            "text": "Gideon v. Wainwright, 372 U.S. 335, 83 S. Ct. 792, 9 L. Ed. 2d 799 (1963)"
        }
    ]
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        config = ProcessingConfig()
        config.enable_verification = False  # Test extraction only first
        config.debug_mode = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        print("✓ Processor initialized")
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}:")
            print(f"   Text: {test_case['text']}")
            
            try:
                result = processor.process_text(test_case['text'])
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                if citations:
                    print(f"   ✓ Found {len(citations)} citations")
                    for j, citation in enumerate(citations):
                        print(f"     Citation {j+1}: {citation.citation}")
                else:
                    print(f"   ✗ No citations found")
                    all_passed = False
                    
                if clusters:
                    print(f"   ✓ Found {len(clusters)} clusters")
                else:
                    print(f"   ⚠ No clusters found (may be normal for single citations)")
                    
            except Exception as e:
                print(f"   ✗ Error: {e}")
                all_passed = False
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("PRODUCTION READINESS SUMMARY")
        print("=" * 60)
        
        if all_passed:
            print("🟢 READY FOR PRODUCTION TESTING")
            print("✓ All test cases passed")
            print("✓ Extraction pipeline working")
            print("✓ No critical errors")
        else:
            print("🔴 NOT READY FOR PRODUCTION")
            print("✗ Some test cases failed")
            print("✗ Need additional fixes")
            
        return all_passed
        
    except Exception as e:
        print(f"✗ Critical error in production readiness test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_production_readiness()
