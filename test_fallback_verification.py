#!/usr/bin/env python3
"""
Test script to verify fallback citation verification is working correctly.
This tests the scenario where CourtListener fails but fallback methods succeed.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_fallback_verification():
    """Test fallback verification for citations not found in CourtListener."""
    
    print("=== Testing Fallback Citation Verification ===")
    print()
    
    # Test citations that are known to not be in CourtListener
    test_citations = [
        "188 Wn.2d 114",  # In re Marriage of Black
        "392 P.3d 1041",  # In re Marriage of Black (parallel)
        "178 Wn. App. 929",  # In re Vulnerable Adult Petition for Knight
        "317 P.3d 1068",  # In re Vulnerable Adult Petition for Knight (parallel)
    ]
    
    try:
        from citation_verification import verify_citations_with_legal_websearch
        
        print("Testing fallback verification...")
        print()
        
        # Create mock citation objects
        class MockCitation:
            def __init__(self, citation_text, extracted_case_name, extracted_date):
                self.citation = citation_text
                self.extracted_case_name = extracted_case_name
                self.extracted_date = extracted_date
                self.verified = False
                self.source = None
                self.url = None
                self.canonical_name = None
                self.canonical_date = None
        
        # Create test citations with extracted case names
        citations = [
            MockCitation("188 Wn.2d 114", "In re Marriage of Black", "2017"),
            MockCitation("392 P.3d 1041", "In re Marriage of Black", "2017"),
            MockCitation("178 Wn. App. 929", "In re Vulnerable Adult Petition for Knight", "2014"),
            MockCitation("317 P.3d 1068", "In re Vulnerable Adult Petition for Knight", "2014"),
        ]
        
        print(f"Input citations:")
        for citation in citations:
            print(f"  {citation.citation} -> {citation.extracted_case_name} ({citation.extracted_date})")
        print()
        
        # Run verification
        print("Running fallback verification...")
        verified_citations = await verify_citations_with_legal_websearch(citations)
        
        print()
        print("Results:")
        print("=" * 60)
        
        for citation in verified_citations:
            print(f"Citation: {citation.citation}")
            print(f"  Verified: {citation.verified}")
            print(f"  Source: {citation.source}")
            print(f"  Extracted: {citation.extracted_case_name} ({citation.extracted_date})")
            print(f"  Canonical: {citation.canonical_name} ({citation.canonical_date})")
            print(f"  URL: {citation.url}")
            print()
        
        # Summary
        verified_count = sum(1 for c in verified_citations if c.verified)
        with_canonical = sum(1 for c in verified_citations if c.verified and c.canonical_name)
        
        print("Summary:")
        print(f"  Total citations: {len(citations)}")
        print(f"  Verified: {verified_count}")
        print(f"  With canonical names: {with_canonical}")
        print(f"  Success rate: {verified_count/len(citations)*100:.1f}%")
        print(f"  Canonical data rate: {with_canonical/verified_count*100:.1f}%" if verified_count > 0 else "  Canonical data rate: N/A")
        
        if with_canonical == verified_count and verified_count > 0:
            print("✅ SUCCESS: All verified citations have canonical names!")
        elif verified_count > 0:
            print("⚠️  PARTIAL: Some verified citations missing canonical names")
        else:
            print("❌ FAILURE: No citations were verified")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback_verification())
