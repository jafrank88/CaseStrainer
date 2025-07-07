#!/usr/bin/env python3
"""
Test script to run a complex document through the main pipeline
"""

import requests
import json
import time

def test_complex_document():
    """Test the main pipeline with a complex document containing multiple citations"""
    
    # Complex document with multiple citations
    complex_text = """
    For the reasons explained below, we affirm the Court of Appeals in part and hold that the order sealing the Disclosure Document was an abuse of discretion because the trial court's findings are not sufficient to satisfy GR 15 or Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982). For similar reasons, the trial court abused its discretion in allowing the Does to remain in pseudonym, and we hold the pseudonym issue is not moot. Given our resolution of these issues, we decline to reach the evidentiary challenges raised in Zink's cross petition for review. We remand to the trial court with instructions to (1) unseal the Disclosure Document, (2) use the Does' actual names in future proceedings and court records (if any) pertaining to this case, and (3) order that the pseudonyms in the Superior Court Management Information System (SCOMIS) indices be replaced with the Does' actual names.

    Following John Doe A, the Court of Appeals here reversed in part and held "that the registration records must be released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished).

    While the petition for review was pending, this court decided John Doe G v. Department of Corrections, which rejected a PRA exemption claim for SSOSA evaluations that the Does had also raised in this case. 190 Wn.2d 185, 410 P.3d 1156 (2018). John Doe G further held, contrary to the trial court in this case, "that names in pleadings are subject to article I, section 10" and that an order to proceed in pseudonym "must meet the Ishikawa factors," as well as GR 15. Id. at 201.

    Following John Doe G, the Court of Appeals reversed the order allowing the Does to proceed in pseudonym and rejected all but one of the Does' PRA exemption claims. Doe II, No. 48000-0-II, slip op. at 11. However, the court held that "unredacted SSOSA evaluations are exempt from disclosure under the PRA." Id. at 12.

    The trial court's findings are insufficient to justify the continued use of pseudonyms and sealing of the Disclosure Document following dismissal of the Does' action. Therefore, the trial court abused its discretion contrary to GR 15.

    GR 15 is a court rule, but it derives from the principles of Ishikawa and article I, section 10's "'separate, clear and specific provision [that] entitles the public . . . to openly administered justice.'" Ishikawa, 97 Wn.2d at 36 (quoting Cohen v. Everett City Council, 85 Wn.2d 385, 388, 535 P.2d 801 (1975)).

    Therefore, in addition to complying with GR 15, an order permitting a party to proceed in pseudonym must satisfy the Ishikawa factors:
    (1) identify the need to seal court records, (2) allow anyone present in the courtroom an opportunity to object, (3) determine whether the requested method is the least restrictive means of protecting the interests threatened, (4) weigh the competing interests and consider alternative methods, and (5) issue an order no broader than necessary.

    John Doe G, 190 Wn.2d at 199 (citing Ishikawa, 97 Wn.2d at 37-39). Each Ishikawa factor "'should be articulated in [the court's] findings and conclusions, which should be as specific as possible rather than conclusory.'" Id. at 202 (alteration in original) (quoting Ishikawa, 97 Wn.2d at 38).

    The first Ishikawa factor requires a showing that public access to the Does' identities in connection with this action "must be restricted to prevent a serious and imminent threat to an important interest." 97 Wn.2d at 37. This "'is more specific, concrete, certain, and definite than' the 'compelling privacy or safety concerns' required by GR 15(c)(2)." M.H.P., 184 Wn.2d at 765 (quoting State v. Waldon, 148 Wn. App. 952, 962-63, 202 P.3d 325 (2009)).

    It has long been established that Washington courts are constitutionally prohibited from restricting the public's access to court records, absent "a serious and imminent threat to an important interest," which must be articulated "as specifically as possible." Ishikawa, 97 Wn.2d at 37; see also Encarnación, 181 Wn.2d at 9. Here, the Does "do not have a legitimate privacy interest to protect" in their identities as sex offenders or as litigants. John Doe G, 190 Wn.2d at 200.

    Before entering its order, the trial court offered those present in the courtroom an opportunity to object, satisfying the second Ishikawa factor. 97 Wn.2d at 38. The trial court also addressed the third and fourth Ishikawa factors, and ruled that allowing the Does to remain in pseudonym and sealing the Disclosure Document would be "the least restrictive means" and the only "viable alternative" that would be "effective in protecting the interests threatened." CP at 432; Ishikawa, 97 Wn.2d at 38.

    Finally, the fifth Ishikawa factor requires that any order "'must be no broader in its application or duration than necessary to serve its purpose.'" Ishikawa, 97 Wn.2d at 39 (quoting Federated Publ'ns v. Kurtz, 94 Wn.2d 51, 64, 615 P.2d 440 (1980)). "If the order involves sealing of records, it shall apply for a specific time period with a burden on the proponent to come before the court at a time specified to justify continued sealing." Id. As we have previously recognized, "[t]his factor requires the trial court to consider durational limits" on orders to continue sealing "presumptively open" court records, such as the order permitting pseudonymous litigation in this case. Richardson, 177 Wn.2d at 362, 360.

    We affirm the Court of Appeals in holding that the trial court abused its discretion by sealing the Disclosure Document because its findings are insufficient to satisfy GR 15. We further hold that the order allowing the Does to remain in pseudonym is not moot and was also an abuse of discretion contrary to GR 15. In addition, we hold that the trial court abused its discretion in ruling that the Ishikawa factors had been satisfied as to both the use of pseudonyms and the sealing of the Disclosure Document. Given our resolution of these issues, we decline to reach the evidentiary issues raised in Zink's cross petition for review.

    Thus, we affirm the Court of Appeals in part, reverse in part, and remand to the trial court with instructions to (1) unseal the Disclosure Document, (2) use the Does' actual names in future proceedings and court records (if any) pertaining to this case, and (3) order that the Does' pseudonyms in the SCOMIS indices be replaced with their actual names.
    """
    
    print("Testing complex document with multiple citations...")
    print(f"Document length: {len(complex_text)} characters")
    
    # Test the analyze endpoint
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    try:
        print("\n1. Submitting document to analyze endpoint...")
        response = requests.post(url, json={"text": complex_text, "source": "Test"}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received: {response.status_code}")
            
            # Check if it's an async response with task_id
            if 'task_id' in data and data.get('status') != 'completed':
                task_id = data['task_id']
                print(f"📋 Task ID: {task_id}")
                
                # Poll for completion
                print("\n2. Polling for task completion...")
                for i in range(60):  # Wait up to 60 seconds
                    time.sleep(2)
                    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        print(f"   Status: {status} (attempt {i+1}/30)")
                        
                        if status == 'completed':
                            print("✅ Processing completed!")
                            results = status_data.get('results', {})
                            analyze_results(results)
                            return results
                        elif status == 'failed':
                            print(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                            return None
                    else:
                        print(f"   Status check failed: {status_response.status_code}")
                
                print("⏰ Timeout waiting for completion")
                return None
            else:
                # Direct response (like from clean server)
                print("✅ Direct response received")
                analyze_results(data)
                return data
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def analyze_results(results):
    """Analyze and display the results"""
    print("\n" + "="*50)
    print("RESULTS ANALYSIS")
    print("="*50)
    
    # Handle different result structures
    if isinstance(results, list):
        citations = results
    else:
        citations = results.get('citations', [])
    
    print(f"📊 Total citations found: {len(citations)}")
    
    if len(citations) == 0:
        print("❌ No citations found")
        return
    
    # Count by verification status
    true_count = 0
    false_count = 0
    true_by_parallel_count = 0
    other_count = 0
    
    for citation in citations:
        verified = citation.get('verified', False)
        if verified == True:
            true_count += 1
        elif verified == False:
            false_count += 1
        elif verified == 'true_by_parallel':
            true_by_parallel_count += 1
        else:
            other_count += 1
    
    print(f"✅ Verified (True): {true_count}")
    print(f"❌ Not Verified (False): {false_count}")
    print(f"🔗 Verified by Parallel: {true_by_parallel_count}")
    print(f"❓ Other: {other_count}")
    
    # Show all citations
    print(f"\n📋 All citations found:")
    for i, citation in enumerate(citations, 1):
        case_name = citation.get('case_name', 'N/A')
        citation_text = citation.get('citation', 'N/A')
        verified = citation.get('verified', 'N/A')
        source = citation.get('source', 'N/A')
        
        print(f"  {i}. {citation_text}")
        print(f"     Case: {case_name}")
        print(f"     Verified: {verified}")
        print(f"     Source: {source}")
        print()

if __name__ == "__main__":
    test_complex_document() 