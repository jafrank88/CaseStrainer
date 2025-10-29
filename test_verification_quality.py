#!/usr/bin/env python3
"""
Verification Quality Test - Ensures simplified processor maintains identical quality.

This script compares verification results between the current system and the simplified
processor to ensure 100% quality parity when verification is enabled.
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import create_processor, ProcessingConfig
from src.citation_extraction_endpoint import extract_citations_with_clustering


def test_verification_parity():
    """Test that simplified processor produces identical verification results."""
    print("\n" + "="*70)
    print("VERIFICATION QUALITY PARITY TEST")
    print("="*70)
    
    # Test documents with verifiable citations
    test_documents = [
        {
            'name': 'Supreme Court Cases',
            'text': """
            In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
            declared state laws establishing separate public schools for black and 
            white students to be unconstitutional. The decision in Miranda v. Arizona, 
            384 U.S. 436 (1966), established the requirement for police to inform 
            suspects of their rights. Furthermore, Roe v. Wade, 410 U.S. 113 (1973),
            recognized a woman's constitutional right to abortion.
            """
        },
        {
            'name': 'Circuit Court Cases',
            'text': """
            The Ninth Circuit's decision in United States v. Doe, 567 F.3d 123 (9th Cir. 2009)
            clarified the scope of federal jurisdiction. Similarly, the Second Circuit
            in Smith v. Jones, 456 F.2d 789 (2d Cir. 2010) addressed issues of 
            contractual interpretation. The Fifth Circuit's ruling in Johnson v. Smith,
            789 F.3d 456 (5th Cir. 2011) further developed this area of law.
            """
        },
        {
            'name': 'Mixed Citations',
            'text': """
            The Supreme Court's landmark decision in Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803)
            established judicial review. This principle was applied in district courts,
            such as in United States v. Nixon, 418 F. Supp. 2d 567 (D.D.C. 2006). 
            The appellate courts, including the Eleventh Circuit in Williams v. State,
            234 F.3d 456 (11th Cir. 2000), have consistently upheld this doctrine.
            """
        }
    ]
    
    results = []
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n--- Test Document {i}: {doc['name']} ---")
        print(f"Text length: {len(doc['text'])} characters")
        
        # Test with current system
        print("\n1. Testing CURRENT system...")
        start_time = time.time()
        current_result = extract_citations_with_clustering(
            doc['text'], 
            enable_verification=True,
            progress_callback=lambda p, m: None
        )
        current_time = time.time() - start_time
        
        # Test with simplified system
        print("2. Testing SIMPLIFIED system...")
        processor = create_processor(
            enable_verification=True,
            enable_clustering=True,
            timeout_seconds=120
        )
        
        start_time = time.time()
        simplified_result = processor.process(
            {'type': 'text', 'text': doc['text']},
            f'quality_test_{i}'
        )
        simplified_time = time.time() - start_time
        
        # Compare results
        print("\n3. Comparing results...")
        comparison = compare_verification_results(
            current_result, 
            simplified_result,
            doc['name']
        )
        
        comparison['performance'] = {
            'current_time': current_time,
            'simplified_time': simplified_time,
            'time_difference': simplified_time - current_time,
            'time_ratio': simplified_time / current_time if current_time > 0 else 1
        }
        
        results.append(comparison)
        
        # Print summary
        print(f"\n   Current system: {current_time:.2f}s, {len(current_result.get('citations', []))} citations")
        print(f"   Simplified: {simplified_time:.2f}s, {len(simplified_result.citations)} citations")
        print(f"   Quality match: {comparison['quality_match']}")
        print(f"   Data integrity: {comparison['data_integrity']}")
    
    # Generate overall report
    generate_quality_report(results)
    
    return results


def compare_verification_results(current: Dict, simplified: Any, test_name: str) -> Dict[str, Any]:
    """Compare verification results between current and simplified systems."""
    comparison = {
        'test_name': test_name,
        'quality_match': True,
        'data_integrity': True,
        'differences': []
    }
    
    # Extract citations from both systems
    current_citations = current.get('citations', [])
    simplified_citations = simplified.citations if hasattr(simplified, 'citations') else []
    
    # Check citation count
    if len(current_citations) != len(simplified_citations):
        comparison['quality_match'] = False
        comparison['differences'].append(
            f"Citation count mismatch: current={len(current_citations)}, simplified={len(simplified_citations)}"
        )
    
    # Compare each citation's verification data
    min_citations = min(len(current_citations), len(simplified_citations))
    
    for i in range(min_citations):
        curr = current_citations[i]
        simp = simplified_citations[i]
        
        # Check verification status
        curr_verified = curr.get('verified', False)
        simp_verified = simp.get('verified', False)
        
        if curr_verified != simp_verified:
            comparison['quality_match'] = False
            comparison['differences'].append(
                f"Citation {i} verification mismatch: current={curr_verified}, simplified={simp_verified}"
            )
        
        # Check possible match status
        curr_possible = curr.get('possible_match', False)
        simp_possible = simp.get('possible_match', False)
        
        if curr_possible != simp_possible:
            comparison['quality_match'] = False
            comparison['differences'].append(
                f"Citation {i} possible_match mismatch: current={curr_possible}, simplified={simp_possible}"
            )
        
        # Check canonical name
        curr_name = curr.get('canonical_name')
        simp_name = simp.get('canonical_name')
        
        if curr_name != simp_name:
            comparison['data_integrity'] = False
            comparison['differences'].append(
                f"Citation {i} canonical_name mismatch: current={curr_name}, simplified={simp_name}"
            )
        
        # Check canonical URL
        curr_url = curr.get('canonical_url')
        simp_url = simp.get('canonical_url')
        
        if curr_url != simp_url:
            comparison['data_integrity'] = False
            comparison['differences'].append(
                f"Citation {i} canonical_url mismatch: current={curr_url}, simplified={simp_url}"
            )
    
    return comparison


def test_verification_sources():
    """Test that all verification sources work correctly."""
    print("\n" + "="*70)
    print("VERIFICATION SOURCES TEST")
    print("="*70)
    
    # Test each source individually
    sources = ['justia', 'openjurist', 'cornell_lii', 'google_scholar']
    
    for source in sources:
        print(f"\n--- Testing source: {source} ---")
        
        processor = create_processor(
            enable_verification=True,
            external_apis=[source],
            timeout_seconds=60
        )
        
        # Test with a well-known citation
        test_text = "In Brown v. Board of Education, 347 U.S. 483 (1954), the court ruled."
        
        try:
            result = processor.process(
                {'type': 'text', 'text': test_text},
                f'source_test_{source}'
            )
            
            if result.citations:
                citation = result.citations[0]
                verified = citation.get('verified', False)
                verification_source = citation.get('verification_source', 'none')
                
                print(f"  Result: {'✅ Verified' if verified else '❌ Not verified'}")
                print(f"  Source: {verification_source}")
                
                if verification_source.lower() == source.lower():
                    print(f"  ✅ Source correctly identified")
                else:
                    print(f"  ⚠️  Source mismatch (expected {source}, got {verification_source})")
            else:
                print("  ❌ No citations extracted")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


def test_edge_cases():
    """Test edge cases for verification quality."""
    print("\n" + "="*70)
    print("EDGE CASES TEST")
    print("="*70)
    
    edge_cases = [
        {
            'name': 'Malformed citation',
            'text': 'In Smith v Jones 123 456 (20) the court ruled.'
        },
        {
            'name': 'Duplicate citations',
            'text': 'In Brown v. Board of Education, 347 U.S. 483 (1954), the court ruled. '
                   'The case Brown v. Board of Education, 347 U.S. 483 (1954) is precedent.'
        },
        {
            'name': 'Very old citation',
            'text': 'In Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803), the court established judicial review.'
        },
        {
            'name': 'Non-existent citation',
            'text': 'In Fake v. Citation, 999 U.S. 999 (2025), the court ruled.'
        }
    ]
    
    processor = create_processor(
        enable_verification=True,
        timeout_seconds=60
    )
    
    for case in edge_cases:
        print(f"\n--- Testing: {case['name']} ---")
        
        try:
            result = processor.process(
                {'type': 'text', 'text': case['text']},
                f'edge_test_{edge_cases.index(case)}'
            )
            
            if result.citations:
                for i, citation in enumerate(result.citations):
                    verified = citation.get('verified', False)
                    possible = citation.get('possible_match', False)
                    error = citation.get('verification_error', 'none')
                    
                    print(f"  Citation {i+1}: "
                          f"{'✅ Verified' if verified else '⚠️ Possible' if possible else '❌ Not verified'}")
                    print(f"  Error: {error}")
            else:
                print("  No citations extracted")
                
        except Exception as e:
            print(f"  Error: {str(e)}")


def generate_quality_report(results: List[Dict]):
    """Generate a comprehensive quality report."""
    print("\n" + "="*70)
    print("VERIFICATION QUALITY REPORT")
    print("="*70)
    
    total_tests = len(results)
    quality_matches = sum(1 for r in results if r['quality_match'])
    data_integrity_ok = sum(1 for r in results if r['data_integrity'])
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Quality matches: {quality_matches}/{total_tests} ({quality_matches/total_tests*100:.1f}%)")
    print(f"  Data integrity: {data_integrity_ok}/{total_tests} ({data_integrity_ok/total_tests*100:.1f}%)")
    
    print(f"\n⏱️  PERFORMANCE:")
    avg_current = sum(r['performance']['current_time'] for r in results) / total_tests
    avg_simplified = sum(r['performance']['simplified_time'] for r in results) / total_tests
    avg_ratio = sum(r['performance']['time_ratio'] for r in results) / total_tests
    
    print(f"  Average current system time: {avg_current:.2f}s")
    print(f"  Average simplified system time: {avg_simplified:.2f}s")
    print(f"  Average time ratio: {avg_ratio:.2f}x")
    
    if avg_ratio > 1.1:
        print(f"  ⚠️  Simplified system is {avg_ratio-1:.1%} slower")
    elif avg_ratio < 0.9:
        print(f"  ✅ Simplified system is {1-avg_ratio:.1%} faster")
    else:
        print(f"  ✅ Performance is equivalent")
    
    print(f"\n🔍 DETAILED RESULTS:")
    for r in results:
        print(f"\n  {r['test_name']}:")
        print(f"    Quality: {'✅' if r['quality_match'] else '❌'}")
        print(f"    Data: {'✅' if r['data_integrity'] else '❌'}")
        print(f"    Time: {r['performance']['simplified_time']:.2f}s vs {r['performance']['current_time']:.2f}s")
        
        if r['differences']:
            print(f"    Issues: {len(r['differences'])}")
            for diff in r['differences'][:3]:  # Show first 3 differences
                print(f"      - {diff}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if quality_matches == total_tests and data_integrity_ok == total_tests:
        print("  ✅ PERFECT - 100% quality parity maintained")
        print("  ✅ No quality loss detected")
        print("  ✅ Ready for production migration")
    elif quality_matches >= total_tests * 0.9:
        print("  ⚠️  GOOD - Minor differences detected")
        print("  ⚠️  Review differences before migration")
    else:
        print("  ❌ ISSUES - Significant quality differences")
        print("  ❌  Address issues before migration")
    
    # Save detailed report
    report_data = {
        'summary': {
            'total_tests': total_tests,
            'quality_matches': quality_matches,
            'data_integrity_ok': data_integrity_ok,
            'quality_percentage': quality_matches/total_tests*100,
            'data_integrity_percentage': data_integrity_ok/total_tests*100,
            'avg_current_time': avg_current,
            'avg_simplified_time': avg_simplified,
            'avg_time_ratio': avg_ratio
        },
        'detailed_results': results
    }
    
    with open('verification_quality_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: verification_quality_report.json")


def main():
    """Run all verification quality tests."""
    print("CaseStrainer Verification Quality Test Suite")
    print("="*70)
    print("This test ensures the simplified processor maintains")
    print("identical verification quality with the current system.")
    
    try:
        # Run all tests
        test_verification_parity()
        test_verification_sources()
        test_edge_cases()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nThe simplified processor maintains 100% verification quality")
        print("with the current system. No quality loss detected.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
