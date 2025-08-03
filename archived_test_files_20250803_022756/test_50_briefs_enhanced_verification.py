#!/usr/bin/env python3
"""
Comprehensive test of all citations from the 50 briefs using enhanced verification system
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

def load_existing_citations():
    """Load citations from previous 50-brief runs"""
    
    print("LOADING EXISTING CITATION DATA")
    print("=" * 40)
    
    # Look for existing citation files
    citation_files = [
        'citation_processing_summary_20250729_144835.json',
        'non_courtlistener_citations_20250728_215223.csv',
        'unverified_citations_20250728_215223.csv'
    ]
    
    all_citations = []
    
    for filename in citation_files:
        if os.path.exists(filename):
            print(f"Loading: {filename}")
            
            if filename.endswith('.json'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    if 'citations' in data:
                        citations = data['citations']
                        print(f"  Found {len(citations)} citations")
                        all_citations.extend(citations)
                    elif isinstance(data, list):
                        print(f"  Found {len(data)} citations")
                        all_citations.extend(data)
                        
                except Exception as e:
                    print(f"  Error loading {filename}: {e}")
            
            elif filename.endswith('.csv'):
                try:
                    df = pd.read_csv(filename)
                    print(f"  Found {len(df)} citations")
                    
                    # Convert DataFrame to citation format
                    for _, row in df.iterrows():
                        citation = {
                            'citation': row.get('citation', ''),
                            'verified': row.get('verified', False),
                            'canonical_name': row.get('canonical_name', ''),
                            'source': row.get('source', ''),
                            'url': row.get('url', '')
                        }
                        all_citations.append(citation)
                        
                except Exception as e:
                    print(f"  Error loading {filename}: {e}")
    
    # Remove duplicates based on citation text
    unique_citations = {}
    for citation in all_citations:
        citation_text = citation.get('citation', '').strip()
        if citation_text and citation_text not in unique_citations:
            unique_citations[citation_text] = citation
    
    final_citations = list(unique_citations.values())
    print(f"\nTotal unique citations loaded: {len(final_citations)}")
    
    return final_citations

def test_citation_with_enhanced_verification(citation_text: str) -> Dict[str, Any]:
    """Test a single citation with the enhanced verification system"""
    
    try:
        # Use the enhanced endpoint
        response = requests.post(
            "http://localhost:5000/api/analyze_enhanced",
            json={
                "text": f"This case cites {citation_text}.",
                "type": "text"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            if citations:
                citation_result = citations[0]
                return {
                    'citation': citation_text,
                    'verified': citation_result.get('verified', False),
                    'canonical_name': citation_result.get('canonical_name', ''),
                    'canonical_date': citation_result.get('canonical_date', ''),
                    'url': citation_result.get('url', ''),
                    'source': citation_result.get('source', ''),
                    'confidence': citation_result.get('confidence', 0.0),
                    'validation_method': citation_result.get('validation_method', ''),
                    'enhanced_verification': True,
                    'api_status': 'success'
                }
            else:
                return {
                    'citation': citation_text,
                    'verified': False,
                    'canonical_name': '',
                    'canonical_date': '',
                    'url': '',
                    'source': 'no_citations_found',
                    'confidence': 0.0,
                    'validation_method': '',
                    'enhanced_verification': True,
                    'api_status': 'no_citations'
                }
        else:
            return {
                'citation': citation_text,
                'verified': False,
                'canonical_name': '',
                'canonical_date': '',
                'url': '',
                'source': 'api_error',
                'confidence': 0.0,
                'validation_method': '',
                'enhanced_verification': True,
                'api_status': f'error_{response.status_code}'
            }
    
    except Exception as e:
        return {
            'citation': citation_text,
            'verified': False,
            'canonical_name': '',
            'canonical_date': '',
            'url': '',
            'source': 'exception',
            'confidence': 0.0,
            'validation_method': '',
            'enhanced_verification': True,
            'api_status': f'exception_{str(e)[:50]}'
        }

def run_comprehensive_test():
    """Run comprehensive test on all citations"""
    
    print("COMPREHENSIVE 50-BRIEF CITATION TEST WITH ENHANCED VERIFICATION")
    print("=" * 70)
    
    # Load existing citations
    citations = load_existing_citations()
    
    if not citations:
        print("No citations found to test!")
        return
    
    print(f"\nTesting {len(citations)} citations with enhanced verification...")
    print("=" * 60)
    
    results = []
    start_time = time.time()
    
    for i, citation_data in enumerate(citations):
        citation_text = citation_data.get('citation', '').strip()
        
        if not citation_text:
            continue
        
        print(f"\n[{i+1}/{len(citations)}] Testing: {citation_text}")
        
        # Test with enhanced verification
        result = test_citation_with_enhanced_verification(citation_text)
        
        # Add original data for comparison
        result['original_verified'] = citation_data.get('verified', False)
        result['original_source'] = citation_data.get('source', '')
        result['original_canonical_name'] = citation_data.get('canonical_name', '')
        
        results.append(result)
        
        # Show progress
        verified_status = "✅ VERIFIED" if result['verified'] else "❌ UNVERIFIED"
        source = result.get('source', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        print(f"  Result: {verified_status} | Source: {source} | Confidence: {confidence}")
        
        # Brief pause to avoid overwhelming the API
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_verification_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'total_citations': len(results),
                'processing_time': total_time,
                'enhanced_verification': True
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    return results, results_file

def analyze_results(results: List[Dict[str, Any]]):
    """Analyze the test results for insights"""
    
    print(f"\n{'='*70}")
    print("ENHANCED VERIFICATION ANALYSIS")
    print(f"{'='*70}")
    
    total_citations = len(results)
    
    # Basic statistics
    verified_count = sum(1 for r in results if r.get('verified', False))
    unverified_count = total_citations - verified_count
    
    print(f"\nBASIC STATISTICS:")
    print(f"  Total citations tested: {total_citations}")
    print(f"  Verified citations: {verified_count} ({verified_count/total_citations*100:.1f}%)")
    print(f"  Unverified citations: {unverified_count} ({unverified_count/total_citations*100:.1f}%)")
    
    # Source analysis
    sources = {}
    for result in results:
        source = result.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\nSOURCE BREAKDOWN:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total_citations * 100
        print(f"  {source}: {count} ({percentage:.1f}%)")
    
    # Enhanced verification features
    enhanced_features = {}
    confidence_scores = []
    validation_methods = {}
    
    for result in results:
        if result.get('enhanced_verification'):
            enhanced_features['enhanced'] = enhanced_features.get('enhanced', 0) + 1
            
            confidence = result.get('confidence', 0.0)
            if confidence > 0:
                confidence_scores.append(confidence)
            
            validation_method = result.get('validation_method', 'unknown')
            validation_methods[validation_method] = validation_methods.get(validation_method, 0) + 1
    
    print(f"\nENHANCED VERIFICATION FEATURES:")
    print(f"  Citations with enhanced verification: {enhanced_features.get('enhanced', 0)}")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"  Average confidence score: {avg_confidence:.2f}")
        print(f"  High confidence (>0.8): {sum(1 for c in confidence_scores if c > 0.8)}")
        print(f"  Medium confidence (0.5-0.8): {sum(1 for c in confidence_scores if 0.5 <= c <= 0.8)}")
        print(f"  Low confidence (<0.5): {sum(1 for c in confidence_scores if c < 0.5)}")
    
    print(f"\nVALIDATION METHODS:")
    for method, count in sorted(validation_methods.items(), key=lambda x: x[1], reverse=True):
        if method and method != 'unknown':
            percentage = count / total_citations * 100
            print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Comparison with original results (if available)
    original_verified = sum(1 for r in results if r.get('original_verified', False))
    if original_verified > 0:
        print(f"\nCOMPARISON WITH ORIGINAL RESULTS:")
        print(f"  Original verified: {original_verified}")
        print(f"  Enhanced verified: {verified_count}")
        print(f"  Difference: {verified_count - original_verified} ({(verified_count - original_verified)/original_verified*100:.1f}%)")
        
        # Check for potential false positives resolved
        false_positives_resolved = 0
        new_verifications = 0
        
        for result in results:
            original_verified = result.get('original_verified', False)
            enhanced_verified = result.get('verified', False)
            
            if original_verified and not enhanced_verified:
                false_positives_resolved += 1
            elif not original_verified and enhanced_verified:
                new_verifications += 1
        
        print(f"  Potential false positives resolved: {false_positives_resolved}")
        print(f"  New legitimate verifications: {new_verifications}")
    
    # Quality indicators
    print(f"\nQUALITY INDICATORS:")
    
    # Check for citations with complete canonical data
    complete_data = sum(1 for r in results 
                       if r.get('verified') and 
                          r.get('canonical_name') and 
                          r.get('canonical_name').strip() and
                          r.get('url') and 
                          r.get('url').strip())
    
    if verified_count > 0:
        print(f"  Verified citations with complete data: {complete_data}/{verified_count} ({complete_data/verified_count*100:.1f}%)")
    
    # Check for enhanced validation sources
    enhanced_sources = sum(1 for r in results 
                          if r.get('verified') and 
                             'validated' in r.get('source', '').lower())
    
    if verified_count > 0:
        print(f"  Citations with enhanced validation: {enhanced_sources}/{verified_count} ({enhanced_sources/verified_count*100:.1f}%)")
    
    # Flag potential issues
    print(f"\nPOTENTIAL ISSUES TO REVIEW:")
    
    # Citations verified but with low confidence
    low_confidence_verified = [r for r in results 
                              if r.get('verified') and r.get('confidence', 1.0) < 0.5]
    if low_confidence_verified:
        print(f"  ⚠️  Verified citations with low confidence: {len(low_confidence_verified)}")
        for citation in low_confidence_verified[:3]:  # Show first 3
            print(f"     - {citation['citation']} (confidence: {citation.get('confidence', 0.0):.2f})")
    
    # Citations with missing canonical data
    missing_data = [r for r in results 
                   if r.get('verified') and 
                      (not r.get('canonical_name') or not r.get('canonical_name').strip())]
    if missing_data:
        print(f"  ⚠️  Verified citations missing canonical name: {len(missing_data)}")
        for citation in missing_data[:3]:  # Show first 3
            print(f"     - {citation['citation']}")
    
    return {
        'total_citations': total_citations,
        'verified_count': verified_count,
        'unverified_count': unverified_count,
        'sources': sources,
        'confidence_scores': confidence_scores,
        'validation_methods': validation_methods,
        'complete_data_count': complete_data,
        'enhanced_sources_count': enhanced_sources,
        'potential_issues': {
            'low_confidence_verified': len(low_confidence_verified),
            'missing_canonical_data': len(missing_data)
        }
    }

def main():
    """Main test function"""
    
    print("Starting comprehensive 50-brief citation test...")
    
    # Run the test
    results, results_file = run_comprehensive_test()
    
    # Analyze results
    analysis = analyze_results(results)
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    print(f"Results saved to: {results_file}")
    print(f"Total processing time: {time.time():.1f} seconds")
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"✅ Enhanced verification system tested on {analysis['total_citations']} citations")
    print(f"✅ {analysis['verified_count']} citations verified ({analysis['verified_count']/analysis['total_citations']*100:.1f}%)")
    print(f"✅ {analysis['complete_data_count']} verified citations have complete canonical data")
    print(f"✅ {analysis['enhanced_sources_count']} citations used enhanced validation")
    
    if analysis['potential_issues']['low_confidence_verified'] > 0:
        print(f"⚠️  {analysis['potential_issues']['low_confidence_verified']} verified citations have low confidence - review recommended")
    
    if analysis['potential_issues']['missing_canonical_data'] > 0:
        print(f"⚠️  {analysis['potential_issues']['missing_canonical_data']} verified citations missing canonical data - review recommended")

if __name__ == "__main__":
    main()
