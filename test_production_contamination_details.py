#!/usr/bin/env python3
"""
Show detailed contamination results for the URL processing
"""

import requests
import json

def test_production_contamination_details():
    """Show which citations still have contamination"""
    
    print("🔍 PRODUCTION CONTAMINATION DETAILS")
    print("=" * 50)
    
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    try:
        response = requests.post(
            api_url,
            json={"url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            contaminated = []
            clean = []
            
            for cit in citations:
                citation_text = cit.get('citation', 'N/A')
                case_name = cit.get('extracted_case_name', 'N/A')
                
                if 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper():
                    contaminated.append((citation_text, case_name))
                else:
                    clean.append((citation_text, case_name))
            
            print(f"Total citations: {len(citations)}")
            print(f"Contaminated: {len(contaminated)}")
            print(f"Clean: {len(clean)}")
            print()
            
            if contaminated:
                print("❌ CONTAMINATED CITATIONS:")
                for i, (citation, case_name) in enumerate(contaminated, 1):
                    print(f"  {i}. {citation} → '{case_name}'")
                print()
            
            print("✅ SAMPLE CLEAN CITATIONS:")
            for i, (citation, case_name) in enumerate(clean[:5], 1):
                print(f"  {i}. {citation} → '{case_name}'")
            
            if len(clean) > 5:
                print(f"  ... and {len(clean) - 5} more clean citations")
            
            print()
            if len(contaminated) == 0:
                print("🎉 PERFECT! No contamination detected!")
            elif len(contaminated) < len(citations) * 0.2:  # Less than 20% contaminated
                print(f"✅ GOOD! Only {len(contaminated)}/{len(citations)} ({len(contaminated)/len(citations)*100:.1f}%) have contamination")
            else:
                print(f"⚠️  NEEDS WORK: {len(contaminated)}/{len(citations)} ({len(contaminated)/len(citations)*100:.1f}%) have contamination")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_contamination_details()
