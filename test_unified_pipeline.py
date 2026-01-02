#!/usr/bin/env python3
"""
UNIFIED PIPELINE TEST SUITE

Comprehensive tests to ensure the unified processing pipeline works correctly
and prevent future regressions. This tests the entire flow from input to output.

TEST COVERAGE:
1. Parallel verification functionality
2. Position data preservation  
3. Processing stage execution
4. Error handling and recovery
5. Response format consistency
6. Performance benchmarks
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_processing_pipeline import process_citations_unified

class UnifiedPipelineTester:
    """Test suite for the unified processing pipeline"""
    
    def __init__(self):
        self.test_results = []
        self.parallel_test_cases = [
            # Case 1: User's example - should mark second citation as parallel
            {
                'name': 'Gresser v. Banner Health - Parallel Verification',
                'text': 'Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059.',
                'expected_parallel_count': 1,
                'expected_total_citations': 2,
                'expected_verified_count': 2
            },
            # Case 2: Single citation - no parallel verification
            {
                'name': 'Single Citation - No Parallel',
                'text': 'Smith v. Jones, 123 F.3d 456.',
                'expected_parallel_count': 0,
                'expected_total_citations': 1,
                'expected_verified_count': 1
            },
            # Case 3: Multiple parallel citations
            {
                'name': 'Multiple Parallel Citations',
                'text': 'Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873.',
                'expected_parallel_count': 2,  # S. Ct. and L. Ed. should be parallel
                'expected_total_citations': 3,
                'expected_verified_count': 3
            }
        ]
    
    async def run_all_tests(self):
        """Run all test cases"""
        print("🧪 UNIFIED PIPELINE TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Parallel Verification Functionality
        await self.test_parallel_verification()
        
        # Test 2: Position Data Preservation
        await self.test_position_data_preservation()
        
        # Test 3: Processing Stage Tracing
        await self.test_processing_stages()
        
        # Test 4: Error Handling
        await self.test_error_handling()
        
        # Test 5: Response Format Consistency
        await self.test_response_format()
        
        # Test 6: Performance Benchmarks
        await self.test_performance()
        
        # Summary
        elapsed = time.time() - start_time
        self.print_summary(elapsed)
    
    async def test_parallel_verification(self):
        """Test that parallel verification works correctly"""
        print("\n📋 TEST 1: Parallel Verification Functionality")
        print("-" * 50)
        
        for i, test_case in enumerate(self.parallel_test_cases):
            print(f"\n  Test 1.{i+1}: {test_case['name']}")
            
            try:
                result = await process_citations_unified(
                    test_case['text'], 
                    trace_id=f"PARALLEL_TEST_{i+1}"
                )
                
                citations = result.get('citations', [])
                metadata = result.get('metadata', {})
                
                # Check citation count
                actual_total = len(citations)
                expected_total = test_case['expected_total_citations']
                total_pass = actual_total == expected_total
                
                # Check parallel verification count
                actual_parallel = sum(1 for c in citations if c.get('true_by_parallel', False))
                expected_parallel = test_case['expected_parallel_count']
                parallel_pass = actual_parallel == expected_parallel
                
                # Check verified count
                actual_verified = sum(1 for c in citations if c.get('verified', False))
                expected_verified = test_case['expected_verified_count']
                verified_pass = actual_verified == expected_verified
                
                # Overall result
                test_passed = total_pass and parallel_pass and verified_pass
                
                print(f"    Citations: {actual_total}/{expected_total} {'✅' if total_pass else '❌'}")
                print(f"    Parallel: {actual_parallel}/{expected_parallel} {'✅' if parallel_pass else '❌'}")
                print(f"    Verified: {actual_verified}/{expected_verified} {'✅' if verified_pass else '❌'}")
                print(f"    Result: {'✅ PASS' if test_passed else '❌ FAIL'}")
                
                if not test_passed:
                    print(f"    Citations found:")
                    for j, cit in enumerate(citations):
                        print(f"      {j+1}. {cit.get('citation')}: verified={cit.get('verified')}, true_by_parallel={cit.get('true_by_parallel')}")
                
                self.test_results.append({
                    'test': f"Parallel Verification {i+1}",
                    'name': test_case['name'],
                    'passed': test_passed,
                    'details': {
                        'total_citations': f"{actual_total}/{expected_total}",
                        'parallel_verifications': f"{actual_parallel}/{expected_parallel}",
                        'verified_citations': f"{actual_verified}/{expected_verified}"
                    }
                })
                
            except Exception as e:
                print(f"    ❌ EXCEPTION: {e}")
                self.test_results.append({
                    'test': f"Parallel Verification {i+1}",
                    'name': test_case['name'],
                    'passed': False,
                    'error': str(e)
                })
    
    async def test_position_data_preservation(self):
        """Test that position data is preserved throughout the pipeline"""
        print("\n📋 TEST 2: Position Data Preservation")
        print("-" * 50)
        
        test_text = "Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059."
        
        try:
            result = await process_citations_unified(test_text, trace_id="POSITION_TEST")
            citations = result.get('citations', [])
            
            position_valid_count = 0
            position_invalid_count = 0
            
            for i, cit in enumerate(citations):
                start_idx = cit.get('start_index')
                end_idx = cit.get('end_index')
                
                if start_idx is not None and end_idx is not None:
                    position_valid_count += 1
                    print(f"    Citation {i+1}: {cit.get('citation')} - Position {start_idx}-{end_idx} ✅")
                else:
                    position_invalid_count += 1
                    print(f"    Citation {i+1}: {cit.get('citation')} - Position {start_idx}-{end_idx} ❌")
            
            test_passed = position_invalid_count == 0
            print(f"    Result: {position_valid_count}/{len(citations)} citations have valid position data")
            print(f"    Overall: {'✅ PASS' if test_passed else '❌ FAIL'}")
            
            self.test_results.append({
                'test': 'Position Data Preservation',
                'passed': test_passed,
                'details': {
                    'valid_positions': position_valid_count,
                    'invalid_positions': position_invalid_count,
                    'total_citations': len(citations)
                }
            })
            
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            self.test_results.append({
                'test': 'Position Data Preservation',
                'passed': False,
                'error': str(e)
            })
    
    async def test_processing_stages(self):
        """Test that all processing stages are executed"""
        print("\n📋 TEST 3: Processing Stage Tracing")
        print("-" * 50)
        
        test_text = "Smith v. Jones, 123 F.3d 456."
        
        try:
            result = await process_citations_unified(test_text, trace_id="STAGE_TEST")
            metadata = result.get('metadata', {})
            
            expected_stages = ['extraction', 'verification', 'formatting', 'completed']
            actual_stages = metadata.get('stages_completed', [])
            
            print(f"    Expected stages: {expected_stages}")
            print(f"    Actual stages: {actual_stages}")
            
            missing_stages = [stage for stage in expected_stages if stage not in actual_stages]
            unexpected_stages = [stage for stage in actual_stages if stage not in expected_stages]
            
            test_passed = len(missing_stages) == 0 and len(unexpected_stages) == 0
            
            if missing_stages:
                print(f"    Missing stages: {missing_stages} ❌")
            if unexpected_stages:
                print(f"    Unexpected stages: {unexpected_stages} ⚠️")
            
            print(f"    Result: {'✅ PASS' if test_passed else '❌ FAIL'}")
            
            self.test_results.append({
                'test': 'Processing Stage Tracing',
                'passed': test_passed,
                'details': {
                    'expected_stages': expected_stages,
                    'actual_stages': actual_stages,
                    'missing_stages': missing_stages,
                    'unexpected_stages': unexpected_stages
                }
            })
            
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            self.test_results.append({
                'test': 'Processing Stage Tracing',
                'passed': False,
                'error': str(e)
            })
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        print("\n📋 TEST 4: Error Handling")
        print("-" * 50)
        
        # Test with empty text
        try:
            result = await process_citations_unified("", trace_id="ERROR_TEST_EMPTY")
            
            # Should return empty result without crashing
            citations = result.get('citations', [])
            metadata = result.get('metadata', {})
            
            empty_text_pass = len(citations) == 0 and metadata.get('status') in ['completed', 'completed_with_errors']
            
            print(f"    Empty text: {len(citations)} citations, status={metadata.get('status')} {'✅' if empty_text_pass else '❌'}")
            
            self.test_results.append({
                'test': 'Error Handling - Empty Text',
                'passed': empty_text_pass,
                'details': {
                    'citation_count': len(citations),
                    'status': metadata.get('status')
                }
            })
            
        except Exception as e:
            print(f"    Empty text: ❌ EXCEPTION: {e}")
            self.test_results.append({
                'test': 'Error Handling - Empty Text',
                'passed': False,
                'error': str(e)
            })
    
    async def test_response_format(self):
        """Test response format consistency"""
        print("\n📋 TEST 5: Response Format Consistency")
        print("-" * 50)
        
        test_text = "Test v. Case, 123 F.3d 456."
        
        try:
            result = await process_citations_unified(test_text, trace_id="FORMAT_TEST")
            
            # Check required top-level fields
            required_fields = ['citations', 'clusters', 'metadata']
            missing_fields = [field for field in required_fields if field not in result]
            
            # Check metadata fields
            metadata = result.get('metadata', {})
            required_metadata = ['processing_mode', 'trace_id', 'processing_time_ms', 'status']
            missing_metadata = [field for field in required_metadata if field not in metadata]
            
            # Check citation fields
            citations = result.get('citations', [])
            citation_issues = []
            
            for i, cit in enumerate(citations):
                required_citation_fields = ['citation', 'verified', 'true_by_parallel']
                missing_citation_fields = [field for field in required_citation_fields if field not in cit]
                if missing_citation_fields:
                    citation_issues.append(f"Citation {i+1}: missing {missing_citation_fields}")
            
            test_passed = (len(missing_fields) == 0 and 
                          len(missing_metadata) == 0 and 
                          len(citation_issues) == 0)
            
            print(f"    Top-level fields: {required_fields} - Missing: {missing_fields} {'✅' if len(missing_fields) == 0 else '❌'}")
            print(f"    Metadata fields: {required_metadata} - Missing: {missing_metadata} {'✅' if len(missing_metadata) == 0 else '❌'}")
            if citation_issues:
                for issue in citation_issues:
                    print(f"    {issue} ❌")
            else:
                print(f"    Citation fields: All present ✅")
            
            print(f"    Result: {'✅ PASS' if test_passed else '❌ FAIL'}")
            
            self.test_results.append({
                'test': 'Response Format Consistency',
                'passed': test_passed,
                'details': {
                    'missing_top_level_fields': missing_fields,
                    'missing_metadata_fields': missing_metadata,
                    'citation_issues': citation_issues
                }
            })
            
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            self.test_results.append({
                'test': 'Response Format Consistency',
                'passed': False,
                'error': str(e)
            })
    
    async def test_performance(self):
        """Test performance benchmarks"""
        print("\n📋 TEST 6: Performance Benchmarks")
        print("-" * 50)
        
        # Test with different text sizes
        test_cases = [
            {'name': 'Short text (50 chars)', 'text': 'Smith v. Jones, 123 F.3d 456.'},
            {'name': 'Medium text (500 chars)', 'text': 'Test case. ' * 20 + 'Smith v. Jones, 123 F.3d 456. ' + 'More text. ' * 20},
            {'name': 'Long text (2000 chars)', 'text': 'Test case. ' * 100 + 'Smith v. Jones, 123 F.3d 456. ' + 'More text. ' * 100}
        ]
        
        performance_thresholds = {
            'Short text (50 chars)': 5.0,    # 5 seconds
            'Medium text (500 chars)': 10.0,  # 10 seconds  
            'Long text (2000 chars)': 20.0    # 20 seconds
        }
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                result = await process_citations_unified(test_case['text'], trace_id="PERF_TEST")
                elapsed = time.time() - start_time
                
                threshold = performance_thresholds[test_case['name']]
                performance_pass = elapsed <= threshold
                
                print(f"    {test_case['name']}: {elapsed:.2f}s (threshold: {threshold}s) {'✅' if performance_pass else '❌'}")
                
                self.test_results.append({
                    'test': f"Performance - {test_case['name']}",
                    'passed': performance_pass,
                    'details': {
                        'elapsed_time': elapsed,
                        'threshold': threshold,
                        'citation_count': len(result.get('citations', []))
                    }
                })
                
            except Exception as e:
                print(f"    {test_case['name']}: ❌ EXCEPTION: {e}")
                self.test_results.append({
                    'test': f"Performance - {test_case['name']}",
                    'passed': False,
                    'error': str(e)
                })
    
    def print_summary(self, total_elapsed: float):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Time: {total_elapsed:.2f}s")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result.get('error', 'See details')}")
                    if 'details' in result:
                        print(f"    Details: {result['details']}")
        
        print("\n" + "=" * 60)
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! The unified pipeline is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        # Save results to file
        results_file = "unified_pipeline_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'total_elapsed': total_elapsed,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")

async def main():
    """Run the test suite"""
    tester = UnifiedPipelineTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
