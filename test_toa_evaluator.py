#!/usr/bin/env python3
"""
Test the TOA-Based Citation Evaluator
Demonstrates how using Table of Authorities solves the three main issues.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_based_citation_evaluator import ToABasedCitationEvaluator, evaluate_text_with_toa

def test_with_brief():
    """Test the TOA evaluator with a real brief."""
    print("=" * 80)
    print("TESTING TOA-BASED CITATION EVALUATOR")
    print("=" * 80)
    
    # Test with a brief that has a TOA section
    brief_file = "wa_briefs_text/004_COA Respondent Brief.txt"
    
    try:
        with open(brief_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✓ Loaded brief: {len(text):,} characters")
    except Exception as e:
        print(f"✗ Error loading brief: {e}")
        return
    
    # Test the TOA evaluator
    print("\n1. LOADING TOA FROM BRIEF...")
    evaluator = ToABasedCitationEvaluator()
    
    if evaluator.load_toa_from_text(text):
        print("✓ Successfully loaded TOA")
        
        # Show summary
        summary = evaluator.get_summary()
        print(f"   - Canonical cases: {summary['canonical_cases_count']}")
        print(f"   - Citation mappings: {summary['citation_mappings_count']}")
        
        # Show some canonical cases
        print("\n   Sample canonical cases:")
        for i, case in enumerate(summary['canonical_cases'][:5]):
            print(f"     {i+1}. {case['case_name']}")
            print(f"        Citations: {case['citations']}")
            print(f"        Years: {case['years']}")
        
        # Test with a paragraph from the brief
        print("\n2. TESTING CITATION EVALUATION...")
        
        # Find a paragraph with citations
        paragraphs = text.split('\n\n')
        test_paragraph = None
        
        for para in paragraphs:
            if 'Wn.' in para and len(para) > 100:
                test_paragraph = para
                break
        
        if test_paragraph:
            print(f"   Test paragraph: {test_paragraph[:200]}...")
            
            # Evaluate citations in this paragraph
            matches = evaluator.evaluate_citations_in_text(test_paragraph)
            
            print(f"\n   Found {len(matches)} citation matches:")
            for i, match in enumerate(matches):
                print(f"     {i+1}. Citation: {match.citation}")
                print(f"        Case: {match.case_name}")
                print(f"        Year: {match.year}")
                print(f"        Method: {match.method}")
                print(f"        Confidence: {match.confidence}")
        else:
            print("   No suitable test paragraph found")
            
    else:
        print("✗ Failed to load TOA")

def test_with_standard_paragraph():
    """Test with our standard test paragraph."""
    print("\n" + "=" * 80)
    print("TESTING WITH STANDARD TEST PARAGRAPH")
    print("=" * 80)
    
    # Standard test paragraph
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Test paragraph:")
    print(f"   {test_text}")
    
    # Since this doesn't have a TOA, we'll create a mock TOA with the expected cases
    mock_toa_text = """
    TABLE OF AUTHORITIES
    
    CASES CITED
    
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)
    Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)
    Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    # Combine mock TOA with test text
    full_text = mock_toa_text + "\n\n" + test_text
    
    print("\n1. LOADING MOCK TOA...")
    evaluator = ToABasedCitationEvaluator()
    
    if evaluator.load_toa_from_text(full_text):
        print("✓ Successfully loaded mock TOA")
        
        # Show what was loaded
        summary = evaluator.get_summary()
        print(f"   - Canonical cases: {summary['canonical_cases_count']}")
        
        # Evaluate citations in test paragraph
        print("\n2. EVALUATING CITATIONS...")
        matches = evaluator.evaluate_citations_in_text(test_text)
        
        print(f"\n   Found {len(matches)} citation matches:")
        for i, match in enumerate(matches):
            print(f"     {i+1}. Citation: {match.citation}")
            print(f"        Case: {match.case_name}")
            print(f"        Year: {match.year}")
            print(f"        Method: {match.method}")
            print(f"        Confidence: {match.confidence}")
            
        # Compare with expected results
        expected_cases = [
            ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC", "2022"),
            ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC", "2011"),
            ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC", "2003")
        ]
        
        print("\n3. ACCURACY CHECK:")
        for expected_citation, expected_case, expected_year in expected_cases:
            found = False
            for match in matches:
                if expected_citation in match.citation:
                    found = True
                    case_correct = match.case_name == expected_case
                    year_correct = match.year == expected_year
                    status = "✓✓✓" if case_correct and year_correct else "⚠⚠⚠"
                    print(f"   {status} {expected_citation}")
                    print(f"      Expected: {expected_case} ({expected_year})")
                    print(f"      Found:    {match.case_name} ({match.year})")
                    break
            
            if not found:
                print(f"   ✗✗✗ {expected_citation} - NOT FOUND")
    else:
        print("✗ Failed to load mock TOA")

if __name__ == "__main__":
    # Test with real brief first
    test_with_brief()
    
    # Test with standard paragraph
    test_with_standard_paragraph()
    
    print("\n" + "=" * 80)
    print("TOA-BASED EVALUATION COMPLETE")
    print("=" * 80)
