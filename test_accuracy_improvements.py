#!/usr/bin/env python3
"""
Test the accuracy improvements to case name extraction
"""

import sys
import os
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_accuracy_improvements():
    """Test the accuracy improvements with production data"""
    
    print("🔍 TESTING CASE NAME EXTRACTION ACCURACY IMPROVEMENTS")
    print("=" * 60)
    
    # Test the problematic PDF URL
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    try:
        print("Testing improved extraction with production API...")
        response = requests.post(
            api_url,
            json={"url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} total citations")
            
            # Analyze improvements
            print(f"\n📊 ANALYZING ACCURACY IMPROVEMENTS:")
            print("-" * 40)
            
            improved = 0
            same = 0
            regressed = 0
            
            # Focus on the previously problematic citations
            target_citations = [
                "146 Wn.2d 1",      # Dep't → Department
                "119 Wn. App. 886",  # Indus. → Industries  
                "116 Wn.2d 342",     # Missing "City of"
                "804 P.2d 24",       # Missing "City of"
                "114 Wn. App. 245",  # Major error test
                "57 P.3d 273",       # Major error test
                "129 Wn.2d 652",     # Major error test
            ]
            
            print(f"\n🎯 TARGETED IMPROVEMENTS:")
            print("-" * 30)
            
            for cit in citations:
                citation_text = cit.get('citation', '')
                extracted = cit.get('extracted_case_name', 'N/A')
                canonical = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                if citation_text in target_citations:
                    print(f"\n🔍 {citation_text}:")
                    print(f"   Extracted: '{extracted}'")
                    print(f"   Canonical: '{canonical}'")
                    print(f"   Verified: {verified}")
                    
                    # Check for specific improvements
                    if citation_text in ["146 Wn.2d 1", "119 Wn. App. 886"]:
                        # Should see abbreviation expansion
                        if "Department" in extracted and "Dep't" not in extracted:
                            print(f"   ✅ ABBREVIATION EXPANSION WORKING")
                            improved += 1
                        elif "Industries" in extracted and "Indus." not in extracted:
                            print(f"   ✅ ABBREVIATION EXPANSION WORKING")
                            improved += 1
                        else:
                            print(f"   ⚠️  Abbreviation expansion not applied")
                            same += 1
                    
                    elif citation_text in ["116 Wn.2d 342", "804 P.2d 24"]:
                        # Should see missing words added
                        if "City of Bellevue" in extracted:
                            print(f"   ✅ MISSING WORDS DETECTION WORKING")
                            improved += 1
                        else:
                            print(f"   ⚠️  Missing words not added")
                            same += 1
                    
                    elif citation_text in ["114 Wn. App. 245", "57 P.3d 273", "129 Wn.2d 652"]:
                        # Major errors - check if still wrong
                        if "City of Bellevue v. Lorang" in extracted and "Berst" in canonical:
                            print(f"   ❌ MAJOR ERROR STILL PRESENT")
                            regressed += 1
                        elif "City of Bellevue v. Lorang" in extracted and "Manussier" in canonical:
                            print(f"   ❌ MAJOR ERROR STILL PRESENT")
                            regressed += 1
                        else:
                            print(f"   ✅ MAJOR ERROR FIXED")
                            improved += 1
            
            # Calculate overall accuracy
            total_verified = sum(1 for cit in citations if cit.get('verified', False) and cit.get('canonical_name') != 'N/A')
            exact_matches = 0
            
            for cit in citations:
                extracted = cit.get('extracted_case_name', 'N/A')
                canonical = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                if verified and canonical != 'N/A' and extracted != 'N/A':
                    # Normalize for comparison (ignore case, spacing, punctuation)
                    extracted_clean = re.sub(r'[^\w\s]', '', extracted.lower())
                    canonical_clean = re.sub(r'[^\w\s]', '', canonical.lower())
                    
                    if extracted_clean == canonical_clean:
                        exact_matches += 1
            
            accuracy = (exact_matches / total_verified * 100) if total_verified > 0 else 0
            
            print(f"\n📈 ACCURACY SUMMARY:")
            print("-" * 20)
            print(f"✅ Improved citations: {improved}")
            print(f"⚠️  Same citations: {same}")
            print(f"❌ Regressed citations: {regressed}")
            print(f"🎯 Overall accuracy: {accuracy:.1f}% ({exact_matches}/{total_verified})")
            
            # Overall assessment
            print(f"\n🎯 OVERALL ASSESSMENT:")
            print("-" * 25)
            
            if accuracy >= 80:
                print("🎉 EXCELLENT: High accuracy achieved!")
            elif accuracy >= 60:
                print("✅ GOOD: Significant improvement made!")
            elif accuracy >= 40:
                print("⚠️  MODERATE: Some improvement, more work needed")
            else:
                print("❌ NEEDS WORK: Limited improvement")
            
            print(f"\n📋 NEXT STEPS:")
            print("-" * 15)
            if regressed > 0:
                print("1. Fix remaining major errors (context boundary issues)")
            if same > 0:
                print("2. Refine abbreviation detection patterns")
            print("3. Test with more diverse documents")
            print("4. Consider adding more abbreviation mappings")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import re
    test_accuracy_improvements()
