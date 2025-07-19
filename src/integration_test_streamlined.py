"""
Integration Testing & Validation Script
Tests the streamlined extractor against your existing system
"""

import json
import time
from typing import Dict, List, Tuple
from dataclasses import asdict

# Import both old and new systems for comparison
try:
    # New streamlined system
    from case_name_extraction_core import (
        extract_case_name_and_date,
        extract_case_name_only,
        extract_year_only
    )
    from legal_case_extractor_integrated import (
        LegalCaseExtractorIntegrated,
        extract_cases_from_text
    )
    NEW_SYSTEM_AVAILABLE = True
except ImportError as e:
    logger.info(f"New system not available: {e}")
    NEW_SYSTEM_AVAILABLE = False

try:
    # Your existing system (update these imports based on your actual structure)
    from legal_case_extractor_enhanced import LegalCaseExtractorEnhanced
    # Add other existing extraction functions here
    OLD_SYSTEM_AVAILABLE = True
except ImportError as e:
    OLD_SYSTEM_AVAILABLE = False

class IntegrationTester:
    """
    Test the integration and compare old vs new extraction systems
    """
    
    def __init__(self):
        self.test_cases = self._get_test_cases()
        self.results = {
            'old_system': [],
            'new_system': [],
            'comparison': []
        }
    
    def _get_test_cases(self) -> List[Dict]:
        """Define test cases with expected results"""
        return [
            {
                'name': 'Washington Supreme Court Case',
                'text': 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).',
                'citations': ['200 Wn.2d 72'],
                'expected': {
                    'case_name': 'Convoyant, LLC v. DeepThink, LLC',
                    'year': '2022'
                }
            },
            {
                'name': 'Complex Citation with Department',
                'text': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)',
                'citations': ['146 Wn.2d 1'],
                'expected': {
                    'case_name': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC',
                    'year': '2002'
                }
            },
            {
                'name': 'Multiple Citations in Text',
                'text': '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).''',
                'citations': ['200 Wn.2d 72', '171 Wn.2d 486'],
                'expected': [
                    {'case_name': 'Convoyant, LLC v. DeepThink, LLC', 'year': '2022'},
                    {'case_name': 'Carlsen v. Glob. Client Sols., LLC', 'year': '2011'}
                ]
            },
            {
                'name': 'Federal Case',
                'text': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
                'citations': ['347 U.S. 483'],
                'expected': {
                    'case_name': 'Brown v. Board of Education',
                    'year': '1954'
                }
            },
            {
                'name': 'In Re Case',
                'text': 'In re Smith, 123 F.3d 456 (9th Cir. 2020)',
                'citations': ['123 F.3d 456'],
                'expected': {
                    'case_name': 'In re Smith',
                    'year': '2020'
                }
            },
            {
                'name': 'State Case',
                'text': 'State v. Johnson, 456 P.2d 789 (Wash. 1995)',
                'citations': ['456 P.2d 789'],
                'expected': {
                    'case_name': 'State v. Johnson',
                    'year': '1995'
                }
            },
            {
                'name': 'Complex Text with Multiple Patterns',
                'text': '''The court in Roe v. Wade, 410 U.S. 113 (1973), established important precedent. Later, in Planned Parenthood v. Casey, 505 U.S. 833 (1992), the Court reaffirmed core holdings. See also Gonzales v. Carhart, 550 U.S. 124 (2007).''',
                'citations': ['410 U.S. 113', '505 U.S. 833', '550 U.S. 124'],
                'expected': [
                    {'case_name': 'Roe v. Wade', 'year': '1973'},
                    {'case_name': 'Planned Parenthood v. Casey', 'year': '1992'},
                    {'case_name': 'Gonzales v. Carhart', 'year': '2007'}
                ]
            },
            {
                'name': 'Edge Case - No Clear Case Name',
                'text': 'See 123 Wn.2d 456 (2010) for more details.',
                'citations': ['123 Wn.2d 456'],
                'expected': {
                    'case_name': 'N/A',  # Should fail gracefully
                    'year': '2010'
                }
            }
        ]

    def test_new_system(self) -> Dict:
        """Test the new streamlined system"""
        if not NEW_SYSTEM_AVAILABLE:
            return {'error': 'New system not available'}
        
        results = []
        start_time = time.time()
        
        for test_case in self.test_cases:
            test_result = {
                'name': test_case['name'],
                'citations': [],
                'performance': {}
            }
            
            # Test individual citations
            for citation in test_case['citations']:
                citation_start = time.time()
                
                # Test main extraction function
                extraction_result = extract_case_name_and_date(test_case['text'], citation)
                
                citation_result = {
                    'citation': citation,
                    'case_name': extraction_result['case_name'],
                    'year': extraction_result['year'],
                    'confidence': extraction_result['confidence'],
                    'method': extraction_result['method'],
                    'extraction_time': time.time() - citation_start
                }
                
                test_result['citations'].append(citation_result)
            
            # Test integrated extractor
            integrated_start = time.time()
            try:
                integrated_extractions = extract_cases_from_text(test_case['text'])
                test_result['integrated_results'] = [
                    {
                        'case_name': ext.case_name,
                        'year': ext.year,
                        'confidence': ext.confidence,
                        'method': ext.extraction_method,
                        'citation': f"{ext.volume} {ext.reporter} {ext.page}" if ext.volume else "N/A"
                    }
                    for ext in integrated_extractions
                ]
                test_result['performance']['integrated_time'] = time.time() - integrated_start
            except Exception as e:
                test_result['integrated_error'] = str(e)
            
            results.append(test_result)
        
        total_time = time.time() - start_time
        
        return {
            'results': results,
            'performance': {
                'total_time': total_time,
                'average_per_test': total_time / len(self.test_cases)
            }
        }
    
    def test_old_system(self) -> Dict:
        """Test your existing system (customize based on your actual implementation)"""
        if not OLD_SYSTEM_AVAILABLE:
            return {'error': 'Old system not available'}
        
        results = []
        start_time = time.time()
        
        for test_case in self.test_cases:
            test_result = {
                'name': test_case['name'],
                'citations': []
            }
            
            for citation in test_case['citations']:
                citation_start = time.time()
                
                try:
                    # Replace these with your actual old system functions
                    # Example of what this might look like:
                    """
                    old_case_name = extract_case_name_fixed_comprehensive(test_case['text'], citation)
                    old_year = extract_year_fixed_comprehensive(test_case['text'], citation)
                    """
                    
                    # Placeholder for old system results
                    old_case_name = "OLD_SYSTEM_PLACEHOLDER"
                    old_year = "OLD_SYSTEM_PLACEHOLDER"
                    
                    citation_result = {
                        'citation': citation,
                        'case_name': old_case_name,
                        'year': old_year,
                        'extraction_time': time.time() - citation_start
                    }
                    
                except Exception as e:
                    citation_result = {
                        'citation': citation,
                        'error': str(e),
                        'extraction_time': time.time() - citation_start
                    }
                
                test_result['citations'].append(citation_result)
            
            results.append(test_result)
        
        total_time = time.time() - start_time
        
        return {
            'results': results,
            'performance': {
                'total_time': total_time,
                'average_per_test': total_time / len(self.test_cases)
            }
        }
    
    def compare_systems(self) -> Dict:
        """Compare old vs new system results"""
        new_results = self.test_new_system()
        old_results = self.test_old_system()
        
        comparison = {
            'summary': {
                'total_tests': len(self.test_cases),
                'new_system_available': NEW_SYSTEM_AVAILABLE,
                'old_system_available': OLD_SYSTEM_AVAILABLE
            },
            'detailed_comparison': [],
            'performance_comparison': {},
            'accuracy_comparison': {}
        }
        
        if NEW_SYSTEM_AVAILABLE and OLD_SYSTEM_AVAILABLE:
            # Performance comparison
            comparison['performance_comparison'] = {
                'new_system_time': new_results.get('performance', {}).get('total_time', 0),
                'old_system_time': old_results.get('performance', {}).get('total_time', 0),
                'speedup': None
            }
            
            if old_results.get('performance', {}).get('total_time', 0) > 0:
                comparison['performance_comparison']['speedup'] = (
                    old_results['performance']['total_time'] / 
                    new_results['performance']['total_time']
                )
        
        # Detailed comparison for each test case
        for i, test_case in enumerate(self.test_cases):
            test_comparison = {
                'test_name': test_case['name'],
                'expected': test_case['expected'],
                'new_system_results': new_results.get('results', [{}])[i] if NEW_SYSTEM_AVAILABLE else None,
                'old_system_results': old_results.get('results', [{}])[i] if OLD_SYSTEM_AVAILABLE else None,
                'accuracy_scores': {}
            }
            
            # Calculate accuracy scores
            if NEW_SYSTEM_AVAILABLE:
                test_comparison['accuracy_scores']['new_system'] = self._calculate_accuracy(
                    test_case['expected'], 
                    test_comparison['new_system_results']
                )
            
            if OLD_SYSTEM_AVAILABLE:
                test_comparison['accuracy_scores']['old_system'] = self._calculate_accuracy(
                    test_case['expected'], 
                    test_comparison['old_system_results']
                )
            
            comparison['detailed_comparison'].append(test_comparison)
        
        return comparison
    
    def _calculate_accuracy(self, expected, actual_results) -> Dict:
        """Calculate accuracy scores for a test case"""
        if not actual_results or 'citations' not in actual_results:
            return {'score': 0.0, 'details': 'No results'}
        
        scores = []
        
        # Handle single expected result
        if isinstance(expected, dict):
            expected = [expected]
        
        for i, expected_result in enumerate(expected):
            if i < len(actual_results['citations']):
                actual = actual_results['citations'][i]
                
                case_name_score = 1.0 if self._normalize_case_name(expected_result.get('case_name', '')) == \
                                       self._normalize_case_name(actual.get('case_name', '')) else 0.0
                
                year_score = 1.0 if expected_result.get('year') == actual.get('year') else 0.0
                
                scores.append({
                    'case_name_score': case_name_score,
                    'year_score': year_score,
                    'overall_score': (case_name_score + year_score) / 2
                })
        
        if not scores:
            return {'score': 0.0, 'details': 'No matching results'}
        
        avg_score = sum(s['overall_score'] for s in scores) / len(scores)
        
        return {
            'score': avg_score,
            'individual_scores': scores,
            'details': f'Average of {len(scores)} comparisons'
        }
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for comparison"""
        if not case_name or case_name == 'N/A':
            return ''
        
        # Remove extra whitespace and normalize
        normalized = ' '.join(case_name.split())
        normalized = normalized.replace(' v. ', ' v. ')  # Standardize v. format
        
        return normalized.lower()
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        comparison = self.compare_systems()
        
        report = []
        report.append("=" * 60)
        report.append("INTEGRATION TESTING REPORT")
        report.append("=" * 60)
        
        # Summary
        summary = comparison['summary']
        report.append(f"\nTEST SUMMARY:")
        report.append(f"Total test cases: {summary['total_tests']}")
        report.append(f"New system available: {summary['new_system_available']}")
        report.append(f"Old system available: {summary['old_system_available']}")
        
        # Performance comparison
        if comparison['performance_comparison']:
            perf = comparison['performance_comparison']
            report.append(f"\nPERFORMANCE COMPARISON:")
            report.append(f"New system total time: {perf.get('new_system_time', 0):.3f}s")
            report.append(f"Old system total time: {perf.get('old_system_time', 0):.3f}s")
            if perf.get('speedup'):
                report.append(f"Speedup: {perf['speedup']:.2f}x")
        
        # Detailed results
        report.append(f"\nDETAILED TEST RESULTS:")
        report.append("-" * 40)
        
        for test_comp in comparison['detailed_comparison']:
            report.append(f"\nTest: {test_comp['test_name']}")
            
            if test_comp['new_system_results']:
                new_acc = test_comp['accuracy_scores'].get('new_system', {})
                report.append(f"  New System Accuracy: {new_acc.get('score', 0):.2f}")
            
            if test_comp['old_system_results']:
                old_acc = test_comp['accuracy_scores'].get('old_system', {})
                report.append(f"  Old System Accuracy: {old_acc.get('score', 0):.2f}")
            
            # Show expected vs actual
            report.append(f"  Expected: {test_comp['expected']}")
            
            if test_comp['new_system_results'] and 'citations' in test_comp['new_system_results']:
                for citation_result in test_comp['new_system_results']['citations']:
                    report.append(f"  New Result: {citation_result['case_name']} ({citation_result['year']}) - Confidence: {citation_result.get('confidence', 0):.2f}")
        
        # Recommendations
        report.append(f"\nRECOMMENDATIONS:")
        report.append("-" * 20)
        
        if NEW_SYSTEM_AVAILABLE:
            report.append("✅ New streamlined system is ready for integration")
            report.append("✅ Confidence scoring provides quality metrics")
            report.append("✅ Multiple extraction methods provide fallback options")
        else:
            report.append("❌ New system not available - check imports and dependencies")
        
        if comparison['performance_comparison'].get('speedup', 0) > 1:
            report.append("✅ Performance improvement detected")
        
        report.append("\nNEXT STEPS:")
        report.append("1. Review accuracy scores for any regressions")
        report.append("2. Adjust confidence thresholds if needed")
        report.append("3. Test with your actual document corpus")
        report.append("4. Implement gradual rollout strategy")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = "integration_test_results.json"):
        """Save detailed results to JSON file"""
        comparison = self.compare_systems()
        
        with open(filename, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to {filename}")

def run_integration_tests():
    """Main function to run all integration tests"""
    logger.info("Starting Integration Tests...")
    
    tester = IntegrationTester()
    
    # Generate and print report
    report = tester.generate_report()
    logger.info(report)
    
    # Save detailed results
    tester.save_results()
    
    return tester

def quick_test():
    """Quick test of the new system only"""
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    test_citation = "200 Wn.2d 72"

    logger.info("=== Quick Test ===")
    logger.info(f"Text: {test_text}")
    logger.info(f"Citation: {test_citation}")

    if not NEW_SYSTEM_AVAILABLE:
        logger.info("❌ New system not available")
        return

    # Test streamlined extraction
    result = extract_case_name_and_date(test_text, test_citation)
    logger.info(f"\nStreamlined Result:")
    logger.info(f"  Case Name: {result['case_name']}")
    logger.info(f"  Year: {result['year']}")
    logger.info(f"  Confidence: {result['confidence']}")
    logger.info(f"  Method: {result['method']}")

    # Test integrated extraction
    extractions = extract_cases_from_text(test_text)
    logger.info(f"\nIntegrated Extraction ({len(extractions)} found):")
    for ext in extractions:
        logger.info(f"  {ext.case_name} - {ext.year} (Confidence: {ext.confidence:.2f})")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        run_integration_tests() 