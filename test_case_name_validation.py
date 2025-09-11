import unittest
import sys
import os

# Add the src directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

class TestCaseNameValidation(unittest.TestCase):    
    def setUp(self):
        self.processor = UnifiedCitationProcessorV2()
    
    def test_common_case_names(self):
        """Test common case name patterns"""
        test_cases = [
            # Valid cases
            ("Smith v. Jones", True),
            ("Roe v. Wade", True),
            ("In re Gault", True),
            ("Ex parte Milligan", True),
            ("State v. Smith", True),
            ("People v. Anderson", True),
            ("United States v. Nixon", True),
            ("Marbury v. Madison", True),
            ("Brown v. Board of Education", True),
            ("Miranda v. Arizona", True),
            ("In the Matter of Baby M", True),
            ("Ex rel. Smith v. Jones", True),
            ("Commonwealth v. Johnson", True),
            ("Petition of Smith", True),
            
            # Invalid cases
            ("v. Smith", False),  # Missing plaintiff
            ("Smith v.", False),  # Missing defendant
            ("In re", False),  # Missing name
            ("Court of Appeals", False),  # Court name, not case name
            ("Federal Rules of Civil Procedure", False),  # Rules, not case
            ("Title 42 U.S. Code § 1983", False),  # Statute, not case
            ("The court finds that the defendant", False),  # Regular text
            ("See Smith v. Jones", False),  # Citation with signal
            ("Id. at 123", False),  # Short form citation
            ("Supra note 5", False),  # Legal reference
            ("infra Section II.B", False),  # Legal reference
            ("the court held that", False),  # Regular text
            ("as stated in the statute", False),  # Regular text
            ("the defendant's motion to dismiss", False),  # Regular text
            ("the plaintiff's complaint alleges", False),  # Regular text
        ]
        
        for case_name, expected in test_cases:
            with self.subTest(case_name=case_name, expected=expected):
                result = self.processor._is_valid_case_name(case_name)
                self.assertEqual(result, expected, 
                               f"Failed for '{case_name}': expected {expected}, got {result}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        test_cases = [
            ("", False),  # Empty string
            ("A v. B", True),  # Minimal valid case name
            ("A" * 151, False),  # Too long
            ("A v. " + "B" * 146, False),  # Exactly at length limit (but invalid structure)
            ("State v. " + "X" * 141, True),  # Long but valid
            (" ", False),  # Whitespace only
            ("v. ", False),  # Incomplete
            ("In re ", False),  # Incomplete
            ("123 v. 456", False),  # Numbers only
            ("@#$% v. &*()", False),  # Special characters
        ]
        
        for case_name, expected in test_cases:
            with self.subTest(case_name=case_name, expected=expected):
                result = self.processor._is_valid_case_name(case_name)
                self.assertEqual(result, expected,
                               f"Failed for '{case_name}': expected {expected}, got {result}")
    
    def test_common_false_positives(self):
        """Test common false positives that should be rejected"""
        false_positives = [
            "The court of appeals held that",
            "As the district court explained",
            "Under the statute",
            "In the circuit court",
            "The federal rules of civil procedure",
            "Title 42 U.S. Code Section 1983",
            "The constitutional provision",
            "The municipal code states",
            "The appellate division found",
            "The supreme court has held",
            "The court's jurisdiction",
            "The defendant's motion",
            "The plaintiff's complaint",
            "The trial court's decision",
            "The court of criminal appeals",
        ]
        
        for text in false_positives:
            with self.subTest(text=text):
                result = self.processor._is_valid_case_name(text)
                self.assertFalse(result, f"False positive: '{text}' was incorrectly identified as a case name")

if __name__ == "__main__":
    unittest.main(verbosity=2)
