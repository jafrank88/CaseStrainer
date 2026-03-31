#!/usr/bin/env python3
"""
Check what the correct case names should be for the supposedly contaminated citations
"""

import sys
import os
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_correct_case_names():
    """Check correct case names via verification"""
    
    print("🔍 CHECKING CORRECT CASE NAMES FOR PROBLEMATIC CITATIONS")
    print("=" * 65)
    
    # The citations that are getting "City of Bellevue v. Lorang" 
    problematic_citations = [
        "140 Wn.2d 19",
        "992 P.2d 496", 
        "114 Wn. App. 245",
        "57 P.3d 273",
        "129 Wn.2d 652",
        "116 Wn.2d 342",
        "804 P.2d 24"
    ]
    
    from src.citation_verifier import CitationVerifier
    
    verifier = CitationVerifier()
    
    print("Verifying correct case names:")
    print("-" * 40)
    
    for citation in problematic_citations:
        try:
            print(f"\n🔍 {citation}:")
            
            # Try to verify via CourtListener
            result = verifier.verify_citation(citation)
            
            if result and result.verified:
                correct_name = result.canonical_name
                print(f"   ✅ Verified: {correct_name}")
                
                # Check if it's actually "City of Bellevue v. Lorang"
                if "BELLEVUE" in correct_name.upper() and "LORANG" in correct_name.upper():
                    print(f"   📝 This IS actually a City of Bellevue v. Lorang case!")
                else:
                    print(f"   ❌ This is NOT City of Bellevue v. Lorang")
                    print(f"   💡 Current extraction is WRONG")
            else:
                print(f"   ⚠️  Verification failed")
                
                # Try a simple web search to see what we can find
                try:
                    search_url = f"https://www.courtlistener.com/?q={citation}"
                    response = requests.get(search_url, timeout=10)
                    if response.status_code == 200:
                        # Simple text search for case name patterns
                        content = response.text
                        import re
                        
                        # Look for case name patterns in the search results
                        patterns = [
                            r'v\.\s+[^,<(]+',
                            r'>[^<]+v\.\s+[^<]+',
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                print(f"   🔍 Possible matches: {matches[:3]}")
                                break
                                
                except Exception as e:
                    print(f"   ❌ Search failed: {e}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n" + "=" * 65)
    print("📊 ANALYSIS:")
    print("-" * 20)
    print("If these citations are actually 'City of Bellevue v. Lorang' cases,")
    print("then the extraction is CORRECT and there's no contamination.")
    print("If they're different cases, then the extraction is WRONG.")

if __name__ == "__main__":
    check_correct_case_names()
