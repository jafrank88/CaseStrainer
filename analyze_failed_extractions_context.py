#!/usr/bin/env python3
"""
Analyze the context around failed case name extractions to understand why they're failing.
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

def analyze_failed_extractions_context():
    """Analyze the context around failed case name extractions."""
    results = load_adaptive_results()
    
    if not results:
        print("No results to analyze")
        return
    
    # Collect failed extractions with context
    failed_extractions = []
    successful_extractions = []
    
    for doc_result in results:
        filename = doc_result.get('filename', 'Unknown')
        comparison_results = doc_result.get('comparison_results', [])
        
        for comp in comparison_results:
            extracted = comp.get('extracted', {})
            
            case_name = extracted.get('case_name', '').strip()
            citation = extracted.get('citation', '').strip()
            year = extracted.get('year', '').strip()
            
            extraction_data = {
                'filename': filename,
                'case_name': case_name,
                'citation': citation,
                'year': year
            }
            
            if case_name:
                successful_extractions.append(extraction_data)
            else:
                failed_extractions.append(extraction_data)
    
    print("=" * 80)
    print("FAILED CASE NAME EXTRACTION ANALYSIS")
    print("=" * 80)
    
    print(f"Total extractions: {len(failed_extractions) + len(successful_extractions)}")
    print(f"Failed extractions: {len(failed_extractions)}")
    print(f"Successful extractions: {len(successful_extractions)}")
    
    # Analyze citation patterns in failed extractions
    print(f"\nCitation Patterns in Failed Extractions:")
    print("-" * 50)
    
    citation_patterns = defaultdict(int)
    for extraction in failed_extractions:
        citation = extraction['citation']
        if 'Wn.2d' in citation:
            citation_patterns['Wn.2d'] += 1
        elif 'Wn. App.' in citation:
            citation_patterns['Wn. App.'] += 1
        elif 'P.3d' in citation:
            citation_patterns['P.3d'] += 1
        elif 'P.2d' in citation:
            citation_patterns['P.2d'] += 1
        elif 'U.S.' in citation:
            citation_patterns['U.S.'] += 1
        elif 'S.Ct.' in citation:
            citation_patterns['S.Ct.'] += 1
        elif 'L.Ed.' in citation:
            citation_patterns['L.Ed.'] += 1
        elif 'F.' in citation:
            citation_patterns['F.'] += 1
        else:
            citation_patterns['Other'] += 1
    
    for pattern, count in sorted(citation_patterns.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(failed_extractions) * 100
        print(f"{pattern:10} | {count:4d} | {percentage:5.1f}%")
    
    # Show detailed examples of failed extractions
    print(f"\nDetailed Examples of Failed Extractions:")
    print("-" * 50)
    
    # Group by document type
    doc_failures = defaultdict(list)
    for extraction in failed_extractions:
        doc_type = extraction['filename'].split('_')[0] if '_' in extraction['filename'] else 'Unknown'
        doc_failures[doc_type].append(extraction)
    
    # Show examples from documents with most failures
    top_failing_docs = sorted(doc_failures.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    
    for doc_type, extractions in top_failing_docs:
        print(f"\n📄 Document Type: {doc_type} ({len(extractions)} failures)")
        print("-" * 40)
        
        # Show first 5 examples from this document type
        for i, extraction in enumerate(extractions[:5]):
            print(f"{i+1}. Citation: {extraction['citation']}")
            print(f"   Year: {extraction['year']}")
            print(f"   File: {extraction['filename']}")
            print()
    
    # Analyze successful vs failed patterns
    print(f"\nSuccessful vs Failed Extraction Patterns:")
    print("-" * 50)
    
    # Compare citation types
    successful_citations = [e['citation'] for e in successful_extractions]
    failed_citations = [e['citation'] for e in failed_extractions]
    
    def get_citation_type(citation):
        if 'Wn.2d' in citation:
            return 'Wn.2d'
        elif 'Wn. App.' in citation:
            return 'Wn. App.'
        elif 'P.3d' in citation:
            return 'P.3d'
        elif 'U.S.' in citation:
            return 'U.S.'
        elif 'S.Ct.' in citation:
            return 'S.Ct.'
        else:
            return 'Other'
    
    successful_types = Counter([get_citation_type(c) for c in successful_citations])
    failed_types = Counter([get_citation_type(c) for c in failed_citations])
    
    print("Citation Type | Successful | Failed | Success Rate")
    print("-" * 50)
    
    all_types = set(successful_types.keys()) | set(failed_types.keys())
    for citation_type in sorted(all_types):
        successful = successful_types.get(citation_type, 0)
        failed = failed_types.get(citation_type, 0)
        total = successful + failed
        success_rate = successful / total * 100 if total > 0 else 0
        print(f"{citation_type:12} | {successful:10d} | {failed:6d} | {success_rate:6.1f}%")
    
    # Look for patterns in successful extractions
    print(f"\nPatterns in Successful Extractions:")
    print("-" * 50)
    
    successful_case_names = [e['case_name'] for e in successful_extractions]
    
    # Analyze case name patterns
    case_name_patterns = defaultdict(int)
    for case_name in successful_case_names:
        if case_name.startswith('WASHINGTON CASES'):
            case_name_patterns['WASHINGTON CASES prefix'] += 1
        elif 'v.' in case_name:
            case_name_patterns['Contains "v."'] += 1
        elif 'v ' in case_name:
            case_name_patterns['Contains "v "'] += 1
        elif len(case_name.split()) >= 4:
            case_name_patterns['4+ words'] += 1
        elif len(case_name.split()) >= 3:
            case_name_patterns['3 words'] += 1
        else:
            case_name_patterns['Short names'] += 1
    
    for pattern, count in sorted(case_name_patterns.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(successful_case_names) * 100
        print(f"{pattern:20} | {count:4d} | {percentage:5.1f}%")
    
    # Recommendations based on analysis
    print(f"\nRECOMMENDATIONS:")
    print("-" * 50)
    
    # Find the worst performing citation types
    worst_performers = []
    for citation_type in all_types:
        successful = successful_types.get(citation_type, 0)
        failed = failed_types.get(citation_type, 0)
        total = successful + failed
        if total >= 10:  # Only consider types with significant samples
            success_rate = successful / total * 100
            worst_performers.append((citation_type, success_rate, total))
    
    worst_performers.sort(key=lambda x: x[1])
    
    print("Priority improvements needed for:")
    for citation_type, success_rate, total in worst_performers[:3]:
        print(f"  - {citation_type}: {success_rate:.1f}% success rate ({total} total)")
    
    print(f"\nSpecific suggestions:")
    print("1. Focus on improving Wn.2d and P.3d case name extraction")
    print("2. Enhance context window for Washington State cases")
    print("3. Add more robust case name patterns for legal citations")
    print("4. Consider using external case name databases for validation")

if __name__ == "__main__":
    analyze_failed_extractions_context() 