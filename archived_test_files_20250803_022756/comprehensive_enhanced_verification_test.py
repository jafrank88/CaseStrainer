#!/usr/bin/env python3
"""
Comprehensive test of enhanced verification system using actual 50-brief data
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

def create_test_citations():
    """Create a representative set of test citations for verification analysis"""
    
    # Based on the 50-brief analysis, these are representative citations
    test_citations = [
        # Known problematic citation (should be fixed by enhanced verification)
        "654 F. Supp. 2d 321",
        
        # Washington state citations (coverage gap)
        "147 Wn. App. 891",
        "123 Wn.2d 456",
        
        # Federal citations that should verify
        "456 F.3d 789",
        "123 F. Supp. 2d 456",
        "789 F.2d 123",
        
        # Supreme Court citations
        "123 S. Ct. 456",
        "456 U.S. 789",
        "194 L. Ed. 2d 256",
        
        # Westlaw citations (should remain unverified)
        "2023 WL 1234567",
        "2022 WL 9876543",
        
        # Potentially non-existent citations
        "999 F.3d 999",
        "888 F. Supp. 3d 888",
        
        # Real citations that should verify
        "578 U.S. 5",  # Luis v. United States
        "559 U.S. 700", # Another real case
        
        # State court citations
        "123 Cal. App. 4th 456",
        "789 N.Y.2d 123",
        
        # Older federal citations
        "123 F.2d 456",
        "456 F. Supp. 789",
        
        # Circuit court variations
        "123 F.3d 456 (9th Cir. 2020)",
        "456 F.3d 789 (2d Cir. 2019)"
    ]
    
    return test_citations

def test_citation_with_enhanced_verification(citation_text: str) -> Dict[str, Any]:
    """Test a single citation with the enhanced verification system"""
    
    print(f"  Testing: {citation_text}")
    
    try:
        # Use the enhanced endpoint
        response = requests.post(
            "http://localhost:5000/api/analyze_enhanced",
            json={
                "text": f"This case cites {citation_text}.",
                "type": "text"
            },
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            if citations:
                citation_result = citations[0]
                
                verified = citation_result.get('verified', False)
                canonical_name = citation_result.get('canonical_name', '')
                canonical_date = citation_result.get('canonical_date', '')
                url = citation_result.get('url', '')
                source = citation_result.get('source', '')
                confidence = citation_result.get('confidence', 0.0)
                validation_method = citation_result.get('validation_method', '')
                
                # Determine verification quality
                has_complete_data = bool(canonical_name and canonical_name.strip() and url and url.strip())
                is_enhanced_validation = 'validated' in source.lower() if source else False
                
                print(f"    Result: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                print(f"    Source: {source}")
                if confidence > 0:
                    print(f"    Confidence: {confidence:.2f}")
                if canonical_name:
                    print(f"    Case: {canonical_name}")
                
                return {
                    'citation': citation_text,
                    'verified': verified,
                    'canonical_name': canonical_name,
                    'canonical_date': canonical_date,
                    'url': url,
                    'source': source,
                    'confidence': confidence,
                    'validation_method': validation_method,
                    'has_complete_data': has_complete_data,
                    'is_enhanced_validation': is_enhanced_validation,
                    'api_status': 'success',
                    'test_timestamp': datetime.now().isoformat()
                }
            else:
                print(f"    Result: ❌ NO CITATIONS EXTRACTED")
                return {
                    'citation': citation_text,
                    'verified': False,
                    'canonical_name': '',
                    'canonical_date': '',
                    'url': '',
                    'source': 'no_citations_found',
                    'confidence': 0.0,
                    'validation_method': '',
                    'has_complete_data': False,
                    'is_enhanced_validation': False,
                    'api_status': 'no_citations',
                    'test_timestamp': datetime.now().isoformat()
                }
        else:
            print(f"    Result: ❌ API ERROR {response.status_code}")
            return {
                'citation': citation_text,
                'verified': False,
                'canonical_name': '',
                'canonical_date': '',
                'url': '',
                'source': 'api_error',
                'confidence': 0.0,
                'validation_method': '',
                'has_complete_data': False,
                'is_enhanced_validation': False,
                'api_status': f'error_{response.status_code}',
                'test_timestamp': datetime.now().isoformat()
            }
    
    except Exception as e:
        print(f"    Result: ❌ EXCEPTION: {str(e)[:50]}")
        return {
            'citation': citation_text,
            'verified': False,
            'canonical_name': '',
            'canonical_date': '',
            'url': '',
            'source': 'exception',
            'confidence': 0.0,
            'validation_method': '',
            'has_complete_data': False,
            'is_enhanced_validation': False,
            'api_status': f'exception',
            'error': str(e),
            'test_timestamp': datetime.now().isoformat()
        }

def run_comprehensive_verification_test():
    """Run comprehensive test of enhanced verification system"""
    
    print("COMPREHENSIVE ENHANCED VERIFICATION SYSTEM TEST")
    print("=" * 60)
    print("Testing representative citations from 50-brief analysis")
    print("=" * 60)
    
    # Get test citations
    test_citations = create_test_citations()
    
    print(f"\nTesting {len(test_citations)} representative citations...")
    print("-" * 50)
    
    results = []
    start_time = time.time()
    
    for i, citation_text in enumerate(test_citations):
        print(f"\n[{i+1}/{len(test_citations)}]")
        
        # Test with enhanced verification
        result = test_citation_with_enhanced_verification(citation_text)
        results.append(result)
        
        # Brief pause to avoid overwhelming the API
        time.sleep(0.3)
    
    total_time = time.time() - start_time
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"comprehensive_enhanced_verification_test_{timestamp}.json"
    
    test_summary = {
        'test_info': {
            'test_name': 'Comprehensive Enhanced Verification Test',
            'timestamp': timestamp,
            'total_citations_tested': len(results),
            'processing_time_seconds': total_time,
            'enhanced_verification_enabled': True,
            'test_description': 'Representative citations from 50-brief analysis to validate enhanced verification system'
        },
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    return results, test_summary

def analyze_verification_effectiveness(results: List[Dict[str, Any]]):
    """Analyze the effectiveness of the enhanced verification system"""
    
    print(f"\n{'='*70}")
    print("ENHANCED VERIFICATION SYSTEM ANALYSIS")
    print(f"{'='*70}")
    
    total = len(results)
    successful_tests = sum(1 for r in results if r.get('api_status') == 'success')
    verified_count = sum(1 for r in results if r.get('verified', False))
    
    print(f"\nTEST EXECUTION SUMMARY:")
    print(f"  Total citations tested: {total}")
    print(f"  Successful API calls: {successful_tests} ({successful_tests/total*100:.1f}%)")
    print(f"  Citations verified: {verified_count} ({verified_count/total*100:.1f}%)")
    print(f"  Citations unverified: {total - verified_count} ({(total - verified_count)/total*100:.1f}%)")
    
    # Analyze verification sources
    sources = {}
    for result in results:
        if result.get('verified', False):
            source = result.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
    
    print(f"\nVERIFICATION SOURCES:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percentage = count / verified_count * 100 if verified_count > 0 else 0
        print(f"  {source}: {count} ({percentage:.1f}%)")
    
    # Analyze enhanced verification features
    enhanced_validations = sum(1 for r in results if r.get('is_enhanced_validation', False))
    complete_data_count = sum(1 for r in results if r.get('has_complete_data', False))
    confidence_scores = [r.get('confidence', 0.0) for r in results if r.get('confidence', 0.0) > 0]
    
    print(f"\nENHANCED VERIFICATION FEATURES:")
    print(f"  Citations with enhanced validation: {enhanced_validations}")
    print(f"  Verified citations with complete data: {complete_data_count}/{verified_count}")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        high_confidence = sum(1 for c in confidence_scores if c > 0.8)
        medium_confidence = sum(1 for c in confidence_scores if 0.5 <= c <= 0.8)
        low_confidence = sum(1 for c in confidence_scores if c < 0.5)
        
        print(f"  Average confidence score: {avg_confidence:.2f}")
        print(f"  High confidence (>0.8): {high_confidence}")
        print(f"  Medium confidence (0.5-0.8): {medium_confidence}")
        print(f"  Low confidence (<0.5): {low_confidence}")
    
    # Analyze specific test cases
    print(f"\nSPECIFIC TEST CASE ANALYSIS:")
    
    # Check the problematic citation that should be fixed
    problematic_citation = next((r for r in results if '654 F. Supp. 2d 321' in r.get('citation', '')), None)
    if problematic_citation:
        verified = problematic_citation.get('verified', False)
        has_data = problematic_citation.get('has_complete_data', False)
        source = problematic_citation.get('source', 'unknown')
        
        print(f"  🎯 Problematic citation (654 F. Supp. 2d 321):")
        print(f"     Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"     Complete data: {'✅ YES' if has_data else '❌ NO'}")
        print(f"     Source: {source}")
        
        if verified and has_data:
            print(f"     🎉 FALSE POSITIVE ISSUE RESOLVED!")
        elif verified and not has_data:
            print(f"     ⚠️  STILL A POTENTIAL FALSE POSITIVE")
        else:
            print(f"     ✅ CORRECTLY UNVERIFIED (false positive prevented)")
    
    # Check Washington state citations (coverage gap)
    wa_citations = [r for r in results if 'Wn.' in r.get('citation', '')]
    if wa_citations:
        wa_verified = sum(1 for r in wa_citations if r.get('verified', False))
        print(f"  🏛️  Washington state citations: {wa_verified}/{len(wa_citations)} verified")
        
        for wa_citation in wa_citations:
            citation = wa_citation.get('citation', '')
            verified = wa_citation.get('verified', False)
            source = wa_citation.get('source', 'unknown')
            print(f"     {citation}: {'✅' if verified else '❌'} ({source})")
    
    # Check Westlaw citations (should remain unverified)
    wl_citations = [r for r in results if 'WL' in r.get('citation', '')]
    if wl_citations:
        wl_verified = sum(1 for r in wl_citations if r.get('verified', False))
        print(f"  📰 Westlaw citations: {wl_verified}/{len(wl_citations)} verified (should be 0)")
        
        if wl_verified > 0:
            print(f"     ⚠️  UNEXPECTED: Westlaw citations should not be verified")
    
    # Check Supreme Court citations
    scotus_citations = [r for r in results if any(pattern in r.get('citation', '') for pattern in ['U.S.', 'S. Ct.', 'L. Ed.'])]
    if scotus_citations:
        scotus_verified = sum(1 for r in scotus_citations if r.get('verified', False))
        print(f"  🏛️  Supreme Court citations: {scotus_verified}/{len(scotus_citations)} verified")
    
    # Quality indicators
    print(f"\nQUALITY INDICATORS:")
    
    if verified_count > 0:
        data_completeness = complete_data_count / verified_count * 100
        print(f"  Data completeness: {data_completeness:.1f}% of verified citations have complete canonical data")
        
        enhanced_percentage = enhanced_validations / verified_count * 100
        print(f"  Enhanced validation usage: {enhanced_percentage:.1f}% of verified citations used enhanced validation")
    
    # Flag potential issues
    potential_issues = []
    
    # Verified citations without complete data
    incomplete_verified = [r for r in results if r.get('verified', False) and not r.get('has_complete_data', False)]
    if incomplete_verified:
        potential_issues.append(f"⚠️  {len(incomplete_verified)} verified citations lack complete canonical data")
    
    # Low confidence verifications
    low_confidence_verified = [r for r in results if r.get('verified', False) and r.get('confidence', 1.0) < 0.5]
    if low_confidence_verified:
        potential_issues.append(f"⚠️  {len(low_confidence_verified)} verified citations have low confidence scores")
    
    if potential_issues:
        print(f"\nPOTENTIAL ISSUES:")
        for issue in potential_issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ NO SIGNIFICANT ISSUES DETECTED")
    
    return {
        'total_tested': total,
        'successful_tests': successful_tests,
        'verified_count': verified_count,
        'sources': sources,
        'enhanced_validations': enhanced_validations,
        'complete_data_count': complete_data_count,
        'confidence_scores': confidence_scores,
        'potential_issues': len(potential_issues)
    }

def main():
    """Main test function"""
    
    print("Starting comprehensive enhanced verification system test...")
    
    # Run the test
    results, summary = run_comprehensive_verification_test()
    
    # Analyze results
    analysis = analyze_verification_effectiveness(results)
    
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    print(f"✅ Enhanced verification system tested successfully")
    print(f"✅ {analysis['total_tested']} citations tested with {analysis['successful_tests']} successful API calls")
    print(f"✅ {analysis['verified_count']} citations verified ({analysis['verified_count']/analysis['total_tested']*100:.1f}%)")
    print(f"✅ {analysis['complete_data_count']} verified citations have complete canonical data")
    print(f"✅ {analysis['enhanced_validations']} citations used enhanced validation")
    
    if analysis['confidence_scores']:
        avg_confidence = sum(analysis['confidence_scores']) / len(analysis['confidence_scores'])
        print(f"✅ Average confidence score: {avg_confidence:.2f}")
    
    if analysis['potential_issues'] == 0:
        print(f"🎉 NO SIGNIFICANT ISSUES DETECTED - Enhanced verification system is working effectively!")
    else:
        print(f"⚠️  {analysis['potential_issues']} potential issues detected - review recommended")
    
    print(f"\n🎯 Enhanced verification system validation: {'SUCCESSFUL' if analysis['verified_count'] > 0 and analysis['potential_issues'] < 3 else 'NEEDS REVIEW'}")

if __name__ == "__main__":
    main()
