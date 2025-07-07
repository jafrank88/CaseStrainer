#!/usr/bin/env python3
import requests
import json
import time

def test_full_pdf():
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    # Full PDF content from the Washington Supreme Court opinion
    test_text = """
    FILE IN CLERK'S OFFICE SUPREME COURT, STATE OF WASHINGTON JUNE 12, 2025

    THIS OPINION WAS FILED FOR RECORD AT 8 A.M. ON JUNE 12, 2025

    SARAH R. PENDLETON SUPREME COURT CLERK

    IN THE SUPREME COURT OF THE STATE OF WASHINGTON

    JOHN DOE P, JOHN DOE Q, JOHN DOE R, and JOHN DOE S, as individuals and on behalf of others similarly situated, Petitioners, v. THURSTON COUNTY, a municipal organization, and its departments the THURSTON COUNTY PROSECUTING ATTORNEY and THURSTON COUNTY SHERIFF, Respondents, DONNA ZINK and JEFF ZINK, a married couple, Respondents/Cross Petitioners.

    No. 102976-4 En Banc Filed: June 12, 2025

    YU, J. — This case involves a postdismissal challenge to a trial court's order permanently sealing the petitioners' actual names and allowing them to be identified by pseudonym in court records. The underlying case is a PRA1 injunction action, in which the petitioners (John Does P, Q, R, and S) sought to enjoin Thurston County (County) from releasing unredacted sex offender records in response to cross petitioner Donna Zink's PRA request.

    Over the course of these proceedings, nearly all of the Does' PRA exemption claims have been rejected on the merits, and Zink received most of the records she requested. The Does ultimately moved for voluntary dismissal but sought to do so without revealing their identities. The trial court granted the Does' motion and entered a permanent order to (1) maintain the use of pseudonyms in court records pertaining to this case and (2) seal a court record (Disclosure Document) listing the Does' actual names. As a result, the Does have never been publicly identified, by name, as the plaintiffs in this case.

    For the reasons explained below, we affirm the Court of Appeals in part and hold that the order sealing the Disclosure Document was an abuse of discretion because the trial court's findings are not sufficient to satisfy GR 15 or Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982). For similar reasons, the trial court abused its discretion in allowing the Does to remain in pseudonym, and we hold the pseudonym issue is not moot. Given our resolution of these issues, we decline to reach the evidentiary challenges raised in Zink's cross petition for review. We remand to the trial court with instructions to (1) unseal the Disclosure Document, (2) use the Does' actual names in future proceedings and court records (if any) pertaining to this case, and (3) order that the pseudonyms in the Superior Court Management Information System (SCOMIS) indices be replaced with the Does' actual names.

    FACTUAL AND PROCEDURAL BACKGROUND

    This case has a lengthy procedural history, including multiple appeals. It is not necessary to review this history in detail, but a brief overview provides important context for the issues presented.

    A. The Does bring a PRA injunction action in pseudonym and obtain a permanent injunction on summary judgment

    In October 2014, Zink made a PRA request for Thurston County's sex offender records, including any lists or databases, registration records, victim impact statements, and evaluations for special sex offender sentencing alternatives (SSOSAs) and special sex offender disposition alternatives (SSODAs). See RCW 9.94A.670; RCW 13.40.162.

    The County notified the sex offenders named in the records, including the Does, and began preparing its response to Zink's PRA request. The Does are level I sex offenders.2 Does P and Q were convicted of sex offenses as adults; Does R and S were adjudicated as juveniles. Does P and S both attest they are compliant with their registration requirements, and Does R and Q have been relieved of the duty to register.

    In January 2015, the Does filed this action seeking to permanently enjoin the release of unredacted sex offender records in response to Zink's PRA request. The Does asserted several claims of exemption based on statutes outside the PRA governing the dissemination of sex offender records, health care information, and juvenile records. The Does subsequently moved for a preliminary injunction and for permission to proceed in pseudonym. In support, they filed declarations detailing the anticipated harms of being publicly identified as sex offenders, as well as several trial court orders granting similar relief in other cases.

    The trial court granted the Does' motion to remain in pseudonym "throughout the pendency of this action." Clerk's Papers (CP) at 25. The court reasoned that pseudonyms were necessary to preserve the Does' ability to obtain relief, should they ultimately succeed in their PRA injunction action. However, the trial court did not conduct an Ishikawa analysis in accordance with article I, section 10 of the Washington Constitution.3 Instead, the court adopted the Does' argument that article I, section 10 is "not triggered" by pseudonymous litigation. Id. at 748.

    The parties subsequently filed cross motions for summary judgment. The trial court ruled in favor of the Does on all of their PRA exemption claims and found that the Does had "credibly attest[ed] to the substantial and irreparable harm to class members if the requested documents were disclosed without redactions." Id. at 32. Based on these rulings, the trial court granted the Does' motion for summary judgment and permanently enjoined the County from releasing unredacted records in response to Zink's PRA request.

    B. Nearly all of the Does' PRA exemption claims are rejected, but the Does are granted permission to remain in pseudonym

    This action has been the subject of multiple appeals. Over the course of appellate proceedings, nearly all of the Does' PRA exemption claims have been rejected on the merits.

    Zink filed her first appeal after the trial court granted summary judgment to the Does. While the appeal was pending, this court decided John Doe A v. Washington State Patrol, which rejected a PRA exemption claim for sex offender registration records that was materially identical to one of the Does' claims in this case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court of Appeals here reversed in part and held "that the registration records must be released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished).

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

    WE CONCUR: Johnson, J. Madsen, J. González, J. Hach Mclal, 1 Gordon McCloud, J. Montaya-Lewis, J. Whitener, J.
    """
    
    print("=== TESTING FULL PDF CONTENT ===")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        # Make the API request
        response = requests.post(url, json={"text": test_text}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"Task ID: {task_id}")
            
            # Wait for processing to complete
            print("Waiting for processing to complete...")
            for i in range(60):  # Wait up to 60 seconds
                time.sleep(1)
                status_response = requests.get(f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('status') == 'completed':
                        print("Processing completed!")
                        results = status_data.get('results', {})
                        
                        # Handle different result structures
                        if isinstance(results, list):
                            citations = results
                        else:
                            citations = results.get('citations', [])
                        
                        print(f"\n=== BASELINE RESULTS ===")
                        print(f"Total citations found: {len(citations)}")
                        
                        # Count verification statuses
                        true_count = 0
                        false_count = 0
                        true_by_parallel_count = 0
                        
                        for citation in citations:
                            verified = citation.get('verified', False)
                            if verified == True:
                                true_count += 1
                            elif verified == False:
                                false_count += 1
                            elif verified == 'true_by_parallel':
                                true_by_parallel_count += 1
                        
                        print(f"True: {true_count}")
                        print(f"False: {false_count}")
                        print(f"True by parallel: {true_by_parallel_count}")
                        
                        # Show all citations with details
                        print(f"\n=== ALL CITATIONS ===")
                        for i, citation in enumerate(citations):
                            print(f"{i+1}. Citation: {citation.get('citation', 'N/A')}")
                            print(f"   Case Name: {citation.get('case_name', 'N/A')}")
                            print(f"   Verified: {citation.get('verified', 'N/A')}")
                            print(f"   Context: {citation.get('context', 'N/A')[:100]}...")
                            print("---")
                        
                        return results
                    elif status_data.get('status') == 'failed':
                        print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                        return None
                    else:
                        print(f"Status: {status_data.get('status', 'Unknown')}")
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_full_pdf() 