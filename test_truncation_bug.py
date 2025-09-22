#!/usr/bin/env python3

import requests
import json

def test_truncation_bug():
    """Test the truncation bug where '59 P.3d 655' becomes '9 P.3d 655'."""
    
    # Your exact text that contains the problematic citation
    test_text = '''Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).

"Where the legislature provides no statutory definition and a court gives a term its plain and ordinary meaning by reference to a dictionary, the court 'will avoid literal reading of a statute which would result in unlikely, absurd, or strained consequences.'" Tingey v. Haisch, 159 Wn.2d 652, 663-64, 152 P.3d 1020 (2007) (quoting Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002)). "[I]t will not be presumed that the legislature intended absurd results." State v. Delgado, 148 Wn.2d 723, 733, 63 P.3d 792 (2003) (Madsen, J., dissenting) (citing State v. Vela, 100 Wn.2d 636, 641, 673 P.2d 185 (1983))

Total Wine argues that plaintiffs' interpretation of "job applicant" leads to absurd consequences. "Where the legislature provides no statutory definition and a court gives a term its plain and ordinary meaning by reference to a dictionary, the court 'will avoid literal reading of a statute which would result in unlikely, absurd, or strained consequences.'" Tingey v. Haisch, 159 Wn.2d 652, 663-64, 152 P.3d 1020 (2007) (quoting Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002)). We do not presume that the legislature intends absurd results. State v. J.P., 149 Wn.2d 444, 450, 69 P.3d 318 (2003) (quoting State v. Delgado, 148 Wn.2d 723, 733, 63 P.3d 792 (2003) (Madsen, J., dissenting))'''
    
    print("TRUNCATION BUG TEST")
    print("=" * 60)
    print("Testing citation extraction with your exact text...")
    print()
    
    # Check what citations should be found
    expected_citations = [
        "183 Wn.2d 649",
        "355 P.3d 258", 
        "192 Wn.2d 453",
        "430 P.3d 655",
        "159 Wn.2d 652", 
        "152 P.3d 1020",
        "148 Wn.2d 224",
        "59 P.3d 655",  # This should be found, NOT "9 P.3d 655"
        "148 Wn.2d 723",
        "63 P.3d 792",
        "100 Wn.2d 636",
        "673 P.2d 185",
        "149 Wn.2d 444",
        "69 P.3d 318"
    ]
    
    print("EXPECTED CITATIONS IN TEXT:")
    for i, citation in enumerate(expected_citations, 1):
        in_text = citation in test_text
        print(f"{i:2d}. {citation} - {'✅ Found' if in_text else '❌ Missing'}")
    
    print(f"\nSpecial check for '59 P.3d 655': {'✅ Found' if '59 P.3d 655' in test_text else '❌ Missing'}")
    print(f"Special check for '9 P.3d 655': {'❌ Should NOT be found' if '9 P.3d 655' not in test_text else '🚨 FOUND (this is wrong!)'}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        print("Making API request...")
        response = requests.post(url, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"\nAPI RESPONSE:")
            print(f"Found {len(citations)} citations")
            print()
            
            # Check for the specific bug
            found_59_p3d = False
            found_9_p3d = False
            all_citations = []
            
            print("EXTRACTED CITATIONS:")
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                extracted_date = citation.get('extracted_date', 'N/A')
                
                all_citations.append(citation_text)
                
                # Check for the specific bug
                if citation_text == "59 P.3d 655":
                    found_59_p3d = True
                    print(f"{i:2d}. ✅ {citation_text} - CORRECT")
                elif citation_text == "9 P.3d 655":
                    found_9_p3d = True
                    print(f"{i:2d}. 🚨 {citation_text} - BUG! Should be '59 P.3d 655'")
                else:
                    print(f"{i:2d}. {citation_text}")
                
                print(f"     Case: {case_name}")
                print(f"     Extracted: {extracted_case_name} ({extracted_date})")
                print()
            
            # Analysis
            print("BUG ANALYSIS:")
            print("-" * 40)
            if found_9_p3d and not found_59_p3d:
                print("🚨 BUG CONFIRMED: '59 P.3d 655' was truncated to '9 P.3d 655'")
            elif found_59_p3d and not found_9_p3d:
                print("✅ NO BUG: '59 P.3d 655' was extracted correctly")
            elif found_59_p3d and found_9_p3d:
                print("🤔 BOTH FOUND: Both '59 P.3d 655' and '9 P.3d 655' were extracted (duplicate issue)")
            else:
                print("❓ NEITHER FOUND: '59 P.3d 655' was not extracted at all")
            
            # Check for other missing citations
            missing_citations = []
            for expected in expected_citations:
                if expected not in all_citations:
                    missing_citations.append(expected)
            
            if missing_citations:
                print(f"\nMISSING CITATIONS ({len(missing_citations)}):")
                for missing in missing_citations:
                    print(f"  ❌ {missing}")
            
            # Check for unexpected citations
            unexpected_citations = []
            for found in all_citations:
                if found not in expected_citations and found != "9 P.3d 655":  # 9 P.3d 655 is expected to be wrong
                    unexpected_citations.append(found)
            
            if unexpected_citations:
                print(f"\nUNEXPECTED CITATIONS ({len(unexpected_citations)}):")
                for unexpected in unexpected_citations:
                    print(f"  ❓ {unexpected}")
                    
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_truncation_bug()
