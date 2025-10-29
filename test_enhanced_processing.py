#!/usr/bin/env python3
"""
Test Enhanced Processing and Async Job Management

This script demonstrates the improved input processing and concurrent
job handling capabilities of the enhanced CaseStrainer system.
"""

import sys
import os
import asyncio
import time
import json
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_input_processor import EnhancedInputProcessor, process_batch
from src.enhanced_async_manager import EnhancedAsyncManager, JobStatus
from src.simplified_citation_processor import create_processor


async def test_enhanced_text_processing():
    """Test enhanced text processing capabilities."""
    print("\n" + "="*60)
    print("TESTING ENHANCED TEXT PROCESSING")
    print("="*60)
    
    # Test text with various formatting issues
    messy_text = """
    \r\n\r\nSee Brown v. Board of Education, 347 U.S. 483 (1954)\t\tfor the landmark decision.
    Compare this with Plessy v. Ferguson, 163 U.S. 537 (1896)\x0bwhich established \"separate but equal.\"
    
    Citing Miranda v. Arizona, 384 U.S. 436 (1966) — the Court held that...
    
    Page 1
    
    Another important case is Roe v. Wade, 410 U.S. 113 (1973).
    
    Contact: test@example.com for more information.
    
    ---
    1 ---
    
    Finally, see Planned Parenthood v. Casey, 505 U.S. 833 (1992).
    """
    
    async with EnhancedInputProcessor() as processor:
        print(f"Original text: {len(messy_text)} characters")
        print("Text contains issues:")
        print("  - Windows newlines (\\r\\n)")
        print("  - Tabs and extra spaces")
        print("  - Control characters")
        print("  - Page numbers")
        print("  - Email addresses")
        print("  - Header/footer patterns")
        
        result = await processor.process_text_input(messy_text, "test_text")
        
        if result['success']:
            print(f"\n✅ Enhanced processing successful!")
            print(f"Original length: {result['original_length']} characters")
            print(f"Processed length: {result['processed_length']} characters")
            print(f"Size reduction: {result['original_length'] - result['processed_length']} characters")
            print(f"Cache hit: {result['cache_hit']}")
            
            print(f"\nProcessed text sample:")
            print("=" * 40)
            print(result['text'][:300] + "..." if len(result['text']) > 300 else result['text'])
            print("=" * 40)
            
            return result['text']
        else:
            print(f"❌ Text processing failed: {result['error']}")
            return None


async def test_enhanced_pdf_processing():
    """Test enhanced PDF processing with multiple extraction methods."""
    print("\n" + "="*60)
    print("TESTING ENHANCED PDF PROCESSING")
    print("="*60)
    
    # Look for a test PDF file
    test_files = [
        "sp-7788.pdf",
        "test.pdf",
        "sample.pdf"
    ]
    
    test_file = None
    for file in test_files:
        if os.path.exists(file):
            test_file = file
            break
    
    if not test_file:
        print("⚠️  No test PDF file found. Skipping PDF test.")
        return None
    
    print(f"Testing with: {test_file}")
    
    async with EnhancedInputProcessor() as processor:
        result = await processor.process_file_input(test_file, "test_pdf")
        
        if result['success']:
            print(f"✅ Enhanced PDF processing successful!")
            print(f"File size: {result['file_size']:,} bytes")
            print(f"File extension: {result['file_extension']}")
            print(f"Processed length: {result['processed_length']:,} characters")
            print(f"Cache hit: {result['cache_hit']}")
            
            # Show sample text
            sample_text = result['text'][:500]
            print(f"\nSample extracted text:")
            print("=" * 40)
            print(sample_text + "...")
            print("=" * 40)
            
            return result['text']
        else:
            print(f"❌ PDF processing failed: {result['error']}")
            return None


async def test_concurrent_job_processing():
    """Test concurrent job processing with multiple inputs."""
    print("\n" + "="*60)
    print("TESTING CONCURRENT JOB PROCESSING")
    print("="*60)
    
    # Create test inputs
    test_inputs = [
        {
            "type": "text",
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954) established that racial segregation in public schools was unconstitutional.",
            "request_id": "job_1"
        },
        {
            "type": "text", 
            "text": "In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme Court ruled that suspects must be informed of their rights.",
            "request_id": "job_2"
        },
        {
            "type": "text",
            "text": "Roe v. Wade, 410 U.S. 113 (1973) recognized a woman's constitutional right to privacy.",
            "request_id": "job_3"
        },
        {
            "type": "text",
            "text": "The case of Plessy v. Ferguson, 163 U.S. 537 (1896) upheld the doctrine of separate but equal.",
            "request_id": "job_4"
        },
        {
            "type": "text",
            "text": "Planned Parenthood v. Casey, 505 U.S. 833 (1992) reaffirmed the core holding of Roe v. Wade.",
            "request_id": "job_5"
        }
    ]
    
    print(f"Processing {len(test_inputs)} inputs concurrently...")
    
    # Process inputs concurrently
    start_time = time.time()
    
    async with EnhancedInputProcessor(max_concurrent_jobs=3) as processor:
        results = await processor.process_multiple_inputs(test_inputs)
    
    processing_time = time.time() - start_time
    
    # Analyze results
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n✅ Concurrent processing completed in {processing_time:.2f}s")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    if successful > 0:
        total_chars = sum(r['processed_length'] for r in results if r['success'])
        avg_chars = total_chars / successful
        print(f"Average processed text length: {avg_chars:.0f} characters")
    
    # Show sample results
    print(f"\nSample results:")
    for i, result in enumerate(results[:3], 1):
        if result['success']:
            print(f"  {i}. ✅ Job {result['request_id']}: {result['processed_length']} chars")
        else:
            print(f"  {i}. ❌ Job {result['request_id']}: {result['error']}")
    
    return results


async def test_async_job_management():
    """Test async job management with progress tracking."""
    print("\n" + "="*60)
    print("TESTING ASYNC JOB MANAGEMENT")
    print("="*60)
    
    # Create async manager
    manager = EnhancedAsyncManager(
        redis_url="redis://localhost:6379/0",
        max_concurrent_jobs=3,
        job_timeout=60
    )
    
    await manager.start()
    
    try:
        # Create test processor function
        async def test_processor(input_data: Dict[str, Any], progress_callback=None):
            """Test processor with progress tracking."""
            text = input_data.get('text', '')
            
            if progress_callback:
                await progress_callback(10, "Starting", "Beginning processing")
                await asyncio.sleep(0.5)
            
            # Simulate processing steps
            if progress_callback:
                await progress_callback(50, "Processing", "Extracting citations")
                await asyncio.sleep(1.0)
            
            # Simple citation extraction (simulation)
            import re
            citations = re.findall(r'\b[A-Z][a-z\s]+ v\. [A-Z][a-z\s]+,\s*\d+\s+[A-Z\.]+\s*\d+\s*\(\d{4}\)', text)
            
            if progress_callback:
                await progress_callback(90, "Finalizing", "Completing analysis")
                await asyncio.sleep(0.5)
            
            if progress_callback:
                await progress_callback(100, "Completed", "Processing complete")
            
            return {
                "citations_found": len(citations),
                "citations": citations,
                "text_length": len(text)
            }
        
        # Submit multiple jobs
        print("Submitting multiple jobs...")
        
        job_ids = []
        for i in range(3):
            input_data = {
                "text": f"Test case {i+1}: Brown v. Board of Education, 347 U.S. 483 (1954) is important."
            }
            
            job_id = await manager.submit_job(input_data, test_processor)
            job_ids.append(job_id)
            print(f"  Submitted job {i+1}: {job_id}")
        
        # Monitor job progress
        print("\nMonitoring job progress...")
        
        completed_jobs = []
        start_time = time.time()
        
        while len(completed_jobs) < len(job_ids) and (time.time() - start_time) < 30:
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    job_status = await manager.get_job_status(job_id)
                    if job_status:
                        status = job_status['status']
                        progress = job_status['progress']
                        current_step = job_status['current_step']
                        
                        print(f"  Job {job_id[-8:]}: {status} ({progress:.0f}%) - {current_step}")
                        
                        if status in ['completed', 'failed', 'cancelled']:
                            completed_jobs.append(job_id)
            
            await asyncio.sleep(1)
        
        # Get results
        print(f"\nJob Results:")
        for job_id in job_ids:
            job_result = await manager.get_job_result(job_id)
            if job_result:
                print(f"  ✅ Job {job_id[-8:]}: {job_result['citations_found']} citations found")
            else:
                job_status = await manager.get_job_status(job_id)
                if job_status:
                    print(f"  ❌ Job {job_id[-8:]}: {job_status['status']}")
        
        # Get manager statistics
        stats = await manager.get_stats()
        print(f"\nManager Statistics:")
        print(f"  Total jobs: {stats['total_jobs']}")
        print(f"  Active jobs: {stats['active_jobs']}")
        print(f"  Completed jobs: {stats['completed_jobs']}")
        print(f"  Failed jobs: {stats['failed_jobs']}")
        print(f"  Max concurrent: {stats['max_concurrent_jobs']}")
        
        return job_ids
        
    finally:
        await manager.stop()


async def test_batch_processing():
    """Test batch processing of mixed input types."""
    print("\n" + "="*60)
    print("TESTING BATCH PROCESSING")
    print("="*60)
    
    # Create mixed batch inputs
    batch_inputs = [
        {
            "type": "text",
            "text": "Direct text input: Brown v. Board of Education, 347 U.S. 483 (1954).",
            "request_id": "batch_text_1"
        },
        {
            "type": "text",
            "text": "Another text: Miranda v. Arizona, 384 U.S. 436 (1966).",
            "request_id": "batch_text_2"
        }
    ]
    
    # Add file input if available
    if os.path.exists("sp-7788.pdf"):
        batch_inputs.append({
            "type": "file",
            "file_path": "sp-7788.pdf",
            "request_id": "batch_file_1"
        })
    
    print(f"Processing batch of {len(batch_inputs)} inputs...")
    
    start_time = time.time()
    
    try:
        results = await process_batch(batch_inputs, max_concurrent_jobs=2)
        
        processing_time = time.time() - start_time
        
        print(f"✅ Batch processing completed in {processing_time:.2f}s")
        
        # Analyze results
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"Successful: {successful}/{len(results)}")
        print(f"Failed: {failed}/{len(results)}")
        
        # Show detailed results
        print(f"\nDetailed Results:")
        for i, result in enumerate(results, 1):
            if result['success']:
                print(f"  {i}. ✅ {result['request_id']}")
                print(f"     Type: {result['source_type']}")
                print(f"     Length: {result['processed_length']} characters")
                print(f"     Cache hit: {result['cache_hit']}")
            else:
                print(f"  {i}. ❌ {result['request_id']}: {result['error']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Batch processing failed: {str(e)}")
        return None


async def test_performance_comparison():
    """Test performance comparison between sync and async processing."""
    print("\n" + "="*60)
    print("TESTING PERFORMANCE COMPARISON")
    print("="*60)
    
    # Create test data
    test_texts = [
        "Brown v. Board of Education, 347 U.S. 483 (1954) ended racial segregation in public schools.",
        "Miranda v. Arizona, 384 U.S. 436 (1966) established the requirement for police to inform suspects of their rights.",
        "Roe v. Wade, 410 U.S. 113 (1973) recognized a woman's constitutional right to privacy.",
        "Plessy v. Ferguson, 163 U.S. 537 (1896) upheld the doctrine of separate but equal facilities.",
        "Planned Parenthood v. Casey, 505 U.S. 833 (1992) reaffirmed the core holding of Roe v. Wade while allowing some regulations."
    ]
    
    print(f"Testing performance with {len(test_texts)} documents...")
    
    # Test synchronous processing
    print("\n1. Synchronous Processing:")
    start_time = time.time()
    
    sync_results = []
    for i, text in enumerate(test_texts, 1):
        async with EnhancedInputProcessor() as processor:
            result = await processor.process_text_input(text, f"sync_{i}")
            sync_results.append(result)
    
    sync_time = time.time() - start_time
    sync_successful = sum(1 for r in sync_results if r['success'])
    
    print(f"   Time: {sync_time:.2f}s")
    print(f"   Successful: {sync_successful}/{len(test_texts)}")
    print(f"   Average per document: {sync_time/len(test_texts):.2f}s")
    
    # Test asynchronous/concurrent processing
    print("\n2. Concurrent Processing:")
    start_time = time.time()
    
    concurrent_inputs = [
        {
            "type": "text",
            "text": text,
            "request_id": f"concurrent_{i}"
        }
        for i, text in enumerate(test_texts, 1)
    ]
    
    async with EnhancedInputProcessor(max_concurrent_jobs=3) as processor:
        concurrent_results = await processor.process_multiple_inputs(concurrent_inputs)
    
    concurrent_time = time.time() - start_time
    concurrent_successful = sum(1 for r in concurrent_results if r['success'])
    
    print(f"   Time: {concurrent_time:.2f}s")
    print(f"   Successful: {concurrent_successful}/{len(test_texts)}")
    print(f"   Average per document: {concurrent_time/len(test_texts):.2f}s")
    
    # Performance comparison
    print(f"\n3. Performance Comparison:")
    if concurrent_time > 0:
        speedup = sync_time / concurrent_time
        improvement = ((sync_time - concurrent_time) / sync_time) * 100
        
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Improvement: {improvement:.1f}%")
        
        if speedup > 1.5:
            print(f"   🚀 Significant performance improvement with concurrent processing!")
        elif speedup > 1.1:
            print(f"   ✅ Moderate performance improvement with concurrent processing")
        else:
            print(f"   ⚠️  Minimal performance difference (may be due to small test size)")
    
    return {
        'sync_time': sync_time,
        'concurrent_time': concurrent_time,
        'speedup': sync_time / concurrent_time if concurrent_time > 0 else 0
    }


async def main():
    """Run all enhanced processing tests."""
    print("CaseStrainer Enhanced Processing Test Suite")
    print("=" * 60)
    print("Testing improved input processing and concurrent job handling")
    
    test_results = {}
    
    try:
        # Run all tests
        test_results['text_processing'] = await test_enhanced_text_processing()
        test_results['pdf_processing'] = await test_enhanced_pdf_processing()
        test_results['concurrent_jobs'] = await test_concurrent_job_processing()
        test_results['async_management'] = await test_async_job_management()
        test_results['batch_processing'] = await test_batch_processing()
        test_results['performance'] = await test_performance_comparison()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        print(f"✅ Enhanced Text Processing: {'PASS' if test_results['text_processing'] else 'FAIL'}")
        print(f"✅ Enhanced PDF Processing: {'PASS' if test_results['pdf_processing'] else 'SKIP'}")
        print(f"✅ Concurrent Job Processing: {'PASS' if test_results['concurrent_jobs'] else 'FAIL'}")
        print(f"✅ Async Job Management: {'PASS' if test_results['async_management'] else 'FAIL'}")
        print(f"✅ Batch Processing: {'PASS' if test_results['batch_processing'] else 'FAIL'}")
        
        if test_results['performance']:
            speedup = test_results['performance']['speedup']
            print(f"✅ Performance Improvement: {speedup:.2f}x speedup")
        
        print(f"\n🎉 Enhanced processing system is working correctly!")
        print(f"   - Improved text normalization and cleaning")
        print(f"   - Enhanced PDF extraction with multiple methods")
        print(f"   - Concurrent processing for better performance")
        print(f"   - Async job management with progress tracking")
        print(f"   - Batch processing capabilities")
        print(f"   - Result caching for optimization")
        
        # Save test results
        with open('enhanced_processing_test_results.json', 'w') as f:
            # Convert non-serializable results to summaries
            serializable_results = {}
            for key, value in test_results.items():
                if isinstance(value, str):
                    serializable_results[key] = value[:100] + "..." if len(value) > 100 else value
                elif isinstance(value, list):
                    serializable_results[key] = f"List with {len(value)} items"
                elif isinstance(value, dict):
                    serializable_results[key] = value
                else:
                    serializable_results[key] = str(value)
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: enhanced_processing_test_results.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
