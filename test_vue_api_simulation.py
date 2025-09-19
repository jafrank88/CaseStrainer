#!/usr/bin/env python3
"""
Simulate the exact Vue API endpoint flow to identify where the disconnect happens.
"""

import sys
import os
import time
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def simulate_vue_api_endpoint():
    """Simulate the exact Vue API endpoint flow."""
    
    try:
        # Import everything the Vue API uses
        from src.unified_input_processor import UnifiedInputProcessor
        from src.api.services.citation_service import CitationService
        from src.progress_tracker import ProgressTracker
        
        # Test data - same as what API receives
        input_data = """
        Legal Document for Vue API Simulation
        
        Important cases:
        1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
        2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
        3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
        """ + "\n\nAdditional content. " * 1000
        
        input_type = 'text'
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        print("🧪 Simulating Vue API Endpoint Flow")
        print("=" * 60)
        print(f"📄 Input size: {len(input_data)} characters ({len(input_data)/1024:.1f} KB)")
        print(f"🆔 Request ID: {request_id}")
        print()
        
        # Step 1: Initialize progress tracker (like API does)
        print("📊 Step 1: Initialize Progress Tracker")
        progress_tracker = ProgressTracker(request_id)
        progress_tracker.start_step(0, 'Initializing processing...')
        print("  ✅ Progress tracker initialized")
        
        # Step 2: Check size threshold (like API does)
        print("\n🧪 Step 2: Check Size Threshold")
        citation_service = CitationService()
        input_data_for_check = {'type': input_type}
        if input_type == 'text':
            input_data_for_check['text'] = input_data
        
        should_process_immediately = citation_service.should_process_immediately(input_data_for_check)
        print(f"  Should process immediately: {should_process_immediately}")
        
        if should_process_immediately:
            print("  🔄 Would use sync processing path")
            # This shouldn't happen for our large document
            return False
        else:
            print("  🔄 Using async processing path")
            
            # Step 3: Async processing path (like API does)
            print("\n🧪 Step 3: Async Processing Path")
            print("  Updating progress...")
            progress_tracker.update_step(0, 50, 'Queuing for background processing...')
            
            print("  Creating UnifiedInputProcessor...")
            processor = UnifiedInputProcessor()
            
            print("  Calling process_any_input...")
            result = processor.process_any_input(
                input_data=input_data,
                input_type=input_type,
                request_id=request_id
            )
            
            print(f"  📊 Processor result received")
            print(f"    Type: {type(result)}")
            print(f"    Success: {result.get('success') if isinstance(result, dict) else 'N/A'}")
            print(f"    Citations: {len(result.get('citations', [])) if isinstance(result, dict) else 'N/A'}")
            
            # Step 4: API response handling logic (exact copy from vue_api_endpoints.py)
            print("\n🧪 Step 4: API Response Handling Logic")
            
            # Check if we got a sync fallback result or actual async task
            processing_mode = result.get('metadata', {}).get('processing_mode', '')
            print(f"  Processing mode detected: '{processing_mode}'")
            
            if 'task_id' in result:
                # True async processing
                print("  🔄 Handling as true async processing")
                task_id = result.get('task_id')
                progress_tracker.complete_step(0, 'Queued for background processing')
                
                result['progress_data'] = progress_tracker.get_progress_data()
                result['progress_endpoint'] = f'/casestrainer/api/progress/{task_id}'
                result['progress_stream'] = f'/casestrainer/api/progress-stream/{task_id}'
                
                print(f"    Task ID: {task_id}")
                print("    ✅ Async task handling complete")
                
            elif processing_mode == 'sync_fallback':
                # Sync fallback - treat like immediate processing
                print("  🔄 Handling as sync fallback")
                
                if result.get('success'):
                    progress_tracker.complete_step(0, 'Initialization complete')
                    progress_tracker.complete_step(1, 'Citation extraction completed (sync fallback)')
                    progress_tracker.complete_step(2, 'Analysis completed')
                    progress_tracker.complete_step(3, 'Name extraction completed')
                    progress_tracker.complete_step(4, 'Clustering completed')
                    progress_tracker.complete_step(5, 'Verification completed')
                    progress_tracker.complete_all('Sync fallback processing completed successfully')
                    print("    ✅ Progress tracking completed for sync fallback")
                else:
                    progress_tracker.fail_step(1, 'Sync fallback processing failed')
                    print("    ❌ Progress tracking failed for sync fallback")
                
                result['progress_data'] = progress_tracker.get_progress_data()
                print("    ✅ Sync fallback handling complete")
                
            else:
                # Failed to queue and no fallback
                print(f"  ❌ Unexpected processing mode: '{processing_mode}'")
                progress_tracker.fail_step(0, 'Failed to queue for processing')
                result['progress_data'] = progress_tracker.get_progress_data()
        
        # Step 5: Final result processing (like API does)
        print("\n🧪 Step 5: Final Result Processing")
        process_time = time.time() - start_time
        
        if not isinstance(result, dict):
            result = {}
        result['request_id'] = request_id
        result['processing_time'] = process_time
        
        # Calculate document length
        document_length = len(input_data)
        result['document_length'] = document_length
        
        print(f"  📊 Final result summary:")
        print(f"    Success: {result.get('success')}")
        print(f"    Citations: {len(result.get('citations', []))}")
        print(f"    Clusters: {len(result.get('clusters', []))}")
        print(f"    Processing mode: {result.get('metadata', {}).get('processing_mode')}")
        print(f"    Processing time: {process_time:.2f}s")
        print(f"    Document length: {document_length}")
        print(f"    Has progress_data: {'progress_data' in result}")
        
        # Check if we have citations
        citations = result.get('citations', [])
        if len(citations) > 0:
            print(f"  ✅ SUCCESS: {len(citations)} citations found")
            print("  📋 Sample citations:")
            for i, citation in enumerate(citations[:3]):
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', 'N/A')
                    case_name = citation.get('extracted_case_name', 'N/A')
                else:
                    citation_text = str(citation)
                    case_name = 'N/A'
                print(f"    {i+1}. {citation_text} - {case_name}")
            return True
        else:
            print(f"  ❌ FAILURE: No citations found")
            return False
            
    except Exception as e:
        print(f"💥 Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the Vue API simulation."""
    success = simulate_vue_api_endpoint()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Vue API simulation")
    return success

if __name__ == "__main__":
    main()
