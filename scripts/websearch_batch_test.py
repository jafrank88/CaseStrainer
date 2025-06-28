#!/usr/bin/env python3
"""
Batch Web Search Test Script (No CourtListener)

This script tests web search-only verification for a sample of 100 citations from casehold_citations_1000.json.
It logs which web method (Google Scholar, Justia, FindLaw, OSCN) succeeds, the URL, and the time taken.
At the end, it prints and saves per-method success rates and stats.
"""
import asyncio
import json
import logging
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.optimized_web_searcher import OptimizedWebSearcher
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Helper to extract clean citation string
extract_clean = None
try:
    extract_clean = EnhancedMultiSourceVerifier().extract_clean_citation
except Exception:
    extract_clean = lambda x: str(x)

async def batch_websearch_test():
    # Load 100 citations
    with open('casehold_citations_1000.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    sample = data[:100]

    # Prepare results
    results = []
    method_stats = {}
    total = len(sample)

    async with OptimizedWebSearcher() as searcher:
        for i, c in enumerate(sample):
            raw_citation = c.get('citation')
            case_name = c.get('case_name') or c.get('name')
            citation = extract_clean(raw_citation)
            logger.info(f"[{i+1}/{total}] Searching: {citation} ({case_name})")
            start = time.time()
            result = await searcher.search_parallel(citation, case_name, max_workers=3)
            elapsed = time.time() - start
            method = result.get('method') or 'none'
            url = result.get('url')
            verified = result.get('verified', False)
            err = result.get('error')
            results.append({
                'citation': citation,
                'case_name': case_name,
                'method': method,
                'url': url,
                'verified': verified,
                'error': err,
                'elapsed': elapsed
            })
            # Stats
            if method not in method_stats:
                method_stats[method] = {'success': 0, 'fail': 0, 'total_time': 0.0}
            if verified:
                method_stats[method]['success'] += 1
            else:
                method_stats[method]['fail'] += 1
            method_stats[method]['total_time'] += elapsed
            # Respect rate limits
            await asyncio.sleep(1.5)

    # Print summary
    print("\n=== Web Search Batch Test Results ===")
    for method, stats in method_stats.items():
        total = stats['success'] + stats['fail']
        rate = stats['success'] / total if total else 0
        avg_time = stats['total_time'] / total if total else 0
        print(f"{method}: {stats['success']}/{total} ({rate:.1%}) avg {avg_time:.2f}s")
    # Save results
    with open('websearch_batch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Results saved to websearch_batch_results.json")

if __name__ == "__main__":
    asyncio.run(batch_websearch_test()) 