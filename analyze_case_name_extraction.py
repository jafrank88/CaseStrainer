#!/usr/bin/env python3
"""
Analyze case name extraction failures and patterns from adaptive learning results.
"""

import json
import os
from collections import defaultdict, Counter
import re

def load_adaptive_results():
    """Load the adaptive learning results."""
    results_file = "adaptive_results/adaptive_processing_results.json"
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return []
    
    with open(results_file, 'r') as f:
        return json.load(f)

def analyze_case_name_extraction():
    """Analyze case name extraction patterns and failures."""
    results = load_adaptive_results()
    
    if not results:
        print("No results to analyze")
        return
    
    # Collect data for analysis
    case_names = []
    citations = []
    years = []
    filenames = []
    
    # Track patterns
    case_name_patterns = defaultdict(int)
    empty_case_name_contexts = []
    
    for doc_result in results:
        filename = doc_result.get('filename', 'Unknown')
        comparison_results = doc_result.get('comparison_results', [])
        
        for comp in comparison_results:
            extracted = comp.get('extracted', {})
            
            case_name = extracted.get('case_name', '').strip()
            citation = extracted.get('citation', '').strip()
            year = extracted.get('year', '').strip()
            
            case_names.append(case_name)
            citations.append(citation)
            years.append(year)
            filenames.append(filename)
            
            # Analyze case name patterns
            if case_name:
                # Look for common patterns in successful extractions
                if case_name.startswith('WASHINGTON CASES'):
                    case_name_patterns['WASHINGTON CASES prefix'] += 1
                elif 'v.' in case_name:
                    case_name_patterns['Contains "v."'] += 1
                elif 'v ' in case_name:
                    case_name_patterns['Contains "v "'] += 1
                elif len(case_name.split()) >= 3:
                    case_name_patterns['3+ words'] += 1
                else:
                    case_name_patterns['Other patterns'] += 1
            else:
                # Track context when case name is empty
                empty_case_name_contexts.append({
                    'filename': filename,
                    'citation': citation,
                    'year': year
                })
    
    # Analyze the data
    print("=" * 60)
    print("CASE NAME EXTRACTION ANALYSIS")
    print("=" * 60)
    
    total_extractions = len(case_names)
    successful_case_names = sum(1 for name in case_names if name)
    failed_case_names = total_extractions - successful_case_names
    
    print(f"Total extractions: {total_extractions}")
    print(f"Successful case names: {successful_case_names} ({successful_case_names/total_extractions:.1%})")
    print(f"Failed case names: {failed_case_names} ({failed_case_names/total_extractions:.1%})")
    
    # Analyze successful case name patterns
    print(f"\nSuccessful Case Name Patterns:")
    print("-" * 40)
    for pattern, count in sorted(case_name_patterns.items(), key=lambda x: x[1], reverse=True):
        percentage = count / successful_case_names if successful_case_names > 0 else 0
        print(f"{pattern:25} | {count:4d} | {percentage:.1%}")
    
    # Analyze citation patterns when case name fails
    print(f"\nCitation Patterns When Case Name Fails:")
    print("-" * 40)
    
    failed_citations = [c for c, name in zip(citations, case_names) if not name]
    citation_patterns = defaultdict(int)
    
    for citation in failed_citations:
        if 'Wn.' in citation:
            citation_patterns['Washington State (Wn.)'] += 1
        elif 'U.S.' in citation:
            citation_patterns['Federal (U.S.)'] += 1
        elif 'S.Ct.' in citation:
            citation_patterns['Supreme Court (S.Ct.)'] += 1
        elif 'L.Ed.' in citation:
            citation_patterns['Lawyers Edition (L.Ed.)'] += 1
        elif 'F.' in citation:
            citation_patterns['Federal Circuit (F.)'] += 1
        elif 'P.' in citation:
            citation_patterns['Pacific Reporter (P.)'] += 1
        else:
            citation_patterns['Other patterns'] += 1
    
    for pattern, count in sorted(citation_patterns.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(failed_citations) if failed_citations else 0
        print(f"{pattern:25} | {count:4d} | {percentage:.1%}")
    
    # Sample of failed extractions
    print(f"\nSample Failed Extractions (first 10):")
    print("-" * 40)
    for i, context in enumerate(empty_case_name_contexts[:10]):
        print(f"{i+1:2d}. {context['filename']}")
        print(f"    Citation: {context['citation']}")
        print(f"    Year: {context['year']}")
        print()
    
    # Recommendations
    print(f"RECOMMENDATIONS:")
    print("-" * 40)
    
    if failed_case_names > successful_case_names:
        print("⚠️  Case name extraction is failing more than succeeding.")
        print("   Primary issues:")
        
        if citation_patterns['Washington State (Wn.)'] > 0:
            print(f"   - Washington State cases: {citation_patterns['Washington State (Wn.)']} failures")
        if citation_patterns['Federal (U.S.)'] > 0:
            print(f"   - Federal cases: {citation_patterns['Federal (U.S.)']} failures")
        if citation_patterns['Supreme Court (S.Ct.)'] > 0:
            print(f"   - Supreme Court cases: {citation_patterns['Supreme Court (S.Ct.)']} failures")
        
        print("\n   Suggested improvements:")
        print("   1. Enhance context window around citations")
        print("   2. Improve case name regex patterns")
        print("   3. Add more robust case name extraction logic")
        print("   4. Consider using external case name databases")
    else:
        print("✅ Case name extraction is working reasonably well")
    
    # Success rate by document type
    print(f"\nSuccess Rate by Document Type:")
    print("-" * 40)
    
    doc_success_rates = defaultdict(lambda: {'success': 0, 'total': 0})
    
    for filename, case_name in zip(filenames, case_names):
        doc_type = filename.split('_')[0] if '_' in filename else 'Unknown'
        doc_success_rates[doc_type]['total'] += 1
        if case_name:
            doc_success_rates[doc_type]['success'] += 1
    
    for doc_type, stats in sorted(doc_success_rates.items()):
        success_rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
        print(f"{doc_type:15} | {stats['success']:3d}/{stats['total']:3d} | {success_rate:.1%}")

if __name__ == "__main__":
    analyze_case_name_extraction() 