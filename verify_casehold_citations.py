#!/usr/bin/env python3
"""
Verify citations from CaseHOLD dataset and gather statistics on method effectiveness.
"""

import json
import time
import re
from collections import Counter
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def extract_citation_string(citation_obj):
    """Extract plain citation string from eyecite object representation."""
    if isinstance(citation_obj, str):
        # If it's already a string, return as is
        return citation_obj
    
    # Handle eyecite object representations
    citation_str = str(citation_obj)
    
    # Extract citation from FullCaseCitation format
    full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
    if full_case_match:
        return full_case_match.group(1)
    
    # Extract citation from ShortCaseCitation format
    short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation_str)
    if short_case_match:
        return short_case_match.group(1)
    
    # Extract citation from FullLawCitation format
    law_match = re.search(r"FullLawCitation\('([^']+)'", citation_str)
    if law_match:
        return law_match.group(1)
    
    # If no pattern matches, return the original string
    return citation_str

def verify_casehold_citations():
    """Verify citations from CaseHOLD dataset and gather statistics."""
    
    print("Loading CaseHOLD citations...")
    with open('casehold_citations_1000.json', 'r', encoding='utf-8') as f:
        citations = json.load(f)
    
    print(f"Loaded {len(citations)} citations for verification")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Process citations in batches to avoid overwhelming the system
    batch_size = 50  # Smaller batch size for testing
    results = []
    method_stats = Counter()
    
    for i in range(0, len(citations), batch_size):
        batch = citations[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(citations) + batch_size - 1)//batch_size}")
        
        for j, citation_data in enumerate(batch):
            citation_obj = citation_data['citation']
            case_name = citation_data.get('case_name', '')
            
            # Extract plain citation string
            citation = extract_citation_string(citation_obj)
            
            try:
                # Verify citation
                result = verifier.verify_citation_unified_workflow(
                    citation, 
                    extracted_case_name=case_name
                )
                
                # Record result
                results.append({
                    'original_citation': citation_obj,
                    'citation': citation,
                    'case_name': case_name,
                    'verified': result.get('verified', False),
                    'source': result.get('source', ''),
                    'url': result.get('url', ''),
                    'method': result.get('verification_method', ''),
                    'error': result.get('error', '')
                })
                
                # Track method statistics
                method = result.get('verification_method', 'unknown')
                success = 'success' if result.get('verified', False) else 'failed'
                method_stats[(method, success)] += 1
                
                # Progress indicator
                if (j + 1) % 10 == 0:
                    print(f"  Processed {j + 1}/{len(batch)} in current batch")
                
                # Small delay to be respectful to servers
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Error processing citation '{citation}': {e}")
                results.append({
                    'original_citation': citation_obj,
                    'citation': citation,
                    'case_name': case_name,
                    'verified': False,
                    'source': '',
                    'url': '',
                    'method': 'error',
                    'error': str(e)
                })
                method_stats[('error', 'failed')] += 1
    
    # Save results
    print("Saving verification results...")
    with open('casehold_verification_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print statistics
    print("\n" + "="*60)
    print("VERIFICATION STATISTICS")
    print("="*60)
    
    total_citations = len(results)
    verified_citations = sum(1 for r in results if r['verified'])
    verification_rate = (verified_citations / total_citations) * 100 if total_citations > 0 else 0
    
    print(f"Total citations processed: {total_citations}")
    print(f"Successfully verified: {verified_citations}")
    print(f"Verification rate: {verification_rate:.1f}%")
    
    print("\nMethod effectiveness:")
    print("Method\t\tSuccess\tCount\tSuccess Rate")
    print("-" * 50)
    
    # Group by method
    method_totals = Counter()
    method_successes = Counter()
    
    for (method, success), count in method_stats.items():
        method_totals[method] += count
        if success == 'success':
            method_successes[method] += count
    
    for method in sorted(method_totals.keys()):
        total = method_totals[method]
        successes = method_successes[method]
        success_rate = (successes / total) * 100 if total > 0 else 0
        print(f"{method:<15}\t{successes}\t{total}\t{success_rate:.1f}%")
    
    # Save method statistics
    print("\nSaving method statistics...")
    stats_data = {
        'total_citations': total_citations,
        'verified_citations': verified_citations,
        'verification_rate': verification_rate,
        'method_stats': dict(method_stats),
        'method_summary': {
            method: {
                'total': method_totals[method],
                'successes': method_successes[method],
                'success_rate': (method_successes[method] / method_totals[method]) * 100 if method_totals[method] > 0 else 0
            }
            for method in method_totals.keys()
        }
    }
    
    with open('casehold_method_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to:")
    print(f"  - casehold_verification_results.json")
    print(f"  - casehold_method_statistics.json")
    print(f"  - lookup_method_stats.log (detailed per-citation logs)")

if __name__ == "__main__":
    verify_casehold_citations() 