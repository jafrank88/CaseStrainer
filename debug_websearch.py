#!/usr/bin/env python3
"""
Debug Web Search Methods
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

async def debug_websearch():
    print("Debugging web search methods...")
    
    # Test citation
    citation = "410 U.S. 113"
    case_name = "Roe v. Wade"
    
    async with OptimizedWebSearcher() as searcher:
        print(f"\nTesting citation: {citation}")
        print(f"Case name: {case_name}")
        
        # Test each method individually
        methods = ['findlaw', 'courtlistener', 'leagle', 'openjurist', 'bing', 'duckduckgo', 'google', 'justia']
        
        for method in methods:
            print(f"\n--- Testing {method} ---")
            start = time.time()
            
            try:
                if method == 'google':
                    result = await searcher.search_google(citation, case_name)
                elif method == 'justia':
                    result = await searcher.search_justia(citation, case_name)
                elif method == 'bing':
                    result = await searcher.search_bing(citation, case_name)
                elif method == 'duckduckgo':
                    result = await searcher.search_duckduckgo(citation, case_name)
                elif method == 'findlaw':
                    result = await searcher.search_findlaw(citation, case_name)
                elif method == 'courtlistener':
                    result = await searcher.search_courtlistener(citation, case_name)
                elif method == 'leagle':
                    result = await searcher.search_leagle(citation, case_name)
                elif method == 'openjurist':
                    result = await searcher.search_openjurist(citation, case_name)
                
                elapsed = time.time() - start
                
                print(f"Result: {result}")
                print(f"Time: {elapsed:.2f}s")
                if result.get('verified'):
                    print("✓ SUCCESS!")
                else:
                    print(f"✗ FAILED: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                elapsed = time.time() - start
                print(f"✗ EXCEPTION: {e}")
                print(f"Time: {elapsed:.2f}s")
            
            # Wait between methods
            await asyncio.sleep(2)
    
    print("\nDebug completed!")

if __name__ == "__main__":
    asyncio.run(debug_websearch()) 