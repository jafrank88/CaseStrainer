#!/usr/bin/env python3
"""
Test script to verify both citation extraction fix AND verification improvements
"""

import sys
import os
sys.path.append('src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
import asyncio

async def test_citation_extraction_and_verification():
    """Test both citation extraction and verification with the problematic paragraph"""
    
    # The test paragraph that should have 6 citations
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("🧪 Testing Citation Extraction AND Verification Fixes")
    print("=" * 60)
    print(f"Test text length: {len(test_text)} characters")
    print()
    
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    # Test 1: Citation Extraction (should find all 6)
    print("🔍 TEST 1: Citation Extraction")
    print("-" * 30)
    citations = processor._extract_with_regex(test_text)
    print(f"Total citations found: {len(citations)}")
    
    # Expected citations
    expected_citations = [
        "178 Wn. App. 929",
        "317 P.3d 1068", 
        "188 Wn.2d 114",
        "392 P.3d 1041",
        "155 Wn. App. 715",
        "230 P.3d 233"
    ]
    
    print(f"\n📋 Expected citations: {len(expected_citations)}")
    for i, citation in enumerate(expected_citations, 1):
        print(f"  {i}. {citation}")
    
    print(f"\n✅ Found citations: {len(citations)}")
    found_citations = []
    for i, citation in enumerate(citations, 1):
        citation_text = citation.citation
        found_citations.append(citation_text)
        print(f"  {i}. {citation_text} (pattern: {citation.pattern})")
    
    # Check extraction success
    missing = [c for c in expected_citations if c not in found_citations]
    extraction_success = len(missing) == 0
    
    if extraction_success:
        print(f"\n✅ EXTRACTION SUCCESS: All {len(expected_citations)} citations found!")
    else:
        print(f"\n❌ EXTRACTION FAILED: Missing {len(missing)} citations: {missing}")
    
    print(f"\n📈 Extraction success rate: {len([c for c in expected_citations if c in found_citations])}/{len(expected_citations)} = {(len([c for c in expected_citations if c in found_citations])/len(expected_citations)*100):.1f}%")
    
    # Test 2: Full Pipeline with Verification (should improve verification rate)
    print(f"\n🔍 TEST 2: Full Pipeline with Verification")
    print("-" * 40)
    
    try:
        print("Running full processing pipeline with verification enabled...")
        results = await processor.process_text(test_text)
        
        print(f"\n📊 Pipeline Results:")
        print(f"Citations processed: {len(results['citations'])}")
        print(f"Clusters created: {len(results['clusters'])}")
        
        # Check verification status
        verified_citations = [c for c in results['citations'] if getattr(c, 'verified', False)]
        unverified_citations = [c for c in results['citations'] if not getattr(c, 'verified', False)]
        
        print(f"\n🔍 Verification Results:")
        print(f"Verified citations: {len(verified_citations)}")
        print(f"Unverified citations: {len(unverified_citations)}")
        
        if verified_citations:
            print(f"\n✅ Verified citations:")
            for citation in verified_citations:
                print(f"  - {citation.citation} (source: {getattr(citation, 'source', 'unknown')})")
        
        if unverified_citations:
            print(f"\n❌ Unverified citations:")
            for citation in unverified_citations:
                print(f"  - {citation.citation}")
        
        # Check if verification improved from the previous 0% rate
        verification_rate = len(verified_citations) / len(results['citations']) * 100
        print(f"\n📈 Verification success rate: {verification_rate:.1f}%")
        
        # Check if we have any canonical data
        citations_with_canonical = [c for c in results['citations'] if getattr(c, 'canonical_name', None) or getattr(c, 'canonical_date', None)]
        print(f"Citations with canonical data: {len(citations_with_canonical)}")
        
        verification_success = verification_rate > 0  # Any improvement over 0%
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        verification_success = False
    
    # Overall test results
    print(f"\n" + "=" * 60)
    print("📊 OVERALL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Citation Extraction: {'PASS' if extraction_success else 'FAIL'}")
    print(f"✅ Verification Pipeline: {'PASS' if verification_success else 'FAIL'}")
    
    overall_success = extraction_success and verification_success
    print(f"\n🎯 Overall Test Result: {'PASS' if overall_success else 'FAIL'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(test_citation_extraction_and_verification())
    sys.exit(0 if success else 1)
