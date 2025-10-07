"""
Comprehensive Test Suite for Case Name Extraction Improvements
=================================================================

Tests the enhanced pattern matching, context handling, and validation
improvements made to the case name extraction pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.standalone_citation_parser import CitationParser
from src.case_name_extraction_core import extract_case_name_and_date
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TestCaseNameExtraction:
    """Test suite for case name extraction improvements"""
    
    def __init__(self):
        self.parser = CitationParser()
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def run_test(self, name: str, text: str, citation: str, expected_case_name: str, 
                 should_find: bool = True):
        """
        Run a single test case
        
        Args:
            name: Test name
            text: Full text containing the citation
            citation: Citation to search for
            expected_case_name: Expected extracted case name
            should_find: Whether we expect to find a case name
        """
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"{'='*80}")
        print(f"Citation: {citation}")
        print(f"Expected: {expected_case_name if should_find else '[No case name]'}")
        
        try:
            # Extract case name using both methods
            result1 = self.parser.extract_from_text(text, citation)
            result2 = extract_case_name_and_date(text, citation, debug=False)
            
            extracted1 = result1.get('case_name', '')
            extracted2 = result2.get('case_name', '')
            
            print(f"Extracted (parser): {extracted1 or '[None]'}")
            print(f"Extracted (core):   {extracted2 or '[None]'}")
            
            # Check results
            success = False
            if should_find:
                if extracted1 and expected_case_name.lower() in extracted1.lower():
                    success = True
                    print(f"[PASS] Test passed (parser matched)")
                elif extracted2 and expected_case_name.lower() in extracted2.lower():
                    success = True
                    print(f"[PASS] Test passed (core matched)")
                else:
                    print(f"[FAIL] Expected '{expected_case_name}' but got different results")
            else:
                if not extracted1 and not extracted2:
                    success = True
                    print(f"[PASS] Test passed (correctly found no case name)")
                else:
                    print(f"[FAIL] Should not have found a case name")
            
            if success:
                self.passed += 1
            else:
                self.failed += 1
            
            self.test_results.append({
                'name': name,
                'passed': success,
                'expected': expected_case_name,
                'extracted1': extracted1,
                'extracted2': extracted2
            })
            
        except Exception as e:
            print(f"[ERROR] Test failed: {str(e)}")
            logger.exception("Test failed with exception")
            self.failed += 1
            self.test_results.append({
                'name': name,
                'passed': False,
                'error': str(e)
            })
    
    def test_sentence_start_cases(self):
        """Test case names at the beginning of sentences"""
        print("\n" + "="*80)
        print("TESTING: Sentence-Start Case Names")
        print("="*80)
        
        # Test 1: Case name at start of paragraph
        text = """Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). 
        This case established important precedent."""
        self.run_test(
            "Sentence-start case (beginning of paragraph)",
            text,
            "200 Wn.2d 72",
            "Convoyant, LLC v. DeepThink, LLC"
        )
        
        # Test 2: Case name after previous citation
        text = """See Smith v. Jones, 100 P.3d 100 (2020). Doe v. Roe, 200 P.3d 200 (2021) 
        reached a different conclusion."""
        self.run_test(
            "Sentence-start case (after previous case)",
            text,
            "200 P.3d 200",
            "Doe v. Roe"
        )
        
        # Test 3: Multiple cases in sequence
        text = """The court cited three cases. First, Alpha Corp v. Beta Inc, 100 Wn.2d 100 (2020). 
        Second, Gamma LLC v. Delta Co, 200 Wn.2d 200 (2021). Third, Epsilon v. Zeta, 300 Wn.2d 300 (2022)."""
        self.run_test(
            "Middle case in sequence",
            text,
            "200 Wn.2d 200",
            "Gamma LLC v. Delta Co"
        )
    
    def test_special_case_types(self):
        """Test special case name formats (In re, Estate of, etc.)"""
        print("\n" + "="*80)
        print("TESTING: Special Case Types")
        print("="*80)
        
        # Test 1: In re Marriage
        text = """In re Marriage of Chandola, 180 Wn.2d 632, 327 P.3d 644 (2014) established 
        the standard for property division."""
        self.run_test(
            "In re Marriage case",
            text,
            "180 Wn.2d 632",
            "In re Marriage of Chandola"
        )
        
        # Test 2: Estate of
        text = """Estate of Smith, 150 Wn.2d 500, 250 P.3d 100 (2010) addressed 
        inheritance issues."""
        self.run_test(
            "Estate of case",
            text,
            "150 Wn.2d 500",
            "Estate of Smith"
        )
        
        # Test 3: Matter of
        text = """Matter of Jones Trust, 175 Wn.2d 600, 275 P.3d 200 (2012) clarified 
        trust administration rules."""
        self.run_test(
            "Matter of case",
            text,
            "175 Wn.2d 600",
            "Matter of Jones"
        )
        
        # Test 4: Department of
        text = """Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003) 
        addressed environmental regulations."""
        self.run_test(
            "Department case",
            text,
            "146 Wn.2d 1",
            "Dep't of Ecology v. Campbell"
        )
    
    def test_context_isolation(self):
        """Test that context window properly isolates case names"""
        print("\n" + "="*80)
        print("TESTING: Context Isolation")
        print("="*80)
        
        # Test 1: Multiple citations close together
        text = """The principle from Smith v. Jones, 100 Wn.2d 100 (2010) was later 
        applied in Doe v. Roe, 200 Wn.2d 200 (2015) and distinguished in 
        Williams v. Brown, 300 Wn.2d 300 (2020)."""
        self.run_test(
            "Middle citation with neighbors",
            text,
            "200 Wn.2d 200",
            "Doe v. Roe"
        )
        
        # Test 2: Case name should not bleed from previous sentence
        text = """Smith v. Jones established the rule. Later, in Doe v. Roe, 
        200 Wn.2d 200 (2015), the court expanded this principle."""
        self.run_test(
            "Case after period (should not get previous case)",
            text,
            "200 Wn.2d 200",
            "Doe v. Roe"
        )
    
    def test_validation_filters(self):
        """Test that validation properly filters false positives"""
        print("\n" + "="*80)
        print("TESTING: Validation Filters")
        print("="*80)
        
        # Test 1: Should reject procedural text
        text = """The court held that the statute applies, 200 Wn.2d 200 (2015)."""
        self.run_test(
            "Procedural text (should reject)",
            text,
            "200 Wn.2d 200",
            "",
            should_find=False
        )
        
        # Test 2: Should accept proper case name after procedural text
        text = """The court held that the statute applies in Smith v. Jones, 
        200 Wn.2d 200 (2015)."""
        self.run_test(
            "Case name after procedural text",
            text,
            "200 Wn.2d 200",
            "Smith v. Jones"
        )
    
    def test_real_world_examples(self):
        """Test with real-world legal text examples"""
        print("\n" + "="*80)
        print("TESTING: Real-World Examples")
        print("="*80)
        
        # Test 1: Standard test paragraph (from memory)
        text = """A federal court may ask this court to answer a question of Washington law 
        when a resolution of that question is necessary to resolve a case before the federal court. 
        RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). 
        Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 
        171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. 
        Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
        
        self.run_test(
            "Real-world test 1 - Convoyant",
            text,
            "200 Wn.2d 72",
            "Convoyant, LLC v. DeepThink, LLC"
        )
        
        self.run_test(
            "Real-world test 2 - Carlson",
            text,
            "171 Wn.2d 486",
            "Carlson v. Glob. Client Sols., LLC"
        )
        
        self.run_test(
            "Real-world test 3 - Dep't of Ecology",
            text,
            "146 Wn.2d 1",
            "Dep't of Ecology v. Campbell & Gwinn, LLC"
        )
        
        # Test 2: Pro se litigants paragraph (from memory)
        text = """We have long held that pro se litigants are bound by the same rules of 
        procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 
        136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 
        850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . 
        a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal 
        issues . . . cite any authority" or comply with procedural rules may still preclude 
        appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)."""
        
        self.run_test(
            "Real-world test 4 - Holder",
            text,
            "136 Wn. App. 104",
            "Holder v. City of Vancouver"
        )
        
        self.run_test(
            "Real-world test 5 - In re Marriage",
            text,
            "69 Wn. App. 621",
            "In re Marriage of Olson"
        )
        
        self.run_test(
            "Real-world test 6 - State v. Marintorres",
            text,
            "93 Wn. App. 442",
            "State v. Marintorres"
        )
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed:      {self.passed} ({100*self.passed//total if total > 0 else 0}%)")
        print(f"Failed:      {self.failed}")
        print("="*80)
        
        if self.failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('passed', False):
                    print(f"  - {result['name']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
        
        return self.failed == 0


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CASE NAME EXTRACTION - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("\nTesting improvements to:")
    print("  1. Pattern matching (sentence-start detection)")
    print("  2. Context handling (better boundaries)")
    print("  3. Validation (false positive filtering)")
    print("  4. Real-world examples")
    
    tester = TestCaseNameExtraction()
    
    # Run all test suites
    tester.test_sentence_start_cases()
    tester.test_special_case_types()
    tester.test_context_isolation()
    tester.test_validation_filters()
    tester.test_real_world_examples()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

