#!/usr/bin/env python3
"""
Test enhanced fallback verification with both Cornell Law and Justia support
"""

import requests
import json
from datetime import datetime
import time

def test_enhanced_fallback_sources():
    """Test the enhanced fallback system with multiple sources"""
    
    print("TESTING ENHANCED FALLBACK VERIFICATION WITH MULTIPLE SOURCES")
    print("=" * 70)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    # Test citations that should trigger fallback verification
    test_cases = [
        {
            'citation': '194 Wn. 2d 784',
            'case_name': 'State v. Arndt',
            'date': '2019',
            'description': 'Washington state citation (should try Cornell Law, then Justia)'
        },
        {
            'citation': '453 P.3d 696',
            'case_name': 'State v. Armenta',
            'date': '2019',
            'description': 'Pacific Reporter citation (should try Cornell Law, then Justia)'
        },
        {
            'citation': '188 Wn. 2d 766',
            'case_name': 'State v. Lile',
            'date': '2014',
            'description': 'Washington state citation (older case)'
        },
        {
            'citation': '69 P.3d 594',
            'case_name': 'State ex rel. Carroll v. Junker',
            'date': '2003',
            'description': 'Pacific Reporter citation (older case)'
        },
        {
            'citation': '829 P.2d 1069',
            'case_name': 'State v. Russell',
            'date': '1994',
            'description': 'Pacific Reporter 2d citation (very old case)'
        }
    ]
    
    results = []
    stats = {
        'total_tested': 0,
        'verified': 0,
        'unverified': 0,
        'cornell_law_verified': 0,
        'justia_verified': 0,
        'courtlistener_verified': 0,
        'other_verified': 0,
        'api_errors': 0
    }
    
    fallback_examples = []
    
    print(f"Testing {len(test_cases)} citations with enhanced fallback verification...")
    print("-" * 70)
    
    for i, test_case in enumerate(test_cases):
        citation = test_case['citation']
        case_name = test_case['case_name']
        date = test_case['date']
        description = test_case['description']
        
        print(f"\n[{i+1}/{len(test_cases)}] {description}")
        print(f"Citation: {citation}")
        print(f"Expected case: {case_name}")
        print(f"Expected date: {date}")
        
        # Create context-rich test text
        test_text = f"In {case_name} ({date}), the court cited {citation}."
        
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
                    
                    print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                    print(f"  Source: {source}")
                    print(f"  Canonical name: {canonical_name}")
                    print(f"  Canonical date: {canonical_date}")
                    print(f"  Confidence: {confidence}")
                    
                    # Categorize the verification source
                    if verified:
                        stats['verified'] += 1
                        
                        if 'cornell_law' in source.lower() or 'cornell' in source.lower():
                            stats['cornell_law_verified'] += 1
                            print("  🎯 SUCCESS: Verified via Cornell Law!")
                            fallback_examples.append({
                                'citation': citation,
                                'source': 'Cornell Law',
                                'canonical_name': canonical_name,
                                'confidence': confidence
                            })
                            
                        elif 'justia' in source.lower():
                            stats['justia_verified'] += 1
                            print("  🎯 SUCCESS: Verified via Justia!")
                            fallback_examples.append({
                                'citation': citation,
                                'source': 'Justia',
                                'canonical_name': canonical_name,
                                'confidence': confidence
                            })
                            
                        elif 'courtlistener' in source.lower():
                            stats['courtlistener_verified'] += 1
                            print("  ℹ️  Verified via CourtListener")
                            
                        else:
                            stats['other_verified'] += 1
                            print(f"  ℹ️  Verified via other source: {source}")
                    else:
                        stats['unverified'] += 1
                        if source == 'regex':
                            print("  ❌ Only regex extraction - no verification attempted")
                        else:
                            print("  ❌ Verification attempted but failed")
                    
                    results.append({
                        'citation': citation,
                        'verified': verified,
                        'source': source,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_date,
                        'confidence': confidence,
                        'expected_case': case_name,
                        'expected_date': date,
                        'description': description
                    })
                    
                else:
                    print("  ❌ No citations extracted")
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
    print("\n" + "=" * 70)
    print("ENHANCED FALLBACK VERIFICATION RESULTS")
    print("=" * 70)
    
    total_tested = stats['total_tested']
    if total_tested > 0:
        verified_pct = (stats['verified'] / total_tested) * 100
        cornell_pct = (stats['cornell_law_verified'] / total_tested) * 100
        justia_pct = (stats['justia_verified'] / total_tested) * 100
        unverified_pct = (stats['unverified'] / total_tested) * 100
    else:
        verified_pct = cornell_pct = justia_pct = unverified_pct = 0
    
    print(f"Total Citations Tested: {total_tested}")
    print(f"Total Verified: {stats['verified']} ({verified_pct:.1f}%)")
    print(f"  - Cornell Law: {stats['cornell_law_verified']} ({cornell_pct:.1f}%)")
    print(f"  - Justia: {stats['justia_verified']} ({justia_pct:.1f}%)")
    print(f"  - CourtListener: {stats['courtlistener_verified']} ({stats['courtlistener_verified']/total_tested*100:.1f}%)")
    print(f"  - Other sources: {stats['other_verified']} ({stats['other_verified']/total_tested*100:.1f}%)")
    print(f"Unverified: {stats['unverified']} ({unverified_pct:.1f}%)")
    print(f"API Errors: {stats['api_errors']} ({stats['api_errors']/total_tested*100:.1f}%)")
    
    # Show fallback examples
    if fallback_examples:
        print("\n" + "=" * 70)
        print("FALLBACK VERIFICATION EXAMPLES")
        print("=" * 70)
        for i, example in enumerate(fallback_examples):
            print(f"{i+1}. {example['citation']} via {example['source']}")
            print(f"   Canonical: {example['canonical_name']}")
            print(f"   Confidence: {example['confidence']}")
            print()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_fallback_test_{timestamp}.json"
    
    test_results = {
        'test_info': {
            'timestamp': timestamp,
            'endpoint': endpoint,
            'test_type': 'enhanced_fallback_multiple_sources',
            'sources_tested': ['Cornell Law', 'Justia', 'CourtListener']
        },
        'statistics': stats,
        'percentages': {
            'verified': verified_pct,
            'cornell_law': cornell_pct,
            'justia': justia_pct,
            'unverified': unverified_pct
        },
        'fallback_examples': fallback_examples,
        'detailed_results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"Detailed results saved to: {results_file}")
    
    # Overall assessment
    total_fallback = stats['cornell_law_verified'] + stats['justia_verified']
    
    if total_fallback > 0:
        print("\n🎉 SUCCESS: Enhanced fallback verification is working!")
        print(f"   {total_fallback} citations verified via fallback sources")
        print(f"   Cornell Law: {stats['cornell_law_verified']} citations")
        print(f"   Justia: {stats['justia_verified']} citations")
        print(f"   Overall verification rate: {verified_pct:.1f}%")
    elif stats['verified'] > 0:
        print("\n✅ PARTIAL SUCCESS: {} citations verified".format(stats['verified']))
        print("   May be via CourtListener rather than fallback")
    else:
        print("\n❌ NO VERIFICATION: All citations remain unverified")
    
    return total_fallback > 0

if __name__ == "__main__":
    success = test_enhanced_fallback_sources()
    
    if success:
        print("\nFINAL RESULT: Enhanced fallback system with multiple sources is working! 🚀")
    else:
        print("\nFINAL RESULT: May need further investigation of fallback sources")
