#!/usr/bin/env python3
"""
Focused analysis of enhanced verification effectiveness on 50-brief citations
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

def load_sample_citations(max_citations=50):
    """Load a sample of citations from the 50-brief data for focused testing"""
    
    print("LOADING SAMPLE CITATIONS FOR ENHANCED VERIFICATION TEST")
    print("=" * 60)
    
    # Load from the most recent comprehensive results
    citation_file = 'citation_processing_summary_20250729_144835.json'
    
    if not os.path.exists(citation_file):
        print(f"Citation file {citation_file} not found!")
        return []
    
    try:
        with open(citation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        citations = data.get('citations', [])
        print(f"Loaded {len(citations)} total citations from {citation_file}")
        
        # Sample different types of citations for comprehensive testing
        sample_citations = []
        
        # Get verified citations
        verified = [c for c in citations if c.get('verified', False)]
        unverified = [c for c in citations if not c.get('verified', False)]
        
        print(f"  Verified: {len(verified)}")
        print(f"  Unverified: {len(unverified)}")
        
        # Sample from each category
        sample_verified = verified[:min(25, len(verified))]
        sample_unverified = unverified[:min(25, len(unverified))]
        
        sample_citations.extend(sample_verified)
        sample_citations.extend(sample_unverified)
        
        print(f"Selected {len(sample_citations)} citations for testing:")
        print(f"  {len(sample_verified)} verified citations")
        print(f"  {len(sample_unverified)} unverified citations")
        
        return sample_citations[:max_citations]
        
    except Exception as e:
        print(f"Error loading citations: {e}")
        return []

def test_citation_enhanced(citation_text: str) -> Dict[str, Any]:
    """Test a single citation with enhanced verification"""
    
    try:
        # Test with enhanced endpoint
        response = requests.post(
            "http://localhost:5000/api/analyze_enhanced",
            json={
                "text": f"This case cites {citation_text}.",
                "type": "text"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            if citations:
                citation_result = citations[0]
                return {
                    'success': True,
                    'verified': citation_result.get('verified', False),
                    'canonical_name': citation_result.get('canonical_name', ''),
                    'canonical_date': citation_result.get('canonical_date', ''),
                    'url': citation_result.get('url', ''),
                    'source': citation_result.get('source', ''),
                    'confidence': citation_result.get('confidence', 0.0),
                    'validation_method': citation_result.get('validation_method', ''),
                    'api_response': 'success'
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'canonical_name': '',
                    'canonical_date': '',
                    'url': '',
                    'source': 'no_citations_extracted',
                    'confidence': 0.0,
                    'validation_method': '',
                    'api_response': 'no_citations'
                }
        else:
            return {
                'success': False,
                'verified': False,
                'canonical_name': '',
                'canonical_date': '',
                'url': '',
                'source': 'api_error',
                'confidence': 0.0,
                'validation_method': '',
                'api_response': f'http_{response.status_code}'
            }
    
    except Exception as e:
        return {
            'success': False,
            'verified': False,
            'canonical_name': '',
            'canonical_date': '',
            'url': '',
            'source': 'exception',
            'confidence': 0.0,
            'validation_method': '',
            'api_response': f'exception: {str(e)[:50]}'
        }

def run_focused_test():
    """Run focused test on sample citations"""
    
    print("\nFOCUSED ENHANCED VERIFICATION TEST")
    print("=" * 50)
    
    # Load sample citations
    citations = load_sample_citations(50)
    
    if not citations:
        print("No citations loaded for testing!")
        return [], {}
    
    print(f"\nTesting {len(citations)} sample citations...")
    print("-" * 40)
    
    results = []
    start_time = time.time()
    
    for i, citation_data in enumerate(citations):
        citation_text = citation_data.get('citation', '').strip()
        
        if not citation_text:
            continue
        
        print(f"\n[{i+1}/{len(citations)}] Testing: {citation_text[:80]}...")
        
        # Get original data for comparison
        original_verified = citation_data.get('verified', False)
        original_source = citation_data.get('source', '')
        original_canonical_name = citation_data.get('canonical_name', '')
        
        # Test with enhanced verification
        enhanced_result = test_citation_enhanced(citation_text)
        
        # Combine results
        result = {
            'citation': citation_text,
            'original_verified': original_verified,
            'original_source': original_source,
            'original_canonical_name': original_canonical_name,
            'enhanced_verified': enhanced_result.get('verified', False),
            'enhanced_source': enhanced_result.get('source', ''),
            'enhanced_canonical_name': enhanced_result.get('canonical_name', ''),
            'enhanced_canonical_date': enhanced_result.get('canonical_date', ''),
            'enhanced_url': enhanced_result.get('url', ''),
            'enhanced_confidence': enhanced_result.get('confidence', 0.0),
            'enhanced_validation_method': enhanced_result.get('validation_method', ''),
            'api_response': enhanced_result.get('api_response', ''),
            'test_success': enhanced_result.get('success', False)
        }
        
        results.append(result)
        
        # Show comparison
        original_status = "✅ VERIFIED" if original_verified else "❌ UNVERIFIED"
        enhanced_status = "✅ VERIFIED" if enhanced_result.get('verified') else "❌ UNVERIFIED"
        
        print(f"  Original: {original_status} | Source: {original_source}")
        print(f"  Enhanced: {enhanced_status} | Source: {enhanced_result.get('source', 'unknown')}")
        
        if enhanced_result.get('confidence', 0) > 0:
            print(f"  Confidence: {enhanced_result.get('confidence', 0.0):.2f}")
        
        # Brief pause to avoid overwhelming the API
        time.sleep(0.2)
    
    total_time = time.time() - start_time
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_verification_analysis_{timestamp}.json"
    
    summary = {
        'test_info': {
            'timestamp': timestamp,
            'total_citations_tested': len(results),
            'processing_time_seconds': total_time,
            'enhanced_verification_enabled': True
        },
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    return results, summary

def analyze_effectiveness(results: List[Dict[str, Any]]):
    """Analyze the effectiveness of enhanced verification"""
    
    print(f"\n{'='*60}")
    print("ENHANCED VERIFICATION EFFECTIVENESS ANALYSIS")
    print(f"{'='*60}")
    
    total = len(results)
    successful_tests = sum(1 for r in results if r.get('test_success', False))
    
    print(f"\nTEST EXECUTION:")
    print(f"  Total citations tested: {total}")
    print(f"  Successful API calls: {successful_tests} ({successful_tests/total*100:.1f}%)")
    print(f"  Failed API calls: {total - successful_tests}")
    
    # Compare original vs enhanced results
    original_verified = sum(1 for r in results if r.get('original_verified', False))
    enhanced_verified = sum(1 for r in results if r.get('enhanced_verified', False))
    
    print(f"\nVERIFICATION COMPARISON:")
    print(f"  Original system verified: {original_verified}/{total} ({original_verified/total*100:.1f}%)")
    print(f"  Enhanced system verified: {enhanced_verified}/{total} ({enhanced_verified/total*100:.1f}%)")
    print(f"  Difference: {enhanced_verified - original_verified} citations")
    
    # Analyze changes in verification status
    changes = {
        'newly_verified': 0,      # Was unverified, now verified
        'newly_unverified': 0,    # Was verified, now unverified (potential false positive fix)
        'remained_verified': 0,   # Was verified, still verified
        'remained_unverified': 0  # Was unverified, still unverified
    }
    
    for result in results:
        original = result.get('original_verified', False)
        enhanced = result.get('enhanced_verified', False)
        
        if not original and enhanced:
            changes['newly_verified'] += 1
        elif original and not enhanced:
            changes['newly_unverified'] += 1
        elif original and enhanced:
            changes['remained_verified'] += 1
        else:
            changes['remained_unverified'] += 1
    
    print(f"\nVERIFICATION STATUS CHANGES:")
    print(f"  Newly verified: {changes['newly_verified']} (enhanced system found new legitimate citations)")
    print(f"  Newly unverified: {changes['newly_unverified']} (potential false positives resolved)")
    print(f"  Remained verified: {changes['remained_verified']} (consistent legitimate citations)")
    print(f"  Remained unverified: {changes['remained_unverified']} (consistent unverified citations)")
    
    # Analyze enhanced verification features
    enhanced_sources = {}
    confidence_scores = []
    validation_methods = {}
    
    for result in results:
        if result.get('enhanced_verified', False):
            source = result.get('enhanced_source', 'unknown')
            enhanced_sources[source] = enhanced_sources.get(source, 0) + 1
            
            confidence = result.get('enhanced_confidence', 0.0)
            if confidence > 0:
                confidence_scores.append(confidence)
            
            method = result.get('enhanced_validation_method', 'unknown')
            if method:
                validation_methods[method] = validation_methods.get(method, 0) + 1
    
    print(f"\nENHANCED VERIFICATION SOURCES:")
    for source, count in sorted(enhanced_sources.items(), key=lambda x: x[1], reverse=True):
        percentage = count / enhanced_verified * 100 if enhanced_verified > 0 else 0
        print(f"  {source}: {count} ({percentage:.1f}%)")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        high_confidence = sum(1 for c in confidence_scores if c > 0.8)
        medium_confidence = sum(1 for c in confidence_scores if 0.5 <= c <= 0.8)
        low_confidence = sum(1 for c in confidence_scores if c < 0.5)
        
        print(f"\nCONFIDENCE SCORES:")
        print(f"  Average confidence: {avg_confidence:.2f}")
        print(f"  High confidence (>0.8): {high_confidence}")
        print(f"  Medium confidence (0.5-0.8): {medium_confidence}")
        print(f"  Low confidence (<0.5): {low_confidence}")
    
    print(f"\nVALIDATION METHODS:")
    for method, count in sorted(validation_methods.items(), key=lambda x: x[1], reverse=True):
        if method and method != 'unknown':
            percentage = count / enhanced_verified * 100 if enhanced_verified > 0 else 0
            print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Quality analysis
    complete_canonical_data = sum(1 for r in results 
                                 if r.get('enhanced_verified', False) and 
                                    r.get('enhanced_canonical_name', '').strip() and
                                    r.get('enhanced_url', '').strip())
    
    print(f"\nDATA QUALITY:")
    if enhanced_verified > 0:
        print(f"  Verified citations with complete canonical data: {complete_canonical_data}/{enhanced_verified} ({complete_canonical_data/enhanced_verified*100:.1f}%)")
    
    # Flag potential issues
    print(f"\nPOTENTIAL ISSUES:")
    
    # Show examples of newly unverified citations (potential false positives resolved)
    newly_unverified_examples = [r for r in results if r.get('original_verified', False) and not r.get('enhanced_verified', False)]
    if newly_unverified_examples:
        print(f"  🎯 Potential false positives resolved: {len(newly_unverified_examples)}")
        for example in newly_unverified_examples[:3]:
            print(f"     - {example['citation'][:60]}...")
            print(f"       Original: {example.get('original_source', 'unknown')}")
            print(f"       Enhanced: {example.get('enhanced_source', 'unknown')}")
    
    # Show examples of newly verified citations
    newly_verified_examples = [r for r in results if not r.get('original_verified', False) and r.get('enhanced_verified', False)]
    if newly_verified_examples:
        print(f"  ✅ New legitimate verifications: {len(newly_verified_examples)}")
        for example in newly_verified_examples[:3]:
            print(f"     - {example['citation'][:60]}...")
            print(f"       Source: {example.get('enhanced_source', 'unknown')}")
            print(f"       Confidence: {example.get('enhanced_confidence', 0.0):.2f}")
    
    return {
        'total_tested': total,
        'successful_tests': successful_tests,
        'original_verified': original_verified,
        'enhanced_verified': enhanced_verified,
        'changes': changes,
        'enhanced_sources': enhanced_sources,
        'confidence_scores': confidence_scores,
        'validation_methods': validation_methods,
        'complete_canonical_data': complete_canonical_data
    }

def main():
    """Main analysis function"""
    
    print("ENHANCED VERIFICATION EFFECTIVENESS ANALYSIS")
    print("=" * 50)
    
    # Run focused test
    results, summary = run_focused_test()
    
    if not results:
        print("No results to analyze!")
        return
    
    # Analyze effectiveness
    analysis = analyze_effectiveness(results)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    print(f"✅ Enhanced verification system tested on {analysis['total_tested']} citations")
    print(f"✅ {analysis['successful_tests']} successful API calls ({analysis['successful_tests']/analysis['total_tested']*100:.1f}%)")
    print(f"✅ {analysis['enhanced_verified']} citations verified by enhanced system")
    print(f"✅ {analysis['changes']['newly_unverified']} potential false positives resolved")
    print(f"✅ {analysis['changes']['newly_verified']} new legitimate verifications found")
    print(f"✅ {analysis['complete_canonical_data']} verified citations have complete canonical data")
    
    if analysis['confidence_scores']:
        avg_confidence = sum(analysis['confidence_scores']) / len(analysis['confidence_scores'])
        print(f"✅ Average confidence score: {avg_confidence:.2f}")
    
    print(f"\n🎯 Enhanced verification system is {'WORKING EFFECTIVELY' if analysis['changes']['newly_unverified'] > 0 or analysis['enhanced_verified'] > 0 else 'NEEDS REVIEW'}")

if __name__ == "__main__":
    main()
