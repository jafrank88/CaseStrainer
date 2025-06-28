#!/usr/bin/env python3
"""
Quick Web Search Test - 5 citations only
"""
import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.optimized_web_searcher import OptimizedWebSearcher
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def quick_test():
    print("Starting quick web search test...")
    
    # Test citations
    test_citations = [
        {"citation": "410 U.S. 113", "name": "Roe v. Wade"},
        {"citation": "347 U.S. 483", "name": "Brown v. Board of Education"},
        {"citation": "123 F.3d 456", "name": "Sample Federal Case"},
        {"citation": "123 OK 456", "name": "Sample Oklahoma Case"},
        {"citation": "456 Cal.App.4th 789", "name": "Sample California Case"},
    ]
    
    async with OptimizedWebSearcher() as searcher:
        for i, c in enumerate(test_citations):
            citation = c["citation"]
            case_name = c["name"]
            
            print(f"\n[{i+1}/5] Testing: {citation}")
            start = time.time()
            
            try:
                result = await searcher.search_parallel(citation, case_name, max_workers=2)
                elapsed = time.time() - start
                
                if result.get('verified'):
                    print(f"  ✓ SUCCESS via {result.get('method')} ({elapsed:.2f}s)")
                    print(f"    URL: {result.get('url', 'N/A')}")
                else:
                    print(f"  ✗ FAILED ({elapsed:.2f}s)")
                    print(f"    Error: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    print("\nQuick test completed!")

if __name__ == "__main__":
    asyncio.run(quick_test()) 