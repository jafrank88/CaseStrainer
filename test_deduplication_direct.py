"""
Test Deduplication Logic Directly
Tests the deduplication function in isolation to verify it works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from citation_deduplication import deduplicate_citations

def test_deduplication_direct():
    """Test deduplication logic directly with sample data."""
    
    print("🔍 TESTING DEDUPLICATION LOGIC DIRECTLY")
    print("=" * 50)
    
    # Sample citations with duplicates (similar to API response format)
    test_citations = [
        {
            "citation": "150 Wn.2d 674",
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "confidence": 0.9
        },
        {
            "citation": "150 Wn.2d 674",  # Exact duplicate
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "confidence": 0.9
        },
        {
            "citation": "80 P.3d 598",
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "confidence": 0.9
        },
        {
            "citation": "80 P.3d 598",  # Another exact duplicate
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "confidence": 0.9
        },
        {
            "citation": "159 Wn.2d 700",
            "case_name": "Bostain v. Food Express",
            "extracted_case_name": "Bostain v. Food Express",
            "confidence": 0.9
        }
    ]
    
    print(f"📝 Input citations: {len(test_citations)}")
    for i, citation in enumerate(test_citations, 1):
        print(f"   {i}. {citation['citation']} - {citation['case_name']}")
    
    print(f"\n🔄 Running deduplication...")
    
    try:
        deduplicated = deduplicate_citations(test_citations, debug=True)
        
        print(f"\n✅ Deduplication completed!")
        print(f"📊 Results:")
        print(f"   Original count: {len(test_citations)}")
        print(f"   Deduplicated count: {len(deduplicated)}")
        print(f"   Removed: {len(test_citations) - len(deduplicated)} duplicates")
        
        print(f"\n📋 Final citations:")
        for i, citation in enumerate(deduplicated, 1):
            print(f"   {i}. {citation['citation']} - {citation['case_name']}")
        
        # Verify no duplicates remain
        citation_texts = [c.get('citation', '') for c in deduplicated]
        unique_citations = set(citation_texts)
        
        if len(citation_texts) == len(unique_citations):
            print(f"\n✅ SUCCESS: No duplicates remain!")
        else:
            print(f"\n❌ FAILURE: Duplicates still present!")
            from collections import Counter
            counts = Counter(citation_texts)
            for citation, count in counts.items():
                if count > 1:
                    print(f"      '{citation}' appears {count} times")
        
    except Exception as e:
        print(f"❌ Error in deduplication: {e}")
        import traceback
        traceback.print_exc()

def test_deduplication_with_api_data():
    """Test with actual API response data format."""
    
    print(f"\n🔍 TESTING WITH API RESPONSE FORMAT")
    print("=" * 40)
    
    # Simulate actual API response format
    api_citations = [
        {
            "canonical_date": "2003",
            "canonical_name": "Restaurant Development, Inc. v. Cananwill, Inc.",
            "canonical_url": "https://www.courtlistener.com/opinion/4908272/restaurant-development-inc-v-cananwill-inc/",
            "case_name": "Inc. v. Cananwill",
            "citation": "150 Wn.2d\n674",  # Note: newline in citation
            "confidence": 0.9,
            "extracted_case_name": "Inc. v. Cananwill",
            "verified": True
        },
        {
            "canonical_date": "2003",
            "canonical_name": "Restaurant Development, Inc. v. Cananwill, Inc.",
            "canonical_url": "https://www.courtlistener.com/opinion/4908272/restaurant-development-inc-v-cananwill-inc/",
            "case_name": "Inc. v. Cananwill",
            "citation": "150 \nWn.2d 674",  # Different newline position - should be detected as duplicate
            "confidence": 0.9,
            "extracted_case_name": "Inc. v. Cananwill",
            "verified": True
        },
        {
            "canonical_date": "2003",
            "canonical_name": "Restaurant Development, Inc. v. Cananwill, Inc.",
            "canonical_url": "https://www.courtlistener.com/opinion/2538609/restaurant-development-inc-v-cananwill-inc/",
            "case_name": "Inc. v. Cananwill",
            "citation": "80 P.3d 598",
            "confidence": 0.9,
            "extracted_case_name": "Inc. v. Cananwill",
            "verified": True
        }
    ]
    
    print(f"📝 API format citations: {len(api_citations)}")
    for i, citation in enumerate(api_citations, 1):
        print(f"   {i}. '{citation['citation']}' - {citation['case_name']}")
    
    try:
        deduplicated = deduplicate_citations(api_citations, debug=True)
        
        print(f"\n📊 API Format Results:")
        print(f"   Original count: {len(api_citations)}")
        print(f"   Deduplicated count: {len(deduplicated)}")
        print(f"   Removed: {len(api_citations) - len(deduplicated)} duplicates")
        
        print(f"\n📋 Final API citations:")
        for i, citation in enumerate(deduplicated, 1):
            print(f"   {i}. '{citation['citation']}' - {citation['case_name']}")
        
    except Exception as e:
        print(f"❌ Error in API format deduplication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deduplication_direct()
    test_deduplication_with_api_data()
