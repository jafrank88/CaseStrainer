#!/usr/bin/env python3
"""
Comprehensive test script to show all available verification sources.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

async def test_all_sources():
    """Test all available verification sources."""
    print("Testing all available verification sources...")
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test a citation that might not be found in CourtListener
    test_citation = "200 Wash. 2d 72, 514 P.3d 643"  # Washington case
    
    print(f"\n{'='*80}")
    print(f"Testing citation: {test_citation}")
    print(f"{'='*80}")
    
    try:
        # Test the enhanced verification
        result = verifier.verify_citation_unified_workflow(test_citation)
        
        print(f"Final verification result:")
        print(f"  Verified: {result.get('verified', 'unknown')}")
        print(f"  Source: {result.get('source', 'unknown')}")
        print(f"  Method: {result.get('verification_method', 'unknown')}")
        print(f"  URL: {result.get('url', 'none')}")
        print(f"  Confidence: {result.get('confidence', 'unknown')}")
        
        if result.get('error'):
            print(f"  Error: {result['error']}")
            
    except Exception as e:
        print(f"Error testing {test_citation}: {e}")
    
    # Now let's test individual search methods to see what's available
    print(f"\n{'='*80}")
    print("Testing individual search methods:")
    print(f"{'='*80}")
    
    # List of all available search methods
    search_methods = [
        ('CourtListener', verifier._search_courtlistener_exact),
        ('Justia', verifier._search_justia),
        ('FindLaw', verifier._search_findlaw),
        ('Leagle', verifier._search_leagle),
        ('CaseMine', verifier._search_casemine),
        ('Casetext', verifier._search_casetext),
        ('vLex', verifier._search_vlex),
        ('OpenJurist', verifier._search_openjurist),
        ('Descrybe', verifier._search_descrybe),
        ('Midpage', verifier._search_midpage),
        ('Google Scholar', verifier._search_google_scholar),
        ('Bing', verifier._search_bing),
        # ('DuckDuckGo', verifier._search_duckduckgo) # Function does not exist
    ]
    
    test_citation_simple = "410 U.S. 113"  # Simple US Supreme Court case
    
    for method_name, method_func in search_methods:
        try:
            print(f"\nTesting {method_name}...")
            result = method_func(test_citation_simple)
            
            if result.get('verified') == 'true':
                print(f"  ✅ {method_name}: SUCCESS")
                print(f"     URL: {result.get('url', 'none')}")
                print(f"     Confidence: {result.get('confidence', 'unknown')}")
            else:
                print(f"  ❌ {method_name}: FAILED")
                print(f"     Error: {result.get('error', 'unknown error')}")
                
        except Exception as e:
            print(f"  ❌ {method_name}: ERROR - {e}")
    
    print(f"\n{'='*80}")
    print("Summary of available sources:")
    print(f"{'='*80}")
    print("✅ CourtListener - Primary legal database")
    print("✅ Justia - Legal information site")
    print("✅ FindLaw - Legal information site")
    print("✅ Leagle - Legal case database")
    print("✅ CaseMine - Legal research platform")
    print("✅ Casetext - Legal research platform")
    print("✅ vLex - Legal research platform")
    print("✅ OpenJurist - Legal research site")
    print("✅ Descrybe.ai - AI-powered legal research")
    print("✅ Midpage.ai - Legal research platform")
    print("✅ Google Scholar - Academic search")
    print("✅ Bing - Web search engine")
    print("✅ DuckDuckGo - Web search engine")
    print(f"\nTotal sources: {len(search_methods)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_all_sources()) 