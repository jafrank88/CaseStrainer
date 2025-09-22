#!/usr/bin/env python3

def test_large_content_async():
    """Test that large content now processes asynchronously with improved Redis connectivity."""
    
    print("🔍 LARGE CONTENT ASYNC PROCESSING TEST")
    print("=" * 60)
    
    try:
        # Load the large PDF text
        pdf_text_file = "d:/dev/casestrainer/extracted_pdf_text.txt"
        try:
            with open(pdf_text_file, 'r', encoding='utf-8') as f:
                large_text = f.read()
        except FileNotFoundError:
            print(f"❌ PDF text file not found: {pdf_text_file}")
            print("   Please run extract_pdf_text.py first to create this file")
            return
        
        print(f"📊 Large text size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
        
        # Test routing decision
        print(f"\n📊 Testing routing decision...")
        from src.api.services.citation_service import CitationService
        
        citation_service = CitationService()
        input_data_for_check = {'type': 'text', 'text': large_text}
        should_process_immediately = citation_service.should_process_immediately(input_data_for_check)
        
        print(f"   should_process_immediately: {should_process_immediately}")
        print(f"   Expected: False (should be async)")
        
        if should_process_immediately:
            print("   ⚠️  WARNING: Large content is still being routed to sync processing!")
        else:
            print("   ✅ GOOD: Large content correctly routed to async processing")
        
        # Test UnifiedInputProcessor
        print(f"\n📊 Testing UnifiedInputProcessor...")
        from src.unified_input_processor import UnifiedInputProcessor
        
        processor = UnifiedInputProcessor()
        
        # Test with a smaller sample first to ensure basic functionality
        small_sample = large_text[:1000]  # 1KB sample
        print(f"   Testing small sample ({len(small_sample)} chars)...")
        
        small_result = processor.process_any_input(
            input_data={'text': small_sample},
            input_type='text',
            request_id='test_small'
        )
        
        print(f"   Small sample result: {small_result.get('success', False)}")
        print(f"   Processing mode: {small_result.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        # Now test with large content
        print(f"\n   Testing large content ({len(large_text)} chars)...")
        
        large_result = processor.process_any_input(
            input_data={'text': large_text},
            input_type='text',
            request_id='test_large'
        )
        
        print(f"   Large content result: {large_result.get('success', False)}")
        print(f"   Processing mode: {large_result.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        # Check if we got a task_id (indicating async processing)
        if 'task_id' in large_result:
            print(f"   ✅ ASYNC: Got task_id: {large_result['task_id']}")
            print(f"   Status: {large_result.get('status', 'unknown')}")
        else:
            print(f"   ⚠️  SYNC: No task_id found - processed synchronously")
            print(f"   Citations found: {len(large_result.get('citations', []))}")
        
        # Test Redis connectivity
        print(f"\n📊 Testing Redis connectivity...")
        try:
            from redis import Redis
            
            redis_configs = [
                'redis://localhost:6379/0',
                'redis://127.0.0.1:6379/0'
            ]
            
            redis_available = False
            for redis_url in redis_configs:
                try:
                    redis_conn = Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                    redis_conn.ping()
                    print(f"   ✅ Redis available at: {redis_url}")
                    redis_available = True
                    break
                except Exception as e:
                    print(f"   ❌ Redis failed at {redis_url}: {e}")
            
            if not redis_available:
                print(f"   ⚠️  No Redis instance available - will fall back to sync processing")
            
        except Exception as e:
            print(f"   ❌ Redis test error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_large_content_async()
