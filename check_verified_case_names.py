#!/usr/bin/env python3
"""
Check verified case names from production API results
"""

import requests
import json

def check_verified_case_names():
    """Check what the production API verified as the correct case names"""
    
    print("🔍 CHECKING VERIFIED CASE NAMES FROM PRODUCTION API")
    print("=" * 55)
    
    # Get the production API results for the problematic URL
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    try:
        print("Getting results from production API...")
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
            
            # Focus on the supposedly contaminated citations
            problematic_citations = [
                "140 Wn.2d 19",
                "992 P.2d 496", 
                "114 Wn. App. 245",
                "57 P.3d 273",
                "129 Wn.2d 652",
                "116 Wn.2d 342",
                "804 P.2d 24"
            ]
            
            print(f"\nAnalyzing problematic citations:")
            print("-" * 40)
            
            for cit in citations:
                citation_text = cit.get('citation', '')
                extracted_name = cit.get('extracted_case_name', 'N/A')
                canonical_name = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                if citation_text in problematic_citations:
                    print(f"\n🔍 {citation_text}:")
                    print(f"   Extracted: '{extracted_name}'")
                    print(f"   Canonical: '{canonical_name}'")
                    print(f"   Verified: {verified}")
                    
                    if verified and canonical_name != 'N/A':
                        # This is the ground truth from verification
                        if "BELLEVUE" in canonical_name.upper() and "LORANG" in canonical_name.upper():
                            print(f"   ✅ VERIFIED: This IS a City of Bellevue v. Lorang case")
                            print(f"   📝 Extraction is CORRECT (no contamination)")
                        elif "BELLEVUE" in canonical_name.upper():
                            print(f"   ⚠️  VERIFIED: This is a Bellevue case but not Lorang")
                            print(f"   🤔 Extraction might be partially correct")
                        else:
                            print(f"   ❌ VERIFIED: This is NOT a Bellevue v. Lorang case")
                            print(f"   💥 Extraction is WRONG (should be '{canonical_name}')")
                    else:
                        print(f"   ⚠️  Not verified - cannot determine correct name")
            
            print(f"\n" + "=" * 55)
            print("📊 ANALYSIS SUMMARY:")
            print("-" * 20)
            
            # Count how many are actually Bellevue v. Lorang cases
            actually_bellevue = 0
            extraction_errors = 0
            
            for cit in citations:
                citation_text = cit.get('citation', '')
                extracted_name = cit.get('extracted_case_name', 'N/A')
                canonical_name = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                if citation_text in problematic_citations:
                    if verified and canonical_name != 'N/A':
                        if "BELLEVUE" in canonical_name.upper() and "LORANG" in canonical_name.upper():
                            actually_bellevue += 1
                        elif "BELLEVUE" not in extracted_name.upper():
                            # Extracted Bellevue but verified as something else
                            extraction_errors += 1
            
            print(f"Citations that are actually Bellevue v. Lorang: {actually_bellevue}")
            print(f"Citations with extraction errors: {extraction_errors}")
            
            if actually_bellevue > 0:
                print(f"\n✅ CONCLUSION: Most 'contaminated' citations are actually")
                print(f"   legitimate City of Bellevue v. Lorang cases.")
                print(f"   The extraction is CORRECT, not contaminated.")
            
            if extraction_errors > 0:
                print(f"\n❌ CONCLUSION: {extraction_errors} citations have wrong case names.")
                print(f"   This is an extraction error, not contamination.")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_verified_case_names()
