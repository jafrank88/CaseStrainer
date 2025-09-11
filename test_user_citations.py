#!/usr/bin/env python3
"""
Test the specific citations from the user's API response
"""

import requests
import json

def test_user_citations():
    # Based on the API response, this text likely contains the citations:
    # 183 Wn.2d 649, 192 Wn.2d 453, 355 P.3d 258, 430 P.3d 655
    
    # Let me try to reconstruct the text that would produce these citations
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010). We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999). Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015). Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)."""
    
    print("Testing with reconstructed text that should contain the user's citations...")
    print(f"Text length: {len(test_text)}")
    print()
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze',
                               json={'text': test_text, 'type': 'text'},
                               timeout=30)

        if response.status_code == 200:
            data = response.json()
            print('API Response Status: 200')
            print(f'Citations found: {len(data.get("citations", []))}')
            print(f'Clusters: {len(data.get("clusters", []))}')
            
            print('\nCitations from result:')
            result_citations = data.get('result', {}).get('citations', [])
            for i, citation in enumerate(result_citations, 1):
                print(f'  {i}. {citation.get("citation", "N/A")} -> {citation.get("extracted_case_name", "N/A")}')
            
            print('\nClusters:')
            clusters = data.get('result', {}).get('clusters', [])
            for i, cluster in enumerate(clusters, 1):
                print(f'  {i}. {cluster.get("extracted_case_name", "N/A")} ({cluster.get("size", 0)} citations)')
                for cit in cluster.get('citations', []):
                    print(f'     - {cit}')
            
            # Check contamination
            contamination = data.get('result', {}).get('data_separation_validation', {})
            print(f'\nContamination: {contamination.get("contamination_detected", False)} ({contamination.get("contamination_rate", 0)})')
            
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
    except Exception as e:
        print(f'Error calling API: {e}')

if __name__ == "__main__":
    test_user_citations()

