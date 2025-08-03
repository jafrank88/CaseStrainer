#!/usr/bin/env python3
"""
Test fallback verification in production API after fixing FallbackVerifier
"""

import requests
import json
from datetime import datetime

def test_fallback_in_production():
    """Test that fallback verification now works in the production API"""
    
    print("TESTING FALLBACK VERIFICATION IN PRODUCTION API")
    print("=" * 60)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    # Test citations that should trigger fallback verification
    test_cases = [
        {
            'citation': '194 Wn. 2d 784',
            'case_name': 'State v. Arndt',
            'date': '2019',
            'description': 'Washington state citation'
        },
        {
            'citation': '453 P.3d 696',
            'case_name': 'State v. Armenta',
            'date': '2019',
            'description': 'Pacific Reporter citation'
        },
        {
            'citation': '69 P.3d 594',
            'case_name': 'State ex rel. Carroll v. Junker',
            'date': '2003',
            'description': 'Pacific Reporter citation (older)'
        },
        {
            'citation': '188 Wn. 2d 766',
            'case_name': 'State v. Lile',
            'date': '2014',
            'description': 'Washington state citation (older)'
        }
    ]
    
    results = []
    fallback_count = 0
    verified_count = 0
    
    print(f"Testing {len(test_cases)} citations that should trigger fallback verification...")
    print("-" * 60)
    
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
                    
                    print(f"  Status: {'VERIFIED' if verified else 'UNVERIFIED'}")
                    print(f"  Source: {source}")
                    print(f"  Canonical name: {canonical_name}")
                    print(f"  Canonical date: {canonical_date}")
                    print(f"  Confidence: {confidence}")
                    
                    # Check if this is fallback verification
                    is_fallback = False
                    if verified and source:
                        if ('Cornell' in source or 'Justia' in source or 
                            'fallback' in source.lower() or 'generic' in source.lower()):
                            is_fallback = True
                            fallback_count += 1
                            print(f"  SUCCESS: Fallback verification detected!")
                        elif 'CourtListener' in source:
                            print(f"  INFO: CourtListener verification (not fallback)")
                        else:
                            print(f"  INFO: Other verification source")
                    
                    if verified:
                        verified_count += 1
                    
                    results.append({
                        'citation': citation,
                        'verified': verified,
                        'source': source,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_date,
                        'confidence': confidence,
                        'is_fallback': is_fallback,
                        'description': description
                    })
                    
                else:
                    print(f"  ERROR: No citations extracted from text")
                    results.append({
                        'citation': citation,
                        'verified': False,
                        'source': 'no_extraction',
                        'error': 'No citations extracted',
                        'description': description
                    })
            else:
                print(f"  ERROR: API returned status {response.status_code}")
                results.append({
                    'citation': citation,
                    'verified': False,
                    'source': 'api_error',
                    'error': f'HTTP {response.status_code}',
                    'description': description
                })
                
        except Exception as e:
            print(f"  ERROR: Exception - {str(e)}")
            results.append({
                'citation': citation,
                'verified': False,
                'source': 'exception',
                'error': str(e),
                'description': description
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("FALLBACK VERIFICATION TEST RESULTS")
    print(f"{'='*60}")
    
    total_tested = len(test_cases)
    print(f"Total citations tested: {total_tested}")
    print(f"Citations verified: {verified_count} ({verified_count/total_tested*100:.1f}%)")
    print(f"Fallback verifications: {fallback_count} ({fallback_count/total_tested*100:.1f}%)")
    
    if fallback_count > 0:
        print(f"\nSUCCESS: Fallback verification is now working!")
        print(f"Fixed FallbackVerifier is successfully verifying state citations.")
    elif verified_count > 0:
        print(f"\nPARTIAL SUCCESS: Citations are being verified, but may be via CourtListener")
        print(f"This could mean CourtListener coverage improved, or fallback isn't needed")
    else:
        print(f"\nISSUE: No citations were verified - there may still be a problem")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"fallback_production_test_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'endpoint': endpoint,
                'total_tested': total_tested,
                'verified_count': verified_count,
                'fallback_count': fallback_count
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return fallback_count > 0

if __name__ == "__main__":
    success = test_fallback_in_production()
    
    if success:
        print(f"\nOVERALL: Fallback verification fix is working in production!")
    else:
        print(f"\nOVERALL: May need further investigation or CourtListener is handling these citations")
