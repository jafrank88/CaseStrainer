#!/usr/bin/env python3
"""
Test fallback verification on non-CourtListener, non-WL citations in production
"""

import json
import requests
from datetime import datetime
import time

def test_non_cl_non_wl_citations():
    """Test fallback verification specifically on non-CL, non-WL citations from the comprehensive analysis"""
    
    print("TESTING FALLBACK VERIFICATION ON NON-CL, NON-WL CITATIONS")
    print("=" * 70)
    
    # Load the comprehensive analysis results to get unverified citations
    try:
        with open('comprehensive_all_citations_analysis_20250730_120812.json', 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading analysis results: {e}")
        return
    
    # Extract non-WL unverified citations from the previous analysis
    unverified_citations = analysis_data.get('unverified_citations', [])
    non_wl_unverified = [
        citation for citation in unverified_citations 
        if not ('WL' in citation['citation'] or 'WESTLAW' in citation['citation'].upper())
    ]
    
    print(f"Found {len(non_wl_unverified)} non-WL unverified citations from previous analysis")
    
    if not non_wl_unverified:
        print("✅ No non-WL unverified citations found - all non-WL citations may already be verified")
        return
    
    # Test a representative sample (first 20 citations to avoid overwhelming the system)
    test_sample = non_wl_unverified[:20]
    print(f"Testing sample of {len(test_sample)} citations with fixed fallback verification...")
    print("-" * 70)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    results = []
    stats = {
        'total_tested': 0,
        'now_verified': 0,
        'still_unverified': 0,
        'fallback_verified': 0,
        'courtlistener_verified': 0,
        'api_errors': 0
    }
    
    fallback_sources = []
    newly_verified = []
    
    for i, citation_data in enumerate(test_sample):
        citation = citation_data['citation']
        expected_case = citation_data.get('expected_case', '')
        expected_date = citation_data.get('expected_date', '')
        file_name = citation_data.get('file_name', '')
        
        print(f"\n[{i+1}/{len(test_sample)}] Testing: {citation}")
        print(f"  Expected case: {expected_case}")
        print(f"  Expected date: {expected_date}")
        print(f"  From file: {file_name}")
        
        # Create context-rich input
        if expected_case and expected_case != 'N/A' and expected_date and expected_date != 'N/A':
            test_text = f"In {expected_case} ({expected_date}), the court cited {citation}."
        elif expected_case and expected_case != 'N/A':
            test_text = f"In {expected_case}, the court cited {citation}."
        elif expected_date and expected_date != 'N/A':
            test_text = f"In {expected_date}, the court cited {citation}."
        else:
            test_text = f"This case cites {citation}."
        
        stats['total_tested'] += 1
        
        try:
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                
                if citations_found:
                    citation_result = citations_found[0]
                    verified = citation_result.get('verified', False)
                    source = citation_result.get('source', 'unknown')
                    canonical_name = citation_result.get('canonical_name', '')
                    canonical_date = citation_result.get('canonical_date', '')
                    confidence = citation_result.get('confidence', 0.0)
                    
                    print(f"  Status: {'✅ NOW VERIFIED' if verified else '❌ STILL UNVERIFIED'}")
                    print(f"  Source: {source}")
                    print(f"  Canonical name: {canonical_name}")
                    print(f"  Canonical date: {canonical_date}")
                    print(f"  Confidence: {confidence}")
                    
                    # Categorize the result
                    if verified:
                        stats['now_verified'] += 1
                        
                        # Check if this is fallback verification
                        if ('Cornell' in source or 'Justia' in source or 
                            'fallback' in source.lower() or 'generic' in source.lower()):
                            stats['fallback_verified'] += 1
                            fallback_sources.append(source)
                            print(f"  🎉 SUCCESS: Fallback verification via {source}!")
                            
                            newly_verified.append({
                                'citation': citation,
                                'source': source,
                                'canonical_name': canonical_name,
                                'canonical_date': canonical_date,
                                'confidence': confidence,
                                'expected_case': expected_case,
                                'expected_date': expected_date
                            })
                            
                        elif 'CourtListener' in source:
                            stats['courtlistener_verified'] += 1
                            print(f"  ℹ️  Now verified by CourtListener (coverage improved)")
                        else:
                            print(f"  ℹ️  Verified by other source: {source}")
                    else:
                        stats['still_unverified'] += 1
                        if source == 'regex':
                            print(f"  ❌ Still only regex extraction - fallback not triggered")
                        else:
                            print(f"  ❌ Verification attempted but failed")
                    
                    results.append({
                        'citation': citation,
                        'verified': verified,
                        'source': source,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_date,
                        'confidence': confidence,
                        'expected_case': expected_case,
                        'expected_date': expected_date,
                        'file_name': file_name
                    })
                    
                else:
                    print(f"  ❌ No citations extracted")
                    stats['api_errors'] += 1
                    
            else:
                print(f"  ❌ API error: {response.status_code}")
                stats['api_errors'] += 1
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            stats['api_errors'] += 1
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Generate comprehensive report
    print(f"\n{'='*70}")
    print("FALLBACK VERIFICATION TEST RESULTS")
    print(f"{'='*70}")
    
    total_tested = stats['total_tested']
    if total_tested > 0:
        now_verified_pct = (stats['now_verified'] / total_tested) * 100
        fallback_pct = (stats['fallback_verified'] / total_tested) * 100
        still_unverified_pct = (stats['still_unverified'] / total_tested) * 100
    else:
        now_verified_pct = fallback_pct = still_unverified_pct = 0
    
    print(f"Total Non-CL, Non-WL Citations Tested: {total_tested}")
    print(f"Now Verified: {stats['now_verified']} ({now_verified_pct:.1f}%)")
    print(f"  - Via Fallback: {stats['fallback_verified']} ({fallback_pct:.1f}%)")
    print(f"  - Via CourtListener: {stats['courtlistener_verified']} ({stats['courtlistener_verified']/total_tested*100:.1f}%)")
    print(f"Still Unverified: {stats['still_unverified']} ({still_unverified_pct:.1f}%)")
    print(f"API Errors: {stats['api_errors']} ({stats['api_errors']/total_tested*100:.1f}%)")
    
    # Fallback source analysis
    if fallback_sources:
        print(f"\n{'='*70}")
        print("FALLBACK VERIFICATION SOURCES")
        print(f"{'='*70}")
        from collections import Counter
        source_counts = Counter(fallback_sources)
        for source, count in source_counts.most_common():
            print(f"{source}: {count} citations")
    
    # Show examples of newly verified citations
    if newly_verified:
        print(f"\n{'='*70}")
        print("EXAMPLES OF NEWLY VERIFIED CITATIONS")
        print(f"{'='*70}")
        for i, citation_info in enumerate(newly_verified[:5]):  # Show first 5
            print(f"{i+1}. {citation_info['citation']}")
            print(f"   Source: {citation_info['source']}")
            print(f"   Canonical: {citation_info['canonical_name']} ({citation_info['canonical_date']})")
            print(f"   Expected: {citation_info['expected_case']} ({citation_info['expected_date']})")
            print(f"   Confidence: {citation_info['confidence']}")
            print()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"non_cl_non_wl_fallback_test_{timestamp}.json"
    
    test_results = {
        'test_info': {
            'timestamp': timestamp,
            'endpoint': endpoint,
            'test_type': 'non_cl_non_wl_fallback_verification',
            'sample_size': total_tested
        },
        'statistics': stats,
        'percentages': {
            'now_verified': now_verified_pct,
            'fallback_verified': fallback_pct,
            'still_unverified': still_unverified_pct
        },
        'fallback_sources': dict(Counter(fallback_sources)) if fallback_sources else {},
        'newly_verified_examples': newly_verified,
        'detailed_results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    print(f"Detailed results saved to: {results_file}")
    
    # Overall assessment
    if stats['fallback_verified'] > 0:
        print(f"\n🎉 SUCCESS: Fallback verification is working in production!")
        print(f"   {stats['fallback_verified']} citations now verified via fallback sources")
        improvement = (stats['now_verified'] / total_tested) * 100
        print(f"   Overall improvement: {improvement:.1f}% of previously unverified citations now verified")
    elif stats['now_verified'] > 0:
        print(f"\n✅ PARTIAL SUCCESS: {stats['now_verified']} citations now verified")
        print(f"   May be due to improved CourtListener coverage rather than fallback")
    else:
        print(f"\n❌ NO IMPROVEMENT: All citations still unverified")
        print(f"   Fallback verification may still have issues")
    
    return stats['fallback_verified'] > 0

if __name__ == "__main__":
    success = test_non_cl_non_wl_citations()
    
    if success:
        print(f"\nFINAL RESULT: Fallback verification system is working in production! 🚀")
    else:
        print(f"\nFINAL RESULT: May need further investigation of fallback system")
