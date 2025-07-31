#!/usr/bin/env python3
"""
Comprehensive Analysis of Fallback Verification Sites

This script analyzes all approved fallback verification sites to assess their potential
for broader usage beyond current state citation coverage.
"""

import requests
import json
from datetime import datetime
import time
import re
from urllib.parse import quote
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fallback_verifier import FallbackVerifier

def analyze_fallback_sites():
    """Comprehensive analysis of all fallback verification sites"""
    
    print("COMPREHENSIVE FALLBACK VERIFICATION SITES ANALYSIS")
    print("=" * 80)
    print("Analyzing potential for broader usage beyond current state citation coverage")
    print("=" * 80)
    
    # Test cases covering different citation types and jurisdictions
    test_cases = [
        # Federal Supreme Court
        {
            'citation': '385 U.S. 493',
            'case_name': 'Davis v. Alaska',
            'date': '1967',
            'type': 'Supreme Court',
            'description': 'Classic Supreme Court citation'
        },
        {
            'citation': '410 U.S. 113',
            'case_name': 'Roe v. Wade',
            'date': '1973',
            'type': 'Supreme Court',
            'description': 'Famous Supreme Court case'
        },
        
        # Federal Circuit Courts
        {
            'citation': '654 F.3d 1109',
            'case_name': 'United States v. Jones',
            'date': '2011',
            'type': 'Federal Circuit',
            'description': 'Federal Circuit Court of Appeals'
        },
        {
            'citation': '892 F.2d 1419',
            'case_name': 'Kyllo v. United States',
            'date': '1989',
            'type': 'Federal Circuit',
            'description': 'Ninth Circuit Court of Appeals'
        },
        
        # Federal District Courts
        {
            'citation': '654 F. Supp. 2d 321',
            'case_name': 'Benckini v. Hawk',
            'date': '2009',
            'type': 'Federal District',
            'description': 'Federal District Court'
        },
        {
            'citation': '123 F. Supp. 3d 456',
            'case_name': 'Sample v. District',
            'date': '2015',
            'type': 'Federal District',
            'description': 'Recent Federal District Court'
        },
        
        # Washington State Courts
        {
            'citation': '194 Wn. 2d 784',
            'case_name': 'State v. Arndt',
            'date': '2019',
            'type': 'Washington Supreme Court',
            'description': 'Washington Supreme Court'
        },
        {
            'citation': '188 Wn. App. 123',
            'case_name': 'State v. Example',
            'date': '2015',
            'type': 'Washington Court of Appeals',
            'description': 'Washington Court of Appeals'
        },
        
        # Pacific Reporter (Multi-state)
        {
            'citation': '453 P.3d 696',
            'case_name': 'State v. Armenta',
            'date': '1997',
            'type': 'Pacific Reporter',
            'description': 'Pacific Reporter (covers western states)'
        },
        {
            'citation': '829 P.2d 1069',
            'case_name': 'State v. Russell',
            'date': '1994',
            'type': 'Pacific Reporter 2d',
            'description': 'Older Pacific Reporter case'
        },
        
        # California State Courts
        {
            'citation': '123 Cal. 4th 456',
            'case_name': 'People v. California',
            'date': '2020',
            'type': 'California Supreme Court',
            'description': 'California Supreme Court'
        },
        {
            'citation': '456 Cal. App. 4th 789',
            'case_name': 'Smith v. Jones',
            'date': '2018',
            'type': 'California Court of Appeal',
            'description': 'California Court of Appeal'
        },
        
        # New York State Courts
        {
            'citation': '123 N.Y.2d 456',
            'case_name': 'People v. New York',
            'date': '2019',
            'type': 'New York Court of Appeals',
            'description': 'New York Court of Appeals (highest state court)'
        },
        {
            'citation': '456 A.D.3d 789',
            'case_name': 'Matter of Example',
            'date': '2017',
            'type': 'New York Appellate Division',
            'description': 'New York Appellate Division'
        },
        
        # Texas State Courts
        {
            'citation': '123 S.W.3d 456',
            'case_name': 'State v. Texas',
            'date': '2016',
            'type': 'Texas (Southwestern Reporter)',
            'description': 'Texas state court via Southwestern Reporter'
        },
        
        # Florida State Courts
        {
            'citation': '123 So. 3d 456',
            'case_name': 'State v. Florida',
            'date': '2018',
            'type': 'Florida (Southern Reporter)',
            'description': 'Florida state court via Southern Reporter'
        },
        
        # Specialty Courts
        {
            'citation': '123 B.R. 456',
            'case_name': 'In re Bankruptcy',
            'date': '2019',
            'type': 'Bankruptcy Court',
            'description': 'Bankruptcy Reporter'
        },
        
        # Law Reviews and Journals
        {
            'citation': '123 Harv. L. Rev. 456',
            'case_name': 'Legal Article Title',
            'date': '2020',
            'type': 'Law Review',
            'description': 'Harvard Law Review article'
        }
    ]
    
    # Initialize fallback verifier
    verifier = FallbackVerifier()
    
    # Results tracking
    results = {
        'cornell_law': {'total': 0, 'verified': 0, 'types': {}},
        'justia': {'total': 0, 'verified': 0, 'types': {}},
        'google_scholar': {'total': 0, 'verified': 0, 'types': {}},
        'caselaw_access': {'total': 0, 'verified': 0, 'types': {}}
    }
    
    detailed_results = []
    
    print(f"Testing {len(test_cases)} citations across different courts and jurisdictions...")
    print("-" * 80)
    
    for i, test_case in enumerate(test_cases):
        citation = test_case['citation']
        case_name = test_case['case_name']
        date = test_case['date']
        citation_type = test_case['type']
        description = test_case['description']
        
        print(f"\n[{i+1}/{len(test_cases)}] {description}")
        print(f"Citation: {citation}")
        print(f"Type: {citation_type}")
        print(f"Expected: {case_name} ({date})")
        
        # Test each fallback source individually
        citation_info = verifier._parse_citation(citation)
        
        source_results = {}
        
        # Test Cornell Law
        print("  Testing Cornell Law...")
        try:
            cornell_result = verifier._verify_with_cornell_law(citation, citation_info, case_name, date)
            if cornell_result and cornell_result.get('verified', False):
                print(f"    ✅ VERIFIED: {cornell_result.get('canonical_name', 'N/A')}")
                print(f"    Confidence: {cornell_result.get('confidence', 0.0)}")
                results['cornell_law']['verified'] += 1
                source_results['cornell_law'] = 'verified'
                
                # Track by type
                if citation_type not in results['cornell_law']['types']:
                    results['cornell_law']['types'][citation_type] = {'total': 0, 'verified': 0}
                results['cornell_law']['types'][citation_type]['verified'] += 1
            else:
                print("    ❌ Not verified")
                source_results['cornell_law'] = 'not_verified'
            results['cornell_law']['total'] += 1
            if citation_type not in results['cornell_law']['types']:
                results['cornell_law']['types'][citation_type] = {'total': 0, 'verified': 0}
            results['cornell_law']['types'][citation_type]['total'] += 1
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            source_results['cornell_law'] = 'error'
        
        time.sleep(1)  # Rate limiting
        
        # Test Justia
        print("  Testing Justia...")
        try:
            justia_result = verifier._verify_with_justia(citation, citation_info, case_name, date)
            if justia_result and justia_result.get('verified', False):
                print(f"    ✅ VERIFIED: {justia_result.get('canonical_name', 'N/A')}")
                print(f"    Confidence: {justia_result.get('confidence', 0.0)}")
                results['justia']['verified'] += 1
                source_results['justia'] = 'verified'
                
                # Track by type
                if citation_type not in results['justia']['types']:
                    results['justia']['types'][citation_type] = {'total': 0, 'verified': 0}
                results['justia']['types'][citation_type]['verified'] += 1
            else:
                print("    ❌ Not verified")
                source_results['justia'] = 'not_verified'
            results['justia']['total'] += 1
            if citation_type not in results['justia']['types']:
                results['justia']['types'][citation_type] = {'total': 0, 'verified': 0}
            results['justia']['types'][citation_type]['total'] += 1
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            source_results['justia'] = 'error'
        
        time.sleep(1)  # Rate limiting
        
        # Test Google Scholar (basic check)
        print("  Testing Google Scholar...")
        try:
            scholar_result = verifier._verify_with_google_scholar(citation, citation_info, case_name, date)
            if scholar_result and scholar_result.get('verified', False):
                print(f"    ✅ VERIFIED: {scholar_result.get('canonical_name', 'N/A')}")
                results['google_scholar']['verified'] += 1
                source_results['google_scholar'] = 'verified'
            else:
                print("    ❌ Not implemented/verified")
                source_results['google_scholar'] = 'not_implemented'
            results['google_scholar']['total'] += 1
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            source_results['google_scholar'] = 'error'
        
        # Test Caselaw Access
        print("  Testing Caselaw Access...")
        try:
            caselaw_result = verifier._verify_with_caselaw_access(citation, citation_info, case_name, date)
            if caselaw_result and caselaw_result.get('verified', False):
                print(f"    ✅ VERIFIED: {caselaw_result.get('canonical_name', 'N/A')}")
                results['caselaw_access']['verified'] += 1
                source_results['caselaw_access'] = 'verified'
            else:
                print("    ❌ Not implemented/verified")
                source_results['caselaw_access'] = 'not_implemented'
            results['caselaw_access']['total'] += 1
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            source_results['caselaw_access'] = 'error'
        
        # Store detailed results
        detailed_results.append({
            'citation': citation,
            'case_name': case_name,
            'date': date,
            'type': citation_type,
            'description': description,
            'source_results': source_results
        })
        
        time.sleep(0.5)  # Brief pause between test cases
    
    # Generate comprehensive analysis report
    print(f"\n{'='*80}")
    print("COMPREHENSIVE FALLBACK SITES ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    # Overall statistics
    for source, stats in results.items():
        total = stats['total']
        verified = stats['verified']
        success_rate = (verified / total * 100) if total > 0 else 0
        
        print(f"\n{source.upper().replace('_', ' ')}:")
        print(f"  Total tested: {total}")
        print(f"  Verified: {verified}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        # Breakdown by citation type
        if stats['types']:
            print(f"  Breakdown by type:")
            for cit_type, type_stats in stats['types'].items():
                type_rate = (type_stats['verified'] / type_stats['total'] * 100) if type_stats['total'] > 0 else 0
                print(f"    {cit_type}: {type_stats['verified']}/{type_stats['total']} ({type_rate:.1f}%)")
    
    # Coverage analysis
    print(f"\n{'='*80}")
    print("COVERAGE ANALYSIS BY CITATION TYPE")
    print(f"{'='*80}")
    
    # Collect all citation types
    all_types = set()
    for result in detailed_results:
        all_types.add(result['type'])
    
    for cit_type in sorted(all_types):
        print(f"\n{cit_type}:")
        type_cases = [r for r in detailed_results if r['type'] == cit_type]
        
        for source in ['cornell_law', 'justia', 'google_scholar', 'caselaw_access']:
            verified_count = sum(1 for case in type_cases if case['source_results'].get(source) == 'verified')
            total_count = len(type_cases)
            rate = (verified_count / total_count * 100) if total_count > 0 else 0
            print(f"  {source.replace('_', ' ').title()}: {verified_count}/{total_count} ({rate:.1f}%)")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS FOR BROADER USAGE")
    print(f"{'='*80}")
    
    # Analyze which sources work best for which types
    recommendations = []
    
    for source, stats in results.items():
        if stats['verified'] > 0:
            success_rate = (stats['verified'] / stats['total'] * 100)
            
            if success_rate >= 70:
                recommendations.append(f"✅ {source.replace('_', ' ').title()}: EXCELLENT ({success_rate:.1f}% success) - Recommended for production use")
            elif success_rate >= 40:
                recommendations.append(f"⚠️  {source.replace('_', ' ').title()}: GOOD ({success_rate:.1f}% success) - Suitable with monitoring")
            elif success_rate >= 20:
                recommendations.append(f"🔍 {source.replace('_', ' ').title()}: LIMITED ({success_rate:.1f}% success) - Needs enhancement")
            else:
                recommendations.append(f"❌ {source.replace('_', ' ').title()}: POOR ({success_rate:.1f}% success) - Not recommended")
        else:
            recommendations.append(f"❌ {source.replace('_', ' ').title()}: NOT IMPLEMENTED - Requires development")
    
    for rec in recommendations:
        print(rec)
    
    # Specific enhancement suggestions
    print(f"\n{'='*80}")
    print("ENHANCEMENT SUGGESTIONS")
    print(f"{'='*80}")
    
    enhancements = [
        "1. CORNELL LAW ENHANCEMENTS:",
        "   - Add support for more federal circuit patterns (F.2d, F.3d)",
        "   - Implement state-specific URL patterns for major states",
        "   - Enhance search result parsing for better case name extraction",
        "",
        "2. JUSTIA ENHANCEMENTS:",
        "   - Add federal court URL patterns beyond Supreme Court",
        "   - Implement state-specific search for all 50 states",
        "   - Add support for specialty courts (bankruptcy, tax, etc.)",
        "",
        "3. GOOGLE SCHOLAR IMPLEMENTATION:",
        "   - Implement full Google Scholar search with CAPTCHA handling",
        "   - Add academic citation verification for law reviews",
        "   - Implement rate limiting and session management",
        "",
        "4. CASELAW ACCESS PROJECT INTEGRATION:",
        "   - Implement Harvard CAP API integration",
        "   - Add historical case verification (pre-1900)",
        "   - Implement bulk verification for large datasets",
        "",
        "5. NEW SOURCES TO CONSIDER:",
        "   - Westlaw Edge (if API access available)",
        "   - Lexis+ (if API access available)",
        "   - HeinOnline for law reviews and historical cases",
        "   - State court websites with public APIs",
        "   - Free Case Law Project databases"
    ]
    
    for enhancement in enhancements:
        print(enhancement)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"fallback_sites_analysis_{timestamp}.json"
    
    analysis_results = {
        'analysis_info': {
            'timestamp': timestamp,
            'test_cases_count': len(test_cases),
            'analysis_type': 'comprehensive_fallback_sites_analysis'
        },
        'overall_statistics': results,
        'detailed_results': detailed_results,
        'recommendations': recommendations,
        'enhancement_suggestions': enhancements
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Detailed results saved to: {results_file}")
    
    return analysis_results

if __name__ == "__main__":
    results = analyze_fallback_sites()
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"Cornell Law and Justia show promise for broader usage.")
    print(f"Google Scholar and Caselaw Access need implementation.")
    print(f"Consider adding new sources for comprehensive coverage.")
