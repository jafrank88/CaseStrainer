#!/usr/bin/env python3
"""
Test enhanced verification with correct URL path
"""

import requests
import json
from datetime import datetime

def test_enhanced_verification_endpoints():
    """Test different endpoint paths to find the working one"""
    
    print("TESTING ENHANCED VERIFICATION ENDPOINTS")
    print("=" * 50)
    
    # Test citation
    test_citation = "654 F. Supp. 2d 321"  # Known problematic citation
    test_payload = {
        "text": f"This case cites {test_citation}.",
        "type": "text"
    }
    
    # Different possible endpoint URLs
    endpoints_to_test = [
        "http://localhost:5001/api/analyze_enhanced",
        "http://localhost:5001/casestrainer/api/analyze_enhanced", 
        "http://localhost:5001/analyze_enhanced",
        "http://localhost:5001/api/analyze",
        "http://localhost:5001/casestrainer/api/analyze"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting endpoint: {endpoint}")
        
        try:
            response = requests.post(
                endpoint,
                json=test_payload,
                timeout=10
            )
            
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                print(f"  ✅ SUCCESS - Found {len(citations)} citations")
                
                if citations:
                    citation_result = citations[0]
                    verified = citation_result.get('verified', False)
                    source = citation_result.get('source', '')
                    canonical_name = citation_result.get('canonical_name', '')
                    
                    print(f"  Citation: {citation_result.get('citation', '')}")
                    print(f"  Verified: {'✅' if verified else '❌'}")
                    print(f"  Source: {source}")
                    if canonical_name:
                        print(f"  Case Name: {canonical_name}")
                    
                    # This is our working endpoint!
                    return endpoint, citation_result
                
            elif response.status_code == 404:
                print(f"  ❌ NOT FOUND")
            else:
                print(f"  ❌ ERROR: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Error details: {error_data}")
                except:
                    print(f"  Response text: {response.text[:100]}")
                    
        except Exception as e:
            print(f"  ❌ EXCEPTION: {str(e)[:50]}")
    
    return None, None

def run_enhanced_verification_test(working_endpoint):
    """Run the enhanced verification test with the working endpoint"""
    
    print(f"\n{'='*60}")
    print("ENHANCED VERIFICATION EFFECTIVENESS TEST")
    print(f"Using endpoint: {working_endpoint}")
    print(f"{'='*60}")
    
    # Key test citations
    test_citations = [
        "654 F. Supp. 2d 321",  # Known false positive case - should be fixed
        "578 U.S. 5",           # Luis v. United States - should verify
        "147 Wn. App. 891",     # Washington state - coverage gap test
        "2023 WL 1234567",      # Westlaw - should not verify
        "456 F.3d 789",         # Federal - may verify if exists
        "999 F.3d 999",         # Likely non-existent - should not verify
    ]
    
    results = []
    
    for i, citation in enumerate(test_citations):
        print(f"\n[{i+1}/{len(test_citations)}] Testing: {citation}")
        
        try:
            response = requests.post(
                working_endpoint,
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
                        print(f"  Validation Method: {validation_method}")
                    
                    # Check data completeness
                    has_complete_data = bool(canonical_name and canonical_name.strip() and url and url.strip())
                    
                    if verified and not has_complete_data:
                        print(f"  ⚠️  WARNING: Verified but incomplete canonical data")
                    elif verified and has_complete_data:
                        print(f"  ✅ Complete verification data")
                    
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
    
    return results

def analyze_results(results):
    """Analyze the enhanced verification test results"""
    
    print(f"\n{'='*60}")
    print("ENHANCED VERIFICATION ANALYSIS")
    print(f"{'='*60}")
    
    total = len(results)
    successful = sum(1 for r in results if r.get('status') == 'success')
    verified = sum(1 for r in results if r.get('verified', False))
    complete_data = sum(1 for r in results if r.get('has_complete_data', False))
    
    print(f"Total citations tested: {total}")
    print(f"Successful API calls: {successful} ({successful/total*100:.1f}%)")
    print(f"Citations verified: {verified} ({verified/total*100:.1f}%)")
    if verified > 0:
        print(f"Verified with complete data: {complete_data}/{verified} ({complete_data/verified*100:.1f}%)")
    
    # Analyze verification sources
    sources = {}
    for result in results:
        if result.get('verified', False):
            source = result.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
    
    if sources:
        print(f"\nVerification sources:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
    
    # Key test case analysis
    print(f"\nKEY TEST CASES:")
    
    # Check the problematic citation
    problematic = next((r for r in results if '654 F. Supp. 2d 321' in r.get('citation', '')), None)
    if problematic:
        verified = problematic.get('verified', False)
        has_data = problematic.get('has_complete_data', False)
        source = problematic.get('source', 'unknown')
        
        print(f"  🎯 Problematic Citation (654 F. Supp. 2d 321):")
        print(f"     Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"     Complete data: {'✅ YES' if has_data else '❌ NO'}")
        print(f"     Source: {source}")
        
        if verified and has_data:
            print(f"     🎉 ENHANCED VERIFICATION SUCCESS - Proper verification with complete data")
        elif verified and not has_data:
            print(f"     ⚠️  POTENTIAL FALSE POSITIVE - Verified but missing canonical data")
        else:
            print(f"     ✅ FALSE POSITIVE PREVENTED - Citation correctly unverified")
    
    # Check Luis v. United States
    luis = next((r for r in results if '578 U.S. 5' in r.get('citation', '')), None)
    if luis:
        verified = luis.get('verified', False)
        case_name = luis.get('canonical_name', '')
        print(f"  📚 Luis v. United States (578 U.S. 5): {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        if verified and case_name:
            print(f"     Case Name: {case_name}")
    
    # Check Washington state citation
    wa = next((r for r in results if 'Wn. App.' in r.get('citation', '')), None)
    if wa:
        verified = wa.get('verified', False)
        source = wa.get('source', 'unknown')
        print(f"  🏛️  Washington State Citation: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        if verified:
            print(f"     Source: {source} (coverage gap filled!)")
    
    # Check Westlaw citation
    wl = next((r for r in results if 'WL' in r.get('citation', '')), None)
    if wl:
        verified = wl.get('verified', False)
        print(f"  📰 Westlaw Citation: {'✅ CORRECTLY UNVERIFIED' if not verified else '⚠️  UNEXPECTEDLY VERIFIED'}")
    
    # Overall assessment
    print(f"\n{'='*60}")
    print("OVERALL ASSESSMENT")
    print(f"{'='*60}")
    
    if successful >= total * 0.8:  # 80% success rate
        print("✅ API connectivity: EXCELLENT")
    elif successful >= total * 0.5:  # 50% success rate
        print("⚠️  API connectivity: FAIR")
    else:
        print("❌ API connectivity: POOR")
    
    if verified > 0 and complete_data/verified >= 0.8:  # 80% of verified have complete data
        print("✅ Data quality: EXCELLENT")
    elif verified > 0 and complete_data/verified >= 0.5:  # 50% of verified have complete data
        print("⚠️  Data quality: FAIR")
    else:
        print("❌ Data quality: POOR")
    
    # Check if false positive issue is resolved
    if problematic and not problematic.get('verified', False):
        print("✅ False positive prevention: WORKING")
    elif problematic and problematic.get('verified', False) and problematic.get('has_complete_data', False):
        print("✅ Enhanced verification: WORKING (legitimate verification)")
    elif problematic and problematic.get('verified', False) and not problematic.get('has_complete_data', False):
        print("⚠️  False positive prevention: NEEDS REVIEW")
    else:
        print("❓ False positive prevention: UNCLEAR")
    
    overall_status = "EXCELLENT" if (successful >= total * 0.8 and 
                                   (verified == 0 or complete_data/verified >= 0.8)) else "NEEDS REVIEW"
    
    print(f"\n🎯 ENHANCED VERIFICATION SYSTEM STATUS: {overall_status}")
    
    return {
        'total': total,
        'successful': successful,
        'verified': verified,
        'complete_data': complete_data,
        'sources': sources,
        'overall_status': overall_status
    }

def main():
    """Main test function"""
    
    # First, find the working endpoint
    working_endpoint, sample_result = test_enhanced_verification_endpoints()
    
    if not working_endpoint:
        print("\n❌ FAILED TO FIND WORKING ENDPOINT")
        print("The enhanced verification system may not be properly deployed.")
        return
    
    print(f"\n✅ FOUND WORKING ENDPOINT: {working_endpoint}")
    
    # Run comprehensive test
    results = run_enhanced_verification_test(working_endpoint)
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_verification_test_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'working_endpoint': working_endpoint,
                'total_tested': analysis['total'],
                'successful_calls': analysis['successful'],
                'verified_count': analysis['verified'],
                'overall_status': analysis['overall_status']
            },
            'results': results,
            'analysis': analysis
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main()
