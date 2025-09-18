"""
Debug Async Worker Issue
Tests the UnifiedSyncProcessor directly to see if it works outside of async context.
"""

def test_unified_sync_processor_direct():
    """Test UnifiedSyncProcessor directly to see if it works."""
    
    print("🔍 TESTING UNIFIED SYNC PROCESSOR DIRECTLY")
    print("=" * 45)
    
    try:
        from src.unified_sync_processor import UnifiedSyncProcessor, ProcessingOptions
        
        # Create processor with same config as async worker
        options = ProcessingOptions(
            enable_verification=True,
            enable_clustering=True,
            enable_caching=True,
            force_ultra_fast=False,
            skip_clustering_threshold=300,
            ultra_fast_threshold=500,
            sync_threshold=5 * 1024,
            max_citations_for_skip_clustering=3
        )
        processor = UnifiedSyncProcessor(options)
        
        # Test text
        text = """Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)
Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)"""
        
        print(f"📝 Testing with text length: {len(text)} characters")
        
        # Test the process_text method
        print(f"🔄 Calling processor.process_text()...")
        
        import time
        start_time = time.time()
        
        result = processor.process_text_unified(text, {'request_id': "test_request_id"})
        
        processing_time = time.time() - start_time
        
        print(f"✅ UnifiedSyncProcessor completed in {processing_time:.2f} seconds")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Citations: {len(result.get('citations', []))}")
        print(f"   Processing strategy: {result.get('processing_strategy', 'unknown')}")
        
        if result.get('success', False):
            citations = result.get('citations', [])
            
            # Check deduplication
            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
            unique_citations = set(citation_texts)
            duplicates = len(citation_texts) - len(unique_citations)
            
            print(f"   Duplicates: {duplicates}")
            print(f"   ✅ Deduplication: {'WORKING' if duplicates == 0 else 'FAILED'}")
            
            return True
        else:
            print(f"   ❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UnifiedSyncProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_worker_simulation():
    """Simulate what the async worker does step by step."""
    
    print(f"\n🔍 SIMULATING ASYNC WORKER STEPS")
    print("-" * 35)
    
    try:
        # Step 1: Import modules (like the worker does)
        print(f"Step 1: Importing modules...")
        from src.unified_sync_processor import UnifiedSyncProcessor, ProcessingOptions
        print(f"   ✅ Imports successful")
        
        # Step 2: Create config (like the worker does)
        print(f"Step 2: Creating config...")
        options = ProcessingOptions(
            enable_verification=True,
            enable_clustering=True,
            enable_caching=True,
            force_ultra_fast=False,
            skip_clustering_threshold=300,
            ultra_fast_threshold=500,
            sync_threshold=5 * 1024,
            max_citations_for_skip_clustering=3
        )
        print(f"   ✅ Config created")
        
        # Step 3: Create processor (like the worker does)
        print(f"Step 3: Creating processor...")
        processor = UnifiedSyncProcessor(options)
        print(f"   ✅ Processor created")
        
        # Step 4: Prepare input data (like the worker does)
        print(f"Step 4: Preparing input data...")
        input_data = {
            'text': """Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)
Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)"""
        }
        text = input_data.get('text', '')
        task_id = "simulation_test"
        print(f"   ✅ Input prepared: {len(text)} characters")
        
        # Step 5: Process (like the worker does)
        print(f"Step 5: Processing...")
        import time
        start_time = time.time()
        
        result = processor.process_text_unified(text, {'request_id': task_id})
        
        processing_time = time.time() - start_time
        print(f"   ✅ Processing completed in {processing_time:.2f} seconds")
        
        # Step 6: Format result (like the worker does)
        print(f"Step 6: Formatting result...")
        if result.get('success', False):
            formatted_result = {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),
                'metadata': {
                    'processing_strategy': result.get('processing_strategy', 'async_unified'),
                    'text_length': len(text)
                }
            }
            print(f"   ✅ Result formatted successfully")
            print(f"   Citations: {len(formatted_result.get('citations', []))}")
            return True
        else:
            print(f"   ❌ Processing failed: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debugging tests."""
    
    print("🎯 ASYNC WORKER DEBUG")
    print("=" * 25)
    
    # Test 1: Direct processor test
    direct_success = test_unified_sync_processor_direct()
    
    # Test 2: Simulate worker steps
    simulation_success = test_async_worker_simulation()
    
    print(f"\n📊 DEBUG RESULTS")
    print("=" * 15)
    print(f"✅ Direct processor test: {'SUCCESS' if direct_success else 'FAILED'}")
    print(f"✅ Worker simulation: {'SUCCESS' if simulation_success else 'FAILED'}")
    
    if direct_success and simulation_success:
        print(f"\n🤔 CONCLUSION: UnifiedSyncProcessor works fine")
        print(f"   The issue might be in the async worker environment or Redis communication")
    elif not direct_success:
        print(f"\n🔍 CONCLUSION: UnifiedSyncProcessor has issues")
        print(f"   Need to investigate the processor itself")
    else:
        print(f"\n🔍 CONCLUSION: Mixed results - need more investigation")

if __name__ == "__main__":
    main()
