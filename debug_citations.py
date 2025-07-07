#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

from unified_citation_extractor import extract_citations_from_text

def debug_citation_extraction():
    # Test text with the Washington Supreme Court opinion content
    test_text = """
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
    
    print("=== DEBUGGING CITATION EXTRACTION ===")
    print(f"Text length: {len(test_text)} characters")
    
    # Extract citations directly
    citations = extract_citations_from_text(test_text)
    
    print(f"\n=== EXTRACTED CITATIONS ===")
    print(f"Total citations found: {len(citations)}")
    
    for i, citation in enumerate(citations):
        print(f"\n{i+1}. Citation: {citation}")
    
    # Manually identify expected citations
    print(f"\n=== EXPECTED CITATIONS (manual analysis) ===")
    expected_citations = [
        "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)",
        "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)",
        "John Doe G v. Department of Corrections, 190 Wn.2d 185, 410 P.3d 1156 (2018)",
        "Cohen v. Everett City Council, 85 Wn.2d 385, 388, 535 P.2d 801 (1975)",
        "State v. Waldon, 148 Wn. App. 952, 962-63, 202 P.3d 325 (2009)",
        "Federated Publ'ns v. Kurtz, 94 Wn.2d 51, 64, 615 P.2d 440 (1980)"
    ]
    
    print(f"Expected citations: {len(expected_citations)}")
    for i, citation in enumerate(expected_citations):
        print(f"{i+1}. {citation}")
    
    # Check which expected citations were found
    found_citations = [c.strip() for c in citations]
    print(f"\n=== MISSING CITATIONS ===")
    missing = []
    for expected in expected_citations:
        found = False
        for found_citation in found_citations:
            if expected.replace(" ", "").replace(",", "").replace(".", "").lower() in found_citation.replace(" ", "").replace(",", "").replace(".", "").lower():
                found = True
                break
        if not found:
            missing.append(expected)
    
    print(f"Missing citations: {len(missing)}")
    for citation in missing:
        print(f"- {citation}")

if __name__ == "__main__":
    debug_citation_extraction() 