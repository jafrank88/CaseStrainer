#!/usr/bin/env python3
"""
Test suite for case name extraction functionality, focusing on handling introductory phrases.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from extract_case_name import clean_case_name, extract_case_name_from_text
from enhanced_case_name_extractor import EnhancedCaseNameExtractor
from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from citation_extractor import CitationExtractor

class TestCaseNameExtraction(unittest.TestCase):
    """Test case name extraction and cleaning functionality."""

    def test_clean_case_name(self):
        """Test the clean_case_name function with various introductory phrases."""
        test_cases = [
            ("quoting Ellis v. City of Seattle", "Ellis v. City of Seattle"),
            ("cited in Smith v. Jones", "Smith v. Jones"),
            ("referenced in Brown v. Board of Education", "Brown v. Board of Education"),
            ("as stated in Roe v. Wade", "Roe v. Wade"),
            ("as held in Miranda v. Arizona", "Miranda v. Arizona"),
            ("the court in United States v. Nixon", "United States v. Nixon"),
            ("judge in State v. Johnson", "State v. Johnson"),
            ("opinion in In re Smith", "In re Smith"),
            ("see Doe v. Roe", "Doe v. Roe"),
            ("cf. Example v. Test", "Example v. Test"),
            ("e.g., Sample v. Case", "Sample v. Case"),
            ("i.e., Another v. Example", "Another v. Example"),
            ("according to Test v. Case", "Test v. Case"),
            ("per Sample v. Example", "Sample v. Example"),
            ("as per Another v. Test", "Another v. Test"),
            ("Unknown Case", "Unknown Case"),  # Should remain unchanged
            ("Case not found", "Case not found"),  # Should remain unchanged
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_case_name(input_text)
                self.assertEqual(result, expected, f"Failed for input: {input_text}")

    def test_extract_case_name_from_text(self):
        """Test the extract_case_name_from_text function with context containing introductory phrases."""
        test_cases = [
            {
                "text": "The court held that quoting Ellis v. City of Seattle, 142 Wash. 2d 450, 13 P.3d 1065 (2000), establishes the standard.",
                "citation": "142 Wash. 2d 450",
                "expected": "Ellis v. City of Seattle"
            },
            {
                "text": "As stated in Smith v. Jones, 123 U.S. 456 (2020), the principle applies.",
                "citation": "123 U.S. 456",
                "expected": "Smith v. Jones"
            },
            {
                "text": "The judge in Brown v. Board of Education, 347 U.S. 483 (1954), ruled that...",
                "citation": "347 U.S. 483",
                "expected": "Brown v. Board of Education"
            },
            {
                "text": "See Roe v. Wade, 410 U.S. 113 (1973), for the precedent.",
                "citation": "410 U.S. 113",
                "expected": "Roe v. Wade"
            }
        ]

        for test_case in test_cases:
            with self.subTest(text=test_case["text"]):
                result = extract_case_name_from_text(test_case["text"], test_case["citation"])
                self.assertEqual(result, test_case["expected"], f"Failed for citation: {test_case['citation']}")

    def test_enhanced_case_name_extractor(self):
        """Test the EnhancedCaseNameExtractor with introductory phrases."""
        extractor = EnhancedCaseNameExtractor()
        test_text = "The court held that quoting Ellis v. City of Seattle, 142 Wash. 2d 450, establishes the standard."
        citation = "142 Wash. 2d 450"
        result = extractor.extract_case_name_from_context(test_text, citation)
        self.assertEqual(result, "Ellis v. City of Seattle")

    def test_enhanced_multi_source_verifier_cleaning(self):
        """Test the EnhancedMultiSourceVerifier's case name cleaning."""
        verifier = EnhancedMultiSourceVerifier()
        test_case_name = "quoting Ellis v. City of Seattle"
        cleaned = verifier._clean_case_name(test_case_name)
        self.assertEqual(cleaned, "Ellis v. City of Seattle")
        is_valid = verifier._is_valid_case_name(test_case_name)
        self.assertTrue(is_valid)

    def test_citation_extractor_cleaning(self):
        """Test the CitationExtractor's case name cleaning."""
        citation_extractor = CitationExtractor()
        test_case_name = "quoting Smith v. Jones"
        cleaned = citation_extractor._clean_case_name(test_case_name)
        self.assertEqual(cleaned, "Smith v. Jones")
        is_valid = citation_extractor._is_valid_case_name(test_case_name)
        self.assertTrue(is_valid)

if __name__ == '__main__':
    unittest.main(verbosity=2)
