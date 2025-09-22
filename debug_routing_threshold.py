#!/usr/bin/env python3

def debug_routing_threshold():
    """Debug the actual routing threshold being used."""
    
    print("🔍 ROUTING THRESHOLD DEBUG")
    print("=" * 50)
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        
        print(f"SYNC_THRESHOLD: {service.SYNC_THRESHOLD} bytes")
        print(f"ULTRA_FAST_THRESHOLD: {service.ULTRA_FAST_THRESHOLD} bytes")
        print(f"CLUSTERING_THRESHOLD: {service.CLUSTERING_THRESHOLD} bytes")
        print()
        
        # Test different sizes
        test_sizes = [100, 1000, 5000, 5120, 5121, 6000, 10000]
        
        print("SIZE TESTING:")
        print("-" * 30)
        
        for size in test_sizes:
            test_text = "x" * size
            mode = service.determine_processing_mode(test_text)
            threshold_check = "< threshold" if size < service.SYNC_THRESHOLD else ">= threshold"
            print(f"  {size:5,} bytes → {mode:5} ({threshold_check})")
        
        print()
        
        # Test the specific case that's failing
        failing_size = 5700
        failing_text = "x" * failing_size
        
        print("FAILING CASE ANALYSIS:")
        print("-" * 30)
        print(f"Text size: {failing_size} bytes")
        print(f"Threshold: {service.SYNC_THRESHOLD} bytes")
        print(f"Size >= Threshold: {failing_size >= service.SYNC_THRESHOLD}")
        
        mode = service.determine_processing_mode(failing_text)
        print(f"Determined mode: {mode}")
        
        # Test should_process_immediately
        input_data = {'type': 'text', 'text': failing_text}
        should_sync = service.should_process_immediately(input_data)
        print(f"should_process_immediately: {should_sync}")
        
        print()
        
        # Test extract_text_from_input
        extracted_text = service.extract_text_from_input(input_data)
        if extracted_text:
            print(f"Extracted text length: {len(extracted_text)} bytes")
            extracted_mode = service.determine_processing_mode(extracted_text)
            print(f"Mode from extracted text: {extracted_mode}")
        else:
            print("Text extraction failed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_routing_threshold()
