#!/usr/bin/env python3
"""
Validate year extraction accuracy using known citation patterns and test cases.
This script tests the year extraction logic against various citation formats.
"""

import os
import sys
import json
import re
from pathlib import Path
import argparse
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from case_name_extraction_core import extract_case_name_triple_comprehensive

class YearExtractionValidator:
    """Validate year extraction accuracy."""
    
    def __init__(self):
        self.test_cases = self.create_test_cases()
        
    def create_test_cases(self) -> List[Dict[str, Any]]:
        """Create test cases for year extraction validation."""
        return [
            # Standard Washington citations
            {
                'citation': 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)',
                'expected_years': [2022],
                'description': 'Standard WA Supreme Court citation with year in parentheses'
            },
            {
                'citation': 'Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)',
                'expected_years': [2011],
                'description': 'WA Supreme Court citation with year'
            },
            {
                'citation': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)',
                'expected_years': [2003],
                'description': 'WA Supreme Court citation with apostrophe in name'
            },
            
            # Citations without years
            {
                'citation': 'RCW 2.60.020',
                'expected_years': [],
                'description': 'Statute citation without year'
            },
            {
                'citation': 'Washington State Constitution, Article I, Section 3',
                'expected_years': [],
                'description': 'Constitutional reference without year'
            },
            
            # Multiple years in citation
            {
                'citation': 'Smith v. Jones, 150 Wn.2d 123 (2003), overruled by Brown v. White, 160 Wn.2d 456 (2010)',
                'expected_years': [2003, 2010],
                'description': 'Citation with multiple years'
            },
            
            # Federal citations
            {
                'citation': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
                'expected_years': [1954],
                'description': 'US Supreme Court citation'
            },
            {
                'citation': 'Roe v. Wade, 410 U.S. 113 (1973)',
                'expected_years': [1973],
                'description': 'US Supreme Court citation'
            },
            
            # Ninth Circuit citations
            {
                'citation': 'United States v. Doe, 123 F.3d 456 (9th Cir. 1997)',
                'expected_years': [1997],
                'description': 'Ninth Circuit citation'
            },
            
            # Washington Court of Appeals
            {
                'citation': 'State v. Johnson, 123 Wn. App. 456 (2004)',
                'expected_years': [2004],
                'description': 'WA Court of Appeals citation'
            },
            
            # Edge cases
            {
                'citation': 'Case v. Name, 100 Wn.2d 123, 456 P.2d 789 (1980)',
                'expected_years': [1980],
                'description': 'Citation with 2-digit year in reporter'
            },
            {
                'citation': 'Another v. Case, 200 Wn.2d 456, 789 P.3d 123 (2023)',
                'expected_years': [2023],
                'description': 'Recent citation'
            },
            
            # Problematic cases
            {
                'citation': 'Case v. Name, 100 Wn.2d 123 (no year provided)',
                'expected_years': [],
                'description': 'Citation with text indicating no year'
            },
            {
                'citation': 'Case v. Name, 100 Wn.2d 123 (2000s)',
                'expected_years': [],
                'description': 'Citation with decade instead of year'
            }
        ]
    
    def extract_years_regex(self, citation: str) -> List[int]:
        """Extract years using regex patterns."""
        years = []
        
        # Pattern 1: Year in parentheses at end
        matches = re.findall(r'\((\d{4})\)', citation)
        for match in matches:
            year = int(match)
            if 1900 <= year <= 2030:
                years.append(year)
        
        # Pattern 2: Year after comma at end
        matches = re.findall(r',\s*(\d{4})\s*$', citation)
        for match in matches:
            year = int(match)
            if 1900 <= year <= 2030:
                years.append(year)
        
        # Pattern 3: Any 4-digit year (more permissive)
        matches = re.findall(r'\b(19|20)\d{2}\b', citation)
        for match in matches:
            year = int(match)
            if 1900 <= year <= 2030:
                years.append(year)
        
        return sorted(list(set(years)))
    
    def extract_years_core(self, citation: str) -> List[int]:
        """Extract years using the core extraction function."""
        try:
            result = extract_case_name_triple_comprehensive(citation)
            if result and 'extracted_year' in result and result['extracted_year']:
                return [result['extracted_year']]
        except Exception as e:
            pass
        return []
    
    def extract_years_combined(self, citation: str) -> List[int]:
        """Extract years using combined methods."""
        years = set()
        
        # Try regex first
        regex_years = self.extract_years_regex(citation)
        years.update(regex_years)
        
        # Try core extraction
        core_years = self.extract_years_core(citation)
        years.update(core_years)
        
        return sorted(list(years))
    
    def validate_extraction_method(self, method_name: str, extraction_func) -> Dict[str, Any]:
        """Validate a specific extraction method."""
        results = {
            'method': method_name,
            'total_tests': len(self.test_cases),
            'correct': 0,
            'incorrect': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'accuracy': 0.0,
            'test_results': []
        }
        
        for test_case in self.test_cases:
            citation = test_case['citation']
            expected_years = test_case['expected_years']
            description = test_case['description']
            
            # Extract years using the method
            extracted_years = extraction_func(citation)
            
            # Compare results
            is_correct = set(extracted_years) == set(expected_years)
            false_positive = len(set(extracted_years) - set(expected_years))
            false_negative = len(set(expected_years) - set(extracted_years))
            
            test_result = {
                'citation': citation,
                'description': description,
                'expected_years': expected_years,
                'extracted_years': extracted_years,
                'is_correct': is_correct,
                'false_positives': false_positive,
                'false_negatives': false_negative
            }
            
            results['test_results'].append(test_result)
            
            if is_correct:
                results['correct'] += 1
            else:
                results['incorrect'] += 1
            
            results['false_positives'] += false_positive
            results['false_negatives'] += false_negative
        
        # Calculate accuracy
        results['accuracy'] = results['correct'] / results['total_tests']
        
        return results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation of year extraction methods."""
        print("Year Extraction Validation")
        print("=" * 50)
        
        methods = [
            ('Regex Only', self.extract_years_regex),
            ('Core Only', self.extract_years_core),
            ('Combined', self.extract_years_combined)
        ]
        
        all_results = {}
        
        for method_name, extraction_func in methods:
            print(f"\nTesting {method_name}...")
            results = self.validate_extraction_method(method_name, extraction_func)
            all_results[method_name] = results
            
            print(f"  Accuracy: {results['accuracy']:.1%}")
            print(f"  Correct: {results['correct']}/{results['total_tests']}")
            print(f"  False Positives: {results['false_positives']}")
            print(f"  False Negatives: {results['false_negatives']}")
        
        # Find best method
        best_method = max(all_results.keys(), key=lambda k: all_results[k]['accuracy'])
        best_accuracy = all_results[best_method]['accuracy']
        
        print(f"\n{'='*50}")
        print(f"Best Method: {best_method} ({best_accuracy:.1%} accuracy)")
        
        return {
            'validation_results': all_results,
            'best_method': best_method,
            'best_accuracy': best_accuracy,
            'test_cases': self.test_cases
        }
    
    def show_detailed_results(self, results: Dict[str, Any]):
        """Show detailed results for each method."""
        print("\nDetailed Results:")
        print("=" * 50)
        
        for method_name, method_results in results['validation_results'].items():
            print(f"\n{method_name}:")
            print("-" * 30)
            
            # Show incorrect cases
            incorrect_cases = [r for r in method_results['test_results'] if not r['is_correct']]
            
            if incorrect_cases:
                print(f"  Incorrect cases ({len(incorrect_cases)}):")
                for case in incorrect_cases:
                    print(f"    Citation: {case['citation']}")
                    print(f"    Expected: {case['expected_years']}")
                    print(f"    Extracted: {case['extracted_years']}")
                    print(f"    Description: {case['description']}")
                    print()
            else:
                print("  All cases correct!")
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save validation results to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Validate year extraction accuracy')
    parser.add_argument('--output', '-o', default='year_extraction_validation.json', 
                       help='Output JSON file for results')
    parser.add_argument('--detailed', '-d', action='store_true', 
                       help='Show detailed results')
    
    args = parser.parse_args()
    
    validator = YearExtractionValidator()
    results = validator.run_validation()
    
    if args.detailed:
        validator.show_detailed_results(results)
    
    validator.save_results(results, args.output)

if __name__ == "__main__":
    main() 