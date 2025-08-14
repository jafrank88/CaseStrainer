#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for CaseStrainer
Tests extracted name/year, canonical name/year, canonical URL, and clustering correctness
"""

import sys
import os
import json
import time
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_text_extraction_and_clustering():
    """Test citation extraction, clustering, and canonical data for known legal text."""
    print("\n" + "="*80)
    print("COMPREHENSIVE BACKEND EXTRACTION & CLUSTERING TEST")
    print("="*80)
    
    # Test cases with known citations and expected results
    test_cases = [
        {
            "name": "Luis v. United States - Parallel Citations",
            "text": """
            In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
            the Supreme Court held that the pretrial restraint of a criminal defendant's 
            legitimate, untainted assets needed to pay for counsel violates the Sixth Amendment.
            """,
            "expected_clusters": 1,
            "expected_citations": 3,
            "expected_canonical_name": "Luis v. United States",
            "expected_canonical_year": "2016"
        },
        {
            "name": "Brown v. Board - Single Citation",
            "text": """
            The landmark decision in Brown v. Board of Education, 347 U.S. 483 (1954), 
            overturned the "separate but equal" doctrine established in Plessy v. Ferguson.
            """,
            "expected_clusters": 2,  # Brown and Plessy
            "expected_citations": 2,
            "expected_canonical_name": "Brown v. Board of Education",
            "expected_canonical_year": "1954"
        },
        {
            "name": "Multiple Cases with Parallel Citations",
            "text": """
            The Court in Miranda v. Arizona, 384 U.S. 436, 86 S. Ct. 1602, 16 L. Ed. 2d 694 (1966),
            established the famous Miranda warnings. This built upon earlier precedent from
            Gideon v. Wainwright, 372 U.S. 335, 83 S. Ct. 792, 9 L. Ed. 2d 799 (1963).
            """,
            "expected_clusters": 2,  # Miranda and Gideon clusters
            "expected_citations": 6,  # 3 for each case
            "expected_canonical_names": ["Miranda v. Arizona", "Gideon v. Wainwright"],
            "expected_canonical_years": ["1966", "1963"]
        }
    ]
    
    # Import the unified processor
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        processor = UnifiedInputProcessor()
        print("✅ UnifiedInputProcessor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import UnifiedInputProcessor: {e}")
        return False
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Process the text
            start_time = time.time()
            result = processor.process_any_input(
                input_data=test_case['text'],
                input_type='text',
                request_id=f'test_{i}',
                source_name=f'test_case_{i}'
            )
            processing_time = time.time() - start_time
            
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            
            if not result or not result.get('success'):
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                all_tests_passed = False
                continue
            
            # Extract results
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"📊 Results Summary:")
            print(f"   - Citations found: {len(citations)}")
            print(f"   - Clusters formed: {len(clusters)}")
            
            # Test 1: Citation count
            expected_citations = test_case['expected_citations']
            if len(citations) == expected_citations:
                print(f"✅ Citation count: {len(citations)} (expected {expected_citations})")
            else:
                print(f"❌ Citation count: {len(citations)} (expected {expected_citations})")
                all_tests_passed = False
            
            # Test 2: Cluster count
            expected_clusters = test_case['expected_clusters']
            if len(clusters) == expected_clusters:
                print(f"✅ Cluster count: {len(clusters)} (expected {expected_clusters})")
            else:
                print(f"❌ Cluster count: {len(clusters)} (expected {expected_clusters})")
                all_tests_passed = False
            
            # Test 3: Detailed analysis of citations and clusters
            print(f"\n📋 Detailed Citation Analysis:")
            for j, citation in enumerate(citations):
                print(f"   Citation {j+1}: {citation.get('citation', 'N/A')}")
                print(f"     - Extracted name: {citation.get('case_name', 'N/A')}")
                print(f"     - Extracted year: {citation.get('year', 'N/A')}")
                print(f"     - Canonical name: {citation.get('canonical_name', 'N/A')}")
                print(f"     - Canonical year: {citation.get('canonical_date', 'N/A')}")
                print(f"     - Canonical URL: {citation.get('canonical_url', 'N/A')}")
                print(f"     - Verification status: {citation.get('verification_status', 'N/A')}")
                print(f"     - Cluster ID: {citation.get('cluster_id', 'N/A')}")
            
            print(f"\n🔗 Cluster Analysis:")
            for j, cluster in enumerate(clusters):
                cluster_citations = cluster.get('citations', [])
                print(f"   Cluster {j+1}: {len(cluster_citations)} citations")
                print(f"     - Cluster name: {cluster.get('case_name', 'N/A')}")
                print(f"     - Cluster year: {cluster.get('year', 'N/A')}")
                print(f"     - Citations: {[c.get('citation', 'N/A') for c in cluster_citations]}")
            
            # Test 4: Canonical data verification
            if 'expected_canonical_name' in test_case:
                canonical_names_found = [c.get('canonical_name') for c in citations if c.get('canonical_name')]
                expected_name = test_case['expected_canonical_name']
                if any(expected_name in name for name in canonical_names_found if name):
                    print(f"✅ Canonical name found: {expected_name}")
                else:
                    print(f"❌ Canonical name not found: {expected_name}")
                    print(f"   Found names: {canonical_names_found}")
                    all_tests_passed = False
            
            # Test 5: Canonical year verification
            if 'expected_canonical_year' in test_case:
                canonical_years_found = [c.get('canonical_date') for c in citations if c.get('canonical_date')]
                expected_year = test_case['expected_canonical_year']
                if expected_year in canonical_years_found:
                    print(f"✅ Canonical year found: {expected_year}")
                else:
                    print(f"❌ Canonical year not found: {expected_year}")
                    print(f"   Found years: {canonical_years_found}")
                    all_tests_passed = False
            
            # Test 6: Canonical URL verification
            canonical_urls_found = [c.get('canonical_url') for c in citations if c.get('canonical_url')]
            if canonical_urls_found:
                print(f"✅ Canonical URLs found: {len(canonical_urls_found)}")
                for url in canonical_urls_found[:2]:  # Show first 2
                    print(f"   - {url}")
            else:
                print(f"⚠️  No canonical URLs found")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_tests_passed = False
    
    print(f"\n" + "="*80)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Backend extraction and clustering is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Backend needs investigation")
    print("="*80)
    
    return all_tests_passed

def test_courtlistener_integration():
    """Test CourtListener API integration and canonical data retrieval."""
    print(f"\n🔍 COURTLISTENER API INTEGRATION TEST")
    print("-" * 60)
    
    try:
        from src.courtlistener_verification import verify_with_courtlistener
        from src.config import get_config_value
        
        # Get API key from config
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        if not api_key:
            print(f"⚠️  No CourtListener API key found, skipping integration test")
            return True  # Skip test but don't fail
        
        # Test with a known citation
        test_citation = "578 U.S. 5"
        test_case_name = "Luis v. United States"
        
        print(f"Testing citation: {test_citation}")
        print(f"Expected case name: {test_case_name}")
        
        # Call with correct signature (api_key, citation, extracted_case_name)
        result = verify_with_courtlistener(api_key, test_citation, extracted_case_name=test_case_name)
        
        if result and result.get('verified'):
            print(f"✅ CourtListener verification successful")
            print(f"   - Canonical name: {result.get('canonical_name', 'N/A')}")
            print(f"   - Canonical year: {result.get('canonical_date', 'N/A')}")
            print(f"   - Canonical URL: {result.get('canonical_url', 'N/A')}")
            return True
        else:
            print(f"❌ CourtListener verification failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ CourtListener test failed: {e}")
        print(f"   Error details: {str(e)}")
        # Try simpler test without case name
        try:
            print(f"   Trying simpler verification without case name...")
            result = verify_with_courtlistener(api_key, test_citation)
            if result and result.get('verified'):
                print(f"✅ CourtListener verification successful (simple)")
                return True
        except Exception as e2:
            print(f"   Simple verification also failed: {e2}")
        return False

def main():
    """Run all comprehensive backend tests."""
    print("🚀 Starting Comprehensive Backend Test Suite")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Text extraction and clustering
    extraction_passed = test_text_extraction_and_clustering()
    
    # Test 2: CourtListener integration
    courtlistener_passed = test_courtlistener_integration()
    
    # Final summary
    print(f"\n" + "="*80)
    print("🏁 FINAL TEST SUMMARY")
    print("="*80)
    print(f"✅ Text Extraction & Clustering: {'PASSED' if extraction_passed else 'FAILED'}")
    print(f"✅ CourtListener Integration: {'PASSED' if courtlistener_passed else 'FAILED'}")
    
    if extraction_passed and courtlistener_passed:
        print(f"\n🎉 ALL BACKEND TESTS PASSED!")
        print(f"The citation extraction pipeline is working correctly.")
        return True
    else:
        print(f"\n❌ SOME BACKEND TESTS FAILED!")
        print(f"The system needs investigation and fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
