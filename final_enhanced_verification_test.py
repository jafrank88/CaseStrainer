#!/usr/bin/env python3
"""
Final enhanced verification test using correct API prefix
"""

import requests
import json
from datetime import datetime

def test_enhanced_verification_final():
    """Test enhanced verification with correct API endpoint"""
    
    print("FINAL ENHANCED VERIFICATION TEST")
    print("=" * 50)
    print("Using correct endpoint: /casestrainer/api/analyze")
    print("=" * 50)
    
    # Test citations including the known problematic one
    test_citations = [
        "654 F. Supp. 2d 321",  # Known false positive case - should be fixed
        "578 U.S. 5",           # Luis v. United States - should verify
        "147 Wn. App. 891",     # Washington state - coverage gap test
        "2023 WL 1234567",      # Westlaw - should not verify
        "456 F.3d 789",         # Federal - may verify if exists
        "999 F.3d 999",         # Likely non-existent - should not verify
    ]
    
    results = []
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    for i, citation in enumerate(test_citations):
        print(f"\n[{i+1}/{len(test_citations)}] Testing: {citation}")
        
        try:
            # Test with the correct endpoint
            response = requests.post(
                endpoint,
                json={
                    "text": f"This case cites {citation}.",
                    "type": "text"
                },
                timeout=20
            )
            
            print(f"  Status Code: {response.status_code}")
            
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
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data}")
                except:
                    print(f"  Response: {response.text[:100]}")
                
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

def analyze_final_results(results):
    """Analyze the final enhanced verification test results"""
    
    print(f"\n{'='*70}")
    print("ENHANCED VERIFICATION SYSTEM ANALYSIS")
    print(f"{'='*70}")
    
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
    validation_methods = {}
    confidence_scores = []
    
    for result in results:
        if result.get('verified', False):
            source = result.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            
            method = result.get('validation_method', 'unknown')
            if method and method != 'unknown':
                validation_methods[method] = validation_methods.get(method, 0) + 1
            
            confidence = result.get('confidence', 0.0)
            if confidence > 0:
                confidence_scores.append(confidence)
    
    if sources:
        print(f"\nVerification sources:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            percentage = count / verified * 100 if verified > 0 else 0
            print(f"  {source}: {count} ({percentage:.1f}%)")
    
    if validation_methods:
        print(f"\nValidation methods:")
        for method, count in sorted(validation_methods.items(), key=lambda x: x[1], reverse=True):
            percentage = count / verified * 100 if verified > 0 else 0
            print(f"  {method}: {count} ({percentage:.1f}%)")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        high_confidence = sum(1 for c in confidence_scores if c > 0.8)
        medium_confidence = sum(1 for c in confidence_scores if 0.5 <= c <= 0.8)
        low_confidence = sum(1 for c in confidence_scores if c < 0.5)
        
        print(f"\nConfidence scores:")
        print(f"  Average: {avg_confidence:.2f}")
        print(f"  High (>0.8): {high_confidence}")
        print(f"  Medium (0.5-0.8): {medium_confidence}")
        print(f"  Low (<0.5): {low_confidence}")
    
    # Key test case analysis
    print(f"\n{'='*50}")
    print("KEY TEST CASES ANALYSIS")
    print(f"{'='*50}")
    
    # Check the problematic citation (654 F. Supp. 2d 321)
    problematic = next((r for r in results if '654 F. Supp. 2d 321' in r.get('citation', '')), None)
    if problematic:
        verified = problematic.get('verified', False)
        has_data = problematic.get('has_complete_data', False)
        source = problematic.get('source', 'unknown')
        
        print(f"🎯 PROBLEMATIC CITATION (654 F. Supp. 2d 321):")
        print(f"   Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"   Complete data: {'✅ YES' if has_data else '❌ NO'}")
        print(f"   Source: {source}")
        
        if verified and has_data:
            print(f"   🎉 ENHANCED VERIFICATION SUCCESS - Proper verification with complete data!")
        elif verified and not has_data:
            print(f"   ⚠️  POTENTIAL FALSE POSITIVE - Verified but missing canonical data")
        else:
            print(f"   ✅ FALSE POSITIVE PREVENTED - Citation correctly unverified")
    
    # Check Luis v. United States (578 U.S. 5)
    luis = next((r for r in results if '578 U.S. 5' in r.get('citation', '')), None)
    if luis:
        verified = luis.get('verified', False)
        case_name = luis.get('canonical_name', '')
        source = luis.get('source', 'unknown')
        print(f"\n📚 LUIS V. UNITED STATES (578 U.S. 5):")
        print(f"   Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        if verified:
            print(f"   Case Name: {case_name}")
            print(f"   Source: {source}")
    
    # Check Washington state citation (147 Wn. App. 891)
    wa = next((r for r in results if 'Wn. App.' in r.get('citation', '')), None)
    if wa:
        verified = wa.get('verified', False)
        source = wa.get('source', 'unknown')
        print(f"\n🏛️  WASHINGTON STATE CITATION (147 Wn. App. 891):")
        print(f"   Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"   Source: {source}")
        if verified:
            print(f"   🎉 COVERAGE GAP FILLED by enhanced verification!")
        else:
            print(f"   📝 Coverage gap remains (expected for some state reporters)")
    
    # Check Westlaw citation (2023 WL 1234567)
    wl = next((r for r in results if 'WL' in r.get('citation', '')), None)
    if wl:
        verified = wl.get('verified', False)
        print(f"\n📰 WESTLAW CITATION (2023 WL 1234567):")
        print(f"   Status: {'✅ CORRECTLY UNVERIFIED' if not verified else '⚠️  UNEXPECTEDLY VERIFIED'}")
        if verified:
            print(f"   ⚠️  WARNING: Westlaw citations should typically not be verified")
    
    # Check likely non-existent citation (999 F.3d 999)
    fake = next((r for r in results if '999 F.3d 999' in r.get('citation', '')), None)
    if fake:
        verified = fake.get('verified', False)
        print(f"\n🚫 LIKELY NON-EXISTENT CITATION (999 F.3d 999):")
        print(f"   Status: {'✅ CORRECTLY UNVERIFIED' if not verified else '⚠️  FALSE POSITIVE'}")
    
    # Overall assessment
    print(f"\n{'='*70}")
    print("OVERALL ENHANCED VERIFICATION ASSESSMENT")
    print(f"{'='*70}")
    
    # API connectivity assessment
    if successful >= total * 0.8:
        print("✅ API connectivity: EXCELLENT")
        api_status = "excellent"
    elif successful >= total * 0.5:
        print("⚠️  API connectivity: FAIR")
        api_status = "fair"
    else:
        print("❌ API connectivity: POOR")
        api_status = "poor"
    
    # Data quality assessment
    if verified > 0:
        data_quality_ratio = complete_data / verified
        if data_quality_ratio >= 0.8:
            print("✅ Data quality: EXCELLENT")
            data_status = "excellent"
        elif data_quality_ratio >= 0.5:
            print("⚠️  Data quality: FAIR")
            data_status = "fair"
        else:
            print("❌ Data quality: POOR")
            data_status = "poor"
    else:
        print("❓ Data quality: NO VERIFIED CITATIONS TO ASSESS")
        data_status = "no_data"
    
    # False positive prevention assessment
    if problematic:
        if not problematic.get('verified', False):
            print("✅ False positive prevention: WORKING")
            fp_status = "working"
        elif problematic.get('verified', False) and problematic.get('has_complete_data', False):
            print("✅ Enhanced verification: WORKING (legitimate verification)")
            fp_status = "enhanced_working"
        else:
            print("⚠️  False positive prevention: NEEDS REVIEW")
            fp_status = "needs_review"
    else:
        print("❓ False positive prevention: UNCLEAR (test case not found)")
        fp_status = "unclear"
    
    # Coverage assessment
    coverage_improvements = 0
    if wa and wa.get('verified', False):
        coverage_improvements += 1
        print("✅ Coverage improvement: Washington state citations now verified")
    
    # Overall system status
    if (api_status == "excellent" and 
        data_status in ["excellent", "fair"] and 
        fp_status in ["working", "enhanced_working"]):
        overall_status = "EXCELLENT"
        print(f"\n🎉 ENHANCED VERIFICATION SYSTEM STATUS: {overall_status}")
        print("The enhanced verification system is working effectively!")
    elif (api_status in ["excellent", "fair"] and 
          successful > 0):
        overall_status = "GOOD"
        print(f"\n✅ ENHANCED VERIFICATION SYSTEM STATUS: {overall_status}")
        print("The enhanced verification system is functional with minor issues.")
    else:
        overall_status = "NEEDS REVIEW"
        print(f"\n⚠️  ENHANCED VERIFICATION SYSTEM STATUS: {overall_status}")
        print("The enhanced verification system needs investigation.")
    
    return {
        'total': total,
        'successful': successful,
        'verified': verified,
        'complete_data': complete_data,
        'sources': sources,
        'validation_methods': validation_methods,
        'confidence_scores': confidence_scores,
        'api_status': api_status,
        'data_status': data_status,
        'fp_status': fp_status,
        'coverage_improvements': coverage_improvements,
        'overall_status': overall_status
    }

def main():
    """Main test function"""
    
    print("Starting final enhanced verification system test...")
    
    # Run the test
    results = test_enhanced_verification_final()
    
    # Analyze results
    analysis = analyze_final_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"final_enhanced_verification_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'endpoint_used': 'http://localhost:5001/casestrainer/api/analyze',
                'total_tested': analysis['total'],
                'successful_calls': analysis['successful'],
                'verified_count': analysis['verified'],
                'overall_status': analysis['overall_status']
            },
            'results': results,
            'analysis': analysis
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Enhanced verification system tested on {analysis['total']} citations")
    print(f"✅ {analysis['successful']} successful API calls")
    print(f"✅ {analysis['verified']} citations verified")
    print(f"✅ {analysis['complete_data']} verified citations have complete data")
    print(f"✅ Overall system status: {analysis['overall_status']}")
    
    if analysis['coverage_improvements'] > 0:
        print(f"🎉 {analysis['coverage_improvements']} coverage improvements detected!")
    
    return analysis

if __name__ == "__main__":
    main()
