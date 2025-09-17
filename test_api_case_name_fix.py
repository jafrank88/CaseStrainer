"""
Test API Case Name Fix
Tests the actual API with the improved case name extraction.
"""

import requests
import json

def test_api_case_name_extraction():
    """Test the API with the problematic text to see if case names are now extracted correctly."""
    
    print("🔍 TESTING API CASE NAME EXTRACTION FIX")
    print("=" * 50)
    
    # Your actual problematic text
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
    
    print(f"📝 Testing text length: {len(test_text)} characters")
    print(f"🌐 Sending request to: {url}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"✅ API Response received")
            print(f"📊 Citations found: {len(citations)}")
            print()
            
            # Expected improvements
            expected_fixes = {
                "559 P.3d 545": "Lucid Grp. USA, Inc. v. Dep't of Licensing",
                "150 Wn.2d 674": "Rest. Dev., Inc. v. Cananwill, Inc.",
                "80 P.3d 598": "Rest. Dev., Inc. v. Cananwill, Inc.",
                "173 Wn.2d 296": "Five Corners Fam. Farmers v. State",
                "268 P.3d 892": "Five Corners Fam. Farmers v. State",
                "159 Wn.2d 700": "Bostain v. Food Express, Inc.",
                "153 P.3d 846": "Bostain v. Food Express, Inc."
            }
            
            print("🔍 CASE NAME EXTRACTION ANALYSIS:")
            print("-" * 40)
            
            improvements = 0
            total_tested = 0
            
            for citation in citations:
                citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                extracted_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                
                if citation_text in expected_fixes:
                    total_tested += 1
                    expected_name = expected_fixes[citation_text]
                    
                    print(f"Citation: {citation_text}")
                    print(f"  Before Fix: Inc. v. [truncated]")
                    print(f"  After Fix:  {extracted_name}")
                    print(f"  Expected:   {expected_name}")
                    print(f"  Canonical:  {canonical_name}")
                    
                    # Check if the extraction improved
                    if expected_name.lower() in extracted_name.lower() or extracted_name.lower() in expected_name.lower():
                        if len(extracted_name) > 15:  # More than just "Inc. v. Something"
                            print(f"  ✅ IMPROVED! (Complete case name extracted)")
                            improvements += 1
                        else:
                            print(f"  ⚠️  PARTIAL (Still truncated)")
                    else:
                        print(f"  ❌ NO IMPROVEMENT")
                    
                    print()
            
            print(f"📈 IMPROVEMENT SUMMARY:")
            print(f"   Total tested: {total_tested}")
            print(f"   Improved: {improvements}")
            print(f"   Success rate: {(improvements/total_tested*100):.1f}%" if total_tested > 0 else "N/A")
            print()
            
            # Check for duplicates (should be reduced with deduplication)
            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
            unique_citations = set(citation_texts)
            duplicates = len(citation_texts) - len(unique_citations)
            
            print(f"🔄 DEDUPLICATION CHECK:")
            print(f"   Total citations: {len(citation_texts)}")
            print(f"   Unique citations: {len(unique_citations)}")
            print(f"   Duplicates: {duplicates}")
            
            if duplicates == 0:
                print(f"   ✅ NO DUPLICATES (Deduplication working!)")
            else:
                print(f"   ⚠️  {duplicates} duplicates found")
                # Show which citations are duplicated
                from collections import Counter
                counts = Counter(citation_texts)
                for citation, count in counts.items():
                    if count > 1:
                        print(f"      '{citation}' appears {count} times")
            
        else:
            print(f"❌ API request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api_case_name_extraction()
