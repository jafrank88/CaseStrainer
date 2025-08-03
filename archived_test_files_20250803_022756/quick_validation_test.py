#!/usr/bin/env python3
"""
Quick validation test of enhanced verification with case names and dates
"""

import csv
import json
import requests
from datetime import datetime

def quick_validation_test():
    """Quick test of enhanced verification with actual case names and dates"""
    
    print("QUICK VALIDATION TEST - ENHANCED VERIFICATION WITH CASE NAMES")
    print("=" * 70)
    
    # Load a few sample citations from the CSV
    test_citations = []
    
    try:
        with open('non_courtlistener_citations_20250728_215223.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if count >= 10:  # Test first 10 citations
                    break
                
                citation_text = row.get('citation_text', '').strip()
                case_name = row.get('extracted_case_name', '').strip()
                date = row.get('extracted_date', '').strip()
                
                if citation_text and citation_text != 'N/A':
                    test_citations.append({
                        'citation': citation_text,
                        'case_name': case_name if case_name != 'N/A' else '',
                        'date': date if date != 'N/A' else '',
                        'file_name': row.get('file_name', '')
                    })
                    count += 1
                    
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return
    
    if not test_citations:
        print("No test citations loaded!")
        return
    
    print(f"Testing {len(test_citations)} citations with enhanced verification...")
    print("-" * 70)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    results = []
    
    for i, citation_data in enumerate(test_citations):
        citation = citation_data['citation']
        case_name = citation_data['case_name']
        date = citation_data['date']
        
        print(f"\n[{i+1}/{len(test_citations)}] Testing: {citation}")
        if case_name:
            print(f"  Expected Case: {case_name}")
        if date:
            print(f"  Expected Date: {date}")
        
        # Create rich context
        if case_name and date:
            test_text = f"In {case_name} ({date}), the court cited {citation}."
        elif case_name:
            test_text = f"In {case_name}, the court cited {citation}."
        elif date:
            test_text = f"In {date}, the court cited {citation}."
        else:
            test_text = f"This case cites {citation}."
        
        try:
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
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
                    source = citation_result.get('source', '')
                    confidence = citation_result.get('confidence', 0.0)
                    
                    print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                    print(f"  Source: {source}")
                    
                    if verified:
                        if canonical_name:
                            print(f"  Found Case: {canonical_name}")
                        if canonical_date:
                            print(f"  Found Date: {canonical_date}")
                        if confidence > 0:
                            print(f"  Confidence: {confidence:.2f}")
                        
                        # Check context validation
                        name_match = False
                        date_match = False
                        
                        if case_name and canonical_name:
                            # Simple name matching
                            case_words = set(case_name.lower().split())
                            canonical_words = set(canonical_name.lower().split())
                            if case_words and canonical_words:
                                overlap = len(case_words.intersection(canonical_words))
                                name_match = overlap > 0
                        
                        if date and canonical_date:
                            date_match = date in canonical_date or canonical_date in date or date[:4] in canonical_date
                        
                        if (case_name and not name_match) or (date and not date_match):
                            print(f"  ⚠️  Context mismatch - possible false positive")
                        elif name_match or date_match:
                            print(f"  ✅ Context validated")
                    
                    results.append({
                        'citation': citation,
                        'expected_case': case_name,
                        'expected_date': date,
                        'verified': verified,
                        'found_case': canonical_name,
                        'found_date': canonical_date,
                        'source': source,
                        'confidence': confidence,
                        'context_match': name_match or date_match if verified else None
                    })
                    
                else:
                    print(f"  Status: ❌ NO CITATIONS EXTRACTED")
                    results.append({
                        'citation': citation,
                        'expected_case': case_name,
                        'expected_date': date,
                        'verified': False,
                        'found_case': '',
                        'found_date': '',
                        'source': 'no_citations',
                        'confidence': 0.0,
                        'context_match': None
                    })
            else:
                print(f"  Status: ❌ API ERROR {response.status_code}")
                results.append({
                    'citation': citation,
                    'expected_case': case_name,
                    'expected_date': date,
                    'verified': False,
                    'found_case': '',
                    'found_date': '',
                    'source': 'api_error',
                    'confidence': 0.0,
                    'context_match': None
                })
                
        except Exception as e:
            print(f"  Status: ❌ EXCEPTION: {str(e)[:50]}")
            results.append({
                'citation': citation,
                'expected_case': case_name,
                'expected_date': date,
                'verified': False,
                'found_case': '',
                'found_date': '',
                'source': 'exception',
                'confidence': 0.0,
                'context_match': None
            })
    
    # Analysis
    print(f"\n{'='*70}")
    print("QUICK VALIDATION ANALYSIS")
    print(f"{'='*70}")
    
    total = len(results)
    verified = sum(1 for r in results if r['verified'])
    with_context = sum(1 for r in results if r['context_match'] is True)
    potential_false_positives = sum(1 for r in results if r['verified'] and r['context_match'] is False)
    
    print(f"Total citations tested: {total}")
    print(f"Citations verified: {verified} ({verified/total*100:.1f}%)")
    if verified > 0:
        print(f"Verified with context validation: {with_context}/{verified} ({with_context/verified*100:.1f}%)")
        print(f"Potential false positives: {potential_false_positives}/{verified} ({potential_false_positives/verified*100:.1f}%)")
    
    # Sources
    sources = {}
    for r in results:
        if r['verified']:
            source = r['source']
            sources[source] = sources.get(source, 0) + 1
    
    if sources:
        print(f"\nVerification sources:")
        for source, count in sources.items():
            print(f"  {source}: {count}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"quick_validation_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'total_tested': total,
                'verified_count': verified,
                'context_validated': with_context,
                'potential_false_positives': potential_false_positives
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    # Overall assessment
    print(f"\n{'='*70}")
    print("OVERALL ASSESSMENT")
    print(f"{'='*70}")
    
    if verified > 0 and potential_false_positives == 0:
        print("✅ Enhanced verification working excellently - no false positives detected!")
    elif verified > 0 and potential_false_positives <= verified * 0.2:
        print("✅ Enhanced verification working well - minimal false positives")
    elif verified > 0:
        print("⚠️  Enhanced verification needs review - some false positives detected")
    else:
        print("❓ No verifications to assess")
    
    print(f"🎯 Enhanced verification system status: {'EXCELLENT' if potential_false_positives == 0 and verified > 0 else 'GOOD' if verified > 0 else 'NEEDS REVIEW'}")

if __name__ == "__main__":
    quick_validation_test()
