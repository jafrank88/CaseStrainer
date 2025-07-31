#!/usr/bin/env python3
"""
Comprehensive analysis of ALL 2045 citations from 50 briefs
"""

import csv
import json
import requests
from datetime import datetime
from collections import defaultdict
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_all_citations_comprehensive():
    """Analyze ALL citations from 50 briefs to get complete verification statistics"""
    
    print("COMPREHENSIVE ANALYSIS OF ALL 2045 CITATIONS")
    print("=" * 70)
    print("Testing ALL citations from 50 briefs with stable production servers")
    print("=" * 70)
    
    # Load ALL citations from CSV
    citations_data = []
    
    try:
        with open('non_courtlistener_citations_20250728_215223.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                citation_text = row.get('citation_text', '').strip()
                if citation_text and citation_text != 'N/A':
                    citations_data.append({
                        'citation': citation_text,
                        'case_name': row.get('extracted_case_name', '').strip(),
                        'date': row.get('extracted_date', '').strip(),
                        'file_name': row.get('file_name', '').strip()
                    })
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    total_citations = len(citations_data)
    print(f"Loaded {total_citations} citations from 50 briefs")
    
    # Categorize citations by type first
    print("\nCategorizing citations by type...")
    citation_types = defaultdict(list)
    wl_citations = []
    
    for citation_data in citations_data:
        citation = citation_data['citation']
        
        # Check for WL citations
        if 'WL' in citation or 'WESTLAW' in citation.upper():
            wl_citations.append(citation_data)
            citation_types['WL'].append(citation_data)
        # Check for other patterns
        elif 'U.S.' in citation:
            citation_types['U.S. Supreme Court'].append(citation_data)
        elif 'F.3d' in citation or 'F.2d' in citation or 'F. Supp' in citation:
            citation_types['Federal'].append(citation_data)
        elif 'S. Ct.' in citation:
            citation_types['Supreme Court Reporter'].append(citation_data)
        elif 'L. Ed.' in citation:
            citation_types['Lawyers Edition'].append(citation_data)
        elif 'Wn.' in citation:
            citation_types['Washington State'].append(citation_data)
        elif 'P.3d' in citation or 'P.2d' in citation:
            citation_types['Pacific Reporter'].append(citation_data)
        else:
            citation_types['Other'].append(citation_data)
    
    print(f"\nCitation Type Breakdown:")
    for ctype, citations in sorted(citation_types.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {ctype}: {len(citations)} citations")
    
    if wl_citations:
        print(f"\n🎯 Found {len(wl_citations)} WL (Westlaw) citations to test!")
    else:
        print(f"\n📝 No WL citations found in dataset")
    
    print(f"\nStarting verification of ALL {total_citations} citations...")
    print("-" * 70)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    # Results tracking
    results = []
    stats = {
        'total_tested': 0,
        'courtlistener_verified': 0,
        'fallback_verified': 0,
        'unverified': 0,
        'api_errors': 0,
        'extraction_failures': 0,
        'wl_verified': 0,
        'wl_unverified': 0
    }
    
    sources = defaultdict(int)
    unverified_citations = []
    verification_failures = []
    wl_results = []
    
    def test_citation(citation_data, index):
        """Test a single citation"""
        citation = citation_data['citation']
        case_name = citation_data['case_name']
        date = citation_data['date']
        file_name = citation_data['file_name']
        
        if index % 100 == 0:
            print(f"[{index+1}/{total_citations}] Testing: {citation}")
        
        # Create context-rich input
        if case_name and case_name != 'N/A' and date and date != 'N/A':
            test_text = f"In {case_name} ({date}), the court cited {citation}."
        elif case_name and case_name != 'N/A':
            test_text = f"In {case_name}, the court cited {citation}."
        elif date and date != 'N/A':
            test_text = f"In {date}, the court cited {citation}."
        else:
            test_text = f"This case cites {citation}."
        
        result_data = {
            'citation': citation,
            'expected_case': case_name,
            'expected_date': date,
            'file_name': file_name,
            'verified': False,
            'canonical_name': '',
            'canonical_date': '',
            'source': 'unknown',
            'confidence': 0.0,
            'is_wl': 'WL' in citation or 'WESTLAW' in citation.upper(),
            'api_success': False
        }
        
        try:
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                result_data['api_success'] = True
                
                if citations_found:
                    citation_result = citations_found[0]
                    result_data['verified'] = citation_result.get('verified', False)
                    result_data['canonical_name'] = citation_result.get('canonical_name', '')
                    result_data['canonical_date'] = citation_result.get('canonical_date', '')
                    result_data['source'] = citation_result.get('source', 'unknown')
                    result_data['confidence'] = citation_result.get('confidence', 0.0)
                else:
                    result_data['source'] = 'no_extraction'
                    
            else:
                result_data['source'] = f'api_error_{response.status_code}'
                
        except Exception as e:
            result_data['source'] = f'exception_{str(e)[:20]}'
        
        return result_data
    
    # Process citations with threading for speed
    print("Processing citations (this may take a while for 2045 citations)...")
    
    # Use smaller batch size to avoid overwhelming the API
    batch_size = 10
    max_workers = 5
    
    all_results = []
    
    for i in range(0, total_citations, batch_size):
        batch = citations_data[i:i+batch_size]
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_citation = {
                executor.submit(test_citation, citation_data, i+j): (citation_data, i+j) 
                for j, citation_data in enumerate(batch)
            }
            
            for future in as_completed(future_to_citation):
                try:
                    result_data = future.result()
                    batch_results.append(result_data)
                except Exception as e:
                    citation_data, idx = future_to_citation[future]
                    print(f"Exception processing citation {idx}: {e}")
        
        all_results.extend(batch_results)
        
        # Progress update
        processed = min(i + batch_size, total_citations)
        print(f"Processed {processed}/{total_citations} citations ({processed/total_citations*100:.1f}%)")
        
        # Small delay between batches
        time.sleep(1)
    
    # Analyze results
    print(f"\nAnalyzing {len(all_results)} results...")
    
    for result_data in all_results:
        stats['total_tested'] += 1
        
        if result_data['api_success']:
            if result_data['verified']:
                if 'CourtListener' in result_data['source']:
                    stats['courtlistener_verified'] += 1
                else:
                    stats['fallback_verified'] += 1
                    
                # Track WL verification
                if result_data['is_wl']:
                    stats['wl_verified'] += 1
                    wl_results.append(result_data)
            else:
                stats['unverified'] += 1
                unverified_citations.append(result_data)
                
                # Track WL unverified
                if result_data['is_wl']:
                    stats['wl_unverified'] += 1
                    wl_results.append(result_data)
            
            sources[result_data['source']] += 1
        else:
            if 'api_error' in result_data['source']:
                stats['api_errors'] += 1
            else:
                stats['extraction_failures'] += 1
            
            verification_failures.append(result_data)
    
    # Calculate percentages
    total_tested = stats['total_tested']
    if total_tested > 0:
        courtlistener_pct = (stats['courtlistener_verified'] / total_tested) * 100
        fallback_pct = (stats['fallback_verified'] / total_tested) * 100
        unverified_pct = (stats['unverified'] / total_tested) * 100
        error_pct = ((stats['api_errors'] + stats['extraction_failures']) / total_tested) * 100
    else:
        courtlistener_pct = fallback_pct = unverified_pct = error_pct = 0
    
    # Generate comprehensive report
    print(f"\n{'='*70}")
    print("COMPREHENSIVE VERIFICATION STATISTICS - ALL 2045 CITATIONS")
    print(f"{'='*70}")
    
    print(f"Total Citations Tested: {total_tested}")
    print(f"CourtListener Verified: {stats['courtlistener_verified']} ({courtlistener_pct:.1f}%)")
    print(f"Fallback Verified: {stats['fallback_verified']} ({fallback_pct:.1f}%)")
    print(f"Total Verified: {stats['courtlistener_verified'] + stats['fallback_verified']} ({courtlistener_pct + fallback_pct:.1f}%)")
    print(f"Unverified: {stats['unverified']} ({unverified_pct:.1f}%)")
    print(f"API/Extraction Errors: {stats['api_errors'] + stats['extraction_failures']} ({error_pct:.1f}%)")
    
    # WL Citation Analysis
    total_wl = stats['wl_verified'] + stats['wl_unverified']
    if total_wl > 0:
        print(f"\n{'='*70}")
        print("WL (WESTLAW) CITATION ANALYSIS")
        print(f"{'='*70}")
        print(f"Total WL Citations: {total_wl}")
        print(f"WL Verified: {stats['wl_verified']} ({stats['wl_verified']/total_wl*100:.1f}%)")
        print(f"WL Unverified: {stats['wl_unverified']} ({stats['wl_unverified']/total_wl*100:.1f}%)")
        
        if stats['wl_verified'] > 0:
            print(f"⚠️  WARNING: {stats['wl_verified']} WL citations were verified - this may be incorrect")
        else:
            print(f"✅ CORRECT: All WL citations remain unverified as expected")
    
    print(f"\n{'='*70}")
    print("VERIFICATION SOURCES")
    print(f"{'='*70}")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_tested) * 100 if total_tested > 0 else 0
        print(f"{source}: {count} ({pct:.1f}%)")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"comprehensive_all_citations_analysis_{timestamp}.json"
    
    analysis_data = {
        'analysis_info': {
            'timestamp': timestamp,
            'total_citations_tested': total_tested,
            'endpoint_tested': endpoint,
            'analysis_type': 'comprehensive_all_citations'
        },
        'statistics': stats,
        'percentages': {
            'courtlistener_verified': courtlistener_pct,
            'fallback_verified': fallback_pct,
            'total_verified': courtlistener_pct + fallback_pct,
            'unverified': unverified_pct,
            'errors': error_pct
        },
        'citation_type_breakdown': {ctype: len(citations) for ctype, citations in citation_types.items()},
        'sources': dict(sources),
        'wl_analysis': {
            'total_wl_citations': total_wl,
            'wl_verified': stats['wl_verified'],
            'wl_unverified': stats['wl_unverified'],
            'wl_results': wl_results[:50]  # First 50 WL results
        },
        'unverified_citations': unverified_citations[:100],  # First 100 unverified
        'verification_failures': verification_failures[:50],  # First 50 failures
        'detailed_results': all_results[:500]  # First 500 detailed results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"Detailed results saved to: {results_file}")
    
    # Overall assessment
    total_verified_pct = courtlistener_pct + fallback_pct
    if total_verified_pct >= 90:
        assessment = "EXCELLENT"
    elif total_verified_pct >= 80:
        assessment = "GOOD"
    elif total_verified_pct >= 70:
        assessment = "FAIR"
    else:
        assessment = "NEEDS IMPROVEMENT"
    
    print(f"\nOverall Verification Performance: {assessment}")
    print(f"Total Verification Rate: {total_verified_pct:.1f}%")
    print(f"CourtListener Coverage: {courtlistener_pct:.1f}%")
    
    if total_wl > 0:
        print(f"WL Citation Handling: {'✅ CORRECT' if stats['wl_verified'] == 0 else '⚠️ REVIEW NEEDED'}")
    
    return results_file

if __name__ == "__main__":
    analyze_all_citations_comprehensive()
