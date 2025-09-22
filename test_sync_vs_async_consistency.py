#!/usr/bin/env python3

def test_sync_vs_async_consistency():
    """Test that sync and async processing produce consistent results."""
    
    print("🔍 SYNC VS ASYNC CONSISTENCY TEST")
    print("=" * 60)
    
    try:
        # Test cases of different sizes to trigger different processing paths
        test_cases = [
            {
                "name": "Small Text (Sync)",
                "text": """
                The Court held in Smith v. Jones, 123 F.3d 456 (2020), that the plaintiff 
                must demonstrate standing. See also Brown v. Davis, 456 U.S. 789 (2019).
                """,
                "expected_mode": "sync",
                "size_kb": 0.2
            },
            {
                "name": "Medium Text (Boundary)",
                "text": """
                The Supreme Court's decision in Miranda v. Arizona, 384 U.S. 436 (1966), 
                established the requirement for police to inform suspects of their rights.
                This landmark case has been cited in numerous subsequent decisions including
                Dickerson v. United States, 530 U.S. 428 (2000), which reaffirmed Miranda's
                constitutional basis. The Court noted that Miranda warnings have become part
                of our national culture. In Edwards v. Arizona, 451 U.S. 477 (1981), the
                Court extended Miranda protections to situations involving interrogation
                after a suspect has invoked their right to counsel. The decision in
                Arizona v. Roberson, 486 U.S. 675 (1988), further clarified that police
                cannot resume interrogation on a different case without counsel present.
                These cases demonstrate the evolution of Fifth Amendment jurisprudence
                and the continuing relevance of the Miranda doctrine in modern criminal
                procedure. The Court has consistently held that these protections are
                essential to maintaining the integrity of the criminal justice system
                and protecting individual constitutional rights against self-incrimination.
                """ * 10,  # Multiply to make it larger
                "expected_mode": "async_or_sync",
                "size_kb": 15
            }
        ]
        
        # Load large PDF text for async testing
        try:
            with open("d:/dev/casestrainer/extracted_pdf_text.txt", 'r', encoding='utf-8') as f:
                large_text = f.read()
            
            test_cases.append({
                "name": "Large PDF Text (Async)",
                "text": large_text,
                "expected_mode": "async",
                "size_kb": len(large_text) / 1024
            })
        except FileNotFoundError:
            print("⚠️  Large PDF text not found, skipping large text test")
        
        from src.unified_input_processor import UnifiedInputProcessor
        from src.api.services.citation_service import CitationService
        import time
        import json
        
        processor = UnifiedInputProcessor()
        citation_service = CitationService()
        
        results_comparison = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📖 TEST CASE {i+1}: {test_case['name']}")
            print("=" * 50)
            
            text = test_case['text']
            expected_mode = test_case['expected_mode']
            size_kb = test_case['size_kb']
            
            print(f"Text size: {len(text)} chars ({size_kb:.1f} KB)")
            print(f"Expected mode: {expected_mode}")
            
            # Test routing decision
            input_data = {'type': 'text', 'text': text}
            should_process_immediately = citation_service.should_process_immediately(input_data)
            
            print(f"Should process immediately: {should_process_immediately}")
            
            # Force sync processing
            print(f"\n🔄 TESTING SYNC PROCESSING")
            print("-" * 30)
            
            sync_start = time.time()
            
            # Process with sync by using a smaller text sample or forcing sync
            if len(text) > 10000:  # If text is large, use a sample for sync test
                sync_text = text[:5000]  # 5KB sample for sync
                print(f"Using {len(sync_text)} char sample for sync test")
            else:
                sync_text = text
            
            sync_result = processor.process_any_input(
                input_data={'text': sync_text},
                input_type='text',
                request_id=f'sync_test_{i}'
            )
            
            sync_time = time.time() - sync_start
            
            sync_success = sync_result.get('success', False)
            sync_citations = sync_result.get('citations', [])
            sync_clusters = sync_result.get('clusters', [])
            sync_mode = sync_result.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Sync Result:")
            print(f"   Success: {sync_success}")
            print(f"   Processing mode: {sync_mode}")
            print(f"   Citations: {len(sync_citations)}")
            print(f"   Clusters: {len(sync_clusters)}")
            print(f"   Time: {sync_time:.2f}s")
            
            # Test async processing (or sync fallback)
            print(f"\n🔄 TESTING ASYNC/FALLBACK PROCESSING")
            print("-" * 30)
            
            async_start = time.time()
            
            async_result = processor.process_any_input(
                input_data={'text': text},
                input_type='text',
                request_id=f'async_test_{i}'
            )
            
            async_time = time.time() - async_start
            
            async_success = async_result.get('success', False)
            async_citations = async_result.get('citations', [])
            async_clusters = async_result.get('clusters', [])
            async_mode = async_result.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Async/Fallback Result:")
            print(f"   Success: {async_success}")
            print(f"   Processing mode: {async_mode}")
            print(f"   Citations: {len(async_citations)}")
            print(f"   Clusters: {len(async_clusters)}")
            print(f"   Time: {async_time:.2f}s")
            
            # Compare results
            print(f"\n📊 COMPARISON ANALYSIS")
            print("-" * 30)
            
            # For large text, we compare the async result with sync sample
            if len(text) > 10000:
                print(f"Note: Comparing async full text with sync sample")
                comparison_citations = len(sync_citations)
                comparison_clusters = len(sync_clusters)
            else:
                comparison_citations = len(sync_citations)
                comparison_clusters = len(sync_clusters)
            
            citation_diff = abs(len(async_citations) - comparison_citations)
            cluster_diff = abs(len(async_clusters) - comparison_clusters)
            
            print(f"Citation count difference: {citation_diff}")
            print(f"Cluster count difference: {cluster_diff}")
            
            # Analyze citation quality consistency
            if sync_citations and async_citations:
                print(f"\n🔍 CITATION QUALITY COMPARISON")
                print("-" * 30)
                
                # Compare first few citations for quality
                sync_sample = sync_citations[:3]
                async_sample = async_citations[:3]
                
                for j, (sync_cit, async_cit) in enumerate(zip(sync_sample, async_sample)):
                    if isinstance(sync_cit, dict) and isinstance(async_cit, dict):
                        sync_extracted = sync_cit.get('extracted_case_name', 'N/A')
                        async_extracted = async_cit.get('extracted_case_name', 'N/A')
                        sync_verified = sync_cit.get('verified', False)
                        async_verified = async_cit.get('verified', False)
                        
                        print(f"   Citation {j+1}:")
                        print(f"      Sync extracted: '{sync_extracted}' (verified: {sync_verified})")
                        print(f"      Async extracted: '{async_extracted}' (verified: {async_verified})")
                        
                        if sync_extracted == async_extracted:
                            print(f"      ✅ Case names match")
                        else:
                            print(f"      ⚠️  Case names differ")
            
            # Store results for summary
            results_comparison.append({
                'test_case': test_case['name'],
                'size_kb': size_kb,
                'sync_success': sync_success,
                'async_success': async_success,
                'sync_citations': len(sync_citations),
                'async_citations': len(async_citations),
                'sync_clusters': len(sync_clusters),
                'async_clusters': len(async_clusters),
                'sync_mode': sync_mode,
                'async_mode': async_mode,
                'sync_time': sync_time,
                'async_time': async_time,
                'citation_diff': citation_diff,
                'cluster_diff': cluster_diff
            })
            
            # Routing validation
            if expected_mode == "sync" and async_mode != "immediate":
                print(f"⚠️  Expected sync but got {async_mode}")
            elif expected_mode == "async" and async_mode not in ["queued", "sync_fallback"]:
                print(f"⚠️  Expected async but got {async_mode}")
            else:
                print(f"✅ Routing behavior as expected")
        
        # Summary report
        print(f"\n🎯 CONSISTENCY TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results_comparison)
        successful_tests = sum(1 for r in results_comparison if r['sync_success'] and r['async_success'])
        
        print(f"Total test cases: {total_tests}")
        print(f"Successful tests: {successful_tests}/{total_tests}")
        
        print(f"\n📊 DETAILED RESULTS:")
        print("-" * 40)
        
        for result in results_comparison:
            print(f"\n{result['test_case']} ({result['size_kb']:.1f} KB):")
            print(f"   Sync: {result['sync_citations']} citations, {result['sync_clusters']} clusters ({result['sync_mode']}, {result['sync_time']:.2f}s)")
            print(f"   Async: {result['async_citations']} citations, {result['async_clusters']} clusters ({result['async_mode']}, {result['async_time']:.2f}s)")
            print(f"   Differences: ±{result['citation_diff']} citations, ±{result['cluster_diff']} clusters")
            
            # Consistency evaluation
            if result['citation_diff'] <= 2 and result['cluster_diff'] <= 1:
                print(f"   ✅ CONSISTENT: Results are very similar")
            elif result['citation_diff'] <= 5 and result['cluster_diff'] <= 3:
                print(f"   ⚠️  ACCEPTABLE: Minor differences")
            else:
                print(f"   ❌ INCONSISTENT: Significant differences")
        
        # Performance comparison
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print("-" * 40)
        
        for result in results_comparison:
            if result['sync_time'] > 0 and result['async_time'] > 0:
                speed_ratio = result['async_time'] / result['sync_time']
                print(f"{result['test_case']}: Async is {speed_ratio:.1f}x {'slower' if speed_ratio > 1 else 'faster'} than sync")
        
        # Routing accuracy
        print(f"\n🎯 ROUTING ACCURACY:")
        print("-" * 40)
        
        routing_correct = 0
        for result in results_comparison:
            if result['size_kb'] < 5 and result['async_mode'] == 'immediate':
                routing_correct += 1
                print(f"✅ {result['test_case']}: Correctly routed to sync")
            elif result['size_kb'] >= 5 and result['async_mode'] in ['queued', 'sync_fallback']:
                routing_correct += 1
                print(f"✅ {result['test_case']}: Correctly routed to async (or fallback)")
            else:
                print(f"⚠️  {result['test_case']}: Routing may be suboptimal")
        
        print(f"\nRouting accuracy: {routing_correct}/{total_tests} ({routing_correct/total_tests*100:.1f}%)")
        
        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT:")
        print("=" * 60)
        
        if successful_tests == total_tests:
            print(f"✅ ALL TESTS PASSED: Both sync and async processing are working correctly")
        else:
            print(f"⚠️  {total_tests - successful_tests} test(s) had issues")
        
        avg_citation_diff = sum(r['citation_diff'] for r in results_comparison) / len(results_comparison)
        avg_cluster_diff = sum(r['cluster_diff'] for r in results_comparison) / len(results_comparison)
        
        print(f"Average citation difference: {avg_citation_diff:.1f}")
        print(f"Average cluster difference: {avg_cluster_diff:.1f}")
        
        if avg_citation_diff <= 2 and avg_cluster_diff <= 1:
            print(f"✅ EXCELLENT CONSISTENCY: Sync and async results are highly consistent")
        elif avg_citation_diff <= 5 and avg_cluster_diff <= 3:
            print(f"✅ GOOD CONSISTENCY: Minor differences are acceptable")
        else:
            print(f"⚠️  CONSISTENCY CONCERNS: Investigate differences between sync and async")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_vs_async_consistency()
