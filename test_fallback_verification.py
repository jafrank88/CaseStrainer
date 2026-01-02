#!/usr/bin/env python3
"""
Test Law Resource.org through the fallback verification pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import UnifiedVerificationMaster

async def test_fallback_verification():
    """Test Law Resource.org through fallback verification"""
    
    print("🧪 Testing Law Resource.org through fallback verification...")
    
    # Initialize the verification master
    verifier = UnifiedVerificationMaster()
    
    # Create a citation that should fail initial verification and trigger fallback
    test_citation = {
        'citation': '161 F.3d 584',
        'case_name': 'In Smith v. Jones',
        'extracted_case_name': 'In Smith v. Jones',
        'extracted_date': None,
        'canonical_name': None,
        'canonical_date': None,
        'canonical_url': None,
        'verified': False,
        'url': None,
        'court': None,
        'docket_number': None,
        'confidence': 0.9,
        'method': 'clean_pipeline_v1',
        'pattern': '',
        'context': '',
        'start_index': 19,
        'end_index': 31,
        'is_parallel': False,
        'is_cluster': False,
        'parallel_citations': [],
        'cluster_members': [],
        'pinpoint_pages': [],
        'docket_numbers': [],
        'case_history': [],
        'publication_status': None,
        'source': 'Unknown',
        'error': None,
        'metadata': {'detector': 'eyecite', 'type': 'FullCaseCitation', 'eyecite_extracted': True},
        'cluster_id': None,
        'true_by_parallel': False,
        'is_verified': False,
        'name_mismatch': False,
        'date_mismatch': False,
        'mismatch_confidence': 0.0,
        'possible_match': False,
        'processing_trace_id': 'test123',
        'processing_stages': ['extraction', 'verification', 'formatting', 'completed'],
        'cluster_year': None,
        'cluster_size': 1,
        'is_in_cluster': False
    }
    
    print(f"📋 Citation: {test_citation['citation']}")
    print(f"👥 Case name: {test_citation['extracted_case_name']}")
    
    try:
        # Call the enhanced fallback verification directly
        print("\n🔍 Calling enhanced fallback verification...")
        result = await verifier._verify_with_enhanced_fallback(
            test_citation['citation'],
            test_citation['extracted_case_name'],
            test_citation['extracted_date'],
            remaining_timeout=30.0
        )
        
        print(f"\n📊 Fallback Verification Result:")
        print(f"   Verified: {result.verified}")
        print(f"   Source: {result.source}")
        print(f"   Canonical Name: {result.canonical_name}")
        print(f"   Canonical URL: {result.canonical_url}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Method: {result.method}")
        print(f"   Error: {result.error}")
        
        if result.verified and "Law Resource.org" in result.source:
            print(f"\n✅ SUCCESS: Law Resource.org verification works through fallback!")
            return True
        elif result.verified:
            print(f"\n⚠️  SUCCESS: Citation verified but via different source: {result.source}")
            return True
        else:
            print(f"\n❌ FAILURE: Fallback verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during fallback verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_fallback_verification())
    
    if success:
        print("\n✅ Fallback verification is working!")
    else:
        print("\n❌ Fallback verification has issues")
