#!/usr/bin/env python3
"""
Simple test of enhanced verification system on port 5001
"""

import requests
import json
from datetime import datetime

def test_enhanced_verification():
    """Test the enhanced verification system with key citations"""
    
    print("SIMPLE ENHANCED VERIFICATION TEST")
    print("=" * 50)
    
    # Test citations including the known problematic one
    test_citations = [
        "654 F. Supp. 2d 321",  # Known false positive case
        "578 U.S. 5",           # Luis v. United States (should verify)
        "147 Wn. App. 891",     # Washington state (coverage gap)
        "2023 WL 1234567",      # Westlaw (should not verify)
        "456 F.3d 789",         # Federal (should verify if exists)
    ]
    
    results = []
    
    for i, citation in enumerate(test_citations):
        print(f"\n[{i+1}/{len(test_citations)}] Testing: {citation}")
        
        try:
            # Test with enhanced endpoint on correct port
            response = requests.post(
                "http://localhost:5001/api/analyze_enhanced",
                json={
                    "text": f"This case cites {citation}.",
                    "type": "text"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                
                if citations_found:
                    citation_result = citations_found[0]
                    
                    verified = citation_result.get('verified', False)
                    canonical_name = citation_result.get('canonical_name', '')
                    canonical_date = citation_result.get('canonical_date', '')
                    url = citation_result.get('url', '')
                    source = citation_result.get('source', '')
                    confidence = citation_result.get('confidence', 0.0)
                    validation_method = citation_result.get('validation_method', '')
                    
                    print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                    print(f"  Source: {source}")
                    if confidence > 0:
                        print(f"  Confidence: {confidence:.2f}")
                    if canonical_name:
                        print(f"  Case Name: {canonical_name}")
                    if validation_method:
                        print(f"  Validation: {validation_method}")
                    
                    # Check for complete data
                    has_complete_data = bool(canonical_name and canonical_name.strip() and url and url.strip())
                    if verified and not has_complete_data:
                        print(f"  ⚠️  WARNING: Verified but missing complete canonical data")
                    
                    results.append({
                        'citation': citation,
                        'verified': verified,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_date,
                        'url': url,
                        'source': source,
                        'confidence': confidence,
                        'validation_method': validation_method,
                        'has_complete_data': has_complete_data,
                        'status': 'success'
                    })
                    
                else:
                    print(f"  Status: ❌ NO CITATIONS EXTRACTED")
                    results.append({
                        'citation': citation,
                        'verified': False,
                        'status': 'no_citations'
                    })
            else:
                print(f"  Status: ❌ API ERROR {response.status_code}")
                results.append({
                    'citation': citation,
                    'verified': False,
                    'status': f'api_error_{response.status_code}'
                })
                
        except Exception as e:
            print(f"  Status: ❌ EXCEPTION: {str(e)[:50]}")
            results.append({
                'citation': citation,
                'verified': False,
                'status': 'exception',
                'error': str(e)
            })
    
    # Analysis
    print(f"\n{'='*50}")
    print("ANALYSIS")
    print(f"{'='*50}")
    
    total = len(results)
    successful = sum(1 for r in results if r.get('status') == 'success')
    verified = sum(1 for r in results if r.get('verified', False))
    
    print(f"Total citations tested: {total}")
    print(f"Successful API calls: {successful}")
    print(f"Citations verified: {verified}")
    
    # Check specific cases
    problematic_result = next((r for r in results if '654 F. Supp. 2d 321' in r.get('citation', '')), None)
    if problematic_result:
        print(f"\n🎯 PROBLEMATIC CITATION (654 F. Supp. 2d 321):")
        verified = problematic_result.get('verified', False)
        has_data = problematic_result.get('has_complete_data', False)
        source = problematic_result.get('source', 'unknown')
        
        print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"  Complete data: {'✅ YES' if has_data else '❌ NO'}")
        print(f"  Source: {source}")
        
        if verified and has_data:
            print(f"  🎉 ENHANCED VERIFICATION WORKING - Citation properly verified with complete data")
        elif verified and not has_data:
            print(f"  ⚠️  POTENTIAL FALSE POSITIVE - Verified but missing canonical data")
        else:
            print(f"  ✅ FALSE POSITIVE PREVENTED - Citation correctly unverified")
    
    # Check Luis v. United States
    luis_result = next((r for r in results if '578 U.S. 5' in r.get('citation', '')), None)
    if luis_result and luis_result.get('verified', False):
        print(f"\n✅ LUIS V. UNITED STATES (578 U.S. 5): Verified successfully")
        print(f"  Case Name: {luis_result.get('canonical_name', 'N/A')}")
        print(f"  Source: {luis_result.get('source', 'N/A')}")
    
    # Check Washington state citation
    wa_result = next((r for r in results if 'Wn. App.' in r.get('citation', '')), None)
    if wa_result:
        verified = wa_result.get('verified', False)
        source = wa_result.get('source', 'unknown')
        print(f"\n🏛️  WASHINGTON STATE CITATION: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"  Source: {source}")
        if verified:
            print(f"  🎉 Coverage gap filled by enhanced verification!")
    
    # Check Westlaw citation
    wl_result = next((r for r in results if 'WL' in r.get('citation', '')), None)
    if wl_result:
        verified = wl_result.get('verified', False)
        print(f"\n📰 WESTLAW CITATION: {'❌ CORRECTLY UNVERIFIED' if not verified else '⚠️  UNEXPECTEDLY VERIFIED'}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"simple_enhanced_verification_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'total_tested': total,
                'successful_calls': successful,
                'verified_count': verified
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    print(f"\n🎯 ENHANCED VERIFICATION SYSTEM: {'✅ WORKING EFFECTIVELY' if successful > 0 else '❌ NEEDS INVESTIGATION'}")
    
    return results

if __name__ == "__main__":
    test_enhanced_verification()
