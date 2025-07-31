#!/usr/bin/env python3
"""
Comprehensive analysis of 50-brief citations with stable production servers
"""

import csv
import json
import requests
from datetime import datetime
from collections import defaultdict
import time

def analyze_50_brief_citations():
    """Analyze all citations from 50 briefs to get verification statistics"""
    
    print("COMPREHENSIVE 50-BRIEF CITATION ANALYSIS")
    print("=" * 60)
    print("Testing with stable production servers (running 13+ hours)")
    print("=" * 60)
    
    # Load citations from CSV
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
    
    # Test a representative sample (first 100 citations for speed)
    sample_size = min(100, total_citations)
    test_citations = citations_data[:sample_size]
    
    print(f"Testing sample of {sample_size} citations...")
    print("-" * 60)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    # Results tracking
    results = []
    stats = {
        'total_tested': 0,
        'courtlistener_verified': 0,
        'fallback_verified': 0,
        'unverified': 0,
        'api_errors': 0,
        'extraction_failures': 0
    }
    
    sources = defaultdict(int)
    unverified_citations = []
    verification_failures = []
    
    for i, citation_data in enumerate(test_citations):
        citation = citation_data['citation']
        case_name = citation_data['case_name']
        date = citation_data['date']
        file_name = citation_data['file_name']
        
        print(f"[{i+1}/{sample_size}] Testing: {citation}")
        
        # Create context-rich input
        if case_name and case_name != 'N/A' and date and date != 'N/A':
            test_text = f"In {case_name} ({date}), the court cited {citation}."
        elif case_name and case_name != 'N/A':
            test_text = f"In {case_name}, the court cited {citation}."
        elif date and date != 'N/A':
            test_text = f"In {date}, the court cited {citation}."
        else:
            test_text = f"This case cites {citation}."
        
        try:
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
                timeout=20
            )
            
            stats['total_tested'] += 1
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                
                if citations_found:
                    citation_result = citations_found[0]
                    verified = citation_result.get('verified', False)
                    canonical_name = citation_result.get('canonical_name', '')
                    canonical_date = citation_result.get('canonical_date', '')
                    source = citation_result.get('source', 'unknown')
                    confidence = citation_result.get('confidence', 0.0)
                    
                    # Track source statistics
                    sources[source] += 1
                    
                    if verified:
                        if 'CourtListener' in source:
                            stats['courtlistener_verified'] += 1
                            print(f"  ✅ CourtListener: {canonical_name}")
                        else:
                            stats['fallback_verified'] += 1
                            print(f"  ✅ Fallback ({source}): {canonical_name}")
                    else:
                        stats['unverified'] += 1
                        unverified_citations.append({
                            'citation': citation,
                            'expected_case': case_name,
                            'expected_date': date,
                            'file_name': file_name,
                            'source_attempted': source
                        })
                        print(f"  ❌ Unverified (source: {source})")
                    
                    # Store detailed result
                    results.append({
                        'citation': citation,
                        'expected_case': case_name,
                        'expected_date': date,
                        'file_name': file_name,
                        'verified': verified,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_date,
                        'source': source,
                        'confidence': confidence
                    })
                    
                else:
                    stats['extraction_failures'] += 1
                    verification_failures.append({
                        'citation': citation,
                        'issue': 'No citations extracted',
                        'file_name': file_name
                    })
                    print(f"  ❌ No citations extracted")
                    
            else:
                stats['api_errors'] += 1
                verification_failures.append({
                    'citation': citation,
                    'issue': f'API error {response.status_code}',
                    'file_name': file_name
                })
                print(f"  ❌ API error {response.status_code}")
                
        except Exception as e:
            stats['api_errors'] += 1
            verification_failures.append({
                'citation': citation,
                'issue': f'Exception: {str(e)[:50]}',
                'file_name': file_name
            })
            print(f"  ❌ Exception: {str(e)[:50]}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
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
    print(f"\n{'='*60}")
    print("COMPREHENSIVE VERIFICATION STATISTICS")
    print(f"{'='*60}")
    
    print(f"Total Citations Tested: {total_tested}")
    print(f"CourtListener Verified: {stats['courtlistener_verified']} ({courtlistener_pct:.1f}%)")
    print(f"Fallback Verified: {stats['fallback_verified']} ({fallback_pct:.1f}%)")
    print(f"Total Verified: {stats['courtlistener_verified'] + stats['fallback_verified']} ({courtlistener_pct + fallback_pct:.1f}%)")
    print(f"Unverified: {stats['unverified']} ({unverified_pct:.1f}%)")
    print(f"API/Extraction Errors: {stats['api_errors'] + stats['extraction_failures']} ({error_pct:.1f}%)")
    
    print(f"\n{'='*60}")
    print("VERIFICATION SOURCES")
    print(f"{'='*60}")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_tested) * 100 if total_tested > 0 else 0
        print(f"{source}: {count} ({pct:.1f}%)")
    
    print(f"\n{'='*60}")
    print("UNVERIFIED CITATIONS ANALYSIS")
    print(f"{'='*60}")
    
    if unverified_citations:
        print(f"Found {len(unverified_citations)} unverified citations:")
        
        # Group by citation pattern
        citation_patterns = defaultdict(list)
        for item in unverified_citations:
            citation = item['citation']
            # Extract reporter pattern
            parts = citation.split()
            if len(parts) >= 3:
                pattern = f"{parts[1]} {parts[2]}"  # e.g., "F.3d", "U.S."
            else:
                pattern = "Other"
            citation_patterns[pattern].append(item)
        
        print(f"\nUnverified by Citation Pattern:")
        for pattern, items in sorted(citation_patterns.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {pattern}: {len(items)} citations")
            for item in items[:3]:  # Show first 3 examples
                print(f"    - {item['citation']} (from {item['file_name']})")
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")
    else:
        print("🎉 All citations were successfully verified!")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"50_brief_verification_analysis_{timestamp}.json"
    
    analysis_data = {
        'analysis_info': {
            'timestamp': timestamp,
            'total_citations_available': total_citations,
            'sample_size': sample_size,
            'endpoint_tested': endpoint
        },
        'statistics': stats,
        'percentages': {
            'courtlistener_verified': courtlistener_pct,
            'fallback_verified': fallback_pct,
            'total_verified': courtlistener_pct + fallback_pct,
            'unverified': unverified_pct,
            'errors': error_pct
        },
        'sources': dict(sources),
        'unverified_citations': unverified_citations,
        'verification_failures': verification_failures,
        'detailed_results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
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
    
    if unverified_pct > 10:
        print(f"\n⚠️  High unverified rate ({unverified_pct:.1f}%) - review unverified citations above")
    
    return results_file

if __name__ == "__main__":
    analyze_50_brief_citations()
