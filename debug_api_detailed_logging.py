#!/usr/bin/env python3
"""
Add detailed logging to understand exactly what's happening in the API flow.
"""

import sys
import os
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_api_with_detailed_logging():
    """Debug the API flow with detailed logging."""
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        from src.api.services.citation_service import CitationService
        
        # Create test document
        test_text = """
        Legal Document for Detailed Debug
        
        Important cases:
        1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
        2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
        3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
        """ + "\n\nAdditional content. " * 1000  # Make it large
        
        print("🔍 Detailed API Flow Debug")
        print("=" * 60)
        print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
        print()
        
        # Step 1: Test size threshold logic
        print("🧪 Step 1: Testing Size Threshold Logic")
        citation_service = CitationService()
        input_data_for_check = {'type': 'text', 'text': test_text}
        should_process_immediately = citation_service.should_process_immediately(input_data_for_check)
        print(f"  Should process immediately: {should_process_immediately}")
        print(f"  Expected: False (document is {len(test_text)/1024:.1f} KB > 2KB threshold)")
        
        if should_process_immediately:
            print("  ❌ ISSUE: Large document incorrectly marked for immediate processing")
            return False
        else:
            print("  ✅ Size threshold logic working correctly")
        
        # Step 2: Test unified input processor directly
        print("\n🧪 Step 2: Testing UnifiedInputProcessor Directly")
        processor = UnifiedInputProcessor()
        request_id = str(uuid.uuid4())
        
        print(f"  Request ID: {request_id}")
        print("  Calling processor.process_any_input()...")
        
        result = processor.process_any_input(
            input_data=test_text,
            input_type='text',
            request_id=request_id
        )
        
        print(f"\n📊 Step 3: Analyzing Processor Result")
        print(f"  Result type: {type(result)}")
        print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"  Success: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        print(f"  Has task_id: {'task_id' in result if isinstance(result, dict) else False}")
        print(f"  Has citations: {'citations' in result if isinstance(result, dict) else False}")
        print(f"  Citations count: {len(result.get('citations', [])) if isinstance(result, dict) else 'N/A'}")
        print(f"  Has metadata: {'metadata' in result if isinstance(result, dict) else False}")
        
        if isinstance(result, dict) and 'metadata' in result:
            metadata = result['metadata']
            processing_mode = metadata.get('processing_mode', 'N/A')
            print(f"  Processing mode: {processing_mode}")
            print(f"  Source: {metadata.get('source', 'N/A')}")
            print(f"  Fallback reason: {metadata.get('fallback_reason', 'N/A')}")
            print(f"  Error details: {metadata.get('error_details', 'N/A')}")
            
            # Step 4: Simulate API response handling
            print(f"\n🧪 Step 4: Simulating API Response Handling")
            print(f"  Processing mode detected: '{processing_mode}'")
            
            if 'task_id' in result:
                print("  ✅ Would be handled as async task")
                return False  # This shouldn't happen for our test
            elif processing_mode == 'sync_fallback':
                print("  ✅ Would be handled as sync fallback")
                citations = result.get('citations', [])
                if len(citations) > 0:
                    print(f"  ✅ Sync fallback has {len(citations)} citations")
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
                    print("  ❌ Sync fallback has no citations")
                    return False
            elif processing_mode == 'immediate':
                print("  ✅ Would be handled as immediate processing")
                citations = result.get('citations', [])
                return len(citations) > 0
            elif processing_mode == 'queued':
                print("  ⚠️ Processing mode is 'queued' but no task_id")
                print("  🔍 This suggests async failed but fallback didn't trigger correctly")
                return False
            else:
                print(f"  ❌ Unexpected processing mode: '{processing_mode}'")
                return False
        else:
            print("  ❌ No metadata in result")
            return False
            
    except Exception as e:
        print(f"💥 Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the detailed debug."""
    success = debug_api_with_detailed_logging()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Detailed API debug")
    return success

if __name__ == "__main__":
    main()
