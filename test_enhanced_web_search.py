#!/usr/bin/env python3
"""
Test script for the new EnhancedWebSearcher with all supported sources.
"""

import asyncio
import time
from src.websearch_utils import LegalWebsearchEngine

async def test_enhanced_web_search():
    """Test the enhanced web searcher with multiple citations."""
    
    test_citations = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483",  # Brown v. Board of Education
        "171 Wn.2d 486", # Washington case
        "514 P.3d 643",  # Pacific Reporter case
    ]
    
    print("🚀 Testing Enhanced Web Searcher")
    print("=" * 60)
    
    async with LegalWebsearchEngine() as searcher:
        for i, citation in enumerate(test_citations, 1):
            print(f"\n[{i}/{len(test_citations)}] Testing: {citation}")
            print("-" * 40)
            
            start_time = time.time()
            
            # Test individual sources
            sources = [
                ('Justia', searcher.search_justia),
                ('FindLaw', searcher.search_findlaw),
                ('CourtListener Web', searcher.search_courtlistener_web),
                ('Leagle', searcher.search_leagle),
                ('OpenJurist', searcher.search_openjurist),
                ('CaseMine', searcher.search_casemine),
                ('Casetext', searcher.search_casetext),
                ('vLex', searcher.search_vlex),
                ('Google Scholar', searcher.search_google_scholar),
                ('Bing', searcher.search_bing),
                ('DuckDuckGo', searcher.search_duckduckgo),
            ]
            
            found_sources = []
            
            for source_name, search_func in sources:
                try:
                    result = await search_func(citation)
                    if result.get('verified'):
                        found_sources.append({
                            'source': source_name,
                            'case_name': result.get('case_name'),
                            'confidence': result.get('confidence', 0),
                            'url': result.get('url', 'N/A')
                        })
                        print(f"  ✅ {source_name}: {result.get('case_name', 'N/A')} (confidence: {result.get('confidence', 0):.2f})")
                    else:
                        print(f"  ❌ {source_name}: Not found")
                except Exception as e:
                    print(f"  💥 {source_name}: Error - {str(e)[:50]}...")
            
            # Test concurrent search
            print(f"\n  🔄 Testing concurrent search...")
            try:
                concurrent_result = await searcher.search_multiple_sources(citation, max_concurrent=5)
                if concurrent_result.get('verified'):
                    print(f"  ✅ Concurrent: {concurrent_result.get('case_name', 'N/A')} via {concurrent_result.get('source', 'Unknown')}")
                else:
                    print(f"  ❌ Concurrent: Not found")
            except Exception as e:
                print(f"  💥 Concurrent: Error - {str(e)[:50]}...")
            
            duration = time.time() - start_time
            print(f"\n  ⏱️  Total time: {duration:.2f}s")
            print(f"  📊 Found in {len(found_sources)} sources")
            
            if found_sources:
                best_result = max(found_sources, key=lambda x: x['confidence'])
                print(f"  🏆 Best result: {best_result['case_name']} via {best_result['source']} (confidence: {best_result['confidence']:.2f})")
    
    print(f"\n🎉 Enhanced web search testing complete!")
    print(f"💡 The new module provides access to {len(sources)} legal databases")
    print(f"🔧 Features: Advanced extraction, concurrent search, intelligent prioritization")

async def test_extraction_capabilities():
    """Test the enhanced extraction capabilities."""
    
    print(f"\n🔍 Testing Enhanced Extraction Capabilities")
    print("=" * 60)
    
    from src.enhanced_web_searcher import EnhancedWebExtractor
    
    extractor = EnhancedWebExtractor()
    
    # Test HTML content extraction
    test_html = """
    <html>
    <head>
        <title>Roe v. Wade - 410 U.S. 113 (1973)</title>
        <meta property="og:title" content="Roe v. Wade">
        <meta property="article:published_time" content="1973-01-22">
        <link rel="canonical" href="https://supreme.justia.com/cases/federal/us/410/113/">
    </head>
    <body>
        <h1 class="case-title">Roe v. Wade</h1>
        <div class="case-info">
            <span class="court">United States Supreme Court</span>
            <span class="date">Decided: January 22, 1973</span>
            <span class="docket">Docket No. 70-18</span>
        </div>
        <p>The case of Roe v. Wade, 410 U.S. 113 (1973), established...</p>
    </body>
    </html>
    """
    
    result = extractor.extract_from_page_content(test_html, "https://example.com", "410 U.S. 113")
    
    print(f"Extraction Results:")
    print(f"  Case Name: {result.get('case_name', 'Not found')}")
    print(f"  Date: {result.get('date', 'Not found')}")
    print(f"  Court: {result.get('court', 'Not found')}")
    print(f"  URL: {result.get('canonical_url', 'Not found')}")
    print(f"  Confidence: {result.get('confidence', 0):.2f}")
    print(f"  Methods: {', '.join(result.get('extraction_methods', []))}")

if __name__ == "__main__":
    print("Enhanced Web Searcher Test Suite")
    print("=================================")
    
    # Run the main test
    asyncio.run(test_enhanced_web_search())
    
    # Run extraction test
    asyncio.run(test_extraction_capabilities())
    
    print(f"\n📚 Migration Guide: See docs/WEB_SEARCH_MIGRATION.md")
    print(f"🔧 Old modules are deprecated but still functional") 