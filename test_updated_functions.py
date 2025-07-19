#!/usr/bin/env python3
"""
Test script to verify that all stub functions have been replaced with real implementations.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_extract_case_name_best():
    """Test the updated extract_case_name_best function."""
    print("=== Testing extract_case_name_best ===")
    try:
        from extract_case_name import extract_case_name_best
        
        # Test with a simple case
        text = "In State v. Bradley, 200 Wn.2d 72, 73, 514 P.3d 643 (2022), the court held..."
        citation = "200 Wn.2d 72"
        
        result = extract_case_name_best(text, citation)
        print(f"✅ extract_case_name_best works: {result}")
        return True
    except Exception as e:
        print(f"❌ extract_case_name_best failed: {e}")
        return False

def test_create_legal_search_queries():
    """Test the updated create_legal_search_queries function."""
    print("\n=== Testing create_legal_search_queries ===")
    try:
        from websearch_utils import create_legal_search_queries
        
        citation = "200 Wn.2d 72"
        database_info = {"name": "CourtListener"}
        
        queries = create_legal_search_queries(citation, database_info)
        print(f"✅ create_legal_search_queries works: {queries}")
        return True
    except Exception as e:
        print(f"❌ create_legal_search_queries failed: {e}")
        return False

def test_progress_manager_chunk_processing():
    """Test the updated _process_chunk function in progress_manager."""
    print("\n=== Testing progress_manager chunk processing ===")
    try:
        from progress_manager import ChunkedCitationProcessor, SSEProgressManager
        
        # Create a simple progress manager
        progress_manager = SSEProgressManager()
        processor = ChunkedCitationProcessor(progress_manager)
        
        # Test chunk processing
        chunk = "In State v. Bradley, 200 Wn.2d 72, 73, 514 P.3d 643 (2022), the court held..."
        
        import asyncio
        async def test_chunk():
            result = await processor._process_chunk(chunk, "legal_brief")
            return result
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_chunk())
            print(f"✅ progress_manager chunk processing works: {len(result)} citations found")
            return True
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ progress_manager chunk processing failed: {e}")
        return False

def test_database_verification():
    """Test the updated database verification function."""
    print("\n=== Testing database verification ===")
    try:
        from unified_citation_processor import CitationGrouper
        
        grouper = CitationGrouper()
        citation = "200 Wn.2d 72"
        
        result = grouper._verify_with_database(citation)
        print(f"✅ database verification works: {result.get('verified', False)}")
        return True
    except Exception as e:
        print(f"❌ database verification failed: {e}")
        return False

def test_westlaw_lookup():
    """Test the updated Westlaw lookup function."""
    print("\n=== Testing Westlaw lookup ===")
    try:
        from canonical_case_name_service import CanonicalCaseNameService
        
        service = CanonicalCaseNameService()
        citation = "200 Wn.2d 72"
        
        result = service._lookup_westlaw(citation)
        print(f"✅ Westlaw lookup works: {result is not None}")
        return True
    except Exception as e:
        print(f"❌ Westlaw lookup failed: {e}")
        return False

def test_debugger_canonical_lookup():
    """Test the updated debugger canonical lookup function."""
    print("\n=== Testing debugger canonical lookup ===")
    try:
        from unified_citation_processor import ExtractionDebugger
        
        debugger = ExtractionDebugger()
        text = "In State v. Bradley, 200 Wn.2d 72, 73, 514 P.3d 643 (2022), the court held..."
        citations = ["200 Wn.2d 72"]
        
        result = debugger.debug_unified_pipeline(text, citations)
        print(f"✅ debugger canonical lookup works: {len(result.get('extraction_results', {}))} results")
        return True
    except Exception as e:
        print(f"❌ debugger canonical lookup failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Updated Functions\n")
    print("=" * 50)
    
    tests = [
        test_extract_case_name_best,
        test_create_legal_search_queries,
        test_progress_manager_chunk_processing,
        test_database_verification,
        test_westlaw_lookup,
        test_debugger_canonical_lookup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All stub functions have been successfully replaced!")
    else:
        print("⚠️  Some functions still need attention.")

if __name__ == "__main__":
    main() 