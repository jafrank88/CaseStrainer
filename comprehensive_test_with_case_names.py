#!/usr/bin/env python3
"""
Comprehensive test using actual 50-brief citation data with case names and dates
"""

import csv
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any

def load_actual_citations_with_case_names(max_citations=50):
    """Load actual citations from CSV files with case names and dates"""
    
    print("LOADING ACTUAL 50-BRIEF CITATIONS WITH CASE NAMES AND DATES")
    print("=" * 70)
    
    citations = []
    
    # CSV files with actual citation data
    csv_files = [
        'non_courtlistener_citations_20250728_215223.csv',
        'non_courtlistener_citations_20250729_144835.csv',
        'non_courtlistener_citations_20250729_174752.csv'
    ]
    
    for csv_file in csv_files:
        try:
            print(f"Loading from: {csv_file}")
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                file_citations = []
                
                for row in reader:
                    citation_text = row.get('citation_text', '').strip()
                    extracted_case_name = row.get('extracted_case_name', '').strip()
                    extracted_date = row.get('extracted_date', '').strip()
                    verification_status = row.get('verification_status', '').strip()
                    file_name = row.get('file_name', '').strip()
                    
                    if citation_text and citation_text != 'N/A':
                        file_citations.append({
                            'citation': citation_text,
                            'case_name': extracted_case_name if extracted_case_name != 'N/A' else '',
                            'date': extracted_date if extracted_date != 'N/A' else '',
                            'original_verification_status': verification_status,
                            'file_name': file_name,
                            'has_case_name': bool(extracted_case_name and extracted_case_name != 'N/A'),
                            'has_date': bool(extracted_date and extracted_date != 'N/A')
                        })
                
                citations.extend(file_citations)
                print(f"  Loaded {len(file_citations)} citations")
                
                # Use the first file that loads successfully
                if file_citations:
                    break
                    
        except Exception as e:
            print(f"  Error loading {csv_file}: {e}")
    
    if not citations:
        print("No CSV data loaded, creating test set...")
        return []
    
    # Sample different types of citations for comprehensive testing
    print(f"\nTotal citations available: {len(citations)}")
    
    # Prioritize citations with case names and dates
    citations_with_names = [c for c in citations if c['has_case_name']]
    citations_with_dates = [c for c in citations if c['has_date']]
    citations_with_both = [c for c in citations if c['has_case_name'] and c['has_date']]
    
    print(f"Citations with case names: {len(citations_with_names)}")
    print(f"Citations with dates: {len(citations_with_dates)}")
    print(f"Citations with both: {len(citations_with_both)}")
    
    # Create a balanced sample
    sample_citations = []
    
    # First, add citations with both case name and date (highest priority)
    sample_citations.extend(citations_with_both[:min(30, len(citations_with_both))])
    
    # Then add citations with just case names
    remaining_slots = max_citations - len(sample_citations)
    if remaining_slots > 0:
        citations_name_only = [c for c in citations_with_names if c not in sample_citations]
        sample_citations.extend(citations_name_only[:min(remaining_slots//2, len(citations_name_only))])
    
    # Finally add any remaining citations
    remaining_slots = max_citations - len(sample_citations)
    if remaining_slots > 0:
        remaining_citations = [c for c in citations if c not in sample_citations]
        sample_citations.extend(remaining_citations[:remaining_slots])
    
    print(f"\nSelected {len(sample_citations)} citations for testing:")
    with_both = sum(1 for c in sample_citations if c['has_case_name'] and c['has_date'])
    with_name = sum(1 for c in sample_citations if c['has_case_name'])
    with_date = sum(1 for c in sample_citations if c['has_date'])
    
    print(f"  With case name and date: {with_both}")
    print(f"  With case name: {with_name}")
    print(f"  With date: {with_date}")
    
    return sample_citations

def test_citation_with_context(citation_data: Dict[str, Any], production_endpoint: str) -> Dict[str, Any]:
    """Test a citation with its case name and date context"""
    
    citation_text = citation_data['citation']
    case_name = citation_data['case_name']
    date = citation_data['date']
    
    # Create rich context for testing
    if case_name and date:
        test_text = f"In {case_name} ({date}), the court cited {citation_text}."
    elif case_name:
        test_text = f"In {case_name}, the court cited {citation_text}."
    elif date:
        test_text = f"In {date}, the court cited {citation_text}."
    else:
        test_text = f"This case cites {citation_text}."
    
    try:
        response = requests.post(
            production_endpoint,
            json={
                "text": test_text,
                "type": "text"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            citations_found = result.get('citations', [])
            
            if citations_found:
                citation_result = citations_found[0]
                
                # Check if the verification matches expected case name/date
                canonical_name = citation_result.get('canonical_name', '')
                canonical_date = citation_result.get('canonical_date', '')
                
                # Calculate match scores
                name_match = 0.0
                date_match = 0.0
                
                if case_name and canonical_name:
                    # Simple case name matching (could be improved with fuzzy matching)
                    name_words = set(case_name.lower().split())
                    canonical_words = set(canonical_name.lower().split())
                    if name_words and canonical_words:
                        name_match = len(name_words.intersection(canonical_words)) / len(name_words.union(canonical_words))
                
                if date and canonical_date:
                    # Simple date matching
                    if date in canonical_date or canonical_date in date:
                        date_match = 1.0
                    elif date[:4] in canonical_date:  # Year match
                        date_match = 0.5
                
                return {
                    'citation': citation_text,
                    'case_name': case_name,
                    'date': date,
                    'test_text': test_text,
                    'verified': citation_result.get('verified', False),
                    'canonical_name': canonical_name,
                    'canonical_date': canonical_date,
                    'url': citation_result.get('url', ''),
                    'source': citation_result.get('source', ''),
                    'confidence': citation_result.get('confidence', 0.0),
                    'validation_method': citation_result.get('validation_method', ''),
                    'has_complete_data': bool(canonical_name.strip() and citation_result.get('url', '').strip()),
                    'name_match_score': name_match,
                    'date_match_score': date_match,
                    'context_validation': name_match > 0.3 or date_match > 0.0,  # Basic validation
                    'api_status': 'success',
                    'status_code': 200,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'citation': citation_text,
                    'case_name': case_name,
                    'date': date,
                    'test_text': test_text,
                    'verified': False,
                    'canonical_name': '',
                    'canonical_date': '',
                    'url': '',
                    'source': 'no_citations_extracted',
                    'confidence': 0.0,
                    'validation_method': '',
                    'has_complete_data': False,
                    'name_match_score': 0.0,
                    'date_match_score': 0.0,
                    'context_validation': False,
                    'api_status': 'no_citations',
                    'status_code': 200,
                    'response_time': response.elapsed.total_seconds()
                }
        else:
            return {
                'citation': citation_text,
                'case_name': case_name,
                'date': date,
                'test_text': test_text,
                'verified': False,
                'canonical_name': '',
                'canonical_date': '',
                'url': '',
                'source': 'api_error',
                'confidence': 0.0,
                'validation_method': '',
                'has_complete_data': False,
                'name_match_score': 0.0,
                'date_match_score': 0.0,
                'context_validation': False,
                'api_status': f'error_{response.status_code}',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
            }
            
    except Exception as e:
        return {
            'citation': citation_text,
            'case_name': case_name,
            'date': date,
            'test_text': test_text,
            'verified': False,
            'canonical_name': '',
            'canonical_date': '',
            'url': '',
            'source': 'exception',
            'confidence': 0.0,
            'validation_method': '',
            'has_complete_data': False,
            'name_match_score': 0.0,
            'date_match_score': 0.0,
            'context_validation': False,
            'api_status': 'exception',
            'error': str(e),
            'status_code': 0,
            'response_time': 0
        }

def run_comprehensive_test_with_case_names():
    """Run comprehensive test with case names and dates"""
    
    print("\nCOMPREHENSIVE ENHANCED VERIFICATION TEST WITH CASE NAMES")
    print("=" * 80)
    print("Testing enhanced verification with actual case names and dates from 50 briefs")
    print("=" * 80)
    
    # Load actual citations with case names and dates
    citations_data = load_actual_citations_with_case_names(50)
    
    if not citations_data:
        print("No citations loaded for testing!")
        return [], {}
    
    # Production endpoint
    production_endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    print(f"\nTesting {len(citations_data)} citations with context against:")
    print(f"  {production_endpoint}")
    print("-" * 80)
    
    results = []
    start_time = time.time()
    
    for i, citation_data in enumerate(citations_data):
        citation_text = citation_data['citation']
        case_name = citation_data['case_name']
        date = citation_data['date']
        
        print(f"\n[{i+1}/{len(citations_data)}] Testing: {citation_text}")
        if case_name:
            print(f"  Case Name: {case_name}")
        if date:
            print(f"  Date: {date}")
        
        # Test with enhanced verification including context
        enhanced_result = test_citation_with_context(citation_data, production_endpoint)
        
        # Add original data for comparison
        result = {
            **enhanced_result,
            'original_verification_status': citation_data['original_verification_status'],
            'file_name': citation_data['file_name'],
            'has_input_case_name': citation_data['has_case_name'],
            'has_input_date': citation_data['has_date'],
            'test_timestamp': datetime.now().isoformat()
        }
        
        results.append(result)
        
        # Show results
        verified = enhanced_result.get('verified', False)
        canonical_name = enhanced_result.get('canonical_name', '')
        canonical_date = enhanced_result.get('canonical_date', '')
        name_match = enhanced_result.get('name_match_score', 0.0)
        date_match = enhanced_result.get('date_match_score', 0.0)
        context_valid = enhanced_result.get('context_validation', False)
        
        print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
        print(f"  Source: {enhanced_result.get('source', 'unknown')}")
        
        if verified:
            if canonical_name:
                print(f"  Found Case: {canonical_name[:50]}...")
            if canonical_date:
                print(f"  Found Date: {canonical_date}")
            
            if case_name and name_match > 0:
                print(f"  Name Match: {name_match:.2f}")
            if date and date_match > 0:
                print(f"  Date Match: {date_match:.2f}")
            
            if context_valid:
                print(f"  ✅ Context validation: PASSED")
            elif case_name or date:
                print(f"  ⚠️  Context validation: FAILED (possible false positive)")
        
        if enhanced_result.get('confidence', 0) > 0:
            print(f"  Confidence: {enhanced_result.get('confidence', 0.0):.2f}")
        
        print(f"  Response time: {enhanced_result.get('response_time', 0):.2f}s")
        
        # Brief pause
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"comprehensive_test_with_case_names_{timestamp}.json"
    
    summary = {
        'test_info': {
            'test_name': 'Comprehensive Enhanced Verification Test with Case Names and Dates',
            'timestamp': timestamp,
            'total_citations_tested': len(results),
            'processing_time_seconds': total_time,
            'production_endpoint': production_endpoint,
            'enhanced_verification_enabled': True,
            'context_validation_enabled': True
        },
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    return results, summary

def analyze_results_with_context_validation(results: List[Dict[str, Any]]):
    """Analyze results with context validation"""
    
    print(f"\n{'='*90}")
    print("ENHANCED VERIFICATION ANALYSIS WITH CONTEXT VALIDATION")
    print(f"{'='*90}")
    
    total = len(results)
    successful_tests = sum(1 for r in results if r.get('api_status') == 'success')
    verified = sum(1 for r in results if r.get('verified', False))
    
    print(f"Total citations tested: {total}")
    print(f"Successful API calls: {successful_tests} ({successful_tests/total*100:.1f}%)")
    print(f"Citations verified: {verified} ({verified/total*100:.1f}%)")
    
    # Context validation analysis
    with_input_names = sum(1 for r in results if r.get('has_input_case_name', False))
    with_input_dates = sum(1 for r in results if r.get('has_input_date', False))
    with_both_inputs = sum(1 for r in results if r.get('has_input_case_name', False) and r.get('has_input_date', False))
    
    print(f"\nINPUT CONTEXT ANALYSIS:")
    print(f"  Citations with case names: {with_input_names}")
    print(f"  Citations with dates: {with_input_dates}")
    print(f"  Citations with both: {with_both_inputs}")
    
    # Verification quality analysis
    verified_results = [r for r in results if r.get('verified', False)]
    if verified_results:
        complete_data = sum(1 for r in verified_results if r.get('has_complete_data', False))
        context_validated = sum(1 for r in verified_results if r.get('context_validation', False))
        
        print(f"\nVERIFICATION QUALITY:")
        print(f"  Verified with complete data: {complete_data}/{verified} ({complete_data/verified*100:.1f}%)")
        print(f"  Verified with context validation: {context_validated}/{verified} ({context_validated/verified*100:.1f}%)")
        
        # Potential false positives (verified but failed context validation)
        potential_false_positives = [r for r in verified_results 
                                   if not r.get('context_validation', False) and 
                                      (r.get('has_input_case_name', False) or r.get('has_input_date', False))]
        
        if potential_false_positives:
            print(f"\n⚠️  POTENTIAL FALSE POSITIVES: {len(potential_false_positives)}")
            for fp in potential_false_positives[:3]:  # Show first 3
                print(f"     {fp['citation']} - Expected: {fp.get('case_name', 'N/A')}, Found: {fp.get('canonical_name', 'N/A')}")
    
    # Match score analysis
    name_matches = [r.get('name_match_score', 0.0) for r in verified_results if r.get('name_match_score', 0.0) > 0]
    date_matches = [r.get('date_match_score', 0.0) for r in verified_results if r.get('date_match_score', 0.0) > 0]
    
    if name_matches:
        avg_name_match = sum(name_matches) / len(name_matches)
        high_name_matches = sum(1 for score in name_matches if score > 0.7)
        print(f"\nNAME MATCHING:")
        print(f"  Average name match score: {avg_name_match:.2f}")
        print(f"  High confidence name matches (>0.7): {high_name_matches}/{len(name_matches)}")
    
    if date_matches:
        avg_date_match = sum(date_matches) / len(date_matches)
        perfect_date_matches = sum(1 for score in date_matches if score == 1.0)
        print(f"\nDATE MATCHING:")
        print(f"  Average date match score: {avg_date_match:.2f}")
        print(f"  Perfect date matches: {perfect_date_matches}/{len(date_matches)}")
    
    # Enhanced verification sources
    sources = {}
    for result in verified_results:
        source = result.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\nVERIFICATION SOURCES:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percentage = count / verified * 100 if verified > 0 else 0
        print(f"  {source}: {count} ({percentage:.1f}%)")
    
    # Overall assessment
    print(f"\n{'='*90}")
    print("OVERALL ASSESSMENT WITH CONTEXT VALIDATION")
    print(f"{'='*90}")
    
    api_success_rate = successful_tests / total if total > 0 else 0
    data_quality_rate = complete_data / verified if verified > 0 else 0
    context_validation_rate = context_validated / verified if verified > 0 else 0
    
    if api_success_rate >= 0.95:
        print("✅ API Performance: EXCELLENT")
    elif api_success_rate >= 0.8:
        print("⚠️  API Performance: GOOD")
    else:
        print("❌ API Performance: NEEDS IMPROVEMENT")
    
    if verified > 0:
        if data_quality_rate >= 0.9:
            print("✅ Data Quality: EXCELLENT")
        elif data_quality_rate >= 0.7:
            print("⚠️  Data Quality: GOOD")
        else:
            print("❌ Data Quality: NEEDS IMPROVEMENT")
        
        if context_validation_rate >= 0.8:
            print("✅ Context Validation: EXCELLENT")
        elif context_validation_rate >= 0.6:
            print("⚠️  Context Validation: GOOD")
        else:
            print("❌ Context Validation: NEEDS IMPROVEMENT")
    
    false_positive_rate = len(potential_false_positives) / verified if verified > 0 else 0
    if false_positive_rate <= 0.1:
        print("✅ False Positive Prevention: EXCELLENT")
    elif false_positive_rate <= 0.2:
        print("⚠️  False Positive Prevention: GOOD")
    else:
        print("❌ False Positive Prevention: NEEDS IMPROVEMENT")
    
    # Overall status
    if (api_success_rate >= 0.9 and 
        (verified == 0 or (data_quality_rate >= 0.8 and context_validation_rate >= 0.7))):
        overall_status = "EXCELLENT"
    elif api_success_rate >= 0.8 and successful_tests > 0:
        overall_status = "GOOD"
    else:
        overall_status = "NEEDS REVIEW"
    
    print(f"\n🎯 ENHANCED VERIFICATION WITH CONTEXT VALIDATION: {overall_status}")
    
    return {
        'total': total,
        'successful_tests': successful_tests,
        'verified': verified,
        'complete_data': complete_data if verified > 0 else 0,
        'context_validated': context_validated if verified > 0 else 0,
        'potential_false_positives': len(potential_false_positives) if verified > 0 else 0,
        'overall_status': overall_status
    }

def main():
    """Main test function with case names and dates"""
    
    print("STARTING COMPREHENSIVE TEST WITH CASE NAMES AND DATES")
    print("=" * 80)
    
    # Run comprehensive test
    results, summary = run_comprehensive_test_with_case_names()
    
    if not results:
        print("No results to analyze!")
        return
    
    # Analyze results with context validation
    analysis = analyze_results_with_context_validation(results)
    
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    print(f"✅ Enhanced verification tested on {analysis['total']} citations with case names/dates")
    print(f"✅ {analysis['successful_tests']} successful API calls")
    print(f"✅ {analysis['verified']} citations verified")
    print(f"✅ {analysis['complete_data']} verified citations have complete data")
    print(f"✅ {analysis['context_validated']} verified citations passed context validation")
    
    if analysis['potential_false_positives'] > 0:
        print(f"⚠️  {analysis['potential_false_positives']} potential false positives detected")
    else:
        print(f"✅ No false positives detected")
    
    print(f"\n🎯 Enhanced verification with context validation: {analysis['overall_status']}")
    
    if analysis['overall_status'] == "EXCELLENT":
        print("🎉 Enhanced verification working excellently with proper context validation!")
    elif analysis['overall_status'] == "GOOD":
        print("✅ Enhanced verification working well with minor improvements needed.")
    else:
        print("⚠️  Enhanced verification needs review.")

if __name__ == "__main__":
    main()
