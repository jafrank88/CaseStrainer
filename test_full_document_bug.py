#!/usr/bin/env python3

import requests
import json

def test_full_document_bug():
    """Test with the full document to reproduce the 9 P.3d 655 phantom citation."""
    
    # Your complete text
    full_text = '''Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).

"Where the legislature provides no statutory definition and a court gives a term its plain and ordinary meaning by reference to a dictionary, the court 'will avoid literal reading of a statute which would result in unlikely, absurd, or strained consequences.'" Tingey v. Haisch, 159 Wn.2d 652, 663-64, 152 P.3d 1020 (2007) (quoting Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002)). "[I]t will not be presumed that the legislature intended absurd results." State v. Delgado, 148 Wn.2d 723, 733, 63 P.3d 792 (2003) (Madsen, J., dissenting) (citing State v. Vela, 100 Wn.2d 636, 641, 673 P.2d 185 (1983))

Total Wine argues that plaintiffs' interpretation of "job applicant" leads to absurd consequences. "Where the legislature provides no statutory definition and a court gives a term its plain and ordinary meaning by reference to a dictionary, the court 'will avoid literal reading of a statute which would result in unlikely, absurd, or strained consequences.'" Tingey v. Haisch, 159 Wn.2d 652, 663-64, 152 P.3d 1020 (2007) (quoting Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002)). We do not presume that the legislature intends absurd results. State v. J.P., 149 Wn.2d 444, 450, 69 P.3d 318 (2003) (quoting State v. Delgado, 148 Wn.2d 723, 733, 63 P.3d 792 (2003) (Madsen, J., dissenting))'''
    
    print("FULL DOCUMENT BUG TEST")
    print("=" * 50)
    print("Testing with complete document...")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": full_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations")
            print()
            
            # Look specifically for the phantom citation
            phantom_found = False
            correct_found = False
            
            print("SEARCHING FOR PHANTOM CITATION:")
            for citation in citations:
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                
                if citation_text == "9 P.3d 655":
                    phantom_found = True
                    print(f"🚨 PHANTOM FOUND: {citation_text}")
                    print(f"   Case: {case_name}")
                    print(f"   Start Index: {citation.get('start_index', 'N/A')}")
                    print(f"   End Index: {citation.get('end_index', 'N/A')}")
                    print(f"   Context: {citation.get('context', 'N/A')}")
                    print()
                elif citation_text == "59 P.3d 655":
                    correct_found = True
                    print(f"✅ CORRECT FOUND: {citation_text}")
                    print(f"   Case: {case_name}")
                    print()
            
            if not phantom_found and not correct_found:
                print("❓ Neither '9 P.3d 655' nor '59 P.3d 655' found")
            elif phantom_found and correct_found:
                print("🤔 BOTH phantom and correct citations found")
            elif phantom_found and not correct_found:
                print("🚨 PHANTOM ONLY: Only '9 P.3d 655' found, '59 P.3d 655' missing")
            elif correct_found and not phantom_found:
                print("✅ CORRECT ONLY: Only '59 P.3d 655' found, no phantom")
            
            # Show all P.3d citations for analysis
            print("\nALL P.3d CITATIONS FOUND:")
            p3d_citations = []
            for citation in citations:
                citation_text = citation.get('citation', 'N/A')
                if 'P.3d' in citation_text:
                    p3d_citations.append(citation_text)
                    case_name = citation.get('case_name', 'N/A')
                    print(f"  {citation_text} - {case_name}")
            
            print(f"\nTotal P.3d citations: {len(p3d_citations)}")
            
            # Check if the issue is in the text itself
            print(f"\nTEXT VERIFICATION:")
            print(f"Text contains '59 P.3d 655': {'59 P.3d 655' in full_text}")
            print(f"Text contains '9 P.3d 655': {'9 P.3d 655' in full_text}")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_full_document_bug()
