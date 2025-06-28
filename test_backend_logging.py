#!/usr/bin/env python3
"""
Comprehensive Backend Logging Test

This script tests the citation verification system with detailed logging
to troubleshoot URL field issues and frontend compatibility.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_with_logging(citation: str, context: str = ""):
    """
    Test a single citation with comprehensive logging.
    """
    print(f"\n{'='*80}")
    print(f"TESTING CITATION: {citation}")
    print(f"CONTEXT: {context}")
    print(f"{'='*80}")
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test the unified workflow
        result = verifier.verify_citation_unified_workflow(citation, full_text=context)
        
        # Analyze the result
        print(f"\n📊 RESULT ANALYSIS:")
        print(f"  Verified: {result.get('verified', 'N/A')}")
        print(f"  Case Name: {result.get('case_name', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Source: {result.get('source', 'N/A')}")
        print(f"  Canonical Date: {result.get('canonical_date', 'N/A')}")
        print(f"  Verification Method: {result.get('verification_method', 'N/A')}")
        
        # Check URL field specifically
        url_present = 'url' in result and result['url']
        print(f"\n🔗 URL FIELD ANALYSIS:")
        print(f"  URL Field Present: {'✅ YES' if 'url' in result else '❌ NO'}")
        print(f"  URL Value: {result.get('url', 'MISSING')}")
        print(f"  URL Status: {'✅ OK' if url_present else '❌ MISSING/EMPTY'}")
        
        # Check frontend compatibility
        print(f"\n🎯 FRONTEND COMPATIBILITY:")
        verified = result.get('verified')
        if verified in ['true', 'true_by_parallel', True]:
            print(f"  Verification Status: ✅ OK ({verified})")
        else:
            print(f"  Verification Status: ❌ ISSUE ({verified})")
            
        if url_present and verified in ['true', 'true_by_parallel', True]:
            print(f"  Frontend Link Expected: ✅ YES")
        else:
            print(f"  Frontend Link Expected: ❌ NO")
            
        # Log to file
        log_filename = f"citation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_filepath = os.path.join("logs", log_filename)
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Write detailed result to file
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "citation": citation,
            "context": context,
            "result": result,
            "analysis": {
                "url_present": url_present,
                "url_value": result.get('url', ''),
                "verified": verified,
                "frontend_compatible": verified in ['true', 'true_by_parallel', True],
                "frontend_expects_link": url_present and verified in ['true', 'true_by_parallel', True]
            }
        }
        
        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n📝 Detailed log written to: {log_filepath}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_multiple_citations():
    """
    Test multiple citations to identify patterns.
    """
    test_cases = [
        {
            "citation": "347 U.S. 483",
            "context": "Brown v. Board of Education landmark case"
        },
        {
            "citation": "410 U.S. 113", 
            "context": "Roe v. Wade landmark case"
        },
        {
            "citation": "199 Wn. App. 280",
            "context": "Washington Court of Appeals case"
        },
        {
            "citation": "399 P.3d 1195",
            "context": "Washington parallel citation"
        },
        {
            "citation": "185 Wn.2d 363",
            "context": "Washington Supreme Court case"
        }
    ]
    
    print(f"\n🧪 TESTING {len(test_cases)} CITATIONS")
    print(f"{'='*80}")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{len(test_cases)}")
        result = test_citation_with_logging(test_case["citation"], test_case["context"])
        if result:
            results.append({
                "test_case": test_case,
                "result": result
            })
    
    # Summary
    print(f"\n📈 SUMMARY")
    print(f"{'='*80}")
    
    verified_count = len([r for r in results if r["result"].get('verified') in ['true', 'true_by_parallel', True]])
    url_count = len([r for r in results if r["result"].get('url')])
    link_ready_count = len([r for r in results if r["result"].get('url') and r["result"].get('verified') in ['true', 'true_by_parallel', True]])
    
    print(f"Total Citations Tested: {len(results)}")
    print(f"Verified: {verified_count}")
    print(f"Have URL: {url_count}")
    print(f"Ready for Frontend Link: {link_ready_count}")
    print(f"Success Rate: {link_ready_count/len(results)*100:.1f}%")
    
    # Write summary to file
    summary_filename = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_filepath = os.path.join("logs", summary_filename)
    
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tested": len(results),
        "verified_count": verified_count,
        "url_count": url_count,
        "link_ready_count": link_ready_count,
        "success_rate": link_ready_count/len(results)*100 if results else 0,
        "results": results
    }
    
    with open(summary_filepath, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n📝 Summary written to: {summary_filepath}")
    
    return results

if __name__ == "__main__":
    print("🔍 BACKEND LOGGING TEST")
    print("="*80)
    print("This script will test citation verification with comprehensive logging")
    print("to troubleshoot URL field issues and frontend compatibility.")
    print("="*80)
    
    # Test multiple citations
    results = test_multiple_citations()
    
    print(f"\n✅ TEST COMPLETE")
    print(f"Check the 'logs' directory for detailed output files.") 