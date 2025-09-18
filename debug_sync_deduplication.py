"""
Debug Sync Deduplication Issue
Investigates why we still have 1 duplicate in sync processing.
"""

import requests
import json

def debug_sync_deduplication():
    """Debug the sync deduplication issue in detail."""
    
    print("🔍 DEBUGGING SYNC DEDUPLICATION ISSUE")
    print("=" * 45)
    
    # Use the original problematic text
    test_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one 
reasonable interpretation after this inquiry, it is ambiguous, and we may consider 
extratextual materials to help determine legislative intent, including legislative 
history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases)."""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🌐 Sending request...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            processing_strategy = result.get('result', {}).get('metadata', {}).get('processing_strategy', 'unknown')
            
            print(f"✅ Response received")
            print(f"   Processing strategy: {processing_strategy}")
            print(f"   Total citations: {len(citations)}")
            
            # Analyze all citations in detail
            print(f"\n📋 DETAILED CITATION ANALYSIS:")
            print("-" * 40)
            
            citation_analysis = {}
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                case_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                verified = citation.get('verified', False)
                confidence = citation.get('confidence', 0)
                method = citation.get('method', '')
                
                print(f"{i:2d}. Citation: '{citation_text}'")
                print(f"     Case name: {case_name}")
                print(f"     Canonical: {canonical_name}")
                print(f"     Verified: {verified}")
                print(f"     Confidence: {confidence}")
                print(f"     Method: {method}")
                
                # Track for duplicate analysis
                if citation_text not in citation_analysis:
                    citation_analysis[citation_text] = []
                citation_analysis[citation_text].append({
                    'index': i,
                    'case_name': case_name,
                    'canonical_name': canonical_name,
                    'verified': verified,
                    'confidence': confidence,
                    'method': method
                })
                print()
            
            # Identify duplicates
            print(f"🔍 DUPLICATE ANALYSIS:")
            print("-" * 25)
            
            duplicates_found = False
            for citation_text, instances in citation_analysis.items():
                if len(instances) > 1:
                    duplicates_found = True
                    print(f"❌ DUPLICATE: '{citation_text}' appears {len(instances)} times")
                    
                    for j, instance in enumerate(instances, 1):
                        print(f"   Instance {j}:")
                        print(f"      Position: #{instance['index']}")
                        print(f"      Case name: {instance['case_name']}")
                        print(f"      Canonical: {instance['canonical_name']}")
                        print(f"      Verified: {instance['verified']}")
                        print(f"      Confidence: {instance['confidence']}")
                        print(f"      Method: {instance['method']}")
                    
                    # Analyze why they're different
                    print(f"   🔍 Difference analysis:")
                    verified_states = [inst['verified'] for inst in instances]
                    canonical_states = [inst['canonical_name'] for inst in instances]
                    
                    if len(set(verified_states)) > 1:
                        print(f"      ⚠️  Different verification states: {verified_states}")
                    if len(set(canonical_states)) > 1:
                        print(f"      ⚠️  Different canonical names: {canonical_states}")
                    
                    print()
            
            if not duplicates_found:
                print(f"✅ No duplicates found!")
            
            # Check if deduplication was supposed to run
            print(f"🔧 DEDUPLICATION CHECK:")
            print("-" * 25)
            
            if processing_strategy == 'full_with_verification':
                print(f"   Processing strategy suggests deduplication should have run")
                print(f"   This indicates a potential issue in the deduplication logic")
            else:
                print(f"   Processing strategy: {processing_strategy}")
                print(f"   This might not trigger deduplication")
            
            return duplicates_found
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return True  # Assume failure
            
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        return True  # Assume failure

def test_deduplication_module_directly():
    """Test the deduplication module directly with the problematic data."""
    
    print(f"\n🧪 TESTING DEDUPLICATION MODULE DIRECTLY")
    print("-" * 45)
    
    # Create test data that mimics the duplicate issue
    test_citations = [
        {
            "citation": "80 P.3d 598",
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "canonical_name": "Restaurant Development, Inc. v. Cananwill, Inc.",
            "verified": True,
            "confidence": 0.9,
            "method": "unified_processor"
        },
        {
            "citation": "80 P.3d 598",  # Exact duplicate
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "canonical_name": None,  # Different canonical state
            "verified": False,       # Different verification state
            "confidence": 0.9,
            "method": "unified_processor"
        },
        {
            "citation": "150 Wn.2d 674",
            "case_name": "Inc. v. Cananwill",
            "extracted_case_name": "Inc. v. Cananwill",
            "canonical_name": "Restaurant Development, Inc. v. Cananwill, Inc.",
            "verified": True,
            "confidence": 0.9,
            "method": "unified_processor"
        }
    ]
    
    print(f"📝 Input citations: {len(test_citations)}")
    for i, cit in enumerate(test_citations, 1):
        print(f"   {i}. {cit['citation']} - Verified: {cit['verified']}, Canonical: {cit['canonical_name'] is not None}")
    
    try:
        from src.citation_deduplication import deduplicate_citations
        
        print(f"\n🔄 Running deduplication...")
        deduplicated = deduplicate_citations(test_citations, debug=True)
        
        print(f"\n📊 Results:")
        print(f"   Original: {len(test_citations)} citations")
        print(f"   Deduplicated: {len(deduplicated)} citations")
        print(f"   Removed: {len(test_citations) - len(deduplicated)} duplicates")
        
        print(f"\n📋 Final citations:")
        for i, cit in enumerate(deduplicated, 1):
            print(f"   {i}. {cit['citation']} - Verified: {cit['verified']}, Canonical: {cit['canonical_name'] is not None}")
        
        # Check if the duplicate was removed
        citation_texts = [c['citation'] for c in deduplicated]
        unique_texts = set(citation_texts)
        
        if len(citation_texts) == len(unique_texts):
            print(f"\n✅ DEDUPLICATION MODULE WORKING CORRECTLY!")
            return True
        else:
            print(f"\n❌ DEDUPLICATION MODULE FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing deduplication module: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive sync deduplication debug."""
    
    print("🎯 SYNC DEDUPLICATION DEBUG")
    print("=" * 30)
    
    # Test the deduplication module directly first
    module_works = test_deduplication_module_directly()
    
    # Test the actual API
    api_has_duplicates = debug_sync_deduplication()
    
    print(f"\n📊 SUMMARY")
    print("=" * 15)
    print(f"✅ Deduplication module: {'WORKING' if module_works else 'FAILED'}")
    print(f"✅ API deduplication: {'FAILED' if api_has_duplicates else 'WORKING'}")
    
    if module_works and api_has_duplicates:
        print(f"\n🔍 CONCLUSION: Deduplication module works, but not being applied in API")
        print(f"   This suggests the deduplication call is missing or not being reached")
    elif not module_works:
        print(f"\n🔍 CONCLUSION: Deduplication module itself has issues")
    else:
        print(f"\n🎉 CONCLUSION: Everything is working correctly!")

if __name__ == "__main__":
    main()
