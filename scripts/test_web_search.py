#!/usr/bin/env python3
"""
Simple Web Search Test Script

This script tests the optimized web search functionality with sample citations.
"""

import asyncio
import json
import logging
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.optimized_web_searcher import OptimizedWebSearcher
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_web_search():
    """Test the optimized web search functionality."""
    
    # Sample test citations
    test_citations = [
        {"citation": "410 U.S. 113", "name": "Roe v. Wade", "type": "federal"},
        {"citation": "347 U.S. 483", "name": "Brown v. Board of Education", "type": "federal"},
        {"citation": "123 OK 456", "name": "Sample Oklahoma Case", "type": "state"},
    ]
    
    print("Testing Optimized Web Search")
    print("=" * 50)
    
    async with OptimizedWebSearcher() as searcher:
        for citation_data in test_citations:
            citation = citation_data['citation']
            case_name = citation_data.get('name')
            
            print(f"\nTesting: {citation} ({case_name})")
            
            # Test parallel search
            start_time = time.time()
            result = await searcher.search_parallel(citation, case_name, max_workers=2)
            duration = time.time() - start_time
            
            if result.get('verified'):
                print(f"  ✓ SUCCESS via {result.get('method', 'unknown')} ({duration:.2f}s)")
                print(f"    URL: {result.get('url', 'N/A')}")
            else:
                print(f"  ✗ FAILED ({duration:.2f}s)")
                print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Test enhanced verifier
    print(f"\n\nTesting Enhanced Multi-Source Verifier")
    print("=" * 50)
    
    verifier = EnhancedMultiSourceVerifier()
    
    for citation_data in test_citations:
        citation = citation_data['citation']
        case_name = citation_data.get('name')
        
        print(f"\nTesting: {citation} ({case_name})")
        
        start_time = time.time()
        result = verifier.verify_citation_unified_workflow(citation, case_name)
        duration = time.time() - start_time
        
        if result.get('verified'):
            print(f"  ✓ SUCCESS via {result.get('verification_method', 'unknown')} ({duration:.2f}s)")
            print(f"    URL: {result.get('url', 'N/A')}")
        else:
            print(f"  ✗ FAILED ({duration:.2f}s)")
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Print method statistics
    if hasattr(verifier, 'optimized_searcher') and verifier.optimized_searcher:
        print(f"\n\nMethod Statistics:")
        print("=" * 50)
        stats = verifier.optimized_searcher.get_method_stats()
        for method, data in stats.items():
            print(f"{method}: {data['success_rate']:.1%} success rate, {data['avg_response_time']:.2f}s avg")

async def main():
    """Main test function."""
    try:
        await test_web_search()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 