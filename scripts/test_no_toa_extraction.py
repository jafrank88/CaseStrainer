#!/usr/bin/env python3
"""
Test script for citation extraction from documents WITHOUT Table of Authorities.
This script focuses on testing the core extraction and clustering logic that must work
when users submit documents that don't have structured ToA sections.
"""

import os
import sys
import json
import time
from pathlib import Path
import argparse
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import with absolute paths to avoid relative import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.case_name_extraction_core import extract_case_name_triple_comprehensive
from src.file_utils import extract_text_from_pdf

class NoToAExtractionTester:
    """Test citation extraction from documents without Table of Authorities."""
    
    def __init__(self):
        self.processor = UnifiedCitationProcessorV2()
        
        # Test cases for documents without ToA
        self.test_cases = [
            {
                'name': 'Standard WA Citations',
                'text': '''
                A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
                ''',
                'expected_citations': [
                    '200 Wn.2d 72, 73, 514 P.3d 643 (2022)',
                    '171 Wn.2d 486, 493, 256 P.3d 321 (2011)',
                    '146 Wn.2d 1, 9, 43 P.3d 4 (2003)'
                ],
                'expected_case_names': [
                    'Convoyant, LLC v. DeepThink, LLC',
                    'Carlson v. Glob. Client Sols., LLC',
                    'Dep\'t of Ecology v. Campbell & Gwinn, LLC'
                ],
                'expected_years': [2022, 2011, 2003]
            },
            {
                'name': 'Mixed Citation Types',
                'text': '''
                The Supreme Court has held that Brown v. Board of Education, 347 U.S. 483 (1954) established important precedent. In Washington, we follow State v. Johnson, 123 Wn. App. 456 (2004) and United States v. Doe, 123 F.3d 456 (9th Cir. 1997). The Ninth Circuit has also ruled on this matter.
                ''',
                'expected_citations': [
                    '347 U.S. 483 (1954)',
                    '123 Wn. App. 456 (2004)',
                    '123 F.3d 456 (9th Cir. 1997)'
                ],
                'expected_case_names': [
                    'Brown v. Board of Education',
                    'State v. Johnson',
                    'United States v. Doe'
                ],
                'expected_years': [1954, 2004, 1997]
            },
            {
                'name': 'Complex Citations with Pinpoints',
                'text': '''
                The court considered Smith v. Jones, 150 Wn.2d 123, 125-127 (2003), overruled by Brown v. White, 160 Wn.2d 456, 460 (2010). The dissent argued that the majority ignored precedent.
                ''',
                'expected_citations': [
                    '150 Wn.2d 123, 125-127 (2003)',
                    '160 Wn.2d 456, 460 (2010)'
                ],
                'expected_case_names': [
                    'Smith v. Jones',
                    'Brown v. White'
                ],
                'expected_years': [2003, 2010]
            },
            {
                'name': 'Statutes and Regulations',
                'text': '''
                The statute provides that RCW 2.60.020 governs certified questions. The regulation at WAC 10-08-120 further clarifies this process. The court must follow these provisions.
                ''',
                'expected_citations': [
                    'RCW 2.60.020',
                    'WAC 10-08-120'
                ],
                'expected_case_names': [],  # Statutes don't have case names
                'expected_years': []  # Statutes don't have years
            },
            {
                'name': 'Citations in Footnotes',
                'text': '''
                The court's analysis follows established precedent.¹ The dissent argues otherwise.²

                ¹ See Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72 (2022).
                ² Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486 (2011).
                ''',
                'expected_citations': [
                    '200 Wn.2d 72 (2022)',
                    '171 Wn.2d 486 (2011)'
                ],
                'expected_case_names': [
                    'Convoyant, LLC v. DeepThink, LLC',
                    'Carlson v. Glob. Client Sols., LLC'
                ],
                'expected_years': [2022, 2011]
            }
        ]
    
    def test_case_name_extraction(self, text: str, expected_case_names: List[str]) -> Dict[str, Any]:
        """Test case name extraction from text without ToA."""
        results = {
            'extracted_case_names': [],
            'extraction_methods': [],
            'accuracy': 0.0,
            'false_positives': 0,
            'false_negatives': 0,
            'details': []
        }
        
        # Use the core extraction function
        try:
            case_name, date, confidence = extract_case_name_triple_comprehensive(text)
            if case_name:
                results['extracted_case_names'].append(case_name)
                results['extraction_methods'].append('core_function')
        except Exception as e:
            print(f"Error in core extraction: {e}")
        
        # Use regex patterns to find case names
        import re
        case_patterns = [
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+vs\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bIn\s+re\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bState\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
        ]
        
        for pattern in case_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern == case_patterns[0] or pattern == case_patterns[1]:  # v. or vs. patterns
                    case_name = f"{match.group(1)} v. {match.group(2)}"
                elif pattern == case_patterns[2]:  # In re pattern
                    case_name = f"In re {match.group(1)}"
                elif pattern == case_patterns[3]:  # State v. pattern
                    case_name = f"State v. {match.group(1)}"
                else:
                    case_name = match.group(0)
                
                if case_name not in results['extracted_case_names']:
                    results['extracted_case_names'].append(case_name)
                    results['extraction_methods'].append('regex_pattern')
        
        # Calculate accuracy
        if expected_case_names:
            correct = 0
            for expected in expected_case_names:
                for extracted in results['extracted_case_names']:
                    if self._similar_case_names(expected, extracted):
                        correct += 1
                        break
            
            results['accuracy'] = correct / len(expected_case_names) if expected_case_names else 0.0
            results['false_negatives'] = len(expected_case_names) - correct
            results['false_positives'] = len(results['extracted_case_names']) - correct
        
        return results
    
    def _similar_case_names(self, name1: str, name2: str) -> bool:
        """Check if two case names are similar."""
        # Normalize names
        def normalize(name):
            return re.sub(r'\s+', ' ', name.lower().strip())
        
        norm1 = normalize(name1)
        norm2 = normalize(name2)
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # Check if one contains the other (for partial matches)
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check for common variations
        variations1 = [norm1, norm1.replace('&', 'and'), norm1.replace('and', '&')]
        variations2 = [norm2, norm2.replace('&', 'and'), norm2.replace('and', '&')]
        
        for v1 in variations1:
            for v2 in variations2:
                if v1 == v2:
                    return True
        
        return False
    
    def test_year_extraction(self, text: str, expected_years: List[int]) -> Dict[str, Any]:
        """Test year extraction from text without ToA."""
        results = {
            'extracted_years': [],
            'extraction_methods': [],
            'accuracy': 0.0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Use regex to find years
        import re
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # 4-digit years
            r'\((\d{4})\)',  # Years in parentheses
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if pattern == year_patterns[0]:
                    year = int(match)
                else:
                    year = int(match)
                
                if 1900 <= year <= 2030 and year not in results['extracted_years']:
                    results['extracted_years'].append(year)
                    results['extraction_methods'].append('regex')
        
        # Calculate accuracy
        if expected_years:
            correct = len(set(results['extracted_years']) & set(expected_years))
            results['accuracy'] = correct / len(expected_years) if expected_years else 0.0
            results['false_negatives'] = len(expected_years) - correct
            results['false_positives'] = len(results['extracted_years']) - correct
        
        return results
    
    def test_citation_extraction(self, text: str, expected_citations: List[str]) -> Dict[str, Any]:
        """Test citation extraction from text without ToA."""
        results = {
            'extracted_citations': [],
            'accuracy': 0.0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Use the unified processor
        try:
            extraction_result = self.processor.extract_citations_from_text(text)
            if extraction_result:
                results['extracted_citations'] = extraction_result.get('extracted_citations', [])
        except Exception as e:
            print(f"Error in citation extraction: {e}")
        
        # Calculate accuracy
        if expected_citations:
            correct = 0
            for expected in expected_citations:
                for extracted in results['extracted_citations']:
                    if self._similar_citations(expected, extracted):
                        correct += 1
                        break
            
            results['accuracy'] = correct / len(expected_citations) if expected_citations else 0.0
            results['false_negatives'] = len(expected_citations) - correct
            results['false_positives'] = len(results['extracted_citations']) - correct
        
        return results
    
    def _similar_citations(self, citation1: str, citation2: str) -> bool:
        """Check if two citations are similar."""
        # Normalize citations
        def normalize(citation):
            return re.sub(r'\s+', ' ', citation.lower().strip())
        
        norm1 = normalize(citation1)
        norm2 = normalize(citation2)
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # Check if one contains the other (for partial matches)
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        return False
    
    def test_clustering(self, text: str, expected_citations: List[str]) -> Dict[str, Any]:
        """Test clustering of citations from text without ToA."""
        results = {
            'clusters': [],
            'cluster_count': 0,
            'avg_cluster_size': 0.0,
            'clustering_quality': 0.0
        }
        
        try:
            # Extract citations first
            extraction_result = self.processor.extract_citations_from_text(text)
            if not extraction_result:
                return results
            
            extracted_citations = extraction_result.get('extracted_citations', [])
            
            # Process through clustering
            clustering_result = self.processor.process_citations_through_clustering(
                extracted_citations, text
            )
            
            clusters = clustering_result.get('clusters', [])
            results['clusters'] = clusters
            results['cluster_count'] = len(clusters)
            
            if clusters:
                cluster_sizes = [len(cluster.get('citations', [])) for cluster in clusters]
                results['avg_cluster_size'] = sum(cluster_sizes) / len(cluster_sizes)
                
                # Calculate clustering quality (higher is better)
                # Quality = percentage of citations that are in clusters of size > 1
                total_clustered = sum(size for size in cluster_sizes if size > 1)
                total_citations = sum(cluster_sizes)
                results['clustering_quality'] = total_clustered / total_citations if total_citations > 0 else 0.0
        
        except Exception as e:
            print(f"Error in clustering: {e}")
        
        return results
    
    def run_comprehensive_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive test on a single test case."""
        print(f"\n=== Testing: {test_case['name']} ===")
        
        text = test_case['text']
        expected_citations = test_case['expected_citations']
        expected_case_names = test_case['expected_case_names']
        expected_years = test_case['expected_years']
        
        # Test citation extraction
        citation_results = self.test_citation_extraction(text, expected_citations)
        print(f"Citation extraction: {citation_results['accuracy']:.1%} accuracy")
        print(f"  Extracted: {len(citation_results['extracted_citations'])} citations")
        print(f"  Expected: {len(expected_citations)} citations")
        
        # Test case name extraction
        case_name_results = self.test_case_name_extraction(text, expected_case_names)
        print(f"Case name extraction: {case_name_results['accuracy']:.1%} accuracy")
        print(f"  Extracted: {len(case_name_results['extracted_case_names'])} case names")
        print(f"  Expected: {len(expected_case_names)} case names")
        
        # Test year extraction
        year_results = self.test_year_extraction(text, expected_years)
        print(f"Year extraction: {year_results['accuracy']:.1%} accuracy")
        print(f"  Extracted: {len(year_results['extracted_years'])} years")
        print(f"  Expected: {len(expected_years)} years")
        
        # Test clustering
        clustering_results = self.test_clustering(text, expected_citations)
        print(f"Clustering: {clustering_results['cluster_count']} clusters")
        print(f"  Average cluster size: {clustering_results['avg_cluster_size']:.1f}")
        print(f"  Clustering quality: {clustering_results['clustering_quality']:.1%}")
        
        return {
            'test_name': test_case['name'],
            'citation_extraction': citation_results,
            'case_name_extraction': case_name_results,
            'year_extraction': year_results,
            'clustering': clustering_results
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases."""
        print("No ToA Citation Extraction Testing")
        print("=" * 50)
        
        all_results = []
        overall_stats = {
            'total_tests': len(self.test_cases),
            'avg_citation_accuracy': 0.0,
            'avg_case_name_accuracy': 0.0,
            'avg_year_accuracy': 0.0,
            'avg_clustering_quality': 0.0
        }
        
        for test_case in self.test_cases:
            result = self.run_comprehensive_test(test_case)
            all_results.append(result)
            
            # Accumulate stats
            overall_stats['avg_citation_accuracy'] += result['citation_extraction']['accuracy']
            overall_stats['avg_case_name_accuracy'] += result['case_name_extraction']['accuracy']
            overall_stats['avg_year_accuracy'] += result['year_extraction']['accuracy']
            overall_stats['avg_clustering_quality'] += result['clustering']['clustering_quality']
        
        # Calculate averages
        overall_stats['avg_citation_accuracy'] /= len(self.test_cases)
        overall_stats['avg_case_name_accuracy'] /= len(self.test_cases)
        overall_stats['avg_year_accuracy'] /= len(self.test_cases)
        overall_stats['avg_clustering_quality'] /= len(self.test_cases)
        
        # Print summary
        print(f"\n{'='*50}")
        print("OVERALL RESULTS")
        print(f"{'='*50}")
        print(f"Citation extraction accuracy: {overall_stats['avg_citation_accuracy']:.1%}")
        print(f"Case name extraction accuracy: {overall_stats['avg_case_name_accuracy']:.1%}")
        print(f"Year extraction accuracy: {overall_stats['avg_year_accuracy']:.1%}")
        print(f"Clustering quality: {overall_stats['avg_clustering_quality']:.1%}")
        
        return {
            'overall_stats': overall_stats,
            'test_results': all_results
        }
    
    def test_real_document(self, pdf_path: str) -> Dict[str, Any]:
        """Test extraction on a real PDF document."""
        print(f"\n=== Testing Real Document: {pdf_path} ===")
        
        try:
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                print("Error: Could not extract text from PDF")
                return {}
            
            print(f"Extracted {len(text)} characters from PDF")
            
            # Test citation extraction
            citation_results = self.test_citation_extraction(text, [])
            print(f"Found {len(citation_results['extracted_citations'])} citations")
            
            # Test case name extraction
            case_name_results = self.test_case_name_extraction(text, [])
            print(f"Found {len(case_name_results['extracted_case_names'])} case names")
            
            # Test year extraction
            year_results = self.test_year_extraction(text, [])
            print(f"Found {len(year_results['extracted_years'])} years")
            
            # Test clustering
            clustering_results = self.test_clustering(text, [])
            print(f"Created {clustering_results['cluster_count']} clusters")
            
            return {
                'filename': Path(pdf_path).name,
                'text_length': len(text),
                'citation_extraction': citation_results,
                'case_name_extraction': case_name_results,
                'year_extraction': year_results,
                'clustering': clustering_results
            }
            
        except Exception as e:
            print(f"Error testing real document: {e}")
            return {}
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save test results to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test citation extraction from documents without ToA')
    parser.add_argument('--test-cases', action='store_true', help='Run predefined test cases')
    parser.add_argument('--real-document', help='Test on a real PDF document')
    parser.add_argument('--output', '-o', default='no_toa_test_results.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    tester = NoToAExtractionTester()
    
    if args.test_cases:
        results = tester.run_all_tests()
        tester.save_results(results, args.output)
    
    if args.real_document:
        result = tester.test_real_document(args.real_document)
        if result:
            tester.save_results(result, args.output)
    
    if not args.test_cases and not args.real_document:
        # Run test cases by default
        results = tester.run_all_tests()
        tester.save_results(results, args.output)

if __name__ == "__main__":
    main() 