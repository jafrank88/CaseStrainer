#!/usr/bin/env python3
"""
Quick test of D2 59366-1-II content with shorter timeout
"""

import requests
import json

def test_d2_quick():
    """Quick test with shorter timeout"""
    
    # Shorter text sample to avoid timeout
    d2_short_text = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    STATE OF WASHINGTON,
        Respondent,
    v.
    JOHN DOE,
        Appellant.
    
    No. 59366-1-II
    UNPUBLISHED OPINION
    
    The appellant argues that the trial court erred in denying his motion to suppress. 
    We review de novo whether a traffic stop violates the Fourth Amendment. State v. 
    Ladson, 148 Wn.2d 325, 59 P.3d 771 (2002). The State bears the burden of showing that 
    the officer had reasonable suspicion that the appellant was violating the law. 
    State v. Harrington, 167 Wn.2d 656, 260 P.3d 951 (2011).
    
    In State v. Madsen, 168 Wn.2d 496, 229 P.3d 729 (2010), the Supreme Court held that 
    reasonable suspicion exists when an officer observes a traffic violation.
    """
    
    print("🔍 Quick D2 59366-1-II test...")
    print(f"Text length: {len(d2_short_text)} characters")
    
    try:
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        data = {
            "text": d2_short_text,
            "extract_case_names": True
        }
        
        print("📤 Sending quick test...")
        response = requests.post(url, json=data, timeout=60)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📊 Quick Test Results:")
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            if citations:
                print(f"\n📋 Citations found:")
                for i, citation in enumerate(citations):
                    print(f"{i+1}. {citation.get('citation', 'N/A')}")
                    print(f"   Extracted: '{citation.get('extracted_case_name', 'N/A')}', {citation.get('extracted_date', 'N/A')}")
                    print(f"   Verified: {citation.get('verified', False)}")
                    print(f"   Source: {citation.get('verification_source', 'N/A')}")
                
                print(f"\n✅ SUCCESS: Found {len(citations)} citations from D2 59366-1-II content!")
                
                # Check extraction quality
                clean_names = 0
                for citation in citations:
                    name = citation.get('extracted_case_name', '')
                    if name and len(name) < 50 and 'v.' in name:
                        clean_names += 1
                
                print(f"✅ Clean case names: {clean_names}/{len(citations)}")
                
                if clean_names == len(citations):
                    print(f"🎉 PERFECT: All case names extracted cleanly!")
                elif clean_names >= len(citations) * 0.8:
                    print(f"✅ EXCELLENT: High-quality extraction!")
                else:
                    print(f"⚠️ Some case names need improvement")
            
            else:
                print(f"\n❌ No citations found")
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_d2_quick()
