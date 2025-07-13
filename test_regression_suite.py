#!/usr/bin/env python3
"""
Regression test suite for CaseStrainer citation extraction.
This ensures that changes don't break existing functionality.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

# Test documents with expected results
TEST_CASES = {
    "brief_1": {
        "text": """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)""",
        "expected_citations": 6,
        "expected_clusters": 3,
        "expected_cases": [
            "Convoyant, LLC v. DeepThink, LLC",
            "Carlson v. Glob. Client Sols., LLC", 
            "Dep't of Ecology v. Campbell & Gwinn, LLC"
        ]
    },
    
    "brief_2": {
        "text": """The plaintiff argues that the trial court erred in granting summary judgment. Smith v. Jones, 123 Wash. 2d 456, 789 P.2d 123 (1990). However, this court has held that summary judgment is appropriate when there are no genuine issues of material fact. Brown v. White, 456 Wash. 2d 789, 321 P.2d 456 (1995). The standard of review is de novo. Johnson v. Smith, 789 Wash. 2d 123, 654 P.2d 789 (2000).""",
        "expected_citations": 3,
        "expected_clusters": 3,
        "expected_cases": [
            "Smith v. Jones",
            "Brown v. White",
            "Johnson v. Smith"
        ]
    },
    
    "brief_3": {
        "text": """In this case, the defendant violated RCW 9A.20.021 by committing multiple offenses. The court should apply the rule from State v. Washington, 100 Wash. 2d 123, 456 P.2d 789 (1983). Additionally, the sentencing guidelines require consideration of State v. Oregon, 200 Wash. 2d 456, 789 P.2d 123 (1995).""",
        "expected_citations": 2,
        "expected_clusters": 2,
        "expected_cases": [
            "State v. Washington",
            "State v. Oregon"
        ]
    },
    
    "brief_4": {
        "text": """The appellant contends that the trial court's ruling was contrary to established precedent. In Westlaw citation format, this would be Smith v. Jones, 2023 WL 1234567 (Wash. Ct. App. 2023). The court should also consider Brown v. White, 2023 WL 7654321 (Wash. Ct. App. 2023).""",
        "expected_citations": 2,  # This should work after WL citation support is added
        "expected_clusters": 2,
        "expected_cases": [
            "Smith v. Jones",
            "Brown v. White"
        ],
        "notes": "This test case includes Westlaw (WL) citations that should be supported"
    }
}

def test_regression_suite():
    """Run the complete regression test suite."""
    print("🧪 RUNNING REGRESSION TEST SUITE")
    print("=" * 60)
    
    config = ProcessingConfig(debug_mode=False, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)
    
    all_passed = True
    
    for brief_name, test_case in TEST_CASES.items():
        print(f"\n📄 Testing {brief_name.upper()}:")
        print("-" * 40)
        
        # Process the text
        results = processor.process_text(test_case["text"])
        clusters = processor.group_citations_into_clusters(results)
        
        # Extract case names from results
        extracted_cases = []
        for citation in results:
            if citation.extracted_case_name:
                extracted_cases.append(citation.extracted_case_name)
        
        # Run assertions
        passed = True
        
        # Check citation count
        if len(results) != test_case["expected_citations"]:
            print(f"❌ Expected {test_case['expected_citations']} citations, got {len(results)}")
            passed = False
        else:
            print(f"✅ Citation count: {len(results)}")
        
        # Check cluster count
        if len(clusters) != test_case["expected_clusters"]:
            print(f"❌ Expected {test_case['expected_clusters']} clusters, got {len(clusters)}")
            passed = False
        else:
            print(f"✅ Cluster count: {len(clusters)}")
        
        # Check case names (basic check)
        if len(extracted_cases) < len(test_case["expected_cases"]):
            print(f"❌ Expected at least {len(test_case['expected_cases'])} case names, got {len(extracted_cases)}")
            passed = False
        else:
            print(f"✅ Case names extracted: {len(extracted_cases)}")
        
        # Show details
        print(f"  Citations found: {[c.citation for c in results]}")
        print(f"  Clusters: {len(clusters)}")
        print(f"  Case names: {extracted_cases}")
        
        if "notes" in test_case:
            print(f"  Note: {test_case['notes']}")
        
        if not passed:
            all_passed = False
        else:
            print(f"✅ {brief_name.upper()} PASSED")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL REGRESSION TESTS PASSED!")
        print("✅ No existing functionality was broken")
    else:
        print("❌ SOME REGRESSION TESTS FAILED!")
        print("⚠️  Existing functionality may have been broken")
    
    return all_passed

def test_edge_cases():
    """Test edge cases that should continue to work."""
    print(f"\n🔍 TESTING EDGE CASES")
    print("=" * 40)
    
    config = ProcessingConfig(debug_mode=False, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)
    
    edge_cases = [
        {
            "name": "Missing page numbers",
            "text": "See Smith v. Jones, 123 Wash. 2d 456 (1990)."
        },
        {
            "name": "Multiple reporters", 
            "text": "See Brown v. White, 456 Wash. 2d 789, 321 P.2d 456, 789 P.3d 123 (1995)."
        },
        {
            "name": "OCR errors/typos",
            "text": "See Johnson v. Smith, 789 Wash. 2d 123, 654 P.2d 789 (2000)."  # Normal case
        },
        {
            "name": "Statute citations",
            "text": "See RCW 9A.20.021 and RCW 2.60.020."
        }
    ]
    
    all_edge_cases_passed = True
    
    for edge_case in edge_cases:
        print(f"\nTesting: {edge_case['name']}")
        results = processor.process_text(edge_case["text"])
        
        if len(results) > 0:
            print(f"✅ Extracted {len(results)} citations")
        else:
            print(f"⚠️  No citations extracted (may be expected for statutes)")
        
        # Basic check - shouldn't crash
        try:
            clusters = processor.group_citations_into_clusters(results)
            print(f"✅ Clustering completed successfully")
        except Exception as e:
            print(f"❌ Clustering failed: {e}")
            all_edge_cases_passed = False
    
    return all_edge_cases_passed

if __name__ == "__main__":
    print("🚀 CaseStrainer Regression Test Suite")
    print("This ensures changes don't break existing functionality")
    
    regression_passed = test_regression_suite()
    edge_cases_passed = test_edge_cases()
    
    if regression_passed and edge_cases_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        sys.exit(1) 