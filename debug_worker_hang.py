"""
Debug Worker Hang
Simulates the async worker with detailed logging to find where it hangs.
"""

import time
import logging

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_async_worker_detailed():
    """Simulate the async worker step by step with detailed logging."""
    
    print("🔍 DETAILED ASYNC WORKER SIMULATION")
    print("=" * 40)
    
    task_id = "debug_simulation"
    input_type = "text"
    input_data = {
        'text': "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " * 10  # Small test
    }
    
    try:
        print(f"Step 1: Starting worker simulation...")
        logger.info(f"[TASK:{task_id}] Starting processing of type: {input_type}")
        
        print(f"Step 2: Logging input data...")
        text = input_data.get('text', '')
        logger.info(f"[TASK:{task_id}] Processing text of length {len(text)}")
        
        print(f"Step 3: Importing modules...")
        start_import = time.time()
        from src.unified_sync_processor import UnifiedSyncProcessor, ProcessingOptions
        import_time = time.time() - start_import
        logger.info(f"[TASK:{task_id}] Imports completed in {import_time:.3f}s")
        print(f"   ✅ Imports took {import_time:.3f}s")
        
        print(f"Step 4: Creating configuration...")
        start_config = time.time()
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
        config_time = time.time() - start_config
        logger.info(f"[TASK:{task_id}] Configuration created in {config_time:.3f}s")
        print(f"   ✅ Configuration took {config_time:.3f}s")
        
        print(f"Step 5: Creating processor...")
        start_processor = time.time()
        processor = UnifiedSyncProcessor(options)
        processor_time = time.time() - start_processor
        logger.info(f"[TASK:{task_id}] Processor created in {processor_time:.3f}s")
        print(f"   ✅ Processor creation took {processor_time:.3f}s")
        
        print(f"Step 6: Starting text processing...")
        start_processing = time.time()
        logger.info(f"[TASK:{task_id}] About to call process_text_unified")
        
        # Add timeout mechanism to detect hanging
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Processing timed out after 30 seconds")
        
        # Set timeout (only works on Unix-like systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
        except:
            print("   ⚠️  Timeout mechanism not available on Windows")
        
        try:
            result = processor.process_text_unified(text, {'request_id': task_id})
            processing_time = time.time() - start_processing
            
            try:
                signal.alarm(0)  # Cancel timeout
            except:
                pass
            
            logger.info(f"[TASK:{task_id}] Processing completed in {processing_time:.3f}s")
            print(f"   ✅ Processing took {processing_time:.3f}s")
            
            print(f"Step 7: Analyzing result...")
            if result.get('success', False):
                citations = result.get('citations', [])
                print(f"   ✅ Success: {len(citations)} citations found")
                
                # Check deduplication
                citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                unique_citations = set(citation_texts)
                duplicates = len(citation_texts) - len(unique_citations)
                
                print(f"   ✅ Deduplication: {len(citation_texts)} → {len(unique_citations)} ({duplicates} duplicates)")
                
                print(f"Step 8: Formatting result...")
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
                print(f"\n🎉 WORKER SIMULATION SUCCESSFUL!")
                return True
                
            else:
                print(f"   ❌ Processing failed: {result.get('error', 'Unknown')}")
                return False
                
        except TimeoutError:
            print(f"   ❌ PROCESSING TIMED OUT AFTER 30 SECONDS!")
            print(f"   This suggests the processor is hanging")
            return False
        except Exception as e:
            processing_time = time.time() - start_processing
            print(f"   ❌ Processing failed after {processing_time:.3f}s: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Worker simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processor_components():
    """Test individual components of the processor to isolate the issue."""
    
    print(f"\n🔍 TESTING PROCESSOR COMPONENTS")
    print("-" * 35)
    
    try:
        print(f"Component 1: Testing imports...")
        start = time.time()
        from src.unified_sync_processor import UnifiedSyncProcessor, ProcessingOptions
        print(f"   ✅ Imports: {time.time() - start:.3f}s")
        
        print(f"Component 2: Testing configuration...")
        start = time.time()
        options = ProcessingOptions()
        print(f"   ✅ Config: {time.time() - start:.3f}s")
        
        print(f"Component 3: Testing processor creation...")
        start = time.time()
        processor = UnifiedSyncProcessor(options)
        print(f"   ✅ Processor: {time.time() - start:.3f}s")
        
        print(f"Component 4: Testing minimal processing...")
        start = time.time()
        minimal_text = "150 Wn.2d 674"  # Very minimal
        
        try:
            result = processor.process_text_unified(minimal_text, {'request_id': 'component_test'})
            processing_time = time.time() - start
            
            if processing_time > 5:
                print(f"   ⚠️  Slow processing: {processing_time:.3f}s")
            else:
                print(f"   ✅ Processing: {processing_time:.3f}s")
                
            if result.get('success', False):
                citations = result.get('citations', [])
                print(f"   ✅ Result: {len(citations)} citations")
                return True
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

def main():
    """Run comprehensive worker debugging."""
    
    print("🎯 ASYNC WORKER HANG INVESTIGATION")
    print("=" * 40)
    
    # Test 1: Component testing
    components_work = test_processor_components()
    
    # Test 2: Full worker simulation
    if components_work:
        print(f"\n✅ Components work, testing full simulation...")
        worker_works = simulate_async_worker_detailed()
    else:
        print(f"\n❌ Components failed, skipping full simulation")
        worker_works = False
    
    print(f"\n📊 INVESTIGATION RESULTS")
    print("=" * 25)
    print(f"✅ Individual components: {'WORKING' if components_work else 'FAILED'}")
    print(f"✅ Full worker simulation: {'WORKING' if worker_works else 'FAILED'}")
    
    if components_work and worker_works:
        print(f"\n🤔 CONCLUSION: Worker code works fine locally")
        print(f"   The issue might be in the container environment:")
        print(f"   - Different Python environment")
        print(f"   - Missing dependencies")
        print(f"   - Resource constraints")
        print(f"   - Network/Redis communication issues")
    elif components_work and not worker_works:
        print(f"\n🔍 CONCLUSION: Components work but full processing hangs")
        print(f"   The issue is likely in the processing logic")
    else:
        print(f"\n❌ CONCLUSION: Fundamental component issues")
        print(f"   Need to fix basic processor setup")

if __name__ == "__main__":
    main()
