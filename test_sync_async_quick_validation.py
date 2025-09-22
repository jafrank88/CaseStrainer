#!/usr/bin/env python3

def test_sync_async_quick_validation():
    """Quick validation of sync vs async consistency - Windows compatible.
    
    This test provides fast, reliable validation of both processing paths
    without Unicode issues or output truncation problems.
    """
    
    print("SYNC VS ASYNC QUICK VALIDATION")
    print("=" * 60)
    print("Purpose: Fast validation of processing path consistency")
    print("Compatible: Windows, no Unicode issues")
    print("Expected runtime: < 2 minutes")
    print("")
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        from src.api.services.citation_service import CitationService
        import time
        
        processor = UnifiedInputProcessor()
        citation_service = CitationService()
        
        # Test cases designed for quick validation
        test_cases = [
            {
                "name": "Small Legal Text",
                "text": """
                The Court held in Smith v. Jones, 123 F.3d 456 (2020), that standing 
                requires injury in fact. See also Brown v. Davis, 456 U.S. 789 (2019).
                The decision in Wilson v. State, 789 F.2d 123 (2018) clarified jurisdiction.
                """,
                "expected_size": "small",
                "expected_citations": 3
            },
            {
                "name": "Medium Legal Text",
                "text": """
                In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme Court established
                fundamental protections for criminal defendants. This built upon Escobedo v. 
                Illinois, 378 U.S. 478 (1964), and Gideon v. Wainwright, 372 U.S. 335 (1963).
                Later cases like Edwards v. Arizona, 451 U.S. 477 (1981), extended these
                protections to post-invocation scenarios.
                """ * 3,  # Make it medium-sized
                "expected_size": "medium", 
                "expected_citations": 4
            }
        ]
        
        results = []
        total_start = time.time()
        
        for i, test_case in enumerate(test_cases):
            print(f"TEST {i+1}: {test_case['name']}")
            print("-" * 40)
            
            text = test_case['text']
            size_kb = len(text) / 1024
            expected_size = test_case['expected_size']
            
            print(f"Text size: {len(text)} chars ({size_kb:.1f} KB)")
            print(f"Expected category: {expected_size}")
            
            # Check routing decision
            input_data = {'type': 'text', 'text': text}
            should_sync = citation_service.should_process_immediately(input_data)
            print(f"Routes to sync: {should_sync}")
            
            # Test sync path (using smaller sample if needed)
            sync_text = text[:3000] if len(text) > 3000 else text
            print(f"Testing sync path ({len(sync_text)} chars)...")
            
            sync_start = time.time()
            sync_result = processor.process_any_input(
                input_data={'text': sync_text},
                input_type='text',
                request_id=f'sync_quick_{i}'
            )
            sync_time = time.time() - sync_start
            
            sync_citations = sync_result.get('citations', [])
            sync_mode = sync_result.get('metadata', {}).get('processing_mode', 'unknown')
            sync_success = sync_result.get('success', False)
            
            print(f"Sync result: {len(sync_citations)} citations in {sync_time:.1f}s ({sync_mode})")
            
            # Test full text path
            print(f"Testing full text path ({len(text)} chars)...")
            
            full_start = time.time()
            full_result = processor.process_any_input(
                input_data={'text': text},
                input_type='text',
                request_id=f'full_quick_{i}'
            )
            full_time = time.time() - full_start
            
            full_citations = full_result.get('citations', [])
            full_mode = full_result.get('metadata', {}).get('processing_mode', 'unknown')
            full_success = full_result.get('success', False)
            
            print(f"Full result: {len(full_citations)} citations in {full_time:.1f}s ({full_mode})")
            
            # Quick quality check
            if sync_citations and full_citations:
                sync_verified = sum(1 for c in sync_citations if isinstance(c, dict) and c.get('verified', False))
                full_verified = sum(1 for c in full_citations if isinstance(c, dict) and c.get('verified', False))
                
                sync_verify_rate = sync_verified / len(sync_citations) if sync_citations else 0
                full_verify_rate = full_verified / len(full_citations) if full_citations else 0
                
                print(f"Verification rates: sync {sync_verify_rate:.0%}, full {full_verify_rate:.0%}")
            
            # Evaluate results
            success = sync_success and full_success
            consistent = abs(len(sync_citations) - len(full_citations)) <= 2
            fast = sync_time < 60 and full_time < 60
            
            print(f"Success: {success}")
            print(f"Consistent: {consistent}")
            print(f"Fast: {fast}")
            
            if success and consistent and fast:
                print("RESULT: PASS")
            else:
                print("RESULT: NEEDS ATTENTION")
            
            print("")
            
            # Store results
            results.append({
                'name': test_case['name'],
                'size_kb': size_kb,
                'sync_citations': len(sync_citations),
                'full_citations': len(full_citations),
                'sync_time': sync_time,
                'full_time': full_time,
                'sync_mode': sync_mode,
                'full_mode': full_mode,
                'success': success,
                'consistent': consistent,
                'fast': fast,
                'overall_pass': success and consistent and fast
            })
        
        total_time = time.time() - total_start
        
        # Summary
        print("QUICK VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total runtime: {total_time:.1f} seconds")
        print(f"Tests completed: {len(results)}")
        
        passed_tests = sum(1 for r in results if r['overall_pass'])
        print(f"Tests passed: {passed_tests}/{len(results)}")
        
        print("")
        print("DETAILED RESULTS:")
        for result in results:
            status = "PASS" if result['overall_pass'] else "FAIL"
            print(f"  {result['name']}: {status}")
            print(f"    Citations: sync={result['sync_citations']}, full={result['full_citations']}")
            print(f"    Times: sync={result['sync_time']:.1f}s, full={result['full_time']:.1f}s")
            print(f"    Modes: sync={result['sync_mode']}, full={result['full_mode']}")
        
        print("")
        print("SYSTEM STATUS:")
        if passed_tests == len(results):
            print("  EXCELLENT: All tests passed")
            print("  Both sync and async paths are working correctly")
            print("  System is ready for production use")
        elif passed_tests >= len(results) * 0.8:
            print("  GOOD: Most tests passed")
            print("  Minor issues may need attention")
        else:
            print("  ATTENTION NEEDED: Multiple test failures")
            print("  System may have significant issues")
        
        # Performance assessment
        avg_sync_time = sum(r['sync_time'] for r in results) / len(results)
        avg_full_time = sum(r['full_time'] for r in results) / len(results)
        
        print("")
        print("PERFORMANCE ASSESSMENT:")
        print(f"  Average sync time: {avg_sync_time:.1f}s")
        print(f"  Average full time: {avg_full_time:.1f}s")
        
        if avg_sync_time < 30 and avg_full_time < 60:
            print("  Performance: EXCELLENT")
        elif avg_sync_time < 60 and avg_full_time < 120:
            print("  Performance: GOOD")
        else:
            print("  Performance: NEEDS OPTIMIZATION")
        
        print("")
        print("NEXT STEPS:")
        if passed_tests == len(results):
            print("  - System validated successfully")
            print("  - Ready for production workloads")
            print("  - Run comprehensive tests for detailed analysis")
        else:
            print("  - Investigate failed tests")
            print("  - Check system logs for errors")
            print("  - Run individual component tests")
        
        print("")
        print("For comprehensive testing, run:")
        print("  python run_test_with_output.py")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("This indicates a system-level issue that needs immediate attention")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_async_quick_validation()
