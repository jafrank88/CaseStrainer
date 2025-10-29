#!/usr/bin/env python3
"""
Test Document Processing - Complete End-to-End Verification

This script tests the optimized processor with real documents to ensure:
1. Case names and years are correctly extracted from user-submitted text
2. Clustering is accurate compared to manual review of the original document
3. Verification quality matches expected standards
4. Performance improvements are realized
"""

import sys
import os
import time
import json
from typing import Dict, Any, List, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import create_processor, ProcessingConfig
from src.citation_extraction_endpoint import extract_citations_with_clustering


def analyze_expected_citations(text: str) -> List[Dict[str, Any]]:
    """
    Manually analyze the document to identify expected citations.
    This simulates what a human would find when reviewing the document.
    """
    import re
    
    expected = []
    
    # Supreme Court landmark cases
    sc_cases = [
        {
            'citation': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
            'case_name': 'Brown v. Board of Education',
            'year': '1954',
            'type': 'Supreme Court',
            'should_cluster': False  # Unique case
        },
        {
            'citation': 'Plessy v. Ferguson, 163 U.S. 537 (1896)',
            'case_name': 'Plessy v. Ferguson',
            'year': '1896',
            'type': 'Supreme Court',
            'should_cluster': False  # Different case
        },
        {
            'citation': 'Miranda v. Arizona, 384 U.S. 436 (1966)',
            'case_name': 'Miranda v. Arizona',
            'year': '1966',
            'type': 'Supreme Court',
            'should_cluster': False  # Unique case
        },
        {
            'citation': 'Roe v. Wade, 410 U.S. 113 (1973)',
            'case_name': 'Roe v. Wade',
            'year': '1973',
            'type': 'Supreme Court',
            'should_cluster': False  # Unique case
        },
        {
            'citation': 'Planned Parenthood v. Casey, 505 U.S. 833 (1992)',
            'case_name': 'Planned Parenthood v. Casey',
            'year': '1992',
            'type': 'Supreme Court',
            'should_cluster': False  # Unique case
        }
    ]
    
    # Look for these patterns in the text
    for case in sc_cases:
        if case['citation'] in text or case['case_name'] in text:
            expected.append(case)
    
    return expected


def extract_manual_review_data(text: str) -> Dict[str, Any]:
    """
    Simulate manual review of the document to establish ground truth.
    """
    return {
        'expected_citations': analyze_expected_citations(text),
        'document_type': 'Legal Analysis',
        'expected_clusters': 5,  # Each Supreme Court case should be separate
        'key_entities': ['Supreme Court', 'civil rights', 'constitutional law'],
        'time_period': '1896-1992',
        'jurisdiction': 'United States Supreme Court'
    }


def test_document_processing():
    """Test complete document processing with extraction and clustering."""
    print("\n" + "="*80)
    print("COMPLETE DOCUMENT PROCESSING TEST")
    print("="*80)
    
    # Test document with complex legal citations
    test_document = """
    CONSTITUTIONAL LAW ANALYSIS: CIVIL RIGHTS EVOLUTION
    
    The foundation of modern civil rights jurisprudence was established in the landmark 
    decision of Brown v. Board of Education, 347 U.S. 483 (1954), where the United States 
    Supreme Court unanimously held that state laws establishing separate public schools 
    for black and white students were unconstitutional. This decision effectively overturned 
    the "separate but equal" doctrine established in Plessy v. Ferguson, 163 U.S. 537 (1896), 
    which had permitted racial segregation under the Fourteenth Amendment.
    
    The Court further developed procedural rights in Miranda v. Arizona, 384 U.S. 436 (1966), 
    establishing the requirement for law enforcement to inform suspects of their constitutional 
    rights, including the right to remain silent and the right to an attorney. This decision 
    fundamentally changed police procedures across the United States.
    
    In the realm of reproductive rights, Roe v. Wade, 410 U.S. 113 (1973), recognized a woman's 
    constitutional right to privacy in obtaining an abortion during the first trimester. 
    This precedent was later modified but not entirely overturned in Planned Parenthood v. 
    Casey, 505 U.S. 833 (1992), which introduced the "undue burden" standard for 
    restrictions on abortion access.
    
    These cases collectively demonstrate the evolution of constitutional interpretation 
    and the Court's role in expanding civil liberties and individual rights under the 
    United States Constitution.
    """
    
    print(f"\n📄 DOCUMENT ANALYSIS:")
    print(f"   Length: {len(test_document)} characters")
    print(f"   Type: Constitutional Law Analysis")
    print(f"   Time Period: 1896-1992")
    
    # Establish ground truth through manual review
    print(f"\n🔍 MANUAL REVIEW (Ground Truth):")
    ground_truth = extract_manual_review_data(test_document)
    expected_citations = ground_truth['expected_citations']
    
    print(f"   Expected citations: {len(expected_citations)}")
    for i, cit in enumerate(expected_citations, 1):
        print(f"   {i}. {cit['case_name']} ({cit['year']}) - {cit['type']}")
    
    print(f"   Expected clusters: {ground_truth['expected_clusters']}")
    print(f"   Jurisdiction: {ground_truth['jurisdiction']}")
    
    # Test with optimized processor
    print(f"\n🚀 TESTING OPTIMIZED PROCESSOR:")
    start_time = time.time()
    
    processor = create_processor(
        enable_verification=True,
        enable_clustering=True,
        timeout_seconds=120
    )
    
    result = processor.process(
        {'type': 'text', 'text': test_document},
        'document_test'
    )
    
    optimized_time = time.time() - start_time
    
    # Test with legacy system for comparison
    print(f"\n🔄 TESTING LEGACY SYSTEM:")
    start_time = time.time()
    
    legacy_result = extract_citations_with_clustering(
        test_document,
        enable_verification=True
    )
    
    legacy_time = time.time() - start_time
    
    # Analyze extraction accuracy
    print(f"\n📊 EXTRACTION ANALYSIS:")
    extraction_analysis = analyze_extraction_accuracy(
        expected_citations, 
        result.citations, 
        "Optimized"
    )
    
    legacy_extraction_analysis = analyze_extraction_accuracy(
        expected_citations,
        legacy_result.get('citations', []),
        "Legacy"
    )
    
    # Analyze clustering accuracy
    print(f"\n🔗 CLUSTERING ANALYSIS:")
    clustering_analysis = analyze_clustering_accuracy(
        expected_citations,
        result.citations,
        result.clusters,
        "Optimized"
    )
    
    legacy_clustering_analysis = analyze_clustering_accuracy(
        expected_citations,
        legacy_result.get('citations', []),
        legacy_result.get('clusters', []),
        "Legacy"
    )
    
    # Analyze verification quality
    print(f"\n✅ VERIFICATION ANALYSIS:")
    verification_analysis = analyze_verification_quality(
        result.citations,
        result.verification_results,
        "Optimized"
    )
    
    legacy_verification_analysis = analyze_verification_quality(
        legacy_result.get('citations', []),
        legacy_result.get('verification_results', {}),
        "Legacy"
    )
    
    # Performance comparison
    print(f"\n⚡ PERFORMANCE COMPARISON:")
    print(f"   Optimized processor: {optimized_time:.2f}s")
    print(f"   Legacy system: {legacy_time:.2f}s")
    if legacy_time > 0:
        improvement = (legacy_time - optimized_time) / legacy_time * 100
        print(f"   Performance improvement: {improvement:.1f}%")
    
    # Generate comprehensive report
    generate_comprehensive_report(
        ground_truth,
        extraction_analysis,
        clustering_analysis,
        verification_analysis,
        legacy_extraction_analysis,
        legacy_clustering_analysis,
        legacy_verification_analysis,
        optimized_time,
        legacy_time
    )
    
    return True


def analyze_extraction_accuracy(expected: List[Dict], actual: List[Dict], system_name: str) -> Dict[str, Any]:
    """Analyze how accurately citations were extracted."""
    
    actual_citations = [c.get('citation', '') for c in actual]
    actual_case_names = [c.get('extracted_case_name', '') for c in actual]
    actual_years = [c.get('extracted_date', '') for c in actual]
    
    # Check extraction completeness
    found_citations = []
    missing_citations = []
    
    for expected_cit in expected:
        expected_citation = expected_cit['citation']
        expected_case_name = expected_cit['case_name']
        expected_year = expected_cit['year']
        
        found = False
        for i, actual_cit in enumerate(actual_citations):
            # Check for citation match
            if (expected_citation.lower() in actual_cit.lower() or 
                actual_cit.lower() in expected_citation.lower()):
                
                # Check case name extraction
                case_name_extracted = actual_case_names[i] and expected_case_name.lower() in actual_case_names[i].lower()
                
                # Check year extraction
                year_extracted = actual_years[i] and expected_year in actual_years[i]
                
                found_citations.append({
                    'expected': expected_cit,
                    'actual': actual_cit,
                    'case_name_extracted': case_name_extracted,
                    'year_extracted': year_extracted
                })
                found = True
                break
        
        if not found:
            missing_citations.append(expected_cit)
    
    # Calculate metrics
    total_expected = len(expected)
    total_found = len(found_citations)
    completeness = total_found / total_expected if total_expected > 0 else 0
    
    case_name_accuracy = sum(1 for f in found_citations if f['case_name_extracted']) / total_found if total_found > 0 else 0
    year_accuracy = sum(1 for f in found_citations if f['year_extracted']) / total_found if total_found > 0 else 0
    
    print(f"   {system_name} Extraction:")
    print(f"     Total expected: {total_expected}")
    print(f"     Successfully extracted: {total_found}")
    print(f"     Completeness: {completeness:.1%}")
    print(f"     Case name accuracy: {case_name_accuracy:.1%}")
    print(f"     Year accuracy: {year_accuracy:.1%}")
    
    if missing_citations:
        print(f"     Missing citations: {len(missing_citations)}")
        for missing in missing_citations[:2]:  # Show first 2
            print(f"       - {missing['citation']}")
    
    return {
        'system': system_name,
        'total_expected': total_expected,
        'total_found': total_found,
        'completeness': completeness,
        'case_name_accuracy': case_name_accuracy,
        'year_accuracy': year_accuracy,
        'missing_citations': missing_citations,
        'found_citations': found_citations
    }


def analyze_clustering_accuracy(expected: List[Dict], actual_citations: List[Dict], 
                               actual_clusters: List[Dict], system_name: str) -> Dict[str, Any]:
    """Analyze clustering accuracy."""
    
    # Count actual clusters
    total_clusters = len(actual_clusters)
    expected_clusters = len(expected)  # Each case should be separate
    
    # Check if citations are properly grouped
    cluster_analysis = []
    for i, cluster in enumerate(actual_clusters):
        cluster_citations = cluster.get('citations', [])
        cluster_size = len(cluster_citations)
        cluster_case_names = [c.get('extracted_case_name', '') for c in cluster_citations]
        
        # Check if this cluster represents a single case (should be true for our test)
        unique_case_names = set([name.strip().lower() for name in cluster_case_names if name.strip()])
        is_single_case = len(unique_case_names) <= 1
        
        cluster_analysis.append({
            'cluster_id': i,
            'size': cluster_size,
            'is_single_case': is_single_case,
            'case_names': cluster_case_names
        })
    
    # Calculate clustering quality
    single_case_clusters = sum(1 for c in cluster_analysis if c['is_single_case'])
    clustering_quality = single_case_clusters / total_clusters if total_clusters > 0 else 0
    
    print(f"   {system_name} Clustering:")
    print(f"     Total clusters: {total_clusters}")
    print(f"     Expected clusters: {expected_clusters}")
    print(f"     Single-case clusters: {single_case_clusters}")
    print(f"     Clustering quality: {clustering_quality:.1%}")
    
    # Show cluster details
    for cluster in cluster_analysis[:3]:  # Show first 3
        print(f"     Cluster {cluster['cluster_id']}: {cluster['size']} citations, "
              f"{'✅ single case' if cluster['is_single_case'] else '⚠️ multiple cases'}")
    
    return {
        'system': system_name,
        'total_clusters': total_clusters,
        'expected_clusters': expected_clusters,
        'clustering_quality': clustering_quality,
        'cluster_analysis': cluster_analysis
    }


def analyze_verification_quality(citations: List[Dict], verification_results: Dict, 
                                 system_name: str) -> Dict[str, Any]:
    """Analyze verification quality."""
    
    if not citations:
        return {
            'system': system_name,
            'total_citations': 0,
            'verified_count': 0,
            'verification_rate': 0,
            'sources_used': []
        }
    
    total_citations = len(citations)
    verified_count = sum(1 for c in citations if c.get('verified', False))
    possible_matches = sum(1 for c in citations if c.get('possible_match', False))
    sources_used = list(set([c.get('verification_source', 'unknown') for c in citations if c.get('verification_source')]))
    
    verification_rate = (verified_count + possible_matches) / total_citations
    
    print(f"   {system_name} Verification:")
    print(f"     Total citations: {total_citations}")
    print(f"     Verified: {verified_count}")
    print(f"     Possible matches: {possible_matches}")
    print(f"     Verification rate: {verification_rate:.1%}")
    print(f"     Sources used: {sources_used}")
    
    return {
        'system': system_name,
        'total_citations': total_citations,
        'verified_count': verified_count,
        'possible_matches': possible_matches,
        'verification_rate': verification_rate,
        'sources_used': sources_used
    }


def generate_comprehensive_report(ground_truth: Dict, opt_extraction: Dict, 
                                 opt_clustering: Dict, opt_verification: Dict,
                                 leg_extraction: Dict, leg_clustering: Dict, 
                                 leg_verification: Dict, opt_time: float, 
                                 leg_time: float):
    """Generate a comprehensive report of all findings."""
    
    print(f"\n" + "="*80)
    print("COMPREHENSIVE PROCESSING REPORT")
    print("="*80)
    
    # Extraction comparison
    print(f"\n📋 EXTRACTION COMPARISON:")
    print(f"                    | Optimized | Legacy | Improvement")
    print(f"                    |-----------|--------|------------")
    print(f"   Completeness     | {opt_extraction['completeness']:.1%}      | {leg_extraction['completeness']:.1%}    | {(opt_extraction['completeness'] - leg_extraction['completeness'])*100:+.1f}%")
    print(f"   Case Name Acc.   | {opt_extraction['case_name_accuracy']:.1%}      | {leg_extraction['case_name_accuracy']:.1%}    | {(opt_extraction['case_name_accuracy'] - leg_extraction['case_name_accuracy'])*100:+.1f}%")
    print(f"   Year Accuracy     | {opt_extraction['year_accuracy']:.1%}      | {leg_extraction['year_accuracy']:.1%}    | {(opt_extraction['year_accuracy'] - leg_extraction['year_accuracy'])*100:+.1f}%")
    
    # Clustering comparison
    print(f"\n🔗 CLUSTERING COMPARISON:")
    print(f"                    | Optimized | Legacy | Status")
    print(f"                    |-----------|--------|--------")
    print(f"   Total Clusters   | {opt_clustering['total_clusters']:9d} | {leg_clustering['total_clusters']:6d} | {'✅' if opt_clustering['total_clusters'] == leg_clustering['total_clusters'] else '⚠️'}")
    print(f"   Clustering Quality| {opt_clustering['clustering_quality']:.1%}      | {leg_clustering['clustering_quality']:.1%}    | {'✅' if opt_clustering['clustering_quality'] >= leg_clustering['clustering_quality'] else '⚠️'}")
    
    # Verification comparison
    print(f"\n✅ VERIFICATION COMPARISON:")
    print(f"                    | Optimized | Legacy | Status")
    print(f"                    |-----------|--------|--------")
    print(f"   Verification Rate| {opt_verification['verification_rate']:.1%}      | {leg_verification['verification_rate']:.1%}    | {'✅' if opt_verification['verification_rate'] >= leg_verification['verification_rate'] else '⚠️'}")
    print(f"   Sources Used      | {len(opt_verification['sources_used']):9d} | {len(leg_verification['sources_used']):6d} | {'✅' if len(opt_verification['sources_used']) > 0 else '❌'}")
    
    # Performance comparison
    print(f"\n⚡ PERFORMANCE COMPARISON:")
    print(f"   Optimized Time: {opt_time:.2f}s")
    print(f"   Legacy Time: {leg_time:.2f}s")
    if leg_time > 0:
        improvement = (leg_time - opt_time) / leg_time * 100
        print(f"   Performance Improvement: {improvement:.1f}%")
        print(f"   Status: {'🚀 Excellent' if improvement > 20 else '✅ Good' if improvement > 0 else '⚠️ No improvement'}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    # Quality scores
    extraction_quality = (opt_extraction['completeness'] + opt_extraction['case_name_accuracy'] + opt_extraction['year_accuracy']) / 3
    clustering_quality = opt_clustering['clustering_quality']
    verification_quality = opt_verification['verification_rate']
    
    overall_quality = (extraction_quality + clustering_quality + verification_quality) / 3
    
    print(f"   Extraction Quality: {extraction_quality:.1%} {'✅' if extraction_quality >= 0.9 else '⚠️' if extraction_quality >= 0.8 else '❌'}")
    print(f"   Clustering Quality: {clustering_quality:.1%} {'✅' if clustering_quality >= 0.9 else '⚠️' if clustering_quality >= 0.8 else '❌'}")
    print(f"   Verification Quality: {verification_quality:.1%} {'✅' if verification_quality >= 0.8 else '⚠️' if verification_quality >= 0.6 else '❌'}")
    print(f"   Overall Quality: {overall_quality:.1%} {'🎉' if overall_quality >= 0.9 else '✅' if overall_quality >= 0.8 else '⚠️' if overall_quality >= 0.7 else '❌'}")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    if overall_quality >= 0.9:
        print("   ✅ READY FOR PRODUCTION - Excellent quality and performance")
    elif overall_quality >= 0.8:
        print("   ✅ READY FOR PRODUCTION - Good quality with minor improvements possible")
    elif overall_quality >= 0.7:
        print("   ⚠️  READY FOR BETA - Consider improvements before full production")
    else:
        print("   ❌ NOT READY - Significant improvements needed")
    
    # Save detailed report
    report_data = {
        'ground_truth': ground_truth,
        'optimized_results': {
            'extraction': opt_extraction,
            'clustering': opt_clustering,
            'verification': opt_verification,
            'processing_time': opt_time
        },
        'legacy_results': {
            'extraction': leg_extraction,
            'clustering': leg_clustering,
            'verification': leg_verification,
            'processing_time': leg_time
        },
        'overall_quality': overall_quality,
        'recommendations': 'READY FOR PRODUCTION' if overall_quality >= 0.8 else 'NEEDS IMPROVEMENT'
    }
    
    with open('document_processing_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: document_processing_report.json")


def main():
    """Run complete document processing test."""
    print("CaseStrainer Document Processing Test")
    print("="*80)
    print("Testing complete end-to-end document processing with extraction,")
    print("clustering, and verification compared to manual review.")
    
    try:
        test_document_processing()
        
        print("\n" + "="*80)
        print("✅ DOCUMENT PROCESSING TEST COMPLETED")
        print("="*80)
        print("Check the comprehensive report above for detailed results.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
