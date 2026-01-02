#!/usr/bin/env python3
"""
Debug test to check if pre-verification is setting source correctly
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import get_master_verifier

def test_preverification_debug():
    """Test if pre-verification sets source correctly."""
    
    print("=" * 60)
    print("TESTING PRE-VERIFICATION SOURCE SETTING")
    print("=" * 60)
    
    # Test citations from Permian Basin case
    citation_texts = ["377 U.S. 33", "382 U.S. 154", "385 U.S. 83"]
    case_names = ["Permian Basin Area Rate Cases v. FPC"] * 3
    case_dates = ["1974"] * 3
    
    # Create citation dicts like the endpoint does
    citations = []
    for i, citation in enumerate(citation_texts):
        citations.append({
            'citation': citation,
            'extracted_case_name': case_names[i],
            'extracted_date': case_dates[i],
            'start_index': i * 20,
            'end_index': i * 20 + 10,
            'method': 'clean_pipeline_v1',
            'confidence': 0.9,
            'metadata': {}
        })
    
    print(f"Testing {len(citations)} citations...")
    print()
    
    try:
        # Get the verifier
        verifier = get_master_verifier()
        
        print("🔥 Running pre-verification...")
        
        # Track timing
        start_time = time.time()
        
        # Run verification (like the endpoint does)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                verifier.verify_citations_batch(citation_texts, case_names, case_dates)
            )
        finally:
            loop.close()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("=" * 60)
        print("PRE-VERIFICATION RESULTS")
        print("=" * 60)
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Total citations: {len(results)}")
        print()
        
        # Apply results to citations (like the endpoint does)
        pre_verified = 0
        for i, r in enumerate(results or []):
            if not isinstance(citations[i], dict):
                continue
            if getattr(r, 'verified', False):
                citations[i]['verified'] = True
                citations[i]['possible_match'] = False
                citations[i]['canonical_name'] = getattr(r, 'canonical_name', None)
                citations[i]['canonical_date'] = getattr(r, 'canonical_date', None)
                citations[i]['canonical_url'] = getattr(r, 'canonical_url', None)
                citations[i]['verification_source'] = getattr(r, 'source', None)
                citations[i]['verification_error'] = None
                pre_verified += 1
            else:
                citations[i]['verified'] = False
                citations[i]['possible_match'] = False
                citations[i]['verification_source'] = getattr(r, 'source', None)
                citations[i]['verification_error'] = getattr(r, 'error', None)
        
        print(f"Pre-verified: {pre_verified}/{len(citations)}")
        print()
        
        # Check what was set in the citations
        print("CITATION DATA AFTER PRE-VERIFICATION:")
        for i, cit_dict in enumerate(citations):
            print(f"Citation {i+1}: {cit_dict['citation']}")
            print(f"  verified: {cit_dict.get('verified', False)}")
            print(f"  verification_source: {cit_dict.get('verification_source', 'NOT SET')}")
            print(f"  canonical_name: {cit_dict.get('canonical_name', 'NOT SET')}")
            print()
        
        # Check if verification_source is set correctly
        sources_set = 0
        for cit_dict in citations:
            if cit_dict.get('verification_source') and cit_dict.get('verification_source') != 'Unknown':
                sources_set += 1
        
        print(f"Sources properly set: {sources_set}/{len(citations)}")
        
        if sources_set > 0:
            print("✅ PRE-VERIFICATION IS WORKING: Sources are being set correctly")
        else:
            print("❌ PRE-VERIFICATION BROKEN: Sources are not being set")
        
        return sources_set > 0
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_preverification_debug()
    sys.exit(0 if success else 1)
