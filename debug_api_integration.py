#!/usr/bin/env python3
"""
Debug API Integration - Test citation processing at different levels
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_direct_unified_processor():
    """Test the unified processor directly"""
    print("=" * 60)
    print("TESTING UNIFIED PROCESSOR DIRECTLY")
    print("=" * 60)
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        config = ProcessingConfig()
        config.enable_verification = False
        config.debug_mode = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        
        test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        print(f"Processing: {test_text}")
        
        # Run async processor
        result = asyncio.run(processor.process_text(test_text))
        
        print(f"Direct Processor Results:")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        
        return len(result.get('citations', [])) > 0
        
    except Exception as e:
        print(f"❌ Direct processor failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_citation_service():
    """Test the CitationService process_citations_from_text method"""
    print("\n" + "=" * 60)
    print("TESTING CITATION SERVICE")
    print("=" * 60)
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        
        test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        print(f"Processing: {test_text}")
        
        # Run async service method
        result = asyncio.run(service.process_citations_from_text(test_text))
        
        print(f"Citation Service Results:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        
        if result.get('status') == 'error':
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return len(result.get('citations', [])) > 0
        
    except Exception as e:
        print(f"❌ Citation service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rq_worker_function():
    """Test the RQ worker function directly"""
    print("\n" + "=" * 60)
    print("TESTING RQ WORKER FUNCTION")
    print("=" * 60)
    
    try:
        from src.rq_worker import process_citation_task_direct
        
        task_id = "test_task_123"
        input_type = "text"
        input_data = {"text": "Brown v. Board of Education, 347 U.S. 483 (1954)"}
        
        print(f"Processing via RQ worker function:")
        print(f"  Task ID: {task_id}")
        print(f"  Input Type: {input_type}")
        print(f"  Text: {input_data['text']}")
        
        # Call the worker function directly
        result = process_citation_task_direct(task_id, input_type, input_data)
        
        print(f"RQ Worker Results:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        
        if result.get('status') == 'failed':
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return len(result.get('citations', [])) > 0
        
    except Exception as e:
        print(f"❌ RQ worker function failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("API INTEGRATION DEBUG TEST")
    print("Testing citation processing at different integration levels")
    
    # Test each level
    direct_works = test_direct_unified_processor()
    service_works = test_citation_service()
    worker_works = test_rq_worker_function()
    
    print("\n" + "=" * 60)
    print("DEBUG TEST SUMMARY")
    print("=" * 60)
    print(f"Direct Unified Processor: {'✓ PASS' if direct_works else '✗ FAIL'}")
    print(f"Citation Service: {'✓ PASS' if service_works else '✗ FAIL'}")
    print(f"RQ Worker Function: {'✓ PASS' if worker_works else '✗ FAIL'}")
    
    if direct_works and not service_works:
        print("\n❌ Issue is in CitationService integration")
    elif service_works and not worker_works:
        print("\n❌ Issue is in RQ Worker integration")
    elif not direct_works:
        print("\n❌ Issue is in core Unified Processor")
    elif direct_works and service_works and worker_works:
        print("\n✅ All levels working - issue may be in API endpoint or task queuing")
    else:
        print("\n❓ Mixed results - need further investigation")

if __name__ == "__main__":
    main()
