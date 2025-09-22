#!/usr/bin/env python3

def test_async_path_validation():
    """Test the async processing path specifically with large content."""
    
    print("🔍 ASYNC PATH VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Load large PDF text to force async processing
        try:
            with open("d:/dev/casestrainer/extracted_pdf_text.txt", 'r', encoding='utf-8') as f:
                large_text = f.read()
        except FileNotFoundError:
            print("❌ Large PDF text not found. Please run extract_pdf_text.py first")
            return
        
        size_kb = len(large_text) / 1024
        print(f"📊 Large document size: {len(large_text)} chars ({size_kb:.1f} KB)")
        
        from src.unified_input_processor import UnifiedInputProcessor
        from src.api.services.citation_service import CitationService
        import time
        
        processor = UnifiedInputProcessor()
        citation_service = CitationService()
        
        # Test routing decision
        print(f"\n📊 TESTING ROUTING DECISION")
        print("-" * 40)
        
        input_data = {'type': 'text', 'text': large_text}
        should_process_immediately = citation_service.should_process_immediately(input_data)
        
        print(f"Should process immediately: {should_process_immediately}")
        print(f"Expected: False (should route to async for {size_kb:.1f}KB)")
        
        if should_process_immediately:
            print("⚠️  WARNING: Large content incorrectly routed to sync")
        else:
            print("✅ CORRECT: Large content routed to async")
        
        # Test 1: Small sample (sync baseline)
        print(f"\n🔄 BASELINE: SYNC PROCESSING (5KB sample)")
        print("-" * 40)
        
        sync_sample = large_text[:5000]  # 5KB sample
        
        sync_start = time.time()
        sync_result = processor.process_any_input(
            input_data={'text': sync_sample},
            input_type='text',
            request_id='sync_baseline'
        )
        sync_time = time.time() - sync_start
        
        sync_success = sync_result.get('success', False)
        sync_citations = sync_result.get('citations', [])
        sync_clusters = sync_result.get('clusters', [])
        sync_mode = sync_result.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"✅ Sync Baseline:")
        print(f"   Success: {sync_success}")
        print(f"   Mode: {sync_mode}")
        print(f"   Citations: {len(sync_citations)}")
        print(f"   Clusters: {len(sync_clusters)}")
        print(f"   Time: {sync_time:.2f}s")
        
        # Analyze sync quality
        if sync_citations:
            verified_sync = sum(1 for c in sync_citations if isinstance(c, dict) and c.get('verified', False))
            print(f"   Verified: {verified_sync}/{len(sync_citations)} ({verified_sync/len(sync_citations):.1%})")
            
            # Show sample citations
            for i, citation in enumerate(sync_citations[:3]):
                if isinstance(citation, dict):
                    cit_text = citation.get('citation', 'N/A')
                    extracted = citation.get('extracted_case_name', 'N/A')
                    verified = citation.get('verified', False)
                    print(f"   Sample {i+1}: {cit_text} -> '{extracted}' (verified: {verified})")
        
        # Test 2: Full document (async/fallback)
        print(f"\n🔄 FULL DOCUMENT: ASYNC/FALLBACK PROCESSING")
        print("-" * 40)
        
        full_start = time.time()
        full_result = processor.process_any_input(
            input_data={'text': large_text},
            input_type='text',
            request_id='full_document'
        )
        full_time = time.time() - full_start
        
        full_success = full_result.get('success', False)
        full_citations = full_result.get('citations', [])
        full_clusters = full_result.get('clusters', [])
        full_mode = full_result.get('metadata', {}).get('processing_mode', 'unknown')
        task_id = full_result.get('task_id')
        
        print(f"✅ Full Document Result:")
        print(f"   Success: {full_success}")
        print(f"   Mode: {full_mode}")
        print(f"   Citations: {len(full_citations)}")
        print(f"   Clusters: {len(full_clusters)}")
        print(f"   Time: {full_time:.2f}s")
        print(f"   Task ID: {task_id}")
        
        # Analyze processing mode
        if full_mode == 'queued':
            print(f"   ✅ ASYNC: Successfully queued for async processing")
        elif full_mode == 'sync_fallback':
            print(f"   ⚠️  FALLBACK: Processed synchronously due to Redis unavailability")
        elif full_mode == 'immediate':
            print(f"   ❌ SYNC: Large content processed synchronously (routing issue)")
        else:
            print(f"   ❓ UNKNOWN: Unexpected processing mode")
        
        # Analyze full document quality
        if full_citations:
            verified_full = sum(1 for c in full_citations if isinstance(c, dict) and c.get('verified', False))
            print(f"   Verified: {verified_full}/{len(full_citations)} ({verified_full/len(full_citations):.1%})")
            
            # Check for short/problematic case names
            short_names = []
            for citation in full_citations:
                if isinstance(citation, dict):
                    extracted = citation.get('extracted_case_name', 'N/A')
                    if extracted != 'N/A' and len(extracted) < 10:
                        short_names.append(extracted)
            
            print(f"   Short names: {len(short_names)}")
            if short_names:
                print(f"   Examples: {short_names[:3]}")
        
        # Compare sync vs full results
        print(f"\n📊 SYNC VS ASYNC/FALLBACK COMPARISON")
        print("-" * 40)
        
        # Scale sync results to estimate full document
        sync_density = len(sync_citations) / len(sync_sample) if sync_sample else 0
        estimated_full = int(sync_density * len(large_text))
        
        print(f"Citation density (sync): {sync_density:.6f} citations/char")
        print(f"Estimated full citations: {estimated_full}")
        print(f"Actual full citations: {len(full_citations)}")
        
        if len(full_citations) > 0:
            accuracy = min(len(full_citations), estimated_full) / max(len(full_citations), estimated_full)
            print(f"Scaling accuracy: {accuracy:.1%}")
            
            if len(full_citations) >= estimated_full * 0.8:
                print(f"✅ GOOD: Full processing found expected number of citations")
            else:
                print(f"⚠️  LOW: Full processing found fewer citations than expected")
        
        # Performance comparison
        if sync_time > 0 and full_time > 0:
            time_per_char_sync = sync_time / len(sync_sample)
            time_per_char_full = full_time / len(large_text)
            
            print(f"\nPerformance per character:")
            print(f"   Sync: {time_per_char_sync:.8f} s/char")
            print(f"   Full: {time_per_char_full:.8f} s/char")
            
            if time_per_char_full <= time_per_char_sync * 1.5:
                print(f"✅ EFFICIENT: Full processing scales well")
            else:
                print(f"⚠️  SLOW: Full processing is less efficient")
        
        # Quality comparison (if both have results)
        if sync_citations and full_citations:
            print(f"\n🔍 QUALITY COMPARISON")
            print("-" * 40)
            
            # Compare verification rates
            sync_verified_rate = verified_sync / len(sync_citations) if sync_citations else 0
            full_verified_rate = verified_full / len(full_citations) if full_citations else 0
            
            print(f"Verification rates:")
            print(f"   Sync: {sync_verified_rate:.1%}")
            print(f"   Full: {full_verified_rate:.1%}")
            
            if abs(sync_verified_rate - full_verified_rate) <= 0.1:
                print(f"✅ CONSISTENT: Similar verification rates")
            else:
                print(f"⚠️  DIFFERENT: Verification rates differ significantly")
        
        # Final assessment
        print(f"\n🏆 ASYNC PATH ASSESSMENT")
        print("=" * 60)
        
        assessment_score = 0
        total_checks = 5
        
        # Check 1: Routing correctness
        if not should_process_immediately:
            print(f"✅ Routing: Large content correctly identified for async")
            assessment_score += 1
        else:
            print(f"❌ Routing: Large content incorrectly routed to sync")
        
        # Check 2: Processing success
        if full_success:
            print(f"✅ Processing: Full document processed successfully")
            assessment_score += 1
        else:
            print(f"❌ Processing: Full document processing failed")
        
        # Check 3: Citation extraction
        if len(full_citations) > 0:
            print(f"✅ Extraction: Citations found in full document ({len(full_citations)})")
            assessment_score += 1
        else:
            print(f"❌ Extraction: No citations found in full document")
        
        # Check 4: Verification system
        if full_citations and verified_full > 0:
            print(f"✅ Verification: Citations verified successfully ({verified_full}/{len(full_citations)})")
            assessment_score += 1
        else:
            print(f"❌ Verification: No citations verified")
        
        # Check 5: Performance
        if full_time < 120:  # Less than 2 minutes for 66KB
            print(f"✅ Performance: Processing completed in reasonable time ({full_time:.1f}s)")
            assessment_score += 1
        else:
            print(f"⚠️  Performance: Processing took longer than expected ({full_time:.1f}s)")
        
        print(f"\nOverall Score: {assessment_score}/{total_checks} ({assessment_score/total_checks:.1%})")
        
        if assessment_score >= 4:
            print(f"🎉 EXCELLENT: Async path is working well")
        elif assessment_score >= 3:
            print(f"✅ GOOD: Async path is functional with minor issues")
        else:
            print(f"⚠️  NEEDS WORK: Async path has significant issues")
        
        # Redis status check
        if full_mode == 'sync_fallback':
            print(f"\n📡 REDIS STATUS")
            print("-" * 40)
            print(f"⚠️  Redis unavailable - processing fell back to sync")
            print(f"   This is expected if Redis is not running")
            print(f"   Fallback mechanism is working correctly")
            print(f"   For true async testing, ensure Redis is available")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_async_path_validation()
